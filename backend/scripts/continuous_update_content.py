#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续更新技能完整内容 - 支持断点续传

特性:
1. 自动跳过已更新的 skills（content > min_length）
2. 进度保存，中断后可继续
3. 详细日志记录
4. 适合长时间后台运行

使用方法:
1. python scripts/continuous_update_content.py  # 开始或继续更新
2. nohup python scripts/continuous_update_content.py > update.log 2>&1 &  # 后台运行
"""
import asyncio
import sys
from pathlib import Path
import aiohttp
import logging
import json
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.database import get_session, SkillRepository

# 配置日志
log_file = Path(__file__).parent.parent / "logs" / f"content_update_{datetime.now().strftime('%Y%m%d')}.log"
log_file.parent.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 进度文件
PROGRESS_FILE = Path(__file__).parent.parent / "logs" / "content_update_progress.json"


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.data = self.load()

    def load(self):
        """加载进度"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_new()
        return self.create_new()

    def create_new(self):
        """创建新进度"""
        return {
            'started_at': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat(),
            'processed_ids': [],
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'failed_ids': []
        }

    def save(self):
        """保存进度"""
        self.data['last_update'] = datetime.now().isoformat()
        self.progress_file.parent.mkdir(exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_processed(self, skill_id: int) -> bool:
        """检查是否已处理"""
        return skill_id in self.data['processed_ids']

    def mark_success(self, skill_id: int):
        """标记成功"""
        if skill_id not in self.data['processed_ids']:
            self.data['processed_ids'].append(skill_id)
        self.data['success_count'] += 1
        if skill_id in self.data['failed_ids']:
            self.data['failed_ids'].remove(skill_id)
        self.save()

    def mark_failed(self, skill_id: int):
        """标记失败"""
        if skill_id not in self.data['processed_ids']:
            self.data['processed_ids'].append(skill_id)
        if skill_id not in self.data['failed_ids']:
            self.data['failed_ids'].append(skill_id)
        self.data['failed_count'] += 1
        self.save()

    def mark_skipped(self, skill_id: int):
        """标记跳过"""
        if skill_id not in self.data['processed_ids']:
            self.data['processed_ids'].append(skill_id)
        self.data['skipped_count'] += 1
        self.save()


async def fetch_skill_content_from_github(github_url: str) -> str:
    """从 GitHub 获取 SKILL.md 完整内容"""
    if not github_url or 'github.com' not in github_url:
        return ''

    try:
        if '/tree/' in github_url:
            parts = github_url.split('/tree/')
            if len(parts) == 2:
                base_url = parts[0]
                branch_and_path = parts[1]

                path_parts = branch_and_path.split('/', 1)
                if len(path_parts) == 2:
                    branch = path_parts[0]
                    path = path_parts[1]

                    base_parts = base_url.replace('https://github.com/', '').split('/')
                    if len(base_parts) >= 2:
                        owner = base_parts[0]
                        repo = base_parts[1]

                        raw_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}/SKILL.md'

                        timeout = aiohttp.ClientTimeout(total=30)
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.get(raw_url) as response:
                                if response.status == 200:
                                    content = await response.text()
                                    return content
                                elif response.status == 404:
                                    logger.debug(f"  404: SKILL.md 不存在")
                                    return ''
                                else:
                                    logger.warning(f"  HTTP {response.status}")
                                    return ''

        return ''

    except asyncio.TimeoutError:
        logger.error(f"  超时: {github_url}")
        return ''
    except Exception as e:
        logger.error(f"  获取出错: {e}")
        return ''


async def continuous_update(
    min_length: int = 300,
    batch_size: int = 50,
    delay_between_requests: float = 1.0
):
    """
    持续更新技能内容

    Args:
        min_length: content 长度小于此值才更新（默认 300）
        batch_size: 每批处理数量
        delay_between_requests: 请求间隔（秒）
    """
    logger.info("=" * 60)
    logger.info("开始持续更新技能内容")
    logger.info("=" * 60)

    tracker = ProgressTracker(PROGRESS_FILE)

    logger.info(f"\n进度统计:")
    logger.info(f"  开始时间: {tracker.data['started_at']}")
    logger.info(f"  上次更新: {tracker.data['last_update']}")
    logger.info(f"  已处理: {len(tracker.data['processed_ids'])} 个")
    logger.info(f"  成功: {tracker.data['success_count']}")
    logger.info(f"  失败: {tracker.data['failed_count']}")
    logger.info(f"  跳过: {tracker.data['skipped_count']}")
    logger.info("")

    async with get_session() as session:
        repo = SkillRepository(session)

        # 查询需要更新的技能
        query = text(f"""
            SELECT id, name, github_url, LENGTH(content) as content_len
            FROM skills
            WHERE LENGTH(content) < {min_length}
            AND github_url != ''
            AND github_url LIKE '%github.com%'
            ORDER BY stars DESC, id ASC
        """)

        result = await session.execute(query)
        all_skills = result.fetchall()

        # 过滤掉已处理的
        skills_to_process = [
            s for s in all_skills
            if not tracker.is_processed(s.id)
        ]

        total = len(skills_to_process)
        already_done = len(all_skills) - total

        logger.info(f"待更新技能统计:")
        logger.info(f"  总计需要更新: {len(all_skills)} 个（content < {min_length}）")
        logger.info(f"  已完成: {already_done} 个")
        logger.info(f"  本次处理: {total} 个")
        logger.info("")

        if total == 0:
            logger.info("✅ 所有技能内容已更新完成！")
            return

        # 分批处理
        start_time = time.time()
        current_batch = 0

        for i, skill in enumerate(skills_to_process, 1):
            try:
                logger.info(f"[{i}/{total}] ID:{skill.id} {skill.name}")
                logger.info(f"  当前长度: {skill.content_len} 字符")
                logger.info(f"  GitHub: {skill.github_url[:80]}...")

                # 获取完整内容
                content = await fetch_skill_content_from_github(skill.github_url)

                if content and len(content) > skill.content_len:
                    # 更新数据库
                    await repo.update(skill.id, {'content': content})
                    await session.commit()

                    tracker.mark_success(skill.id)
                    logger.info(f"  ✅ 成功: {skill.content_len} → {len(content)} 字符")

                elif content and len(content) <= skill.content_len:
                    tracker.mark_skipped(skill.id)
                    logger.info(f"  ⏭️ 跳过: 新内容不够长")

                else:
                    tracker.mark_failed(skill.id)
                    logger.warning(f"  ❌ 失败: 无法获取内容")

                # 间隔延迟
                await asyncio.sleep(delay_between_requests)

                # 每 batch_size 个输出进度
                current_batch += 1
                if current_batch >= batch_size:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / i
                    remaining = (total - i) * avg_time

                    logger.info("")
                    logger.info("=" * 60)
                    logger.info(f"进度: {i}/{total} ({i/total*100:.1f}%)")
                    logger.info(f"成功: {tracker.data['success_count']}")
                    logger.info(f"失败: {tracker.data['failed_count']}")
                    logger.info(f"跳过: {tracker.data['skipped_count']}")
                    logger.info(f"耗时: {elapsed/60:.1f} 分钟")
                    logger.info(f"预计剩余: {remaining/60:.1f} 分钟")
                    logger.info("=" * 60)
                    logger.info("")

                    current_batch = 0

            except Exception as e:
                logger.error(f"  ❌ 异常: {e}")
                tracker.mark_failed(skill.id)
                continue

        # 最终统计
        total_time = time.time() - start_time
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ 更新完成！")
        logger.info("=" * 60)
        logger.info(f"总计处理: {total} 个")
        logger.info(f"成功: {tracker.data['success_count']}")
        logger.info(f"失败: {tracker.data['failed_count']}")
        logger.info(f"跳过: {tracker.data['skipped_count']}")
        logger.info(f"总耗时: {total_time/60:.1f} 分钟")
        logger.info("")

        if tracker.data['failed_ids']:
            logger.info(f"失败的 Skill IDs: {tracker.data['failed_ids'][:20]}...")


async def main():
    try:
        await continuous_update(
            min_length=300,
            batch_size=50,
            delay_between_requests=1.0
        )
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ 用户中断，进度已保存，下次运行将继续")
    except Exception as e:
        logger.error(f"\n\n❌ 程序异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

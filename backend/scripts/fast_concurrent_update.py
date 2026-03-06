#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速并发更新 skill_md - 使用异步并发提高速度

性能优化：
1. 使用 asyncio.gather 并发处理多个请求
2. 并发数量：可配置（建议 10-20）
3. 超时时间：15 秒
4. 批量数据库更新
5. GitHub Token 认证（提高限流阈值）
"""
import asyncio
import sys
from pathlib import Path
import aiohttp
import logging
import json
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.database import get_session, SkillRepository

# 配置日志
log_file = Path(__file__).parent.parent / "logs" / f"fast_update_{datetime.now().strftime('%Y%m%d')}.log"
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

PROGRESS_FILE = Path(__file__).parent.parent / "logs" / "fast_update_progress.json"

# 并发配置（定时任务优化版）
CONCURRENT_TASKS = 5   # 同时执行的任务数（稳定运行）
TIMEOUT_SECONDS = 20   # 每个请求的超时时间（增加容错）
BATCH_SIZE = 100       # 批量保存的大小
DELAY_BETWEEN_BATCHES = 2  # 每批之间的延迟（秒，避免限流）

# GitHub Token（从环境变量读取）
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  # 可选，但强烈建议配置


class ProgressTracker:
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.data = self.load()
        self.lock = asyncio.Lock()

    def load(self):
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_new()
        return self.create_new()

    def create_new(self):
        return {
            'started_at': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat(),
            'processed_ids': [],
            'success_count': 0,
            'failed_count': 0,
            'skipped_count': 0,
            'failed_ids': []
        }

    async def save(self):
        async with self.lock:
            self.data['last_update'] = datetime.now().isoformat()
            self.progress_file.parent.mkdir(exist_ok=True)
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_processed(self, skill_id: int) -> bool:
        return skill_id in self.data['processed_ids']

    async def mark_success(self, skill_id: int):
        async with self.lock:
            if skill_id not in self.data['processed_ids']:
                self.data['processed_ids'].append(skill_id)
            self.data['success_count'] += 1
            if skill_id in self.data['failed_ids']:
                self.data['failed_ids'].remove(skill_id)

    async def mark_failed(self, skill_id: int):
        async with self.lock:
            if skill_id not in self.data['processed_ids']:
                self.data['processed_ids'].append(skill_id)
            if skill_id not in self.data['failed_ids']:
                self.data['failed_ids'].append(skill_id)
            self.data['failed_count'] += 1

    async def mark_skipped(self, skill_id: int):
        async with self.lock:
            if skill_id not in self.data['processed_ids']:
                self.data['processed_ids'].append(skill_id)
            self.data['skipped_count'] += 1


async def fetch_skill_content(session: aiohttp.ClientSession, github_url: str) -> tuple[str, str]:
    """
    从 GitHub 获取 SKILL.md 内容（支持 Token 认证）

    Returns:
        tuple[str, str]: (content, error_message)
    """
    if not github_url or 'github.com' not in github_url:
        return '', 'invalid_url'

    try:
        if '/tree/' not in github_url:
            return '', 'no_tree_in_url'

        parts = github_url.split('/tree/')
        if len(parts) != 2:
            return '', 'parse_error'

        base_url = parts[0]
        branch_and_path = parts[1]
        path_parts = branch_and_path.split('/', 1)

        if len(path_parts) != 2:
            return '', 'parse_error'

        branch = path_parts[0]
        path = path_parts[1]
        base_parts = base_url.replace('https://github.com/', '').split('/')

        if len(base_parts) < 2:
            return '', 'parse_error'

        owner = base_parts[0]
        repo = base_parts[1]
        raw_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}/SKILL.md'

        # 构建请求头（如果有 Token 则添加认证）
        headers = {}
        if GITHUB_TOKEN:
            headers['Authorization'] = f'token {GITHUB_TOKEN}'

        async with session.get(raw_url, headers=headers) as response:
            if response.status == 200:
                content = await response.text()
                return content, ''
            elif response.status == 404:
                return '', 'file_not_found'
            elif response.status == 403:
                return '', 'rate_limited'
            else:
                return '', f'http_{response.status}'

    except asyncio.TimeoutError:
        return '', 'timeout'
    except aiohttp.ClientError as e:
        return '', f'network_error'
    except Exception as e:
        return '', f'unknown_error'


async def process_skill(skill, session: aiohttp.ClientSession, tracker: ProgressTracker):
    """处理单个技能"""
    try:
        content, error = await fetch_skill_content(session, skill.github_url)

        if content and len(content) > 0:
            await tracker.mark_success(skill.id)
            return {
                'id': skill.id,
                'name': skill.name,
                'content': content,
                'status': 'success'
            }
        else:
            await tracker.mark_failed(skill.id)
            return {
                'id': skill.id,
                'name': skill.name,
                'error': error,
                'status': 'failed'
            }
    except Exception as e:
        await tracker.mark_failed(skill.id)
        return {
            'id': skill.id,
            'name': skill.name,
            'error': str(e),
            'status': 'failed'
        }


async def batch_update_db(results: list, session):
    """批量更新数据库"""
    repo = SkillRepository(session)
    success_count = 0

    for result in results:
        if result['status'] == 'success':
            try:
                await repo.update(result['id'], {'skill_md': result['content']})
                success_count += 1
            except Exception as e:
                logger.error(f"  数据库更新失败 ID:{result['id']} {e}")

    await session.commit()
    return success_count


async def fast_concurrent_update():
    """快速并发更新"""
    logger.info("=" * 60)
    logger.info(f"快速并发更新 - 并发数: {CONCURRENT_TASKS}")
    if GITHUB_TOKEN:
        logger.info("✅ GitHub Token 已配置（限流: 5000/小时）")
    else:
        logger.warning("⚠️ 未配置 GitHub Token（限流: 60/小时）")
    logger.info("=" * 60)

    tracker = ProgressTracker(PROGRESS_FILE)

    logger.info(f"\n进度统计:")
    logger.info(f"  已处理: {len(tracker.data['processed_ids'])} 个")
    logger.info(f"  成功: {tracker.data['success_count']}")
    logger.info(f"  失败: {tracker.data['failed_count']}")

    async with get_session() as db_session:
        repo = SkillRepository(db_session)

        # 查询需要处理的技能
        query = text(f"""
            SELECT id, name, github_url
            FROM skills
            WHERE (skill_md IS NULL OR skill_md = '')
            AND github_url != ''
            AND github_url LIKE '%github.com%'
            ORDER BY stars DESC, id ASC
        """)

        result = await db_session.execute(query)
        all_skills = result.fetchall()

        # 过滤已处理的
        skills_to_process = [s for s in all_skills if not tracker.is_processed(s.id)]
        total = len(skills_to_process)

        logger.info(f"\n本次处理: {total} 个\n")

        if total == 0:
            logger.info("✅ 所有技能已更新完成！")
            return

        start_time = time.time()
        processed = 0

        # 创建 aiohttp session（设置超时）
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
        async with aiohttp.ClientSession(timeout=timeout) as http_session:

            # 分批处理
            for i in range(0, total, CONCURRENT_TASKS):
                batch = skills_to_process[i:i + CONCURRENT_TASKS]

                # 并发处理一批任务
                tasks = [process_skill(skill, http_session, tracker) for skill in batch]
                results = await asyncio.gather(*tasks)

                # 批量更新数据库
                db_updated = await batch_update_db(results, db_session)

                # 保存进度
                await tracker.save()

                processed += len(batch)

                # 统计本批次结果
                success = sum(1 for r in results if r['status'] == 'success')
                failed = sum(1 for r in results if r['status'] == 'failed')

                # 输出进度
                elapsed = time.time() - start_time
                speed = processed / elapsed if elapsed > 0 else 0
                remaining = (total - processed) / speed if speed > 0 else 0

                logger.info(f"[{processed}/{total}] 本批: ✅{success} ❌{failed} | "
                           f"速度: {speed:.1f}/s | 剩余: {int(remaining/60)}分{int(remaining%60)}秒")

                # 每 BATCH_SIZE 个输出详细统计
                if processed % BATCH_SIZE == 0:
                    logger.info(f"\n=== 进度检查点 {processed}/{total} ===")
                    logger.info(f"总成功: {tracker.data['success_count']}")
                    logger.info(f"总失败: {tracker.data['failed_count']}")
                    logger.info(f"平均速度: {speed:.1f} 个/秒")
                    logger.info(f"预计完成时间: {int(remaining/60)} 分钟\n")

                # 添加批次间延迟，避免限流
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        total_time = time.time() - start_time
        logger.info(f"\n✅ 更新完成！")
        logger.info(f"总耗时: {int(total_time/60)} 分 {int(total_time%60)} 秒")
        logger.info(f"平均速度: {total/total_time:.1f} 个/秒")
        logger.info(f"成功: {tracker.data['success_count']}")
        logger.info(f"失败: {tracker.data['failed_count']}")


async def main():
    try:
        await fast_concurrent_update()
    except KeyboardInterrupt:
        logger.info("\n中断，进度已保存")
    except Exception as e:
        logger.error(f"\n异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

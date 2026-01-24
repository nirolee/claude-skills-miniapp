#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续更新技能完整内容 - 支持断点续传
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

PROGRESS_FILE = Path(__file__).parent.parent / "logs" / "content_update_progress.json"

class ProgressTracker:
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.data = self.load()

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

    def save(self):
        self.data['last_update'] = datetime.now().isoformat()
        self.progress_file.parent.mkdir(exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_processed(self, skill_id: int) -> bool:
        return skill_id in self.data['processed_ids']

    def mark_success(self, skill_id: int):
        if skill_id not in self.data['processed_ids']:
            self.data['processed_ids'].append(skill_id)
        self.data['success_count'] += 1
        if skill_id in self.data['failed_ids']:
            self.data['failed_ids'].remove(skill_id)
        self.save()

    def mark_failed(self, skill_id: int):
        if skill_id not in self.data['processed_ids']:
            self.data['processed_ids'].append(skill_id)
        if skill_id not in self.data['failed_ids']:
            self.data['failed_ids'].append(skill_id)
        self.data['failed_count'] += 1
        self.save()

    def mark_skipped(self, skill_id: int):
        if skill_id not in self.data['processed_ids']:
            self.data['processed_ids'].append(skill_id)
        self.data['skipped_count'] += 1
        self.save()

async def fetch_skill_content_from_github(github_url: str) -> str:
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
        return ''
    except:
        return ''

async def continuous_update(min_length: int = 300, batch_size: int = 50, delay_between_requests: float = 1.0):
    logger.info("=" * 60)
    logger.info("开始持续更新技能内容")
    logger.info("=" * 60)

    tracker = ProgressTracker(PROGRESS_FILE)

    logger.info(f"\n进度统计:")
    logger.info(f"  已处理: {len(tracker.data['processed_ids'])} 个")
    logger.info(f"  成功: {tracker.data['success_count']}")
    logger.info(f"  失败: {tracker.data['failed_count']}")
    logger.info(f"  跳过: {tracker.data['skipped_count']}")

    async with get_session() as session:
        repo = SkillRepository(session)

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

        skills_to_process = [s for s in all_skills if not tracker.is_processed(s.id)]

        total = len(skills_to_process)
        logger.info(f"\n本次处理: {total} 个")

        if total == 0:
            logger.info("✅ 所有技能内容已更新完成！")
            return

        start_time = time.time()

        for i, skill in enumerate(skills_to_process, 1):
            try:
                logger.info(f"[{i}/{total}] ID:{skill.id} {skill.name}")

                content = await fetch_skill_content_from_github(skill.github_url)

                if content and len(content) > skill.content_len:
                    # 保存到skill_md字段，不覆盖原有的content
                    await repo.update(skill.id, {'skill_md': content})
                    await session.commit()
                    tracker.mark_success(skill.id)
                    logger.info(f"  ✅ 成功: {skill.content_len} → {len(content)} 字符")
                elif content:
                    tracker.mark_skipped(skill.id)
                    logger.info(f"  ⏭️ 跳过")
                else:
                    tracker.mark_failed(skill.id)
                    logger.warning(f"  ❌ 失败")

                await asyncio.sleep(delay_between_requests)

                if i % batch_size == 0:
                    elapsed = time.time() - start_time
                    logger.info(f"\n进度: {i}/{total} ({i/total*100:.1f}%)")
                    logger.info(f"成功: {tracker.data['success_count']}\n")

            except Exception as e:
                logger.error(f"  ❌ 异常: {e}")
                tracker.mark_failed(skill.id)

        logger.info("\n✅ 更新完成！")

async def main():
    try:
        await continuous_update()
    except KeyboardInterrupt:
        logger.info("\n中断，进度已保存")
    except Exception as e:
        logger.error(f"\n异常: {e}")

if __name__ == "__main__":
    asyncio.run(main())

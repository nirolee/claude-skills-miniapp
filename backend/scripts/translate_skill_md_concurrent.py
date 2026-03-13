#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续翻译 skill_md 字段 - 支持并发翻译
"""
import asyncio
import sys
from pathlib import Path
import logging
import json
from datetime import datetime
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.database import get_session, SkillRepository
from src.services.ai_translation import translate_text

# 配置日志
log_file = Path(__file__).parent.parent / "logs" / f"skill_md_translation_{datetime.now().strftime('%Y%m%d')}.log"
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

PROGRESS_FILE = Path(__file__).parent.parent / "logs" / "skill_md_translation_progress.json"


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
            'failed_ids': [],
            'total_chars_translated': 0
        }

    async def save(self):
        async with self.lock:
            self.data['last_update'] = datetime.now().isoformat()
            self.progress_file.parent.mkdir(exist_ok=True)
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_processed(self, skill_id: int) -> bool:
        return skill_id in self.data['processed_ids']

    async def mark_success(self, skill_id: int, char_count: int = 0):
        async with self.lock:
            if skill_id not in self.data['processed_ids']:
                self.data['processed_ids'].append(skill_id)
            self.data['success_count'] += 1
            self.data['total_chars_translated'] += char_count
            if skill_id in self.data['failed_ids']:
                self.data['failed_ids'].remove(skill_id)
        await self.save()

    async def mark_failed(self, skill_id: int):
        async with self.lock:
            if skill_id not in self.data['processed_ids']:
                self.data['processed_ids'].append(skill_id)
            if skill_id not in self.data['failed_ids']:
                self.data['failed_ids'].append(skill_id)
            self.data['failed_count'] += 1
        await self.save()


async def translate_skill_md_content(skill_md: str) -> tuple[str, str]:
    """翻译 SKILL.md 内容"""
    if not skill_md or not skill_md.strip():
        return '', 'empty_content'

    try:
        translated = await translate_text(skill_md, source_lang='en', target_lang='zh')
        if translated and len(translated) > 0:
            return translated, ''
        else:
            return '', 'translation_failed'
    except Exception as e:
        error_msg = str(e)
        if 'rate_limit' in error_msg.lower() or '429' in error_msg:
            return '', 'rate_limit'
        elif 'overloaded' in error_msg.lower() or '529' in error_msg:
            return '', 'overloaded'
        elif 'timeout' in error_msg.lower():
            return '', 'timeout'
        else:
            return '', f'{type(e).__name__}: {error_msg[:100]}'


async def translate_single_skill(skill, tracker, semaphore, skill_index, total):
    """翻译单个技能（带并发控制，使用独立 session）"""
    async with semaphore:
        try:
            logger.info(f"[{skill_index}/{total}] ID:{skill.id} {skill.name} ({skill.skill_md_len} 字符)")

            translated_content, error = await translate_skill_md_content(skill.skill_md)

            if translated_content:
                # 使用独立的 session 避免并发冲突
                async with get_session() as session:
                    repo = SkillRepository(session)
                    await repo.update(skill.id, {'skill_md_zh': translated_content})
                    await session.commit()

                await tracker.mark_success(skill.id, skill.skill_md_len)
                logger.info(f"  ✅ 成功: {skill.skill_md_len} → {len(translated_content)} 字符")
                return True, None
            else:
                await tracker.mark_failed(skill.id)
                logger.warning(f"  ❌ 失败: {error}")
                return False, error

        except Exception as e:
            logger.error(f"  ❌ 异常: {e}")
            await tracker.mark_failed(skill.id)
            return False, str(e)


async def continuous_translate(batch_size: int = 50, concurrency: int = 10):
    """
    持续翻译任务

    Args:
        batch_size: 每批处理数量
        concurrency: 并发翻译数量
    """
    logger.info("=" * 60)
    logger.info(f"开始持续翻译 skill_md 字段（并发数: {concurrency}）")
    logger.info("=" * 60)

    tracker = ProgressTracker(PROGRESS_FILE)

    logger.info(f"\n进度统计:")
    logger.info(f"  已处理: {len(tracker.data['processed_ids'])} 个")
    logger.info(f"  成功: {tracker.data['success_count']}")
    logger.info(f"  失败: {tracker.data['failed_count']}")
    logger.info(f"  累计翻译字符数: {tracker.data['total_chars_translated']:,}")

    semaphore = asyncio.Semaphore(concurrency)
    start_time = time.time()
    total_processed = 0
    offset = 0

    # 先查一次总数，仅用于显示进度
    async with get_session() as session:
        count_result = await session.execute(text("""
            SELECT COUNT(*) FROM skills
            WHERE skill_md IS NOT NULL AND skill_md != ''
            AND (skill_md_zh IS NULL OR skill_md_zh = '')
        """))
        grand_total = count_result.scalar()

    logger.info(f"\n待翻译总数: {grand_total} 个")
    if grand_total == 0:
        logger.info("✅ 所有 skill_md 已翻译完成！")
        return

    # 分页查询，每次只加载 batch_size 条，内存恒定
    while True:
        async with get_session() as session:
            result = await session.execute(text("""
                SELECT id, name, skill_md, LENGTH(skill_md) as skill_md_len
                FROM skills
                WHERE skill_md IS NOT NULL AND skill_md != ''
                AND (skill_md_zh IS NULL OR skill_md_zh = '')
                ORDER BY stars DESC, id ASC
                LIMIT :limit OFFSET :offset
            """), {"limit": batch_size, "offset": offset})
            page_skills = result.fetchall()

        if not page_skills:
            break

        # 跳过 progress_file 中已记录的（双重保险）
        batch_skills = [s for s in page_skills if not tracker.is_processed(s.id)]
        if not batch_skills:
            offset += batch_size
            continue

        logger.info(f"\n处理批次 offset={offset}: {len(batch_skills)} 个")

        tasks = [
            translate_single_skill(s, tracker, semaphore, offset + i + 1, grand_total)
            for i, s in enumerate(batch_skills)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        batch_success = sum(1 for r in results if isinstance(r, tuple) and r[0])
        batch_failed = len(results) - batch_success
        total_processed += len(batch_skills)

        elapsed = time.time() - start_time
        avg_time = elapsed / total_processed if total_processed > 0 else 0
        remaining = (grand_total - total_processed) * avg_time

        logger.info(f"批次完成: 成功 {batch_success}, 失败 {batch_failed}")
        logger.info(f"总进度: {total_processed}/{grand_total} ({total_processed/grand_total*100:.1f}%)")
        logger.info(f"成功: {tracker.data['success_count']}, 失败: {tracker.data['failed_count']}")
        logger.info(f"累计翻译: {tracker.data['total_chars_translated']:,} 字符")
        logger.info(f"预计剩余: {int(remaining/60)} 分钟")

        # 检查速率限制
        rate_limit_errors = [r for r in results if isinstance(r, tuple) and not r[0] and r[1] and 'rate_limit' in str(r[1])]
        if len(rate_limit_errors) > batch_size * 0.3:
            logger.warning(f"⏳ 速率限制，等待 60 秒...")
            await asyncio.sleep(60)

        offset += batch_size

    logger.info("\n✅ 翻译任务结束！")
    logger.info(f"成功: {tracker.data['success_count']}")
    logger.info(f"失败: {tracker.data['failed_count']}")
    logger.info(f"总计翻译字符数: {tracker.data['total_chars_translated']:,}")


async def main():
    try:
        # 默认并发数 10，可根据 API 限额调整
        await continuous_translate(batch_size=50, concurrency=10)
    except KeyboardInterrupt:
        logger.info("\n中断，进度已保存")
    except Exception as e:
        logger.error(f"\n异常: {e}")


if __name__ == "__main__":
    asyncio.run(main())

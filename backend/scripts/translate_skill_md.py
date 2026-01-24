#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持续翻译 skill_md 字段 - 支持断点续传
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

    def save(self):
        self.data['last_update'] = datetime.now().isoformat()
        self.progress_file.parent.mkdir(exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def is_processed(self, skill_id: int) -> bool:
        return skill_id in self.data['processed_ids']

    def mark_success(self, skill_id: int, char_count: int = 0):
        if skill_id not in self.data['processed_ids']:
            self.data['processed_ids'].append(skill_id)
        self.data['success_count'] += 1
        self.data['total_chars_translated'] += char_count
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


async def translate_skill_md_content(skill_md: str) -> tuple[str, str]:
    """
    翻译 SKILL.md 内容

    Returns:
        tuple[str, str]: (translated_content, error_message)
        - translated_content: 翻译后的内容，失败时为空字符串
        - error_message: 错误信息，成功时为空字符串
    """
    if not skill_md or not skill_md.strip():
        return '', 'empty_content'

    try:
        # 使用 AI 翻译服务
        translated = await translate_text(skill_md, source_lang='en', target_lang='zh')

        if translated and len(translated) > 0:
            return translated, ''
        else:
            return '', 'translation_failed'

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)

        # 识别常见错误
        if 'rate_limit' in error_msg.lower() or '429' in error_msg:
            return '', 'rate_limit'
        elif 'overloaded' in error_msg.lower() or '529' in error_msg:
            return '', 'overloaded'
        elif 'timeout' in error_msg.lower():
            return '', 'timeout'
        elif 'connection' in error_msg.lower():
            return '', 'network_error'
        else:
            return '', f'{error_type}: {error_msg[:100]}'


async def continuous_translate(batch_size: int = 20, delay_between_requests: float = 3.0):
    logger.info("=" * 60)
    logger.info("开始持续翻译 skill_md 字段")
    logger.info("=" * 60)

    tracker = ProgressTracker(PROGRESS_FILE)

    logger.info(f"\n进度统计:")
    logger.info(f"  已处理: {len(tracker.data['processed_ids'])} 个")
    logger.info(f"  成功: {tracker.data['success_count']}")
    logger.info(f"  失败: {tracker.data['failed_count']}")
    logger.info(f"  跳过: {tracker.data['skipped_count']}")
    logger.info(f"  累计翻译字符数: {tracker.data['total_chars_translated']:,}")

    async with get_session() as session:
        repo = SkillRepository(session)

        query = text("""
            SELECT id, name, skill_md, LENGTH(skill_md) as skill_md_len
            FROM skills
            WHERE skill_md IS NOT NULL
            AND skill_md != ''
            AND (skill_md_zh IS NULL OR skill_md_zh = '')
            ORDER BY stars DESC, id ASC
        """)

        result = await session.execute(query)
        all_skills = result.fetchall()

        skills_to_process = [s for s in all_skills if not tracker.is_processed(s.id)]

        total = len(skills_to_process)
        logger.info(f"\n本次处理: {total} 个")

        if total == 0:
            logger.info("✅ 所有 skill_md 已翻译完成！")
            return

        start_time = time.time()
        consecutive_errors = 0
        max_consecutive_errors = 5

        for i, skill in enumerate(skills_to_process, 1):
            try:
                logger.info(f"[{i}/{total}] ID:{skill.id} {skill.name} ({skill.skill_md_len} 字符)")

                translated_content, error = await translate_skill_md_content(skill.skill_md)

                if translated_content:
                    # 保存翻译结果到 skill_md_zh 字段
                    await repo.update(skill.id, {'skill_md_zh': translated_content})
                    await session.commit()
                    tracker.mark_success(skill.id, skill.skill_md_len)
                    consecutive_errors = 0
                    logger.info(f"  ✅ 成功: {skill.skill_md_len} → {len(translated_content)} 字符")
                else:
                    tracker.mark_failed(skill.id)
                    consecutive_errors += 1
                    logger.warning(f"  ❌ 失败: {error}")

                    # 如果是速率限制或过载，等待更长时间
                    if error == 'rate_limit':
                        logger.warning(f"  ⏳ 触发速率限制，等待 60 秒...")
                        await asyncio.sleep(60)
                        consecutive_errors = 0
                    elif error == 'overloaded':
                        logger.warning(f"  ⏳ API 过载，等待 30 秒...")
                        await asyncio.sleep(30)
                        consecutive_errors = 0

                # 检查连续错误次数
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"\n❌ 连续 {max_consecutive_errors} 次错误，暂停任务")
                    logger.error(f"请检查 API 配置和网络连接")
                    break

                # 正常延迟
                await asyncio.sleep(delay_between_requests)

                if i % batch_size == 0:
                    elapsed = time.time() - start_time
                    avg_time = elapsed / i
                    remaining = (total - i) * avg_time
                    logger.info(f"\n���度: {i}/{total} ({i/total*100:.1f}%)")
                    logger.info(f"成功: {tracker.data['success_count']}, 失败: {tracker.data['failed_count']}")
                    logger.info(f"累计翻译: {tracker.data['total_chars_translated']:,} 字符")
                    logger.info(f"预计剩余时间: {int(remaining/60)} 分钟\n")

            except Exception as e:
                logger.error(f"  ❌ 异常: {e}")
                tracker.mark_failed(skill.id)
                consecutive_errors += 1

                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"\n❌ 连续 {max_consecutive_errors} 次异常，暂停任务")
                    break

        logger.info("\n✅ 翻译任务结束！")
        logger.info(f"成功: {tracker.data['success_count']}")
        logger.info(f"失败: {tracker.data['failed_count']}")
        logger.info(f"总计翻译字符数: {tracker.data['total_chars_translated']:,}")


async def main():
    try:
        await continuous_translate()
    except KeyboardInterrupt:
        logger.info("\n中断，进度已保存")
    except Exception as e:
        logger.error(f"\n异常: {e}")


if __name__ == "__main__":
    asyncio.run(main())

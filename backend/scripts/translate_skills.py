"""
批量翻译已有技能 - 使用 Claude AI

使用方法:
1. 配置 .env 文件中的 ANTHROPIC_API_KEY
2. 运行: python scripts/translate_skills.py --limit 10 (测试)
3. 运行: python scripts/translate_skills.py (翻译全部)
"""
import asyncio
import sys
from pathlib import Path
import argparse
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.database import get_session, SkillRepository
from src.services.ai_translation import translate_skill_fields
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def translate_skills(limit: int = None, skip_translated: bool = True):
    """批量翻译技能

    Args:
        limit: 限制翻译数量（用于测试）
        skip_translated: 跳过已翻译的技能
    """
    logger.info("=== 开始批量翻译技能 ===\n")

    async with get_session() as session:
        repo = SkillRepository(session)

        # 查询需要翻译的技能
        if skip_translated:
            # 只查询未翻译的
            query = text("""
                SELECT id, name, description, content
                FROM skills
                WHERE name_zh IS NULL OR name_zh = ''
                ORDER BY stars DESC
            """)
        else:
            # 查询所有
            query = text("""
                SELECT id, name, description, content
                FROM skills
                ORDER BY stars DESC
            """)

        if limit:
            query = text(str(query) + f" LIMIT {limit}")

        result = await session.execute(query)
        skills = result.fetchall()

        total = len(skills)
        logger.info(f"找到 {total} 个需要翻译的技能\n")

        if total == 0:
            logger.info("没有需要翻译的技能")
            return

        success_count = 0
        failed_count = 0

        for i, skill in enumerate(skills, 1):
            try:
                logger.info(f"[{i}/{total}] 翻译: {skill.name}")

                # 翻译所有字段
                translations = await translate_skill_fields(
                    skill.name,
                    skill.description,
                    skill.content
                )

                # 更新数据库
                if any(translations.values()):  # 至少有一个翻译成功
                    await repo.update(skill.id, translations)
                    await session.commit()
                    success_count += 1
                    logger.info(f"  ✅ 翻译成功: {translations['name_zh']}")
                else:
                    failed_count += 1
                    logger.warning(f"  ⚠️ 翻译失败: 所有字段翻译返回空")

                # 避免请求过快（每个技能3个字段）
                if i < total:
                    await asyncio.sleep(2)

            except Exception as e:
                failed_count += 1
                logger.error(f"  ❌ 翻译失败: {e}")
                continue

        logger.info(f"\n=== 翻译完成 ===")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {failed_count}")
        logger.info(f"总计: {total}")


async def main():
    parser = argparse.ArgumentParser(description='批量翻译技能')
    parser.add_argument('--limit', type=int, help='限制翻译数量（用于测试）')
    parser.add_argument('--all', action='store_true', help='翻译所有技能（包括已翻译的）')

    args = parser.parse_args()

    await translate_skills(
        limit=args.limit,
        skip_translated=not args.all
    )


if __name__ == "__main__":
    asyncio.run(main())

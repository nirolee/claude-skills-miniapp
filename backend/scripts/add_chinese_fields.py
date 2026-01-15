"""
添加中文字段到 skills 表
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.database import get_session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def add_chinese_fields():
    """添加中文字段"""
    logger.info("=== 开始添加中文字段 ===\n")

    async with get_session() as session:
        try:
            # 检查列是否已存在
            result = await session.execute(text("""
                SELECT COUNT(*)
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = 'claude_skills'
                AND TABLE_NAME = 'skills'
                AND COLUMN_NAME = 'name_zh'
            """))
            exists = result.scalar()

            if exists > 0:
                logger.info("中文字段已存在，跳过")
                return

            # 添加 name_zh 列
            logger.info("添加 name_zh 列...")
            await session.execute(text("""
                ALTER TABLE skills
                ADD COLUMN name_zh VARCHAR(200) NULL COMMENT '中文名称'
                AFTER name
            """))

            # 添加 description_zh 列
            logger.info("添加 description_zh 列...")
            await session.execute(text("""
                ALTER TABLE skills
                ADD COLUMN description_zh TEXT NULL COMMENT '中文描述'
                AFTER description
            """))

            # 添加 content_zh 列
            logger.info("添加 content_zh 列...")
            await session.execute(text("""
                ALTER TABLE skills
                ADD COLUMN content_zh TEXT NULL COMMENT '中文内容'
                AFTER content
            """))

            await session.commit()

            logger.info("\n✅ 中文字段添加成功！")

        except Exception as e:
            logger.error(f"❌ 添加字段失败: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(add_chinese_fields())

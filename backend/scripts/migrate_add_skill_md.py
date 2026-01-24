"""
数据库迁移脚本：添加 skill_md 和 skill_md_zh 字段
用于存储完整的 SKILL.md 内容
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import get_engine
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_add_skill_md():
    """添加 skill_md 和 skill_md_zh 字段"""
    logger.info("=== 开始数据库迁移：添加 skill_md 字段 ===\n")

    engine = get_engine()

    async with engine.begin() as conn:
        # 1. 检查字段是否已存在
        logger.info("1. 检查当前表结构...")
        result = await conn.execute(text("SHOW COLUMNS FROM skills LIKE 'skill_md'"))
        if result.fetchone():
            logger.warning("   ⚠️ skill_md 字段已存在，跳过迁移")
            return

        # 2. 添加 skill_md 字段
        logger.info("\n2. 添加 skill_md 字段...")
        try:
            await conn.execute(text("""
                ALTER TABLE skills
                ADD COLUMN skill_md TEXT NULL COMMENT '完整的 SKILL.md 原文' AFTER content_zh
            """))
            logger.info("   ✅ skill_md 字段添加成功")
        except Exception as e:
            logger.error(f"   ❌ skill_md 字段添加失败: {e}")
            raise

        # 3. 添加 skill_md_zh 字段
        logger.info("\n3. 添加 skill_md_zh 字段...")
        try:
            await conn.execute(text("""
                ALTER TABLE skills
                ADD COLUMN skill_md_zh TEXT NULL COMMENT '完整的 SKILL.md 中文翻译' AFTER skill_md
            """))
            logger.info("   ✅ skill_md_zh 字段添加成功")
        except Exception as e:
            logger.error(f"   ❌ skill_md_zh 字段添加失败: {e}")
            raise

        # 4. 验证修改结果
        logger.info("\n4. 验证修改结果...")
        result = await conn.execute(text("SHOW COLUMNS FROM skills"))
        columns = [row[0] for row in result]

        if 'skill_md' in columns and 'skill_md_zh' in columns:
            logger.info("   ✅ 验证通过：新字段已成功添加")
            logger.info(f"   字段列表: {', '.join(columns)}")
        else:
            logger.warning(f"   ⚠️ 验证警告：字段可能未正确添加")

        # 5. 数据迁移（可选）：将现有的长content迁移到skill_md
        logger.info("\n5. 检查是否需要数据迁移...")
        result = await conn.execute(text("""
            SELECT COUNT(*)
            FROM skills
            WHERE CHAR_LENGTH(content) > 1000 AND skill_md IS NULL
        """))
        count = result.fetchone()[0]

        if count > 0:
            logger.info(f"   发现 {count} 条记录的 content 字段较长（>1000字符）")
            response = input(f"\n   是否将这些长内容迁移到 skill_md 字段？(yes/no): ")

            if response.lower() == 'yes':
                await conn.execute(text("""
                    UPDATE skills
                    SET skill_md = content
                    WHERE CHAR_LENGTH(content) > 1000 AND skill_md IS NULL
                """))
                logger.info(f"   ✅ 已迁移 {count} 条记录")
        else:
            logger.info("   无需数据迁移")

    await engine.dispose()
    logger.info("\n=== 迁移完成 ===")


async def rollback_skill_md():
    """回滚：删除 skill_md 和 skill_md_zh 字段"""
    logger.warning("⚠️  警告：此操作会删除 skill_md 和 skill_md_zh 字段及其数据")

    response = input("\n确认要回滚吗？(输入 'YES' 确认): ")
    if response != 'YES':
        logger.info("已取消回滚操作")
        return

    engine = get_engine()

    async with engine.begin() as conn:
        logger.info("删除 skill_md_zh 字段...")
        try:
            await conn.execute(text("ALTER TABLE skills DROP COLUMN skill_md_zh"))
            logger.info("✅ skill_md_zh 字段已删除")
        except Exception as e:
            logger.error(f"❌ 删除失败: {e}")

        logger.info("删除 skill_md 字段...")
        try:
            await conn.execute(text("ALTER TABLE skills DROP COLUMN skill_md"))
            logger.info("✅ skill_md 字段已删除")
        except Exception as e:
            logger.error(f"❌ 删除失败: {e}")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        asyncio.run(rollback_skill_md())
    else:
        asyncio.run(migrate_add_skill_md())

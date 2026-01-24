"""
数据库迁移脚本：扩展 slug 字段长度
从 VARCHAR(200) 扩展到 VARCHAR(500)
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


async def migrate_slug_length():
    """扩展 slug 字段长度"""
    logger.info("=== 开始数据库迁移：扩展 slug 字段 ===\n")

    engine = get_engine()

    async with engine.begin() as conn:
        # 1. 检查当前字段长度
        logger.info("1. 检查当前 slug 字段定义...")
        result = await conn.execute(text("SHOW COLUMNS FROM skills LIKE 'slug'"))
        row = result.fetchone()
        if row:
            logger.info(f"   当前定义: {row[1]}")

        # 2. 修改字段长度
        logger.info("\n2. 扩展 slug 字段长度到 VARCHAR(500)...")
        try:
            await conn.execute(text("""
                ALTER TABLE skills
                MODIFY COLUMN slug VARCHAR(500) NOT NULL
            """))
            logger.info("   ✅ 字段扩展成功")
        except Exception as e:
            logger.error(f"   ❌ 字段扩展失败: {e}")
            raise

        # 3. 验证修改结果
        logger.info("\n3. 验证修改结果...")
        result = await conn.execute(text("SHOW COLUMNS FROM skills LIKE 'slug'"))
        row = result.fetchone()
        if row:
            logger.info(f"   新定义: {row[1]}")
            if 'varchar(500)' in row[1].lower():
                logger.info("   ✅ 验证通过：字段已成功扩展到 VARCHAR(500)")
            else:
                logger.warning(f"   ⚠️ 验证警告：字段定义为 {row[1]}")

        # 4. 检查索引状态
        logger.info("\n4. 检查索引状态...")
        result = await conn.execute(text("SHOW INDEX FROM skills WHERE Column_name = 'slug'"))
        for row in result:
            logger.info(f"   索引: {row[2]} (唯一: {row[1] == 0})")

    await engine.dispose()
    logger.info("\n=== 迁移完成 ===")


async def rollback_slug_length():
    """回滚：缩小 slug 字段长度（仅在需要时使用）"""
    logger.warning("⚠️  警告：此操作会将 slug 字段缩小到 VARCHAR(200)")
    logger.warning("⚠️  如果数据库中有超过 200 字符的 slug，此操作会失败")

    response = input("\n确认要回滚吗？(输入 'YES' 确认): ")
    if response != 'YES':
        logger.info("已取消回滚操作")
        return

    engine = get_engine()

    async with engine.begin() as conn:
        logger.info("回滚 slug 字段长度到 VARCHAR(200)...")
        try:
            await conn.execute(text("""
                ALTER TABLE skills
                MODIFY COLUMN slug VARCHAR(200) NOT NULL
            """))
            logger.info("✅ 回滚成功")
        except Exception as e:
            logger.error(f"❌ 回滚失败: {e}")
            raise

    await engine.dispose()


async def check_long_slugs():
    """检查数据库中过长的 slug"""
    logger.info("=== 检查过长的 slug ===\n")

    engine = get_engine()

    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT
                id,
                name,
                CHAR_LENGTH(slug) as slug_length,
                slug
            FROM skills
            WHERE CHAR_LENGTH(slug) > 200
            ORDER BY slug_length DESC
            LIMIT 10
        """))

        rows = result.fetchall()

        if rows:
            logger.info(f"找到 {len(rows)} 个超长 slug (显示前10个):\n")
            for row in rows:
                logger.info(f"  ID: {row[0]}")
                logger.info(f"  名称: {row[1]}")
                logger.info(f"  Slug 长度: {row[2]}")
                logger.info(f"  Slug: {row[3][:100]}...")
                logger.info("")
        else:
            logger.info("✅ 没有超过 200 字符的 slug")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "rollback":
            asyncio.run(rollback_slug_length())
        elif command == "check":
            asyncio.run(check_long_slugs())
        else:
            print("用法:")
            print("  python migrate_slug_length.py        # 执行迁移")
            print("  python migrate_slug_length.py check  # 检查过长的slug")
            print("  python migrate_slug_length.py rollback  # 回滚迁移")
    else:
        asyncio.run(migrate_slug_length())

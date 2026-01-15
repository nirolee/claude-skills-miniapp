"""
数据库初始化脚本
创建所有表结构
"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import init_db, drop_all
from src.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main(force: bool = False):
    """
    初始化数据库

    Args:
        force: 是否强制重建（删除现有表）
    """
    try:
        settings = get_settings()
        logger.info(f"连接数据库: {settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}")

        if force:
            logger.warning("强制模式：将删除所有现有表")
            confirm = input("确认删除所有表？(yes/no): ")
            if confirm.lower() != "yes":
                logger.info("操作已取消")
                return

            await drop_all()
            logger.info("已删除所有表")

        await init_db()
        logger.info("✅ 数据库初始化成功！")

        logger.info("\n下一步:")
        logger.info("1. 运行 python scripts/import_skills.py 导入技能数据")
        logger.info("2. 运行 python src/api/main.py 启动 API 服务")

    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    asyncio.run(main(force=force))

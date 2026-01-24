"""
修复数据库中的 install_command 字段
将所有错误格式的命令更新为正确的 /skills add 格式
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select, func
from sqlalchemy.sql import text

from src.storage.database import get_session
from src.storage.models import Skill
from src.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fix_install_commands():
    """修复所有技能的安装命令"""
    settings = get_settings()

    async with get_session() as session:
        # 统计需要修复的记录数
        total_result = await session.execute(select(func.count()).select_from(Skill))
        total_count = total_result.scalar()

        wrong_result = await session.execute(
            select(func.count()).select_from(Skill).where(
                Skill.install_command.like('claude%')
            )
        )
        wrong_count = wrong_result.scalar()

        logger.info(f"总记录数: {total_count}")
        logger.info(f"需要修复的记录数: {wrong_count}")

        if wrong_count == 0:
            logger.info("所有记录已经是正确格式，无需修复")
            return {
                "total": total_count,
                "updated": 0,
                "skipped": total_count
            }

        # 使用原生 SQL 批量更新
        # 将 "claude plugin install " 替换为 "/skills add "
        # 将 "claude skill install " 替换为 "/skills add "

        logger.info("正在批量更新记录...")

        # 更新 "claude plugin install" 格式
        result1 = await session.execute(
            text("""
                UPDATE skills
                SET install_command = REPLACE(install_command, 'claude plugin install ', '/skills add ')
                WHERE install_command LIKE 'claude plugin install%'
            """)
        )

        # 更新 "claude skill install" 格式
        result2 = await session.execute(
            text("""
                UPDATE skills
                SET install_command = REPLACE(install_command, 'claude skill install ', '/skills add ')
                WHERE install_command LIKE 'claude skill install%'
            """)
        )

        updated_count = result1.rowcount + result2.rowcount

        logger.info(f"批量更新完成，共更新 {updated_count} 条记录")

        logger.info("=" * 60)
        logger.info(f"修复完成！")
        logger.info(f"总计: {total_count} 个技能")
        logger.info(f"已更新: {updated_count} 个")
        logger.info(f"已跳过: {total_count - updated_count} 个")
        logger.info("=" * 60)

        return {
            "total": total_count,
            "updated": updated_count,
            "skipped": total_count - updated_count
        }


async def main():
    """主函数"""
    try:
        result = await fix_install_commands()
        logger.info(f"修复结果: {result}")
    except Exception as e:
        logger.error(f"修复失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

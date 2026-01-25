"""
添加 install_command_windows 字段到 skills 表
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from src.storage.database import get_engine


async def add_windows_command_column():
    """添加 Windows 安装命令字段"""
    engine = get_engine()

    async with engine.begin() as conn:
        # 检查字段是否已存在
        result = await conn.execute(
            text(
                """
                SELECT COUNT(*) as count
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'skills'
                AND COLUMN_NAME = 'install_command_windows'
                """
            )
        )
        exists = result.scalar()

        if exists:
            print("✅ install_command_windows 字段已存在")
            return

        # 添加新字段
        print("正在添加 install_command_windows 字段...")
        await conn.execute(
            text(
                """
                ALTER TABLE skills
                ADD COLUMN install_command_windows TEXT NULL
                COMMENT 'Windows PowerShell 安装命令'
                AFTER install_command
                """
            )
        )
        print("✅ install_command_windows 字段添加成功")

        # 生成 Windows 命令（将 bash 命令转换为 PowerShell）
        print("\n正在为现有技能生成 Windows 安装命令...")
        await conn.execute(
            text(
                """
                UPDATE skills
                SET install_command_windows = REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(install_command, 'mkdir -p ~/', 'New-Item -Path "$env:USERPROFILE\\'),
                            'cd ~/', 'Set-Location "$env:USERPROFILE\\'),
                        '&&', ';'),
                    '; ;', ';')
                WHERE install_command_windows IS NULL
                """
            )
        )
        print("✅ Windows 安装命令生成完成")


async def main():
    print("=" * 60)
    print("添加 Windows PowerShell 安装命令字段")
    print("=" * 60)

    try:
        await add_windows_command_column()
        print("\n✅ 数据库更新完成！")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

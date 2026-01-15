"""
数据库连接测试脚本
用于诊断 MySQL 连接问题
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import get_settings
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text


async def test_connection():
    """测试数据库连接"""
    settings = get_settings()

    print("=" * 60)
    print("数据库连接配置测试")
    print("=" * 60)
    print(f"\n配置信息:")
    print(f"  数据库主机: {settings.mysql_host}")
    print(f"  数据库端口: {settings.mysql_port}")
    print(f"  数据库用户: {settings.mysql_user}")
    print(f"  数据库名称: {settings.mysql_database}")
    print(f"  字符集: {settings.mysql_charset}")
    print(f"  连接URL: {settings.database_url.replace(settings.mysql_password, '***')}")

    print(f"\n正在测试连接...")

    try:
        # 创建引擎
        engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
        )

        # 测试连接
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await conn.commit()

        print("\n✅ 数据库连接成功！")

        # 测试数据库是否存在
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{settings.mysql_database}'")
            )
            db_exists = result.fetchone() is not None

            if db_exists:
                print(f"✅ 数据库 '{settings.mysql_database}' 存在")

                # 检查表是否存在
                result = await conn.execute(
                    text(f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{settings.mysql_database}'")
                )
                tables = [row[0] for row in result.fetchall()]

                if tables:
                    print(f"✅ 找到 {len(tables)} 张表: {', '.join(tables)}")
                else:
                    print(f"⚠️  数据库存在但没有表，需要运行: python scripts/init_db.py")
            else:
                print(f"❌ 数据库 '{settings.mysql_database}' 不存在")
                print(f"   需要运行: python scripts/init_db.py")

        await engine.dispose()

        print("\n" + "=" * 60)
        print("测试完成！数据库连接正常")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ 数据库连接失败！")
        print(f"\n错误详情: {type(e).__name__}: {e}")

        print("\n可能的原因：")
        print("  1. MySQL 服务未启动")
        print("     - Windows: 在服务管理器中启动 MySQL 服务")
        print("     - 或运行: net start mysql")
        print("  2. MySQL 未安装")
        print("     - 下载安装: https://dev.mysql.com/downloads/mysql/")
        print("  3. 连接配置错误")
        print("     - 检查 .env 文件中的 MYSQL_* 配置")
        print("     - 确认用户名、密码、端口是否正确")
        print("  4. 防火墙阻止连接")
        print("     - 检查防火墙设置，允许端口 3306")

        print("\n" + "=" * 60)
        print("测试失败！请根据上述提示解决问题")
        print("=" * 60)
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(test_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n程序异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

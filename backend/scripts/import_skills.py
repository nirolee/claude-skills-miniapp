"""
导入技能数据脚本
支持从 GitHub 或 SkillsMP 抓取技能并保存到数据库
"""
import asyncio
import sys
import os
import argparse

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler.github_skill_crawler import GitHubSkillCrawler
from src.crawler.skillsmp_crawler import SkillsMPCrawler
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """运行爬虫导入技能"""
    parser = argparse.ArgumentParser(description="导入技能数据到数据库")
    parser.add_argument(
        "--source",
        choices=["github", "skillsmp"],
        default="skillsmp",
        help="数据源：github (anthropics/skills) 或 skillsmp (skillsmp.com/zh)"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=5,
        help="抓取页数（仅 skillsmp，每页12条）"
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="是否抓取详情页（更慢但数据更完整，仅 skillsmp）"
    )

    args = parser.parse_args()

    try:
        logger.info(f"开始导入技能数据（数据源: {args.source}）...")

        # 选择爬虫
        if args.source == "github":
            crawler = GitHubSkillCrawler()
            result = await crawler.run()
        else:  # skillsmp
            crawler = SkillsMPCrawler()
            result = await crawler.run(
                max_pages=args.pages,
                fetch_detail=args.detail
            )

        if result["success"]:
            logger.info(f"\n✅ 导入成功！")
            logger.info(f"  - 数据源: {args.source}")
            logger.info(f"  - 抓取技能数: {result['total_found']}")
            logger.info(f"  - 保存技能数: {result['total_saved']}")
            logger.info(f"  - 耗时: {result['duration_seconds']:.2f} 秒")

            if args.source == "skillsmp":
                logger.info(f"\n📊 统计:")
                logger.info(f"  - 抓取页数: {args.pages} 页")
                logger.info(f"  - 预计剩余: ~{52775 - result['total_found']} 个技能")
                logger.info(f"\n💡 提示:")
                logger.info(f"  - 增加页数: python scripts/import_skills.py --source skillsmp --pages 10")
                logger.info(f"  - 抓取详情: python scripts/import_skills.py --source skillsmp --detail")

            logger.info("\n下一步:")
            logger.info("运行 python src/api/main.py 启动 API 服务")

        else:
            logger.error(f"\n❌ 导入失败: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())

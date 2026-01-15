"""
爬虫部署脚本
用于在 223 服务器上运行
"""
import asyncio
import sys
import os
import logging
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler.improved_skillsmp_crawler import run_improved_crawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="运行优化的 SkillsMP 爬虫")
    parser.add_argument(
        "--pages",
        type=int,
        default=10,
        help="最多滚动页数（默认 10）"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("SkillsMP 爬虫 - 优化版")
    logger.info("=" * 60)

    try:
        # 运行爬虫
        skills = await run_improved_crawler(max_pages=args.pages)

        logger.info("\n" + "=" * 60)
        logger.info(f"✓ 完成")
        logger.info(f"  抓取: {len(skills)} 个技能")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"\n✗ 失败: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

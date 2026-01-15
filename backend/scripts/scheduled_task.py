"""
定时任务：爬取技能 + 自动翻译

执行流程：
1. 运行爬虫获取最新技能数据（幂等）
2. 自动翻译未翻译的技能（使用 Claude AI）

使用方法:
  python scripts/scheduled_task.py --translate-limit 50
"""
import asyncio
import sys
from pathlib import Path
import argparse
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.browser_api_crawler import (
    crawl_all_skills_browser,
    save_skills_to_db,
)
from scripts.translate_skills import translate_skills
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_scheduled_task(translate_limit: int = 50, skip_crawler: bool = False, skip_translation: bool = False):
    """运行定时任务

    Args:
        translate_limit: 每次最多翻译多少个技能（避免超额）
        skip_crawler: 跳过爬虫，只运行翻译
        skip_translation: 跳过翻译，只运行爬虫
    """
    start_time = datetime.now()
    logger.info("=" * 60)
    logger.info(f"定时任务开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    # 第一步：爬取技能
    if not skip_crawler:
        logger.info("\n【步骤 1/2】爬取技能数据...\n")
        try:
            skills = await crawl_all_skills_browser()

            if skills:
                logger.info(f"爬取成功，获取到 {len(skills)} 个技能")
                await save_skills_to_db(skills)
            else:
                logger.warning("未获取到任何技能")

        except Exception as e:
            logger.error(f"爬虫执行失败: {e}")
    else:
        logger.info("\n【步骤 1/2】跳过爬虫\n")

    # 第二步：翻译未翻译的技能
    if not skip_translation:
        logger.info(f"\n【步骤 2/2】翻译未翻译的技能（限制 {translate_limit} 个）...\n")
        try:
            await translate_skills(limit=translate_limit, skip_translated=True)
        except Exception as e:
            logger.error(f"翻译执行失败: {e}")
    else:
        logger.info("\n【步骤 2/2】跳过翻译\n")

    # 完成
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 60)
    logger.info(f"定时任务完成: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"总耗时: {duration:.1f} 秒")
    logger.info("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description='定时任务：爬虫 + 翻译')
    parser.add_argument(
        '--translate-limit',
        type=int,
        default=50,
        help='每次最多翻译多少个技能（默认50）'
    )
    parser.add_argument(
        '--skip-crawler',
        action='store_true',
        help='跳过爬虫，只运行翻译'
    )
    parser.add_argument(
        '--skip-translation',
        action='store_true',
        help='跳过翻译，只运行爬虫'
    )

    args = parser.parse_args()

    await run_scheduled_task(
        translate_limit=args.translate_limit,
        skip_crawler=args.skip_crawler,
        skip_translation=args.skip_translation
    )


if __name__ == "__main__":
    asyncio.run(main())

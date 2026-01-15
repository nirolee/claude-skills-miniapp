"""测试改进的爬虫"""
import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crawler.improved_skillsmp_crawler import run_improved_crawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

async def main():
    print("=" * 60)
    print("测试改进的 SkillsMP 爬虫")
    print("=" * 60)

    try:
        skills = await run_improved_crawler(max_pages=5)

        print("\n" + "=" * 60)
        print(f"✓ 测试完成")
        print(f"  抓取技能数: {len(skills)}")
        print("=" * 60)

        if skills:
            print("\n技能列表预览:")
            for i, skill in enumerate(skills[:10], 1):
                print(f"  {i}. {skill['name']} ({skill['author']}) - {skill['stars']} stars")

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

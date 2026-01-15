"""统计数据库中的技能数量"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.database import get_session, SkillRepository

async def main():
    async with get_session() as session:
        repo = SkillRepository(session)
        skills, total = await repo.list(limit=1000, offset=0)

        print(f"数据库中共有 {total} 个技能")

        # 按分类统计
        categories = {}
        for skill in skills:
            cat = skill.category or 'unknown'
            categories[cat] = categories.get(cat, 0) + 1

        print("\n分类统计:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count} 个")

if __name__ == "__main__":
    asyncio.run(main())

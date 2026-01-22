#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新现有技能的完整内容

从 GitHub 获取完整的 SKILL.md 文件内容来替换现有的简短 description

使用方法:
1. python scripts/update_skill_content.py --limit 10  # 测试更新 10 个
2. python scripts/update_skill_content.py  # 更新所有
"""
import asyncio
import sys
from pathlib import Path
import argparse
import aiohttp
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.database import get_session, SkillRepository

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fetch_skill_content_from_github(github_url: str) -> str:
    """
    从 GitHub 获取 SKILL.md 完整内容

    Args:
        github_url: GitHub 仓库 URL
        例如: https://github.com/anthropics/skills/tree/main/skills/debugging/debug-code

    Returns:
        SKILL.md 的完整内容，失败返回空字符串
    """
    if not github_url or 'github.com' not in github_url:
        return ''

    try:
        # 将 GitHub 页面 URL 转换为 raw content URL
        if '/tree/' in github_url:
            parts = github_url.split('/tree/')
            if len(parts) == 2:
                base_url = parts[0]
                branch_and_path = parts[1]

                path_parts = branch_and_path.split('/', 1)
                if len(path_parts) == 2:
                    branch = path_parts[0]
                    path = path_parts[1]

                    base_parts = base_url.replace('https://github.com/', '').split('/')
                    if len(base_parts) >= 2:
                        owner = base_parts[0]
                        repo = base_parts[1]

                        raw_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}/SKILL.md'

                        timeout = aiohttp.ClientTimeout(total=30)
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.get(raw_url) as response:
                                if response.status == 200:
                                    content = await response.text()
                                    return content
                                else:
                                    logger.warning(f"  HTTP {response.status} for {raw_url}")
                                    return ''

        return ''

    except Exception as e:
        logger.error(f"  获取出错: {e}")
        return ''


async def update_skill_contents(limit: int = None, min_length: int = 300):
    """
    批量更新技能内容

    Args:
        limit: 限制更新数量（用于测试）
        min_length: content 长度小于此值才更新（默认 300 字符）
    """
    logger.info("=== 开始更新技能内容 ===\n")

    async with get_session() as session:
        repo = SkillRepository(session)

        # 查询需要更新的技能（content 较短的）
        query = text(f"""
            SELECT id, name, github_url, LENGTH(content) as content_len
            FROM skills
            WHERE LENGTH(content) < {min_length}
            AND github_url != ''
            AND github_url LIKE '%github.com%'
            ORDER BY stars DESC
        """)

        if limit:
            query = text(str(query) + f" LIMIT {limit}")

        result = await session.execute(query)
        skills = result.fetchall()

        total = len(skills)
        logger.info(f"找到 {total} 个需要更新内容的技能（content < {min_length} 字符）\n")

        if total == 0:
            logger.info("没有需要更新的技能")
            return

        success_count = 0
        failed_count = 0
        skipped_count = 0

        for i, skill in enumerate(skills, 1):
            try:
                logger.info(f"[{i}/{total}] {skill.name}")
                logger.info(f"  当前内容长度: {skill.content_len} 字符")
                logger.info(f"  GitHub: {skill.github_url}")

                # 获取完整内容
                content = await fetch_skill_content_from_github(skill.github_url)

                if content and len(content) > skill.content_len:
                    # 更新数据库
                    await repo.update(skill.id, {'content': content})
                    await session.commit()

                    success_count += 1
                    logger.info(f"  ✅ 更新成功: {skill.content_len} → {len(content)} 字符\n")
                elif content and len(content) <= skill.content_len:
                    skipped_count += 1
                    logger.info(f"  ⏭️ 跳过：新内容不比旧内容长\n")
                else:
                    failed_count += 1
                    logger.warning(f"  ❌ 获取失败\n")

                # 避免请求过快
                if i < total:
                    await asyncio.sleep(1)  # GitHub 限流保护

            except Exception as e:
                failed_count += 1
                logger.error(f"  ❌ 更新失败: {e}\n")
                continue

        logger.info(f"\n=== 更新完成 ===")
        logger.info(f"成功: {success_count}")
        logger.info(f"失败: {failed_count}")
        logger.info(f"跳过: {skipped_count}")
        logger.info(f"总计: {total}")


async def main():
    parser = argparse.ArgumentParser(description='更新技能完整内容')
    parser.add_argument('--limit', type=int, help='限制更新数量（用于测试）')
    parser.add_argument('--min-length', type=int, default=300,
                        help='content 长度小于此值才更新（默认 300）')

    args = parser.parse_args()

    await update_skill_contents(
        limit=args.limit,
        min_length=args.min_length
    )


if __name__ == "__main__":
    asyncio.run(main())

"""
SkillsMP API 爬虫 - 使用发现的 API 端点
"""
import asyncio
import aiohttp
from playwright.async_api import async_playwright
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import get_session, SkillRepository
from src.storage.models import Skill, SkillCategory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_browser_session():
    """使用 Playwright 获取有效的浏览器会话（绕过 Cloudflare）"""
    async with async_playwright() as p:
        logger.info("启动浏览器...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='zh-CN'
        )

        page = await context.new_page()

        logger.info("访问 SkillsMP 首页...")
        try:
            await page.goto('https://skillsmp.com/zh', wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(8)  # 等待 Cloudflare 检查完成

            # 获取 cookies
            cookies = await context.cookies()
            logger.info(f"获取到 {len(cookies)} 个 cookies")

            # 转换为 aiohttp 格式
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}

            await browser.close()
            return cookie_dict

        except Exception as e:
            logger.error(f"获取浏览器会话失败: {e}")
            await browser.close()
            raise


async def fetch_skills_from_api(cookies: dict, page: int = 1, limit: int = 100):
    """使用 API 获取技能列表"""
    url = "https://skillsmp.com/api/skills"
    params = {
        'page': page,
        'limit': limit,
        'sortBy': 'stars',
        'marketplaceOnly': 'false'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://skillsmp.com/zh',
        'Origin': 'https://skillsmp.com',
    }

    async with aiohttp.ClientSession(cookies=cookies, headers=headers) as session:
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"API 请求失败: {response.status}")
                    text = await response.text()
                    logger.error(f"响应内容: {text[:200]}")
                    return None
        except Exception as e:
            logger.error(f"API 请求异常: {e}")
            return None


async def crawl_all_skills():
    """爬取所有技能"""
    logger.info("=== 开始爬取 SkillsMP 所有技能 ===\n")

    # 1. 获取浏览器会话（绕过 Cloudflare）
    logger.info("步骤 1: 绕过 Cloudflare，获取有效会话...")
    cookies = await get_browser_session()
    logger.info("[OK] 会话获取成功\n")

    # 2. 测试 API
    logger.info("步骤 2: 测试 API 端点...")
    first_page = await fetch_skills_from_api(cookies, page=1, limit=100)

    if not first_page:
        logger.error("API 测试失败！")
        return []

    logger.info(f"[OK] API 测试成功")
    logger.info(f"响应结构: {list(first_page.keys())}")

    # 检查响应格式
    if 'skills' in first_page:
        skills_key = 'skills'
        total_key = 'total'
    elif 'data' in first_page:
        skills_key = 'data'
        total_key = 'total'
    elif 'items' in first_page:
        skills_key = 'items'
        total_key = 'totalCount'
    else:
        # 假设直接就是数组
        if isinstance(first_page, list):
            logger.info(f"第 1 页: 获取到 {len(first_page)} 个技能")
            all_skills = first_page

            # 继续爬取后续页面（假设有分页）
            page_num = 2
            while True:
                logger.info(f"正在获取第 {page_num} 页...")
                page_data = await fetch_skills_from_api(cookies, page=page_num, limit=100)

                if not page_data or len(page_data) == 0:
                    break

                logger.info(f"第 {page_num} 页: 获取到 {len(page_data)} 个技能")
                all_skills.extend(page_data)
                page_num += 1

                await asyncio.sleep(1)  # 避免请求过快

            logger.info(f"\n总计获取到 {len(all_skills)} 个技能")
            return all_skills
        else:
            logger.error(f"未知的响应格式: {type(first_page)}")
            logger.error(f"响应内容: {json.dumps(first_page, indent=2, ensure_ascii=False)[:500]}")
            return []

    total_count = first_page.get(total_key, 0)
    first_batch = first_page.get(skills_key, [])

    logger.info(f"总技能数: {total_count}")
    logger.info(f"第 1 页: 获取到 {len(first_batch)} 个技能\n")

    all_skills = first_batch

    # 3. 计算总页数并爬取
    limit_per_page = 100
    total_pages = (total_count + limit_per_page - 1) // limit_per_page

    logger.info(f"步骤 3: 爬取所有 {total_pages} 页...")

    for page_num in range(2, total_pages + 1):
        logger.info(f"正在获取第 {page_num}/{total_pages} 页...")
        page_data = await fetch_skills_from_api(cookies, page=page_num, limit=limit_per_page)

        if not page_data:
            logger.warning(f"第 {page_num} 页获取失败，跳过")
            continue

        page_skills = page_data.get(skills_key, [])
        logger.info(f"  获取到 {len(page_skills)} 个技能")

        all_skills.extend(page_skills)

        # 避免请求过快
        await asyncio.sleep(1)

    logger.info(f"\n=== 爬取完成 ===")
    logger.info(f"总计获取到 {len(all_skills)} 个技能")

    return all_skills


async def save_skills_to_db(skills_data: list):
    """保存技能到数据库"""
    logger.info("\n=== 保存到数据库 ===")

    async with get_session() as session:
        repo = SkillRepository(session)

        saved_count = 0
        updated_count = 0
        error_count = 0

        for skill_data in skills_data:
            try:
                # 映射字段（根据实际 API 响应调整）
                skill = Skill(
                    name=skill_data.get('name', skill_data.get('title', 'Unknown')),
                    slug=skill_data.get('slug', skill_data.get('id', '')),
                    description=skill_data.get('description', ''),
                    author=skill_data.get('author', skill_data.get('owner', 'Unknown')),
                    github_url=skill_data.get('github_url', skill_data.get('url', '')),
                    stars=skill_data.get('stars', 0),
                    forks=skill_data.get('forks', 0),
                    category=SkillCategory.GENERAL,  # 需要根据实际分类映射
                    tags=skill_data.get('tags', []),
                    content=skill_data.get('content', skill_data.get('readme', '')),
                    install_command=f"claude skill install {skill_data.get('github_url', '')}",
                    status='active',
                    is_official=skill_data.get('is_official', False)
                )

                # 检查是否已存在
                existing = await repo.get_by_slug(skill.slug)

                if existing:
                    # 更新
                    existing.name = skill.name
                    existing.description = skill.description
                    existing.stars = skill.stars
                    existing.forks = skill.forks
                    existing.content = skill.content
                    await repo.update(existing)
                    updated_count += 1
                else:
                    # 新增
                    await repo.create(skill)
                    saved_count += 1

            except Exception as e:
                logger.error(f"保存技能失败: {skill_data.get('name', 'Unknown')}, 错误: {e}")
                error_count += 1

        logger.info(f"\n保存结果:")
        logger.info(f"  新增: {saved_count}")
        logger.info(f"  更新: {updated_count}")
        logger.info(f"  失败: {error_count}")


async def main():
    # 爬取所有技能
    skills = await crawl_all_skills()

    if not skills:
        logger.error("未获取到任何技能！")
        return

    # 保存示例数据到文件（调试用）
    output_file = Path(__file__).parent / "api_skills_sample.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(skills[:5], f, indent=2, ensure_ascii=False)
    logger.info(f"\n已保存前 5 个技能样本到: {output_file}")

    # 保存到数据库
    await save_skills_to_db(skills)


if __name__ == "__main__":
    asyncio.run(main())

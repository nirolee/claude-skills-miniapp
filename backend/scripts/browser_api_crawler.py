"""
SkillsMP API 爬虫 - 在浏览器上下文内调用 API
"""
import asyncio
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


async def crawl_all_skills_browser(batch_size=500):
    """在浏览器上下文内爬取所有技能，支持分批保存

    Args:
        batch_size: 每爬取多少页就保存一次到数据库，默认500页
    """
    logger.info("=== 开始爬取 SkillsMP 所有技能 ===\n")

    async with async_playwright() as p:
        logger.info("步骤 1: 启动浏览器...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            locale='zh-CN'
        )

        page = await context.new_page()

        logger.info("步骤 2: 访问首页（绕过 Cloudflare）...")
        try:
            await page.goto('https://skillsmp.com/zh', wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(8)  # 等待 Cloudflare 检查
            logger.info("[OK] 首页加载成功\n")
        except Exception as e:
            logger.error(f"首页加载失败: {e}")
            await browser.close()
            return []

        logger.info("步骤 3: 使用浏览器上下文调用 API...")

        # 在浏览器上下文内执行 fetch 请求
        all_skills = []
        batch_skills = []  # 当前批次的技能
        page_num = 1
        limit = 100
        total_saved = 0

        while True:
            logger.info(f"正在获取第 {page_num} 页...")

            try:
                # 使用 page.evaluate 在浏览器内执行 fetch
                api_response = await page.evaluate(f"""
                    async () => {{
                        const response = await fetch('/api/skills?page={page_num}&limit={limit}&sortBy=stars&marketplaceOnly=false', {{
                            method: 'GET',
                            headers: {{
                                'Accept': 'application/json',
                            }}
                        }});

                        if (!response.ok) {{
                            return {{ error: true, status: response.status }};
                        }}

                        const data = await response.json();
                        return data;
                    }}
                """)

                # 检查是否出错
                if isinstance(api_response, dict) and api_response.get('error'):
                    logger.error(f"API 返回错误: {api_response.get('status')}")
                    break

                # 处理响应数据
                current_page_skills = []
                if isinstance(api_response, list):
                    # 响应直接是数组
                    if len(api_response) == 0:
                        logger.info("没有更多数据")
                        break

                    # 检测重复数据：如果连续获取到相同数量的较少数据，可能已到末尾
                    if len(api_response) < limit * 0.5 and page_num > 10:
                        logger.info(f"  获取到 {len(api_response)} 个技能（数据量较少，可能接近末尾）")
                        # 记录最后几页的数据量，判断是否重复
                        if not hasattr(crawl_all_skills_browser, '_last_sizes'):
                            crawl_all_skills_browser._last_sizes = []
                        crawl_all_skills_browser._last_sizes.append(len(api_response))
                        if len(crawl_all_skills_browser._last_sizes) > 5:
                            crawl_all_skills_browser._last_sizes.pop(0)
                        # 如果连续5页数据量都一样且较少，认为已到末尾
                        if len(crawl_all_skills_browser._last_sizes) == 5 and len(set(crawl_all_skills_browser._last_sizes)) == 1:
                            logger.info("检测到连续5页返回相同数量的数据，判定为已到达末尾")
                            current_page_skills = api_response
                            batch_skills.extend(current_page_skills)
                            all_skills.extend(current_page_skills)
                            break
                    else:
                        logger.info(f"  获取到 {len(api_response)} 个技能")
                    current_page_skills = api_response

                elif isinstance(api_response, dict):
                    # 响应是对象，包含 skills/items/data 字段
                    skills_data = None

                    if 'skills' in api_response:
                        skills_data = api_response['skills']
                        total = api_response.get('total', 0)
                    elif 'items' in api_response:
                        skills_data = api_response['items']
                        total = api_response.get('totalCount', 0)
                    elif 'data' in api_response:
                        skills_data = api_response['data']
                        total = api_response.get('total', 0)

                    if page_num == 1:
                        # 第一页，显示总数
                        logger.info(f"  总技能数: {total}")

                    # 检查是否还有下一页
                    has_next = api_response.get('hasNext', True)
                    if not has_next:
                        logger.info("已到达最后一页（hasNext=false）")
                        if skills_data and len(skills_data) > 0:
                            # 保存最后一页的数据
                            current_page_skills = skills_data
                            logger.info(f"  获取到 {len(skills_data)} 个技能")
                            batch_skills.extend(current_page_skills)
                            all_skills.extend(current_page_skills)
                        break

                    if skills_data is None or len(skills_data) == 0:
                        logger.info("没有更多数据")
                        break

                    logger.info(f"  获取到 {len(skills_data)} 个技能")
                    current_page_skills = skills_data

                else:
                    logger.error(f"未知的响应格式: {type(api_response)}")
                    break

                # 添加到批次和总列表
                batch_skills.extend(current_page_skills)
                all_skills.extend(current_page_skills)

                # 每爬取 batch_size 页就保存一次
                if page_num % batch_size == 0 and batch_skills:
                    logger.info(f"\n--- 已爬取 {page_num} 页，开始分批保存 {len(batch_skills)} 个技能 ---")
                    await save_skills_to_db(batch_skills)
                    total_saved += len(batch_skills)
                    logger.info(f"--- 累计已保存 {total_saved} 个技能到数据库 ---\n")
                    batch_skills = []  # 清空当前批次

                page_num += 1
                await asyncio.sleep(1)  # 避免请求过快

            except Exception as e:
                logger.error(f"第 {page_num} 页获取失败: {e}")
                # 即使出错，也保存已爬取的数据
                if batch_skills:
                    logger.info(f"\n--- 出错前保存剩余 {len(batch_skills)} 个技能 ---")
                    await save_skills_to_db(batch_skills)
                    total_saved += len(batch_skills)
                break

        # 保存最后一批数据
        if batch_skills:
            logger.info(f"\n--- 保存最后一批 {len(batch_skills)} 个技能 ---")
            await save_skills_to_db(batch_skills)
            total_saved += len(batch_skills)

        logger.info(f"\n=== 爬取完成 ===")
        logger.info(f"总计获取到 {len(all_skills)} 个技能")
        logger.info(f"总计保存到数据库 {total_saved} 个技能")

        await browser.close()
        return all_skills


async def map_category(skill_data: dict) -> SkillCategory:
    """映射分类"""
    # 根据技能的 category 或 tags 映射到我们的分类枚举
    category_str = skill_data.get('category', '').lower()
    tags = skill_data.get('tags', [])

    category_mapping = {
        'debug': SkillCategory.DEBUGGING,
        'debugging': SkillCategory.DEBUGGING,
        'test': SkillCategory.TESTING,
        'testing': SkillCategory.TESTING,
        'automation': SkillCategory.AUTOMATION,
        'auto': SkillCategory.AUTOMATION,
        'devops': SkillCategory.DEVOPS,
        'ci': SkillCategory.DEVOPS,
        'deployment': SkillCategory.DEVOPS,
        'docs': SkillCategory.DOCUMENTATION,
        'documentation': SkillCategory.DOCUMENTATION,
        'design': SkillCategory.DESIGN,
        'ui': SkillCategory.DESIGN,
        'data': SkillCategory.DATA_SCIENCE,
        'analytics': SkillCategory.DATA_SCIENCE,
        'ml': SkillCategory.MACHINE_LEARNING,
        'machine-learning': SkillCategory.MACHINE_LEARNING,
        'frontend': SkillCategory.FRONTEND,
        'backend': SkillCategory.BACKEND,
        'fullstack': SkillCategory.FULLSTACK,
        'develop': SkillCategory.GENERAL,
        'code': SkillCategory.GENERAL,
    }

    # ��检查 category 字段
    for key, cat in category_mapping.items():
        if key in category_str:
            return cat

    # 再检查 tags
    for tag in tags:
        tag_lower = str(tag).lower()
        for key, cat in category_mapping.items():
            if key in tag_lower:
                return cat

    return SkillCategory.OTHER


async def save_skills_to_db(skills_data: list):
    """保存技能到数据库"""
    logger.info("\n=== 保存到数据库 ===")

    if not skills_data:
        logger.warning("没有技能需要保存")
        return

    async with get_session() as session:
        repo = SkillRepository(session)

        saved_count = 0
        updated_count = 0
        error_count = 0

        for skill_data in skills_data:
            try:
                # 提取字段（根据实际 API 响应调整）
                name = skill_data.get('name') or skill_data.get('title') or 'Unknown'
                raw_slug = skill_data.get('slug') or skill_data.get('id') or name.lower().replace(' ', '-')
                # 限制 slug 长度，避免数据库错误
                slug = raw_slug[:490] if len(raw_slug) > 490 else raw_slug
                description = skill_data.get('description', '')
                author = skill_data.get('author') or skill_data.get('owner') or 'Unknown'
                github_url = skill_data.get('github_url') or skill_data.get('url') or skill_data.get('repositoryUrl') or ''
                stars = skill_data.get('stars', 0) or 0
                forks = skill_data.get('forks', 0) or 0
                tags = skill_data.get('tags', []) or []
                content = skill_data.get('content') or skill_data.get('readme') or skill_data.get('description') or ''
                is_official = skill_data.get('is_official', False) or skill_data.get('isOfficial', False)

                #映射分类
                category = await map_category(skill_data)

                # 生成安装命令
                install_cmd = f"/skills add {github_url}" if github_url else ''

                # 准备��能数据字典
                skill_dict = {
                    'name': name,
                    'slug': slug,
                    'description': description[:500] if description else '',
                    'author': author,
                    'github_url': github_url,
                    'stars': stars,
                    'forks': forks,
                    'category': category,
                    'tags': tags if isinstance(tags, list) else [],
                    'content': content,
                    'install_command': install_cmd,
                    'status': 'active',
                    'is_official': is_official
                }

                # 检查是否已存在
                existing = await repo.get_by_slug(slug)

                if existing:
                    # 幂等检查：只更新有变化的字段
                    has_changes = False
                    update_data = {}

                    # 检查关键字段是否有变化
                    if existing.name != name:
                        update_data['name'] = name
                        has_changes = True

                    if existing.description != (description[:500] if description else ''):
                        update_data['description'] = description[:500] if description else ''
                        has_changes = True

                    if existing.stars != stars:
                        update_data['stars'] = stars
                        has_changes = True

                    if existing.forks != forks:
                        update_data['forks'] = forks
                        has_changes = True

                    if existing.content != content:
                        update_data['content'] = content
                        has_changes = True

                    if existing.tags != (tags if isinstance(tags, list) else []):
                        update_data['tags'] = tags if isinstance(tags, list) else []
                        has_changes = True

                    # 只有有变化时才更新
                    if has_changes:
                        await repo.update(existing.id, update_data)
                        updated_count += 1
                        logger.debug(f"  更新技能: {name} (变化字段: {list(update_data.keys())})")
                    else:
                        # 跳过，数据未变化
                        pass

                else:
                    # 新增
                    await repo.create(skill_dict)
                    saved_count += 1

            except Exception as e:
                logger.error(f"保存技能失败: {skill_data.get('name', 'Unknown')}, 错误: {e}")
                error_count += 1
                continue

        logger.info(f"\n保存结果:")
        logger.info(f"  新增: {saved_count}")
        logger.info(f"  更新: {updated_count}")
        logger.info(f"  跳过(无变化): {len(skills_data) - saved_count - updated_count - error_count}")
        logger.info(f"  失败: {error_count}")


async def main():
    # 爬取所有技能（已在爬取过程中分批保存到数据库）
    skills = await crawl_all_skills_browser(batch_size=500)

    if not skills:
        logger.error("未获取到任何技能！")
        return

    # 保存样本数据
    output_file = Path(__file__).parent / "api_skills_sample.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(skills[:5], f, indent=2, ensure_ascii=False)
    logger.info(f"\n已保存前 5 个技能样本到: {output_file}")

    logger.info("\n✅ 所有数据已在爬取过程中分批保存到数据库")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的爬虫 - 使用更智能的策略避免限流
"""
import asyncio
from playwright.async_api import async_playwright
import sys
from pathlib import Path
import sys
import io
import aiohttp

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import get_session, SkillRepository
from src.storage.models import SkillCategory
import logging
import random

# 导入分类器
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 简化版分类器（从 classify_skills.py 复制）
CATEGORY_KEYWORDS = {
    SkillCategory.FRONTEND: [
        'react', 'vue', 'angular', 'svelte', 'frontend', 'ui', 'ux',
        'css', 'html', 'component', 'jsx', 'tsx', 'next.js', 'nuxt',
        'tailwind', 'styled', 'responsive', 'web design', 'browser'
    ],
    SkillCategory.BACKEND: [
        'backend', 'server', 'api', 'rest', 'graphql', 'endpoint',
        'express', 'fastapi', 'django', 'flask', 'node.js', 'spring',
        'middleware', 'authentication', 'auth', 'jwt', 'session'
    ],
    SkillCategory.MOBILE: [
        'mobile', 'ios', 'android', 'react native', 'flutter',
        'swift', 'kotlin', 'app development', 'mobile app'
    ],
    SkillCategory.TESTING: [
        'test', 'testing', 'vitest', 'jest', 'pytest', 'unittest',
        'e2e', 'integration test', 'unit test', 'tdd', 'coverage',
        'mock', 'fixture', 'assertion', 'playwright test'
    ],
    SkillCategory.DEBUGGING: [
        'debug', 'debugging', 'troubleshoot', 'error', 'exception',
        'bug', 'fix', 'diagnose', 'trace', 'breakpoint', 'inspect'
    ],
    SkillCategory.CODE_REVIEW: [
        'review', 'code review', 'pull request', 'pr', 'lint',
        'eslint', 'prettier', 'code quality', 'refactor', 'clean code'
    ],
    SkillCategory.DEVOPS: [
        'devops', 'ci/cd', 'docker', 'kubernetes', 'k8s', 'jenkins',
        'gitlab', 'github actions', 'deployment', 'pipeline',
        'container', 'orchestration', 'terraform', 'ansible'
    ],
    SkillCategory.AUTOMATION: [
        'automation', 'script', 'automate', 'workflow', 'cron',
        'scheduled', 'batch', 'task runner', 'orchestration'
    ],
    SkillCategory.BUILD_TOOLS: [
        'build', 'webpack', 'vite', 'rollup', 'bundler', 'compiler',
        'transpiler', 'babel', 'esbuild', 'parcel', 'npm', 'yarn'
    ],
    SkillCategory.DOCUMENTATION: [
        'documentation', 'docstring', 'docs', 'readme', 'guide',
        'tutorial', 'comment', 'jsdoc', 'sphinx', 'markdown',
        'technical writing', 'api doc'
    ],
    SkillCategory.DESIGN: [
        'design', 'ui design', 'ux design', 'figma', 'sketch',
        'prototype', 'wireframe', 'mockup', 'design system'
    ],
    SkillCategory.ARCHITECTURE: [
        'architecture', 'system design', 'microservice', 'monolith',
        'pattern', 'design pattern', 'structure', 'scalability'
    ],
    SkillCategory.DATABASE: [
        'database', 'sql', 'mysql', 'postgres', 'mongodb', 'redis',
        'orm', 'query', 'migration', 'schema', 'index', 'nosql'
    ],
    SkillCategory.DATA_SCIENCE: [
        'data science', 'data analysis', 'pandas', 'numpy', 'jupyter',
        'visualization', 'statistics', 'analytics', 'data processing'
    ],
    SkillCategory.MACHINE_LEARNING: [
        'machine learning', 'ml', 'ai', 'neural network', 'deep learning',
        'pytorch', 'tensorflow', 'model', 'training', 'inference',
        'scikit-learn', 'nlp', 'computer vision', 'llm'
    ],
    SkillCategory.PYTHON: [
        'python', 'py', 'pip', 'pypi', 'conda', 'virtualenv'
    ],
    SkillCategory.JAVASCRIPT: [
        'javascript', 'typescript', 'js', 'ts', 'ecmascript', 'node'
    ],
    SkillCategory.JAVA: [
        'java', 'kotlin', 'jvm', 'spring', 'maven', 'gradle'
    ],
    SkillCategory.CPP: [
        'c++', 'cpp', 'c/c++', 'cmake', 'clang', 'gcc'
    ],
    SkillCategory.GO: [
        'go', 'golang', 'goroutine'
    ],
    SkillCategory.RUST: [
        'rust', 'cargo', 'rustc'
    ],
    SkillCategory.SECURITY: [
        'security', 'vulnerability', 'penetration', 'encryption',
        'ssl', 'tls', 'authentication', 'authorization', 'xss', 'csrf'
    ],
    SkillCategory.PERFORMANCE: [
        'performance', 'optimization', 'optimize', 'speed', 'cache',
        'latency', 'throughput', 'profiling', 'benchmark', 'memory'
    ],
    SkillCategory.SKILL_MANAGEMENT: [
        'skill', 'plugin', 'extension', 'codex', 'claude skill',
        'skill creator', 'skill installer', 'skill writer'
    ],
    SkillCategory.GENERAL: [
        'utility', 'helper', 'tool', 'generator', 'converter',
        'formatter', 'validator', 'parser', 'cli'
    ],
}


def classify_skill(name: str, description: str, tags: list = None) -> SkillCategory:
    """智能分类技能"""
    text = f"{name} {description}"
    if tags:
        text += " " + " ".join(tags)
    text = text.lower()

    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, text))
            score += matches
        if score > 0:
            scores[category] = score

    if scores:
        return max(scores, key=scores.get)
    return SkillCategory.OTHER


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
        # 例如: https://github.com/anthropics/skills/tree/main/skills/debugging/debug-code
        # 转为: https://raw.githubusercontent.com/anthropics/skills/main/skills/debugging/debug-code/SKILL.md

        # 提取路径部分
        if '/tree/' in github_url:
            # 格式: https://github.com/{owner}/{repo}/tree/{branch}/{path}
            parts = github_url.split('/tree/')
            if len(parts) == 2:
                base_url = parts[0]  # https://github.com/{owner}/{repo}
                branch_and_path = parts[1]  # main/skills/debugging/debug-code

                # 分离 branch 和 path
                path_parts = branch_and_path.split('/', 1)
                if len(path_parts) == 2:
                    branch = path_parts[0]  # main
                    path = path_parts[1]    # skills/debugging/debug-code

                    # 从 base_url 提取 owner 和 repo
                    base_parts = base_url.replace('https://github.com/', '').split('/')
                    if len(base_parts) >= 2:
                        owner = base_parts[0]
                        repo = base_parts[1]

                        # 构造 raw URL
                        raw_url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}/SKILL.md'

                        # 使用 aiohttp 获取内容
                        timeout = aiohttp.ClientTimeout(total=30)
                        async with aiohttp.ClientSession(timeout=timeout) as session:
                            async with session.get(raw_url) as response:
                                if response.status == 200:
                                    content = await response.text()
                                    logger.info(f"  ✅ 获取 SKILL.md 成功: {len(content)} 字符")
                                    return content
                                else:
                                    logger.warning(f"  ⚠️ 获取 SKILL.md 失败: HTTP {response.status}")
                                    return ''

        # 如果 URL 格式不匹配，返回空
        logger.warning(f"  ⚠️ 无法解析 GitHub URL: {github_url}")
        return ''

    except Exception as e:
        logger.error(f"  ❌ 获取 SKILL.md 出错: {e}")
        return ''


async def smart_crawl(start_page=1, max_pages=100):
    """智能爬取策略"""
    logger.info("=== 智能爬虫 v2.0 ===\n")

    async with async_playwright() as p:
        # 使用更真实的浏览器配置
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )

        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
        )

        # 隐藏 webdriver 特征
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = await context.new_page()

        try:
            logger.info("访问 SkillsMP...")
            await page.goto('https://skillsmp.com/zh', wait_until='domcontentloaded', timeout=60000)

            # 等待页面完全加载
            logger.info("等待页面初始化...")
            await asyncio.sleep(8)

            # 滚动到底部触发懒加载
            logger.info("模拟滚动浏览...")
            for i in range(3):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(random.uniform(1.5, 3.0))  # 随机延迟

            # 再等待一会儿让 JavaScript 完成初始化
            await asyncio.sleep(5)

            # 现在开始抓取
            all_skills = []
            page_num = start_page
            consecutive_failures = 0
            success_count = 0

            logger.info(f"\n开始从第 {start_page} 页抓取...\n")

            while page_num <= max_pages and consecutive_failures < 3:
                try:
                    # 每次请求前随机延迟 2-5 秒
                    delay = random.uniform(2.0, 5.0)
                    logger.info(f"等待 {delay:.1f} 秒...")
                    await asyncio.sleep(delay)

                    # 尝试多种 API 调用方式
                    api_url = f'/api/skills?page={page_num}&limit=100&sortBy=updatedAt&marketplaceOnly=false'

                    logger.info(f"请求第 {page_num} 页...")

                    result = await page.evaluate(f"""
                        async () => {{
                            try {{
                                const response = await fetch('{api_url}', {{
                                    method: 'GET',
                                    headers: {{
                                        'Accept': 'application/json',
                                        'Content-Type': 'application/json',
                                    }},
                                    credentials: 'include'
                                }});

                                if (!response.ok) {{
                                    return {{
                                        error: true,
                                        status: response.status,
                                        statusText: response.statusText
                                    }};
                                }}

                                const data = await response.json();
                                return {{
                                    success: true,
                                    data: data
                                }};
                            }} catch(e) {{
                                return {{ error: true, message: e.toString() }};
                            }}
                        }}
                    """)

                    if result.get('error'):
                        logger.warning(f"  [!] 第 {page_num} 页失败: {result.get('status', '')} {result.get('message', '')}")
                        consecutive_failures += 1

                        # 如果是 403，等待更长时间
                        if result.get('status') == 403:
                            wait_time = random.uniform(30, 60)
                            logger.warning(f"  遇到限流，等待 {wait_time:.0f} 秒...")
                            await asyncio.sleep(wait_time)

                        page_num += 1
                        continue

                    # 成功获取数据
                    data = result.get('data', {})
                    items = data.get('items', []) or data.get('skills', [])
                    total = data.get('totalCount', 0)

                    if not items:
                        logger.info(f"  第 {page_num} 页无数据")
                        consecutive_failures += 1
                    else:
                        logger.info(f"  [OK] 第 {page_num} 页: {len(items)} 条 (总计: {total})")
                        all_skills.extend(items)
                        success_count += 1
                        consecutive_failures = 0

                    page_num += 1

                    # 每 10 页保存一次
                    if success_count > 0 and success_count % 10 == 0:
                        logger.info(f"\n--- 已抓取 {len(all_skills)} 条，保存中... ---")
                        await save_skills_incremental(all_skills)
                        all_skills = []  # 清空已保存的

                except Exception as e:
                    logger.error(f"  第 {page_num} 页异常: {e}")
                    consecutive_failures += 1
                    page_num += 1

            await browser.close()

            logger.info(f"\n总计抓取: {len(all_skills)} 条")
            return all_skills

        except Exception as e:
            logger.error(f"爬虫失败: {e}")
            import traceback
            traceback.print_exc()
            await browser.close()
            return []


async def save_skills_incremental(skills):
    """增量保存技能（每次只保存新的/更新的）"""
    if not skills:
        return

    logger.info(f"保存 {len(skills)} 条记录...")

    async with get_session() as session:
        repo = SkillRepository(session)

        new_count = 0
        update_count = 0
        skip_count = 0

        for skill in skills:
            try:
                name = skill.get('name', 'Unknown')
                slug = skill.get('id', name.lower().replace(' ', '-'))
                description = skill.get('description', '')[:500]
                author = skill.get('author', 'Unknown')
                github_url = skill.get('githubUrl', '')
                stars = skill.get('stars', 0) or 0
                forks = skill.get('forks', 0) or 0

                # 智能分类
                category = classify_skill(name, description, skill.get('tags', []))

                # 从 GitHub 获取完整的 SKILL.md 内容
                logger.info(f"  正在获取 {name} 的完整内容...")
                content = await fetch_skill_content_from_github(github_url)

                # 如果获取失败，使用 description 作为后备
                if not content or len(content) < 50:
                    logger.warning(f"  ⚠️ 使用 description 作为内容")
                    content = description

                skill_dict = {
                    'name': name,
                    'slug': slug,
                    'description': description,
                    'author': author,
                    'github_url': github_url,
                    'stars': stars,
                    'forks': forks,
                    'category': category,
                    'tags': [],
                    'content': content,  # 使用完整内容
                    'install_command': f'/skills add {github_url}' if github_url else '',
                    'status': 'active',
                    'is_official': skill.get('hasMarketplace', False)
                }

                existing = await repo.get_by_slug(slug)

                if existing:
                    # 只更新 stars/forks/content（如果 content 更完整）
                    update_data = {}
                    if existing.stars != stars:
                        update_data['stars'] = stars
                    if existing.forks != forks:
                        update_data['forks'] = forks
                    if existing.github_url != github_url and github_url:
                        update_data['github_url'] = github_url
                    # 如果新的 content 更长，更新它
                    if len(content) > len(existing.content):
                        update_data['content'] = content
                        logger.info(f"  📝 更新内容: {len(existing.content)} → {len(content)} ��符")

                    if update_data:
                        await repo.update(existing.id, update_data)
                        update_count += 1
                    else:
                        skip_count += 1
                else:
                    await repo.create(skill_dict)
                    new_count += 1

            except Exception as e:
                logger.error(f"保存失败: {skill.get('name')}, {e}")

        logger.info(f"  新增: {new_count}, 更新: {update_count}, 跳过: {skip_count}")


async def main():
    """主函数"""
    from datetime import datetime
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 从第 1 页开始，最多抓取 100 页
    skills = await smart_crawl(start_page=1, max_pages=100)

    if skills:
        await save_skills_incremental(skills)

    logger.info(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("完成！\n")


if __name__ == "__main__":
    asyncio.run(main())

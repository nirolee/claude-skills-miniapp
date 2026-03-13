#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的爬虫 - 使用 cookie 注入绕过 Cloudflare，直接 httpx 请求
"""
import asyncio
from curl_cffi.requests import AsyncSession
import sys
from pathlib import Path
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import get_session, SkillRepository
from src.storage.models import SkillCategory
import logging
import random

# Cookie 文件路径（Netscape 格式，由浏览器导出）
COOKIE_FILE = Path(__file__).parent / 'skillsmp_cookies.txt'

# 导入分类器
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
import re as _re

def _generate_install_commands(github_url):
    """从 GitHub tree URL 生成正确的 git sparse-checkout 安装命令"""
    if not github_url:
        return '', None
    m = _re.match(r'https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)', github_url)
    if not m:
        return '', None
    owner, repo, branch, path = m.groups()
    path = path.rstrip('/')
    skill_name = path.split('/')[-1]
    repo_url = "https://github.com/{}/{}".format(owner, repo)
    backslash = "\\"
    ps_path = path.replace('/', backslash)
    bash = "; ".join([
        "mkdir -p ~/.claude/skills",
        "cd ~/.claude/skills",
        "git clone --depth 1 --branch {} --filter=blob:none --sparse {} .temp-install".format(branch, repo_url),
        "cd .temp-install",
        "git sparse-checkout set {}".format(path),
        "mkdir -p ~/.claude/skills/{}".format(skill_name),
        "cp -r {}/* ~/.claude/skills/{}/".format(path, skill_name),
        "cd ..",
        "rm -rf .temp-install",
        'echo "✅ Skill 安装成功: {}"'.format(skill_name),
    ])
    win = "; ".join([
        'New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills"',
        'Set-Location "$env:USERPROFILE\.claude\skills"',
        "git clone --depth 1 --branch {} --filter=blob:none --sparse {} .temp-install".format(branch, repo_url),
        "Set-Location .temp-install",
        "git sparse-checkout set {}".format(path),
        'New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills\{}"'.format(skill_name),
        'Copy-Item -Recurse -Path "{}\*" -Destination "$env:USERPROFILE\.claude\skills\\\\"'.format(ps_path),
        'Set-Location "$env:USERPROFILE\.claude\skills"',
        "Remove-Item -Recurse -Force .temp-install",
        'Write-Host "✅ Skill 安装成功: {}"'.format(skill_name),
    ])
    return bash, win


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


def load_cookies_from_file(cookie_file: Path) -> dict:
    """从 Netscape 格式 cookie 文件加载 cookies"""
    cookies = {}
    if not cookie_file.exists():
        logger.error(f"Cookie 文件不存��: {cookie_file}")
        return cookies
    with open(cookie_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                name = parts[5]
                value = parts[6]
                cookies[name] = value
    logger.info(f"加载 {len(cookies)} 个 cookies，包含 cf_clearance: {'cf_clearance' in cookies}")
    return cookies


async def smart_crawl(start_page=1, max_pages=100):
    """直接 httpx 请求 + cookie 注入，绕过 Cloudflare"""
    logger.info("=== 智能爬虫 v3.0 (httpx + cookie) ===\n")

    cookies = load_cookies_from_file(COOKIE_FILE)
    if 'cf_clearance' not in cookies:
        logger.error("❌ 未找到 cf_clearance cookie，请重新导出浏览器 cookie 到 skillsmp_cookies.txt")
        return []

    all_skills = []
    page_num = start_page
    consecutive_failures = 0
    success_count = 0

    logger.info(f"开始从第 {start_page} 页抓取，目标: 第 {max_pages} 页\n")

    async with AsyncSession(impersonate='chrome131') as client:
        while page_num <= max_pages and consecutive_failures < 5:
            try:
                delay = random.uniform(1.0, 3.0)
                await asyncio.sleep(delay)

                url = f'https://skillsmp.com/api/skills?page={page_num}&limit=100&sortBy=updatedAt&marketplaceOnly=false'
                logger.info(f"请求第 {page_num} 页...")

                resp = await client.get(url, cookies=cookies, headers={'Referer': 'https://skillsmp.com/'})

                if resp.status_code == 403:
                    logger.error(f"  ❌ 403 Forbidden - cf_clearance 已过期，请重新导出 cookie")
                    logger.error(f"     请从浏览器重新导出 skillsmp.com 的 cookie 到 skillsmp_cookies.txt")
                    break
                elif resp.status_code != 200:
                    logger.warning(f"  [!] 第 {page_num} 页 HTTP {resp.status_code}")
                    consecutive_failures += 1
                    page_num += 1
                    continue

                data = resp.json()
                items = data.get('items', []) or data.get('skills', [])
                total = data.get('totalCount', 0)

                if not items:
                    logger.info(f"  第 {page_num} 页无数据，已到末尾")
                    consecutive_failures += 1
                else:
                    logger.info(f"  ✅ 第 {page_num} 页: {len(items)} 条 (数据源总计: {total})")
                    all_skills.extend(items)
                    success_count += 1
                    consecutive_failures = 0

                page_num += 1

                # 每 20 页保存一次，避免内存积压
                if success_count > 0 and success_count % 20 == 0:
                    logger.info(f"\n--- 已抓取 {len(all_skills)} 条，保存中... ---")
                    await save_skills_incremental(all_skills)
                    all_skills = []

            except Exception as e:
                logger.error(f"  第 {page_num} 页异常: {e}")
                consecutive_failures += 1
                page_num += 1

    logger.info(f"\n本轮抓取完成，缓冲 {len(all_skills)} 条待保存")
    return all_skills


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
                    'content': description,
                    'install_command': _generate_install_commands(github_url)[0],
                    'install_command_windows': _generate_install_commands(github_url)[1],
                    'status': 'active',
                    'is_official': skill.get('hasMarketplace', False)
                }

                existing = await repo.get_by_slug(slug)

                if existing:
                    # 只更新 stars/forks
                    update_data = {}
                    if existing.stars != stars:
                        update_data['stars'] = stars
                    if existing.forks != forks:
                        update_data['forks'] = forks
                    if existing.github_url != github_url and github_url:
                        update_data['github_url'] = github_url

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
    """主函数 - 断点续传，持续抓取全量数据，不覆盖已有内容"""
    import json as _json
    from datetime import datetime
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 读取断点
    progress_file = Path(__file__).parent / 'crawler_progress.json'
    start_page = 1
    if progress_file.exists():
        try:
            d = _json.loads(progress_file.read_text())
            start_page = max(1, d.get('current_page', 1))
            logger.info(f'断点续传，从第 {start_page} 页开始')
        except Exception:
            pass

    MAX_PAGES_PER_RUN = 200  # 每轮抓 200 页（2万条），防止单次运行过久
    while True:
        end_page = start_page + MAX_PAGES_PER_RUN - 1
        logger.info(f'\n=== 本轮抓取第 {start_page} ~ {end_page} 页 ===')
        skills = await smart_crawl(start_page=start_page, max_pages=end_page)

        if skills:
            await save_skills_incremental(skills)

        # 保存断点
        next_page = start_page + MAX_PAGES_PER_RUN
        try:
            d = {}
            if progress_file.exists():
                d = _json.loads(progress_file.read_text())
            d['current_page'] = next_page
            d['last_update'] = datetime.now().isoformat()
            progress_file.write_text(_json.dumps(d, indent=2))
        except Exception:
            pass

        logger.info(f'本轮完成，下轮从第 {next_page} 页开始')

        if not skills:
            logger.info('已到数据末尾，等待 1 小时后从第 1 页重新扫描...')
            await asyncio.sleep(3600)
            start_page = 1
            try:
                d = _json.loads(progress_file.read_text())
                d['current_page'] = 1
                progress_file.write_text(_json.dumps(d, indent=2))
            except Exception:
                pass
        else:
            start_page = next_page
            await asyncio.sleep(10)  # 轮间休息 10 秒


if __name__ == "__main__":
    asyncio.run(main())

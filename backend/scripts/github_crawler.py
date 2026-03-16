#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 爬虫 - 搜索所有含 SKILL.md 的仓库，再逐仓库抓取所有 SKILL.md 文件
策略：仓库搜索按 stars 分片（每段 <=1000 仓库），再对每仓库 Code Search 找所有 SKILL.md
"""
import asyncio
import httpx
import sys
import json
import re
import io
from pathlib import Path
from datetime import datetime
import logging

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import get_session, SkillRepository
from src.storage.models import SkillCategory
from src.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

settings = get_settings()
GITHUB_TOKEN = settings.github_token or ''

PROGRESS_FILE = Path(__file__).parent / 'github_crawler_progress.json'

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json',
}

# stars 分片范围，每段仓库数 <=1000
STARS_RANGES = [
    'stars:>1000',
    'stars:100..1000',
    'stars:10..99',
    'stars:1..9',
    'stars:0',
]

# ── 分类器 ────────────────────────────────────────────────────────────
CATEGORY_KEYWORDS = {
    SkillCategory.FRONTEND: ['react','vue','angular','svelte','frontend','ui','ux','css','html','component','jsx','tsx','next.js','nuxt','tailwind','responsive','browser'],
    SkillCategory.BACKEND: ['backend','server','api','rest','graphql','endpoint','express','fastapi','django','flask','node.js','spring','middleware','authentication','auth','jwt'],
    SkillCategory.MOBILE: ['mobile','ios','android','react native','flutter','swift','kotlin'],
    SkillCategory.TESTING: ['test','testing','vitest','jest','pytest','unittest','e2e','tdd','coverage','mock','playwright test'],
    SkillCategory.DEBUGGING: ['debug','debugging','troubleshoot','error','exception','bug','fix','diagnose'],
    SkillCategory.CODE_REVIEW: ['review','code review','pull request','lint','eslint','prettier','refactor'],
    SkillCategory.DEVOPS: ['devops','ci/cd','docker','kubernetes','k8s','github actions','deployment','pipeline','terraform','ansible'],
    SkillCategory.AUTOMATION: ['automation','automate','workflow','cron','scheduled','slack','notion','jira','webhook','zapier','n8n'],
    SkillCategory.BUILD_TOOLS: ['build','webpack','vite','rollup','bundler','compiler','babel','esbuild','npm','yarn'],
    SkillCategory.DOCUMENTATION: ['documentation','docstring','docs','readme','guide','tutorial','comment','markdown'],
    SkillCategory.DATABASE: ['database','sql','mysql','postgres','mongodb','redis','orm','query','migration','nosql'],
    SkillCategory.MACHINE_LEARNING: ['machine learning','ml','ai','neural network','deep learning','pytorch','tensorflow','nlp','llm'],
    SkillCategory.PYTHON: ['python','pip','pypi','conda'],
    SkillCategory.JAVASCRIPT: ['javascript','typescript','ecmascript','node'],
    SkillCategory.SECURITY: ['security','vulnerability','encryption','ssl','tls','xss','csrf'],
    SkillCategory.PERFORMANCE: ['performance','optimization','optimize','cache','latency','profiling'],
    SkillCategory.GENERAL: ['utility','helper','tool','generator','converter','formatter','validator','cli','fetch','search','weather','translate','file','image'],
}

def classify_skill(name: str, description: str, skill_md: str = '') -> SkillCategory:
    text = f"{name} {name} {name} {description} {description}"
    if skill_md:
        text += ' ' + skill_md[:500]
    text = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(len(re.findall(r'\b' + re.escape(k) + r'\b', text)) for k in keywords)
        if score > 0:
            scores[category] = score
    return max(scores, key=scores.get) if scores else SkillCategory.OTHER


def make_slug(owner: str, repo: str, skill_dir: str) -> str:
    """生成 slug，格式与 skillsmp id 一致：owner-repo-path-skill-md"""
    parts = f"{owner}-{repo}-{skill_dir.replace('/', '-')}-skill-md"
    return parts.lower()


def make_github_url(owner: str, repo: str, branch: str, skill_dir: str) -> str:
    return f"https://github.com/{owner}/{repo}/tree/{branch}/{skill_dir}"


def make_install_commands(owner: str, repo: str, branch: str, skill_dir: str):
    skill_name = skill_dir.split('/')[-1]
    repo_url = f"https://github.com/{owner}/{repo}"
    bash = "; ".join([
        "mkdir -p ~/.claude/skills",
        "cd ~/.claude/skills",
        f"git clone --depth 1 --branch {branch} --filter=blob:none --sparse {repo_url} .temp-install",
        "cd .temp-install",
        f"git sparse-checkout set {skill_dir}",
        f"mkdir -p ~/.claude/skills/{skill_name}",
        f"cp -r {skill_dir}/* ~/.claude/skills/{skill_name}/",
        "cd ..",
        "rm -rf .temp-install",
        f'echo "Skill installed: {skill_name}"',
    ])
    ps_path = skill_dir.replace('/', '\\')
    win = "; ".join([
        f'New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\\.claude\\skills"',
        f'Set-Location "$env:USERPROFILE\\.claude\\skills"',
        f"git clone --depth 1 --branch {branch} --filter=blob:none --sparse {repo_url} .temp-install",
        "Set-Location .temp-install",
        f"git sparse-checkout set {skill_dir}",
        f'New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\\.claude\\skills\\{skill_name}"',
        f'Copy-Item -Recurse -Path "{ps_path}\\*" -Destination "$env:USERPROFILE\\.claude\\skills\\{skill_name}\\"',
        f'Set-Location "$env:USERPROFILE\\.claude\\skills"',
        "Remove-Item -Recurse -Force .temp-install",
        f'Write-Host "Skill installed: {skill_name}"',
    ])
    return bash, win


# ── 限速控制 ─────────────────────────────────────────────────────────
async def gh_get(client: httpx.AsyncClient, url: str, params: dict = None, retries: int = 3):
    """带限速处理的 GitHub API GET"""
    for attempt in range(retries):
        await asyncio.sleep(2)  # 基础间隔，保证 Code Search <=30次/分钟
        try:
            resp = await client.get(url, params=params)

            if resp.status_code == 403:
                remaining = int(resp.headers.get('x-ratelimit-remaining', 1))
                reset = int(resp.headers.get('x-ratelimit-reset', 0))
                if remaining == 0:
                    wait = max(reset - datetime.now().timestamp(), 0) + 5
                    logger.warning(f"Rate limit，等待 {wait:.0f}s...")
                    await asyncio.sleep(wait)
                    continue

            if resp.status_code == 422:
                # 查询太复杂或超限，直接返回空
                return None

            if resp.status_code != 200:
                logger.warning(f"HTTP {resp.status_code}: {url}")
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                continue

            return resp.json()

        except Exception as e:
            logger.warning(f"请求异常: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(5)

    return None


# ── 进度跟踪 ─────────────────────────────────────────────────────────
def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        try:
            return json.loads(PROGRESS_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'completed_repos': [], 'total_new': 0, 'total_update': 0}


def save_progress(progress: dict):
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2, ensure_ascii=False), encoding='utf-8')


# ── 核心逻辑 ─────────────────────────────────────────────────────────
async def get_all_repos_in_range(client: httpx.AsyncClient, stars_range: str) -> list:
    """获取某 stars 范围内所有含 SKILL.md 的仓库"""
    repos = []
    page = 1
    while True:
        data = await gh_get(client, 'https://api.github.com/search/repositories', {
            'q': f'SKILL.md in:path {stars_range}',
            'per_page': 100,
            'page': page,
            'sort': 'stars',
        })
        if not data:
            break
        items = data.get('items', [])
        if not items:
            break
        repos.extend(items)
        total = data.get('total_count', 0)
        logger.info(f"  仓库分片 {stars_range} 第{page}页: {len(items)}个 (总{total})")
        if len(repos) >= total or len(items) < 100:
            break
        page += 1
    return repos


async def get_skill_files_in_repo(client: httpx.AsyncClient, full_name: str) -> list:
    """获取仓库内所有 SKILL.md 文件路径"""
    files = []
    page = 1
    while True:
        data = await gh_get(client, 'https://api.github.com/search/code', {
            'q': f'filename:SKILL.md repo:{full_name}',
            'per_page': 100,
            'page': page,
        })
        if not data:
            break
        items = data.get('items', [])
        if not items:
            break
        files.extend(items)
        total = data.get('total_count', 0)
        if len(files) >= total or len(items) < 100:
            break
        page += 1
    return files


async def fetch_raw_content(client: httpx.AsyncClient, html_url: str) -> str:
    """拉取文件 raw 内容"""
    raw_url = html_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
    try:
        resp = await client.get(raw_url, headers={**HEADERS, 'Accept': 'text/plain'})
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return ''


async def process_repo(client: httpx.AsyncClient, repo: dict, progress: dict) -> tuple:
    """处理一个仓库：找所有 SKILL.md 并保存"""
    full_name = repo['full_name']
    owner, repo_name = full_name.split('/', 1)
    stars = repo.get('stargazers_count', 0)
    forks = repo.get('forks_count', 0)
    description = (repo.get('description') or '')[:500]
    topics = repo.get('topics', [])
    default_branch = repo.get('default_branch', 'main')

    if full_name in progress['completed_repos']:
        return 0, 0, 0

    # 找该仓库所有 SKILL.md
    files = await get_skill_files_in_repo(client, full_name)
    if not files:
        progress['completed_repos'].append(full_name)
        return 0, 0, 0

    logger.info(f"  {full_name} ({stars} stars): {len(files)} 个 SKILL.md")

    new_count = update_count = skip_count = 0

    async with get_session() as session:
        repo_db = SkillRepository(session)

        for file_item in files:
            try:
                file_path = file_item.get('path', '')  # e.g. skills/git-auto/SKILL.md
                skill_dir = str(Path(file_path).parent)
                if skill_dir == '.':
                    skill_dir = ''

                # slug
                slug_path = skill_dir if skill_dir else repo_name
                slug = make_slug(owner, repo_name, slug_path)

                existing = await repo_db.get_by_slug(slug)

                if existing:
                    update_data = {}
                    if existing.stars != stars:
                        update_data['stars'] = stars
                    if existing.forks != forks:
                        update_data['forks'] = forks
                    if update_data:
                        await repo_db.update(existing.id, update_data)
                        update_count += 1
                    else:
                        skip_count += 1
                    continue

                # 新记录：拉 SKILL.md 内容
                html_url = file_item.get('html_url', '')
                skill_md = await fetch_raw_content(client, html_url)

                skill_name = Path(skill_dir).name if skill_dir else repo_name
                github_url = make_github_url(owner, repo_name, default_branch, skill_dir if skill_dir else '.')
                bash_cmd, win_cmd = make_install_commands(owner, repo_name, default_branch, skill_dir if skill_dir else repo_name)
                category = classify_skill(skill_name, description, skill_md)

                await repo_db.create({
                    'name': skill_name,
                    'slug': slug,
                    'description': description,
                    'author': owner,
                    'github_url': github_url,
                    'stars': stars,
                    'forks': forks,
                    'category': category,
                    'tags': topics,
                    'content': description,
                    'skill_md': skill_md,
                    'install_command': bash_cmd,
                    'install_command_windows': win_cmd,
                    'status': 'active',
                    'is_official': False,
                })
                new_count += 1

            except Exception as e:
                logger.error(f"    处理文件失败 {file_path}: {e}")

        await session.commit()

    progress['completed_repos'].append(full_name)
    progress['total_new'] = progress.get('total_new', 0) + new_count
    progress['total_update'] = progress.get('total_update', 0) + update_count
    return new_count, update_count, skip_count


async def main(test_mode: bool = True):
    """
    主函数
    test_mode=True: 只跑 stars>100 的少量仓库验证流程
    test_mode=False: 全量跑所有分片
    """
    if not GITHUB_TOKEN:
        logger.error("未配置 GITHUB_TOKEN")
        return

    logger.info("=" * 60)
    logger.info(f"GitHub SKILL.md 爬虫 (token: {GITHUB_TOKEN[:8]}...)")
    logger.info(f"模式: {'测试(stars>100)' if test_mode else '全量'}")
    logger.info("=" * 60)

    progress = load_progress()
    logger.info(f"已完成仓库: {len(progress['completed_repos'])}个，累计新增: {progress.get('total_new', 0)}")

    ranges = ['stars:>100'] if test_mode else STARS_RANGES

    async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        for stars_range in ranges:
            logger.info(f"\n=== 处理分片: {stars_range} ===")
            repos = await get_all_repos_in_range(client, stars_range)
            logger.info(f"共 {len(repos)} 个仓库")

            for i, repo in enumerate(repos, 1):
                full_name = repo['full_name']
                logger.info(f"[{i}/{len(repos)}] {full_name}")
                new, upd, skip = await process_repo(client, repo, progress)
                logger.info(f"  结果: 新增{new} 更新{upd} 跳过{skip}")
                save_progress(progress)

    logger.info(f"\n完成！总新增: {progress['total_new']}，总更新: {progress['total_update']}")


if __name__ == "__main__":
    import sys
    full_mode = '--full' in sys.argv
    asyncio.run(main(test_mode=not full_mode))

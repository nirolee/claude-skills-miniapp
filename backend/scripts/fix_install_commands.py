"""
修复 install_command 字段：将 /skills add 格式转换为正确的 git sparse-checkout 命令
同时生成对应的 install_command_windows（PowerShell 版本）

适用场景：爬虫写入了错误的 /skills add 格式，但 github_url 是有效的 GitHub tree URL
运行方式：cd backend && python scripts/fix_install_commands.py
"""
import re
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from src.storage.database import get_engine

def parse_github_tree_url(url):
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)', url)
    if not m:
        return None
    owner, repo, branch, path = m.groups()
    path = path.rstrip('/')
    skill_name = path.split('/')[-1]
    repo_url = "https://github.com/{}/{}".format(owner, repo)
    return repo_url, branch, path, skill_name

def generate_bash(repo_url, branch, skill_path, skill_name):
    parts = [
        "mkdir -p ~/.claude/skills",
        "cd ~/.claude/skills",
        "git clone --depth 1 --branch {} --filter=blob:none --sparse {} .temp-install".format(branch, repo_url),
        "cd .temp-install",
        "git sparse-checkout set {}".format(skill_path),
        "mkdir -p ~/.claude/skills/{}".format(skill_name),
        "cp -r {}/* ~/.claude/skills/{}/".format(skill_path, skill_name),
        "cd ..",
        "rm -rf .temp-install",
        'echo "✅ Skill 安装成功: {}"'.format(skill_name),
    ]
    return "; ".join(parts)

def generate_windows(repo_url, branch, skill_path, skill_name):
    backslash = "\\"
    ps_path = skill_path.replace('/', backslash)
    parts = [
        'New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills"',
        'Set-Location "$env:USERPROFILE\.claude\skills"',
        "git clone --depth 1 --branch {} --filter=blob:none --sparse {} .temp-install".format(branch, repo_url),
        "Set-Location .temp-install",
        "git sparse-checkout set {}".format(skill_path),
        'New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills\{}"'.format(skill_name),
        'Copy-Item -Recurse -Path "{}\*" -Destination "$env:USERPROFILE\.claude\skills\\\\"'.format(ps_path),
        'Set-Location "$env:USERPROFILE\.claude\skills"',
        "Remove-Item -Recurse -Force .temp-install",
        'Write-Host "✅ Skill 安装成功: {}"'.format(skill_name),
    ]
    return "; ".join(parts)

async def main():
    engine = get_engine()
    
    async with engine.begin() as conn:
        # 查询所有需要修复的记录
        result = await conn.execute(text(
            "SELECT id, name, github_url FROM skills "
            "WHERE install_command LIKE '/skills add%' "
            "AND github_url LIKE 'https://github.com/%/tree/%'"
        ))
        rows = result.fetchall()
        print("需要修复的记录数: {}".format(len(rows)))
        
        fixed = 0
        skipped = 0
        for row in rows:
            skill_id, name, github_url = row
            parsed = parse_github_tree_url(github_url)
            if not parsed:
                skipped += 1
                continue
            repo_url, branch, skill_path, skill_name = parsed
            bash_cmd = generate_bash(repo_url, branch, skill_path, skill_name)
            win_cmd = generate_windows(repo_url, branch, skill_path, skill_name)
            
            await conn.execute(text(
                "UPDATE skills SET install_command = :bash, install_command_windows = :win WHERE id = :id"
            ), {"bash": bash_cmd, "win": win_cmd, "id": skill_id})
            fixed += 1
            
            if fixed % 500 == 0:
                print("  已处理 {}...".format(fixed))
        
        print("修复完成: {} 条，跳过: {} 条".format(fixed, skipped))

asyncio.run(main())

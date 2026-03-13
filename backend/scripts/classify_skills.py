#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能分类器 - 根据技能名称、描述、标签自动分类
"""
import asyncio
import sys
from pathlib import Path
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage.database import get_session, SkillRepository
from src.storage.models import SkillCategory
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 分类关键词规则
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
        'scheduled', 'batch', 'task runner', 'orchestration',
        'slack', 'github', 'notion', 'jira', 'linear', 'trello',
        'calendar', 'reminder', 'notification', 'webhook', 'trigger',
        'zapier', 'make', 'n8n', 'integrat'
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
        'formatter', 'validator', 'parser', 'cli',
        'fetch', 'search', 'lookup', 'query', 'summarize', 'extract',
        'weather', 'translate', 'notes', 'browser', 'screenshot',
        'file', 'image', 'audio', 'video', 'pdf', 'csv', 'json',
        'manage', 'control', 'monitor', 'capture', 'stream'
    ],
}


def classify_skill(name: str, description: str, tags: list = None, skill_md: str = None) -> SkillCategory:
    """智能分类技能，综合 name/description/tags/skill_md"""
    # name 和 description 权重高，重复3次增加权重
    text = f"{name} {name} {name} {description} {description}"
    if tags:
        text += " " + " ".join(tags)
    # skill_md 内容丰富但噪音多，只取前 500 字符
    if skill_md:
        text += " " + skill_md[:500]

    text = text.lower()

    # 统计每个分类的匹配分数
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            # 使用单词边界匹配，避免误匹配
            pattern = r'\b' + re.escape(keyword) + r'\b'
            matches = len(re.findall(pattern, text))
            score += matches

        if score > 0:
            scores[category] = score

    # 返回得分最高的分类
    if scores:
        best_category = max(scores, key=scores.get)
        return best_category

    return SkillCategory.OTHER


async def reclassify_all_skills():
    """重新分类所有技能，分页处理全量数据"""
    from sqlalchemy import text as sa_text
    logger.info("=== 智能分类器 ===\n")

    PAGE_SIZE = 500
    offset = 0
    category_stats = {}
    update_count = 0
    total_processed = 0

    # 先查总数
    async with get_session() as session:
        result = await session.execute(sa_text("SELECT COUNT(*) FROM skills"))
        grand_total = result.scalar()
    logger.info(f"总技能数: {grand_total}，开始分页重新分类...\n")

    while True:
        async with get_session() as session:
            result = await session.execute(sa_text("""
                SELECT id, name, description, tags, category, skill_md
                FROM skills
                ORDER BY id ASC
                LIMIT :limit OFFSET :offset
            """), {"limit": PAGE_SIZE, "offset": offset})
            rows = result.fetchall()

        if not rows:
            break

        async with get_session() as session:
            repo = SkillRepository(session)
            for row in rows:
                try:
                    import json
                    tags = row.tags if isinstance(row.tags, list) else (json.loads(row.tags) if row.tags else [])
                    old_category = row.category
                    new_category = classify_skill(
                        row.name,
                        row.description or '',
                        tags,
                        row.skill_md
                    )

                    if str(old_category) != str(new_category) and str(old_category) != new_category.value:
                        await repo.update(row.id, {'category': new_category})
                        update_count += 1

                    category_stats[new_category.value] = category_stats.get(new_category.value, 0) + 1
                    total_processed += 1

                except Exception as e:
                    logger.error(f"分类失败: {row.name}, {e}")

        offset += PAGE_SIZE
        logger.info(f"  进度: {total_processed}/{grand_total} ({total_processed/grand_total*100:.1f}%) 已更新: {update_count}")

    logger.info(f"\n✅ 分类完成！")
    logger.info(f"  总处理: {total_processed}，更新: {update_count}")
    logger.info(f"\n📊 分类统计:")
    sorted_stats = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    for category, count in sorted_stats:
        percentage = count / total_processed * 100 if total_processed else 0
        logger.info(f"  {category:20s}: {count:5d} ({percentage:5.1f}%)")


async def main():
    """主函数"""
    from datetime import datetime
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    await reclassify_all_skills()

    logger.info(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())

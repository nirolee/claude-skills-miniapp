"""
改进的 SkillsMP 爬虫
增强 Cloudflare 绕过能力和错误处理
"""
import re
import logging
from typing import List, Dict, Any
import asyncio
import random

from .base_crawler import BaseCrawler
from ..storage.database import get_session, SkillRepository
from ..storage.models import SkillCategory

logger = logging.getLogger(__name__)


class ImprovedSkillsMPCrawler:
    """改进的 SkillsMP 爬虫，增强反检测能力"""

    BASE_URL = "https://skillsmp.com/zh"

    def __init__(self):
        pass

    async def fetch_skills_list(self, max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        抓取技能列表（改进版）

        策略：
        1. 更长的初始等待时间（绕过 Cloudflare）
        2. 随机延迟模拟真实用户
        3. 多种选择器尝试
        4. 详细日志记录
        """
        skills = []

        async with BaseCrawler(
            headless=True,
            timeout=60000  # 增加超时时间到 60 秒
        ) as crawler:
            try:
                logger.info(f"访问 SkillsMP: {self.BASE_URL}")

                # 访问页面
                await crawler.page.goto(self.BASE_URL, wait_until="networkidle", timeout=60000)

                # 等待 Cloudflare 验证完成
                logger.info("等待 Cloudflare 验证...")
                await asyncio.sleep(8)

                # 检查是否被 Cloudflare 拦截
                page_title = await crawler.page.title()
                page_content = await crawler.page.content()

                if "cloudflare" in page_title.lower() or "attention required" in page_title.lower():
                    logger.error(f"被 Cloudflare 拦截: {page_title}")

                    # 尝试等待更长时间
                    logger.info("尝试等待 Cloudflare 自动通过...")
                    await asyncio.sleep(15)

                    # 重新检查
                    page_title = await crawler.page.title()
                    if "cloudflare" in page_title.lower():
                        logger.error("Cloudflare 验证失败，无法继续")
                        return []

                logger.info(f"页面标题: {page_title}")

                # 等待技能列表加载
                logger.info("等待技能列表加载...")

                # 尝试多种可能的选择器
                selectors = [
                    'a[href*="/skills/"]',  # 包含 skills 的链接
                    '[class*="skill"]',      # 包含 skill 的 class
                    '[class*="card"]',       # 卡片布局
                    'article',               # 文章标签
                    '[data-skill]',          # 数据属性
                ]

                skill_elements = []
                for selector in selectors:
                    try:
                        elements = await crawler.page.query_selector_all(selector)
                        if elements:
                            logger.info(f"使用选择器 '{selector}' 找到 {len(elements)} 个元素")
                            skill_elements = elements
                            break
                    except Exception as e:
                        logger.debug(f"选择器 '{selector}' 失败: {e}")

                if not skill_elements:
                    logger.warning("未找到任何技能元素，保存截图用于调试")
                    await crawler.page.screenshot(path='D:/niro/claude-skills-miniapp/backend/scripts/debug_skillsmp.png', full_page=True)

                    # 保存 HTML
                    with open('D:/niro/claude-skills-miniapp/backend/scripts/debug_skillsmp.html', 'w', encoding='utf-8') as f:
                        f.write(page_content)

                    logger.info("已保存调试文件: debug_skillsmp.png 和 debug_skillsmp.html")
                    return []

                # 滚动加载更多
                processed_urls = set()

                for scroll_round in range(max_pages):
                    logger.info(f"第 {scroll_round + 1} 轮加载...")

                    if scroll_round > 0:
                        # 滚动到底部
                        await crawler.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

                        # 随机延迟 2-4 秒
                        delay = random.uniform(2, 4)
                        await asyncio.sleep(delay)

                    # 重新获取所有技能链接
                    links = await crawler.page.query_selector_all('a[href*="/skills/"]')
                    logger.info(f"当前找到 {len(links)} 个技能链接")

                    new_skills_count = 0

                    for link in links:
                        try:
                            url = await link.get_attribute('href')
                            if not url or url in processed_urls:
                                continue

                            processed_urls.add(url)

                            # 完整 URL
                            if not url.startswith('http'):
                                url = f"https://skillsmp.com{url}"

                            # 提取 slug
                            slug_match = re.search(r'/skills/([^/?#]+)', url)
                            if not slug_match:
                                continue

                            slug = slug_match.group(1)

                            # 提取文本信息
                            text = await link.inner_text()
                            lines = [line.strip() for line in text.split('\n') if line.strip()]

                            if not lines:
                                continue

                            # 解析技能信息
                            name = lines[0].replace('.md', '').replace('export', '').strip()
                            description = lines[1] if len(lines) > 1 else ""
                            author = "unknown"
                            stars = 0

                            # 提取作者和 stars
                            for line in lines:
                                # 匹配 stars 格式: "125.9k", "1.2k", "500"
                                if 'k' in line.lower() or line.replace(',', '').isdigit():
                                    stars = self._parse_stars(line)
                                # 匹配仓库格式: "org/repo"
                                if '/' in line and len(line.split('/')) == 2:
                                    parts = line.split('/')
                                    if len(parts[0]) > 0 and len(parts[1]) > 0:
                                        author = parts[0]

                            skill = {
                                'name': name,
                                'slug': self._generate_slug(name, author, url),
                                'description': description,
                                'author': author,
                                'github_url': url,
                                'stars': stars,
                                'category': SkillCategory.OTHER,
                                'tags': self._extract_tags(name + ' ' + description),
                                'install_command': f'claude skill install {url}',
                            }

                            skills.append(skill)
                            new_skills_count += 1

                            logger.info(f"✓ 获取技能: {name} ({author}) - {stars} stars")

                        except Exception as e:
                            logger.debug(f"解析技能失败: {e}")
                            continue

                    logger.info(f"第 {scroll_round + 1} 轮完成，本轮新增 {new_skills_count} 个技能")

                    # 如果没有新增，停止滚动
                    if new_skills_count == 0:
                        logger.info("没有发现新技能，停止加载")
                        break

                logger.info(f"技能列表抓取完成，共 {len(skills)} 个")

            except Exception as e:
                logger.error(f"抓取失败: {e}", exc_info=True)

        return skills

    def _parse_stars(self, text: str) -> int:
        """解析 stars 数量"""
        text = text.strip().lower().replace(',', '')

        if 'k' in text:
            try:
                num = float(text.replace('k', ''))
                return int(num * 1000)
            except:
                return 0

        try:
            return int(text)
        except:
            return 0

    def _generate_slug(self, name: str, author: str, url: str) -> str:
        """生成唯一 slug"""
        # 优先使用 URL 中的 slug
        slug_match = re.search(r'/skills/([^/?#]+)', url)
        if slug_match:
            return slug_match.group(1)

        # 否则生成
        base = f"{author}-{name}" if author and author != "unknown" else name
        slug = base.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")[:200]

    def _extract_tags(self, text: str) -> List[str]:
        """提取技术标签"""
        keywords = [
            "playwright", "react", "vue", "python", "javascript",
            "typescript", "nodejs", "testing", "debugging", "api",
            "docker", "kubernetes", "git", "github", "aws"
        ]

        text_lower = text.lower()
        tags = [kw for kw in keywords if kw in text_lower]
        return tags[:10]

    async def save_skills_to_db(self, skills: List[Dict[str, Any]]) -> int:
        """保存技能到数据库"""
        saved_count = 0

        async with get_session() as session:
            repo = SkillRepository(session)

            for skill_data in skills:
                try:
                    # 检查是否已存在
                    existing = await repo.get_by_slug(skill_data['slug'])
                    if existing:
                        logger.info(f"技能已存在，跳过: {skill_data['name']}")
                        continue

                    # 创建新技能
                    skill = await repo.create(
                        name=skill_data['name'],
                        slug=skill_data['slug'],
                        description=skill_data['description'],
                        author=skill_data['author'],
                        github_url=skill_data['github_url'],
                        stars=skill_data['stars'],
                        category=skill_data['category'],
                        tags=skill_data['tags'],
                        install_command=skill_data['install_command'],
                    )

                    saved_count += 1
                    logger.info(f"✓ 保存成功: {skill.name}")

                except Exception as e:
                    logger.error(f"保存技能失败 {skill_data['name']}: {e}")

        return saved_count


async def run_improved_crawler(max_pages: int = 10):
    """运行改进的爬虫"""
    crawler = ImprovedSkillsMPCrawler()

    logger.info("开始抓取 SkillsMP...")
    skills = await crawler.fetch_skills_list(max_pages=max_pages)

    logger.info(f"抓取到 {len(skills)} 个技能")

    if skills:
        logger.info("开始保存到数据库...")
        saved = await crawler.save_skills_to_db(skills)
        logger.info(f"保存成功 {saved} 个技能")

    return skills

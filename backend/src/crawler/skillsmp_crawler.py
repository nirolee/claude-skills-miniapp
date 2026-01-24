"""
SkillsMP 爬虫
从 skillsmp.com/zh 抓取技能数据
"""
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from .base_crawler import BaseCrawler
from ..config import get_settings
from ..storage.database import get_session, SkillRepository
from ..storage.models import SkillCategory

logger = logging.getLogger(__name__)


class SkillsMPCrawler:
    """SkillsMP 网站爬虫"""

    BASE_URL = "https://skillsmp.com/zh"
    SKILLS_LIST_URL = f"{BASE_URL}"

    def __init__(self):
        self.settings = get_settings()

    def _map_category(self, category_text: str) -> SkillCategory:
        """
        将 SkillsMP 的分类映射到数据库分类

        SkillsMP 分类:
        - tools (工具) -> DEVELOPMENT
        - development (开发) -> DEVELOPMENT
        - data-ai (数据与AI) -> DATA_ANALYSIS
        - business (商业) -> OTHER
        - devops (DevOps) -> DEVOPS
        - testing-security (测试与安全) -> TESTING
        - documentation (文档) -> DOCUMENTATION
        - content-media (内容与媒体) -> OTHER
        - lifestyle (生活方式) -> OTHER
        - research (研究) -> OTHER
        - databases (数据库) -> OTHER
        - blockchain (区块链) -> OTHER
        """
        category_lower = category_text.lower().strip()

        mapping = {
            "testing": SkillCategory.TESTING,
            "testing-security": SkillCategory.TESTING,
            "debugging": SkillCategory.DEBUGGING,
            "development": SkillCategory.DEVELOPMENT,
            "tools": SkillCategory.DEVELOPMENT,
            "automation": SkillCategory.AUTOMATION,
            "documentation": SkillCategory.DOCUMENTATION,
            "design": SkillCategory.DESIGN,
            "data-ai": SkillCategory.DATA_ANALYSIS,
            "devops": SkillCategory.DEVOPS,
        }

        return mapping.get(category_lower, SkillCategory.OTHER)

    def _extract_tags(self, description: str, content: str = "") -> List[str]:
        """从描述和内容中提取标签"""
        tags = set()

        # 常见技术关键词
        keywords = [
            "playwright", "react", "vue", "angular", "python", "javascript",
            "typescript", "nodejs", "fastapi", "express", "testing",
            "debugging", "automation", "deployment", "docker", "kubernetes",
            "aws", "azure", "gcp", "git", "vitest", "pytest", "jest",
            "selenium", "cypress", "api", "rest", "graphql", "sql",
            "mongodb", "redis", "nginx", "ci/cd", "github", "gitlab"
        ]

        combined_text = (description + " " + content).lower()

        for keyword in keywords:
            if keyword in combined_text:
                tags.add(keyword)

        return list(tags)[:10]  # 最多返回10个标签

    def _generate_slug(self, name: str, author: str = "") -> str:
        """生成 URL slug"""
        # 使用 name + author 生成唯一 slug
        base = f"{author}-{name}" if author else name
        slug = base.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug[:200]  # 限制长度

    def _parse_stars(self, stars_text: str) -> int:
        """解析 stars 数量，支持 k 格式（如 95.4k）"""
        if not stars_text:
            return 0

        stars_text = stars_text.strip().lower()

        # 移除逗号
        stars_text = stars_text.replace(",", "")

        # 处理 k (千) 格式
        if "k" in stars_text:
            try:
                num = float(stars_text.replace("k", ""))
                return int(num * 1000)
            except ValueError:
                return 0

        # 处理普通数字
        try:
            return int(stars_text)
        except ValueError:
            return 0

    async def fetch_skills_list(
        self, max_pages: int = 5, start_page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        抓取技能列表

        Args:
            max_pages: 最多抓取多少页（每页12条）
            start_page: 起始页码

        Returns:
            技能基础信息列表
        """
        skills = []

        async with BaseCrawler(headless=True) as crawler:  # 服务器使用 headless 模式
            try:
                # 访问首页
                logger.info(f"访问 SkillsMP 首页: {self.SKILLS_LIST_URL}")
                await crawler.fetch_page(self.SKILLS_LIST_URL)

                # 等待页面完全加载（等待技能列表出现）
                await asyncio.sleep(5)

                processed_urls = set()  # 去重（在循环外定义）
                prev_count = 0  # 记录上一轮的技能数量

                # 使用滚动加载代替翻页（SkillsMP 使用无限滚动）
                for scroll_round in range(max_pages):
                    logger.info(f"正在加载第 {scroll_round + 1} 轮数据...")

                    # 滚动到页面底部触发懒加载
                    if scroll_round > 0:
                        try:
                            await crawler.scroll_to_bottom(pause_time=1000)
                            await asyncio.sleep(3)  # 等待新内容加载
                        except Exception as e:
                            logger.warning(f"滚动加载失败: {e}")
                            break

                    # 获取当前所有技能链接
                    skill_links = await crawler.page.query_selector_all('a[href*="/skills/"]')
                    logger.info(f"当前找到 {len(skill_links)} 个技能链接")

                    for link in skill_links:
                        try:
                            # 提取 URL
                            skill_url = await link.get_attribute("href")
                            if not skill_url or skill_url in processed_urls:
                                continue

                            processed_urls.add(skill_url)

                            # 提取完整 URL
                            if not skill_url.startswith("http"):
                                skill_url = f"https://skillsmp.com{skill_url}"

                            # 提取 slug（从 URL 中）
                            slug_match = re.search(r'/skills/([^/?#]+)', skill_url)
                            if not slug_match:
                                continue

                            slug = slug_match.group(1)

                            # 提取链接内的所有文本内容
                            text_content = await link.inner_text()
                            lines = [line.strip() for line in text_content.split('\n') if line.strip()]

                            # 从文本中解析信息
                            name = ""
                            description = ""
                            author = "unknown"
                            stars = 0
                            updated_at = None

                            # 第一行通常是文件名或技能名
                            if lines:
                                first_line = lines[0]
                                if first_line.endswith('.md'):
                                    name = first_line.replace('.md', '').replace('export', '').strip()
                                else:
                                    name = first_line.replace('export', '').strip()

                            # 尝试提取 stars（如 95.4k, 66.0k）
                            for line in lines:
                                if 'k' in line.lower() and any(c.isdigit() for c in line):
                                    stars = self._parse_stars(line)
                                    break

                            # 尝试提取作者（from "xxx/xxx"）
                            for line in lines:
                                if 'from' in line.lower():
                                    author_match = re.search(r'from\s+"([^"]+)"', line)
                                    if author_match:
                                        author = author_match.group(1).split("/")[0]
                                    break

                            # 提取描述（最长的文本行）
                            for line in lines[1:]:  # 跳过第一行（通常是名称）
                                if len(line) > 30 and 'from' not in line.lower() and 'k' not in line.lower():
                                    description = line
                                    break

                            # 尝试提取日期
                            for line in lines:
                                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
                                if date_match:
                                    updated_at = date_match.group(1)
                                    break

                            # 如果没有名称，使用 slug
                            if not name:
                                name = slug.replace('-', ' ').title()

                            # 如果没有描述，使用默认值
                            if not description:
                                description = f"{name} by {author}"

                            skill_info = {
                                "name": name,
                                "slug": slug,
                                "description": description,
                                "author": author,
                                "github_url": skill_url,
                                "stars": stars,
                                "updated_at": updated_at,
                            }
                            skills.append(skill_info)
                            logger.info(f"✓ 提取技能: {name} ({author}) - {stars} stars")

                        except Exception as e:
                            logger.error(f"提取技能链接失败: {e}")
                            continue

                    logger.info(f"第 {scroll_round + 1} 轮完成，当前共提取 {len(skills)} 个技能")

                    # 检查是否还有新技能（如果本轮没有新增，停止）
                    if scroll_round > 0 and len(skills) == prev_count:
                        logger.info("没有发现新技能，停止加载")
                        break

                    prev_count = len(skills)

                    # 避免请求过快
                    await asyncio.sleep(2)

                logger.info(f"技能列表抓取完成，共 {len(skills)} 个")

            except Exception as e:
                logger.error(f"抓取技能列表失败: {e}")
                import traceback
                traceback.print_exc()
                raise

        return skills

    async def fetch_skill_detail(self, detail_url: str) -> Optional[Dict[str, Any]]:
        """
        抓取技能详情页

        Args:
            detail_url: 技能详情页URL

        Returns:
            完整的技能信息
        """
        async with BaseCrawler(headless=True) as crawler:
            try:
                logger.info(f"访问详情页: {detail_url}")
                await crawler.fetch_page(detail_url)
                await asyncio.sleep(2)

                # 提取完整 Markdown 内容
                content_elem = await crawler.page.query_selector('article, [class*="markdown"], main')
                content = await content_elem.inner_text() if content_elem else ""

                # 提取分类（从页面中的分类标签）
                category_elem = await crawler.page.query_selector('[class*="category"], [class*="tag"]')
                category_text = await category_elem.inner_text() if category_elem else "other"
                category = self._map_category(category_text)

                # 提取 GitHub URL（如果有）
                github_links = await crawler.page.query_selector_all('a[href*="github.com"]')
                github_url = detail_url  # 默认使用详情页URL
                if github_links:
                    github_url = await github_links[0].get_attribute("href")

                # 提取标签
                tags = self._extract_tags(content[:500], content)

                return {
                    "content": content,
                    "category": category,
                    "github_url": github_url,
                    "tags": tags,
                }

            except Exception as e:
                logger.error(f"抓取详情页失败 {detail_url}: {e}")
                return None

    async def save_skills_to_db(self, skills: List[Dict[str, Any]]) -> int:
        """
        保存技能到数据库

        Args:
            skills: 技能数据列表

        Returns:
            保存成功的数量
        """
        saved_count = 0

        async with get_session() as session:
            repo = SkillRepository(session)

            for skill_data in skills:
                try:
                    # 检查是否已存在
                    existing = await repo.get_by_slug(skill_data["slug"])

                    if existing:
                        logger.info(f"技能已存在，跳过: {skill_data['name']}")
                        continue

                    # 生成安装命令
                    skill_data["install_command"] = f"/skills add {skill_data['github_url']}"

                    # 设置默认值
                    skill_data.setdefault("forks", 0)
                    skill_data.setdefault("is_official", False)
                    skill_data.setdefault("status", "active")

                    # 创建新技能
                    await repo.create(skill_data)
                    saved_count += 1
                    logger.info(f"保存技能成功: {skill_data['name']}")

                except Exception as e:
                    logger.error(f"保存技能失败 {skill_data.get('name')}: {e}")
                    continue

        return saved_count

    async def run(
        self,
        max_pages: int = 5,
        fetch_detail: bool = False
    ) -> Dict[str, Any]:
        """
        运行爬虫

        Args:
            max_pages: 最多抓取多少页
            fetch_detail: 是否抓取详情页（更慢但数据更完整）

        Returns:
            执行结果统计
        """
        logger.info(f"开始抓取 SkillsMP 技能（最多 {max_pages} 页）...")

        start_time = datetime.now()

        try:
            # 1. 抓取技能列表
            skills = await self.fetch_skills_list(max_pages=max_pages)
            logger.info(f"抓取到 {len(skills)} 个技能")

            # 2. 如果需要，抓取详情页
            if fetch_detail:
                logger.info("开始抓取详情页...")
                for i, skill in enumerate(skills):
                    detail = await self.fetch_skill_detail(skill["github_url"])
                    if detail:
                        skill.update(detail)

                    # 每10个技能休息一下
                    if (i + 1) % 10 == 0:
                        logger.info(f"已抓取 {i + 1}/{len(skills)} 个详情页")
                        await asyncio.sleep(2)
            else:
                # 不抓取详情页时，使用默认值
                for skill in skills:
                    skill["content"] = skill["description"]
                    skill["category"] = SkillCategory.OTHER
                    skill["tags"] = self._extract_tags(skill["description"])

            # 3. 保存到数据库
            saved_count = await self.save_skills_to_db(skills)
            logger.info(f"保存 {saved_count} 个技能到数据库")

            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            return {
                "success": True,
                "total_found": len(skills),
                "total_saved": saved_count,
                "duration_seconds": duration,
                "message": f"成功抓取 {len(skills)} 个技能，保存 {saved_count} 个",
            }

        except Exception as e:
            logger.error(f"爬虫执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"爬虫执行失败: {e}",
            }

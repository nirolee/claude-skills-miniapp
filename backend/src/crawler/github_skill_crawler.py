"""
GitHub 技能爬虫
从 anthropics/skills 仓库抓取技能数据
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


class GitHubSkillCrawler:
    """GitHub 技能爬虫"""

    GITHUB_SKILLS_URL = "https://github.com/anthropics/skills"
    GITHUB_API_URL = "https://api.github.com/repos/anthropics/skills"

    def __init__(self):
        self.settings = get_settings()

    def _extract_category(self, skill_path: str, content: str) -> SkillCategory:
        """
        从路径和内容推断技能分类

        Args:
            skill_path: 技能路径，如 "skills/debugging/..."
            content: 技能内容

        Returns:
            SkillCategory 枚举值
        """
        # 从路径推断
        path_lower = skill_path.lower()

        if "debug" in path_lower:
            return SkillCategory.DEBUGGING
        elif "test" in path_lower:
            return SkillCategory.TESTING
        elif "automat" in path_lower:
            return SkillCategory.AUTOMATION
        elif "design" in path_lower or "ui" in path_lower or "frontend" in path_lower:
            return SkillCategory.DESIGN
        elif "doc" in path_lower:
            return SkillCategory.DOCUMENTATION
        elif "devops" in path_lower or "deploy" in path_lower:
            return SkillCategory.DEVOPS
        elif "data" in path_lower or "analysis" in path_lower:
            return SkillCategory.DATA_ANALYSIS
        elif "dev" in path_lower:
            return SkillCategory.DEVELOPMENT

        # 从内容推断
        content_lower = content.lower()

        if any(
            keyword in content_lower
            for keyword in ["debug", "troubleshoot", "diagnose"]
        ):
            return SkillCategory.DEBUGGING
        elif any(
            keyword in content_lower
            for keyword in ["test", "testing", "playwright", "selenium"]
        ):
            return SkillCategory.TESTING
        elif any(
            keyword in content_lower for keyword in ["automate", "automation", "script"]
        ):
            return SkillCategory.AUTOMATION
        elif any(
            keyword in content_lower
            for keyword in ["design", "ui", "frontend", "react", "vue"]
        ):
            return SkillCategory.DESIGN
        elif any(
            keyword in content_lower for keyword in ["document", "documentation", "docs"]
        ):
            return SkillCategory.DOCUMENTATION

        return SkillCategory.OTHER

    def _extract_tags(self, content: str) -> List[str]:
        """
        从内容中提取标签

        Args:
            content: 技能内容

        Returns:
            标签列表
        """
        tags = []

        # 常见技术关键词
        keywords = [
            "playwright",
            "react",
            "vue",
            "angular",
            "python",
            "javascript",
            "typescript",
            "nodejs",
            "fastapi",
            "express",
            "testing",
            "debugging",
            "automation",
            "deployment",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "git",
        ]

        content_lower = content.lower()

        for keyword in keywords:
            if keyword in content_lower:
                tags.append(keyword)

        return tags[:10]  # 最多返回10个标签

    def _extract_skill_info(self, content: str) -> Dict[str, Any]:
        """
        从 SKILL.md 内容中提取技能信息

        Args:
            content: SKILL.md 文件内容

        Returns:
            包含 name, description, author 等的字典
        """
        lines = content.split("\n")

        info = {
            "name": "",
            "description": "",
            "author": "anthropics",
        }

        # 提取标题（通常是第一个 # 标题）
        for line in lines:
            if line.startswith("# ") and not info["name"]:
                info["name"] = line[2:].strip()
                break

        # 提取描述（标题后的第一段非空文本）
        found_title = False
        for line in lines:
            if line.startswith("# "):
                found_title = True
                continue

            if found_title and line.strip() and not line.startswith("#"):
                info["description"] = line.strip()
                break

        # 如果没有提取到描述，使用前100个字符
        if not info["description"]:
            info["description"] = content[:100].strip()

        return info

    def _generate_slug(self, name: str) -> str:
        """
        生成 URL slug

        Args:
            name: 技能名称

        Returns:
            slug 字符串
        """
        slug = name.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug

    def _generate_install_command(self, github_url: str) -> str:
        """
        生成安装命令

        Args:
            github_url: GitHub 仓库 URL

        Returns:
            安装命令字符串
        """
        # 假设使用 Claude Code 的插件安装命令
        return f"claude plugin install {github_url}"

    async def fetch_skills_from_github(self) -> List[Dict[str, Any]]:
        """
        从 GitHub 抓取技能列表

        Returns:
            技能数据列表
        """
        skills = []

        async with BaseCrawler(headless=True) as crawler:
            try:
                # 访问 GitHub 技能仓库
                result = await crawler.fetch_page(
                    self.GITHUB_SKILLS_URL,
                    wait_selector=".js-navigation-container",
                )

                logger.info(f"成功访问 {self.GITHUB_SKILLS_URL}")

                # 提取技能目录链接
                skill_links = await crawler.extract_elements(
                    'a[href*="/anthropics/skills/tree/main/skills/"]',
                    extract_type="attribute",
                    attribute="href",
                )

                logger.info(f"找到 {len(skill_links)} 个技能")

                # 访问每个技能详情页
                for link in skill_links[:5]:  # 先只抓取前5个作为测试
                    if not link.startswith("http"):
                        link = f"https://github.com{link}"

                    try:
                        skill_result = await crawler.fetch_page(
                            link, wait_selector=".file-header"
                        )

                        # 提取 SKILL.md 内容
                        skill_content_elements = await crawler.extract_elements(
                            'article.markdown-body',
                            extract_type="text",
                        )

                        if skill_content_elements:
                            skill_content = skill_content_elements[0]

                            # 解析技能信息
                            skill_info = self._extract_skill_info(skill_content)

                            if skill_info["name"]:
                                skill_data = {
                                    "name": skill_info["name"],
                                    "slug": self._generate_slug(skill_info["name"]),
                                    "description": skill_info["description"],
                                    "author": skill_info["author"],
                                    "github_url": link,
                                    "category": self._extract_category(
                                        link, skill_content
                                    ),
                                    "tags": self._extract_tags(skill_content),
                                    "content": skill_content,
                                    "install_command": self._generate_install_command(
                                        link
                                    ),
                                    "is_official": True,
                                    "stars": 0,  # 稍后通过 GitHub API 获取
                                    "forks": 0,
                                }

                                skills.append(skill_data)
                                logger.info(f"成功提取技能: {skill_info['name']}")

                        # 避免请求过快
                        await asyncio.sleep(1)

                    except Exception as e:
                        logger.error(f"处理技能链接失败 {link}: {e}")
                        continue

            except Exception as e:
                logger.error(f"抓取技能列表失败: {e}")
                raise

        return skills

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

                    # 创建新技能
                    await repo.create(skill_data)
                    saved_count += 1
                    logger.info(f"保存技能成功: {skill_data['name']}")

                except Exception as e:
                    logger.error(f"保存技能失败 {skill_data['name']}: {e}")
                    continue

        return saved_count

    async def run(self) -> Dict[str, Any]:
        """
        运行爬虫

        Returns:
            执行结果统计
        """
        logger.info("开始抓取 GitHub 技能...")

        start_time = datetime.now()

        try:
            # 抓取技能
            skills = await self.fetch_skills_from_github()
            logger.info(f"抓取到 {len(skills)} 个技能")

            # 保存到数据库
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

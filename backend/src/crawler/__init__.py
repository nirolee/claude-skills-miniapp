"""爬虫模块"""
from .base_crawler import BaseCrawler
from .github_skill_crawler import GitHubSkillCrawler
from .skillsmp_crawler import SkillsMPCrawler

__all__ = ["BaseCrawler", "GitHubSkillCrawler", "SkillsMPCrawler"]

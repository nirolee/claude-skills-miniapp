"""
配置管理模块
使用 pydantic-settings 从环境变量和 .env 文件读取配置
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import json


def load_claude_code_config() -> Optional[dict]:
    """
    加载 Claude Code 的配置文件

    Returns:
        配置字典，如果文件不存在则返回 None
    """
    try:
        # Claude Code 配置文件路径
        claude_config_path = Path.home() / ".claude" / "settings.json"

        if claude_config_path.exists():
            with open(claude_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('env', {})
    except Exception:
        pass

    return None


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基础配置
    app_name: str = "Claude Skills 小程序"
    app_version: str = "1.0.0"
    debug: bool = False

    # MySQL 数据库配置
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "claude_skills"
    mysql_charset: str = "utf8mb4"

    # Redis 配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # 微信小程序配置
    wechat_appid: str = ""
    wechat_secret: str = ""

    # GitHub API 配置（用于爬取技能数据）
    github_token: Optional[str] = None
    github_api_base: str = "https://api.github.com"

    # Anthropic API 配置（用于翻译功能）
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    anthropic_base_url: Optional[str] = None  # 支持代理配置

    # 爬虫配置
    crawler_user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    crawler_timeout: int = 30000
    max_concurrent_requests: int = 3

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_prefix: str = "/api"
    cors_origins: list[str] = ["*"]

    # 日志配置
    log_level: str = "INFO"
    log_file: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def database_url(self) -> str:
        """构建数据库连接 URL"""
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset={self.mysql_charset}"
        )

    @property
    def redis_url(self) -> str:
        """构建 Redis 连接 URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    def get_anthropic_config(self) -> dict:
        """
        获取 Anthropic API 配置

        优先级：
        1. .env 配置文件
        2. Claude Code 配置 (~/.claude/settings.json)
        3. 系统环境变量（由 SDK 自动读取）

        Returns:
            包含 api_key 和 base_url 的字典
        """
        config = {}

        # 优先使用 .env 配置
        if self.anthropic_api_key:
            config['api_key'] = self.anthropic_api_key
        if self.anthropic_base_url:
            config['base_url'] = self.anthropic_base_url

        # 如果没有配置，尝试从 Claude Code 读取
        if not config.get('api_key'):
            claude_config = load_claude_code_config()
            if claude_config:
                if claude_config.get('ANTHROPIC_API_KEY'):
                    config['api_key'] = claude_config['ANTHROPIC_API_KEY']
                if claude_config.get('ANTHROPIC_BASE_URL'):
                    config['base_url'] = claude_config['ANTHROPIC_BASE_URL']

        # 如果还是没有，让 SDK 自动从环境变量读取（返回空字典）
        return config


# 全局配置单例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

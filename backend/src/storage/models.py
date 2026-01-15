"""
数据模型定义
使用 SQLAlchemy 2.0 声明式映射
"""
from datetime import datetime
from typing import Optional
import enum

from sqlalchemy import (
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    Enum,
    Index,
    ForeignKey,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """所有模型的基类"""

    pass


class SkillCategory(str, enum.Enum):
    """技能分类枚举"""

    DEBUGGING = "debugging"
    TESTING = "testing"
    AUTOMATION = "automation"
    DEVELOPMENT = "development"
    DOCUMENTATION = "documentation"
    DESIGN = "design"
    DATA_ANALYSIS = "data_analysis"
    DEVOPS = "devops"
    OTHER = "other"


class SkillStatus(str, enum.Enum):
    """技能状态枚举"""

    ACTIVE = "active"  # 正常可用
    ARCHIVED = "archived"  # 已归档
    PENDING = "pending"  # 待审核（用户提交）


class Skill(Base):
    """技能模型"""

    __tablename__ = "skills"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 基础信息
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(
        String(200), nullable=False, unique=True, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(200), nullable=False)

    # GitHub 信息
    github_url: Mapped[str] = mapped_column(String(500), nullable=False)
    github_repo: Mapped[Optional[str]] = mapped_column(String(200))  # owner/repo
    stars: Mapped[int] = mapped_column(Integer, default=0)
    forks: Mapped[int] = mapped_column(Integer, default=0)

    # 分类和标签
    category: Mapped[SkillCategory] = mapped_column(
        Enum(SkillCategory), default=SkillCategory.OTHER, index=True
    )
    tags: Mapped[Optional[dict]] = mapped_column(JSON)  # ["tag1", "tag2"]

    # 内容
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 完整的 SKILL.md
    install_command: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # 安装命令

    # 状态
    status: Mapped[SkillStatus] = mapped_column(
        Enum(SkillStatus), default=SkillStatus.ACTIVE, index=True
    )
    is_official: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否官方技能

    # 统计信息（冗余字段，用于快速查询）
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite", back_populates="skill", cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_skill_category_status", "category", "status"),
        Index("idx_skill_stars", "stars"),
        Index("idx_skill_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 微信信息
    openid: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    unionid: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    session_key: Mapped[Optional[str]] = mapped_column(String(100))

    # 用户信息
    nickname: Mapped[str] = mapped_column(String(200), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    gender: Mapped[Optional[int]] = mapped_column(Integer)  # 0=未知, 1=男, 2=女
    city: Mapped[Optional[str]] = mapped_column(String(100))
    province: Mapped[Optional[str]] = mapped_column(String(100))
    country: Mapped[Optional[str]] = mapped_column(String(100))

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # 关系
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, nickname='{self.nickname}')>"


class Favorite(Base):
    """收藏模型"""

    __tablename__ = "favorites"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 外键
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 关系
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="favorites")

    # 约束和索引
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill"),
        Index("idx_favorite_user_id", "user_id"),
        Index("idx_favorite_skill_id", "skill_id"),
        Index("idx_favorite_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Favorite(user_id={self.user_id}, skill_id={self.skill_id})>"


class SkillStats(Base):
    """技能统计模型（按日统计）"""

    __tablename__ = "skill_stats"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 外键
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )

    # 统计日期
    date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # 统计数据
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    favorite_count: Mapped[int] = mapped_column(Integer, default=0)
    share_count: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 约束和索引
    __table_args__ = (
        UniqueConstraint("skill_id", "date", name="uq_skill_date"),
        Index("idx_stats_skill_date", "skill_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<SkillStats(skill_id={self.skill_id}, date={self.date})>"

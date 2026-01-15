"""
数据库连接和数据访问层
使用 SQLAlchemy 2.0 异步模式和 Repository 模式
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy import select, func, update, delete, and_, or_, desc
from sqlalchemy.orm import selectinload

from ..config import get_settings
from .models import Base, Skill, User, Favorite, SkillStats, SkillCategory, SkillStatus

import logging

logger = logging.getLogger(__name__)

# 全局引擎和会话工厂
_engine = None
_async_session_factory = None


def get_engine():
    """获取数据库引擎单例"""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        logger.info(f"数据库引擎已创建: {settings.mysql_host}")
    return _engine


def get_session_factory():
    """获取会话工厂单例"""
    global _async_session_factory
    if _async_session_factory is None:
        engine = get_engine()
        _async_session_factory = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


@asynccontextmanager
async def get_session():
    """获取数据库会话上下文管理器"""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库表结构"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据库表结构初始化完成")


async def drop_all():
    """删除所有表（谨慎使用）"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    logger.warning("所有数据库表已删除")


# ==================== Repository Classes ====================


class SkillRepository:
    """技能数据仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, skill_data: Dict[str, Any]) -> Skill:
        """创建技能"""
        skill = Skill(**skill_data)
        self.session.add(skill)
        await self.session.flush()
        return skill

    async def get_by_id(self, skill_id: int) -> Optional[Skill]:
        """根据ID获取技能"""
        result = await self.session.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Skill]:
        """根据slug获取技能"""
        result = await self.session.execute(select(Skill).where(Skill.slug == slug))
        return result.scalar_one_or_none()

    async def list(
        self,
        category: Optional[SkillCategory] = None,
        status: SkillStatus = SkillStatus.ACTIVE,
        is_official: Optional[bool] = None,
        search_keyword: Optional[str] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[List[Skill], int]:
        """
        获取技能列表

        Returns:
            (skills, total_count)
        """
        # 构建查询条件
        conditions = [Skill.status == status]

        if category:
            conditions.append(Skill.category == category)

        if is_official is not None:
            conditions.append(Skill.is_official == is_official)

        if search_keyword:
            search_pattern = f"%{search_keyword}%"
            conditions.append(
                or_(
                    Skill.name.like(search_pattern),
                    Skill.description.like(search_pattern),
                )
            )

        # 查询总数
        count_query = select(func.count(Skill.id)).where(and_(*conditions))
        total_result = await self.session.execute(count_query)
        total_count = total_result.scalar()

        # 查询数据
        query = select(Skill).where(and_(*conditions))

        # 排序
        if hasattr(Skill, order_by):
            order_column = getattr(Skill, order_by)
            if order_desc:
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)

        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        skills = result.scalars().all()

        return list(skills), total_count

    async def update(self, skill_id: int, update_data: Dict[str, Any]) -> Optional[Skill]:
        """更新技能"""
        stmt = (
            update(Skill)
            .where(Skill.id == skill_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        return await self.get_by_id(skill_id)

    async def increment_view_count(self, skill_id: int):
        """增加浏览次数"""
        stmt = (
            update(Skill)
            .where(Skill.id == skill_id)
            .values(view_count=Skill.view_count + 1)
        )
        await self.session.execute(stmt)

    async def increment_favorite_count(self, skill_id: int, increment: int = 1):
        """增加/减少收藏次数"""
        stmt = (
            update(Skill)
            .where(Skill.id == skill_id)
            .values(favorite_count=Skill.favorite_count + increment)
        )
        await self.session.execute(stmt)

    async def increment_share_count(self, skill_id: int):
        """增加分享次数"""
        stmt = (
            update(Skill)
            .where(Skill.id == skill_id)
            .values(share_count=Skill.share_count + 1)
        )
        await self.session.execute(stmt)

    async def delete(self, skill_id: int):
        """删除技能"""
        stmt = delete(Skill).where(Skill.id == skill_id)
        await self.session.execute(stmt)


class UserRepository:
    """用户数据仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_data: Dict[str, Any]) -> User:
        """创建用户"""
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_openid(self, openid: str) -> Optional[User]:
        """根据openid获取用户"""
        result = await self.session.execute(
            select(User).where(User.openid == openid)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """更新用户信息"""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**update_data, updated_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        return await self.get_by_id(user_id)

    async def update_last_login(self, user_id: int):
        """更新最后登录时间"""
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.utcnow())
        )
        await self.session.execute(stmt)


class FavoriteRepository:
    """收藏数据仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, skill_id: int) -> Favorite:
        """创建收藏"""
        favorite = Favorite(user_id=user_id, skill_id=skill_id)
        self.session.add(favorite)
        await self.session.flush()
        return favorite

    async def get(self, user_id: int, skill_id: int) -> Optional[Favorite]:
        """获取收藏记录"""
        result = await self.session.execute(
            select(Favorite).where(
                and_(Favorite.user_id == user_id, Favorite.skill_id == skill_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: int, offset: int = 0, limit: int = 20
    ) -> tuple[List[Favorite], int]:
        """
        获取用户收藏列表

        Returns:
            (favorites, total_count)
        """
        # 查询总数
        count_query = select(func.count(Favorite.id)).where(
            Favorite.user_id == user_id
        )
        total_result = await self.session.execute(count_query)
        total_count = total_result.scalar()

        # 查询数据（关联加载技能信息）
        query = (
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .options(selectinload(Favorite.skill))
            .order_by(desc(Favorite.created_at))
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(query)
        favorites = result.scalars().all()

        return list(favorites), total_count

    async def delete(self, user_id: int, skill_id: int):
        """删除收藏"""
        stmt = delete(Favorite).where(
            and_(Favorite.user_id == user_id, Favorite.skill_id == skill_id)
        )
        await self.session.execute(stmt)

    async def is_favorited(self, user_id: int, skill_id: int) -> bool:
        """检查是否已收藏"""
        favorite = await self.get(user_id, skill_id)
        return favorite is not None


class SkillStatsRepository:
    """技能统计数据仓库"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, skill_id: int, stat_date: date) -> SkillStats:
        """获取或创建统计记录"""
        result = await self.session.execute(
            select(SkillStats).where(
                and_(SkillStats.skill_id == skill_id, SkillStats.date == stat_date)
            )
        )
        stats = result.scalar_one_or_none()

        if not stats:
            stats = SkillStats(skill_id=skill_id, date=stat_date)
            self.session.add(stats)
            await self.session.flush()

        return stats

    async def increment_view_count(self, skill_id: int, stat_date: date):
        """增加浏览次数"""
        stats = await self.get_or_create(skill_id, stat_date)
        stmt = (
            update(SkillStats)
            .where(SkillStats.id == stats.id)
            .values(view_count=SkillStats.view_count + 1)
        )
        await self.session.execute(stmt)

    async def increment_favorite_count(
        self, skill_id: int, stat_date: date, increment: int = 1
    ):
        """增加/减少收藏次数"""
        stats = await self.get_or_create(skill_id, stat_date)
        stmt = (
            update(SkillStats)
            .where(SkillStats.id == stats.id)
            .values(favorite_count=SkillStats.favorite_count + increment)
        )
        await self.session.execute(stmt)

    async def increment_share_count(self, skill_id: int, stat_date: date):
        """增加分享次数"""
        stats = await self.get_or_create(skill_id, stat_date)
        stmt = (
            update(SkillStats)
            .where(SkillStats.id == stats.id)
            .values(share_count=SkillStats.share_count + 1)
        )
        await self.session.execute(stmt)

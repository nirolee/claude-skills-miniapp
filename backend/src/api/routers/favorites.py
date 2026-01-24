"""
收藏相关 API 路由
"""
from datetime import date

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ...storage.database import (
    get_session,
    FavoriteRepository,
    SkillRepository,
    UserRepository,
    SkillStatsRepository,
)

router = APIRouter(prefix="/favorites", tags=["favorites"])


# ==================== Pydantic Models ====================


class FavoriteRequest(BaseModel):
    """收藏请求"""

    user_id: int
    skill_id: int


class FavoriteResponse(BaseModel):
    """收藏响应"""

    id: int
    user_id: int
    skill_id: int
    created_at: str

    class Config:
        from_attributes = True


class FavoriteWithSkillResponse(BaseModel):
    """带技能信息的收藏响应"""

    id: int
    skill_id: int
    name: str  # 技能名称
    description: str  # 技能描述
    category: str  # 分类
    stars: int  # 星标数
    view_count: int  # 浏览次数
    created_at: str  # 收藏时间


# ==================== API Routes ====================


@router.post("/", response_model=FavoriteResponse)
async def add_favorite(request: FavoriteRequest):
    """
    添加收藏

    同时更新技能的收藏计数
    """
    try:
        async with get_session() as session:
            fav_repo = FavoriteRepository(session)
            skill_repo = SkillRepository(session)
            user_repo = UserRepository(session)
            stats_repo = SkillStatsRepository(session)

            # 验证用户是否存在
            user = await user_repo.get_by_id(request.user_id)
            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")

            # 检查技能是否存在
            skill = await skill_repo.get_by_id(request.skill_id)
            if not skill:
                raise HTTPException(status_code=404, detail="技能不存在")

            # 检查是否已收藏
            existing = await fav_repo.get(request.user_id, request.skill_id)
            if existing:
                raise HTTPException(status_code=400, detail="已经收藏过该技能")

            # 创建收藏
            favorite = await fav_repo.create(request.user_id, request.skill_id)

            # 更新技能收藏计数
            await skill_repo.increment_favorite_count(request.skill_id, 1)
            await stats_repo.increment_favorite_count(request.skill_id, date.today(), 1)

            return FavoriteResponse(
                id=favorite.id,
                user_id=favorite.user_id,
                skill_id=favorite.skill_id,
                created_at=favorite.created_at.isoformat(),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.delete("/")
async def remove_favorite(user_id: int, skill_id: int):
    """
    取消收藏

    同时更新技能的收藏计数
    """
    try:
        async with get_session() as session:
            fav_repo = FavoriteRepository(session)
            skill_repo = SkillRepository(session)
            stats_repo = SkillStatsRepository(session)

            # 检查收藏是否存在
            existing = await fav_repo.get(user_id, skill_id)
            if not existing:
                raise HTTPException(status_code=404, detail="收藏记录不存在")

            # 删除收藏
            await fav_repo.delete(user_id, skill_id)

            # 更新技能收藏计数
            await skill_repo.increment_favorite_count(skill_id, -1)
            await stats_repo.increment_favorite_count(skill_id, date.today(), -1)

            return {"success": True, "message": "取消收藏成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/user/{user_id}")
async def list_user_favorites(user_id: int, page: int = 1, page_size: int = 20):
    """
    获取用户收藏列表

    包含完整的技能信息
    """
    try:
        offset = (page - 1) * page_size

        async with get_session() as session:
            repo = FavoriteRepository(session)

            favorites, total = await repo.list_by_user(
                user_id, offset=offset, limit=page_size
            )

            # 转换为响应模型
            items = [
                FavoriteWithSkillResponse(
                    id=fav.id,
                    skill_id=fav.skill_id,
                    name=fav.skill.name,
                    description=fav.skill.description or "",
                    category=fav.skill.category.value,
                    stars=fav.skill.stars or 0,
                    view_count=fav.skill.view_count or 0,
                    created_at=fav.created_at.isoformat(),
                )
                for fav in favorites
            ]

            return {"total": total, "page": page, "page_size": page_size, "items": items}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/check")
async def check_favorite(user_id: int, skill_id: int):
    """检查是否已收藏"""
    try:
        async with get_session() as session:
            repo = FavoriteRepository(session)

            is_favorited = await repo.is_favorited(user_id, skill_id)

            return {"is_favorited": is_favorited}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")

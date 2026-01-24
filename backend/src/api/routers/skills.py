"""
技能相关 API 路由
"""
from typing import Optional
from datetime import date

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...storage.database import get_session, SkillRepository, SkillStatsRepository
from ...storage.models import SkillCategory, SkillStatus

router = APIRouter(prefix="/skills", tags=["skills"])


# ==================== Pydantic Models ====================


class SkillListResponse(BaseModel):
    """技能列表响应"""

    id: int
    name: str
    name_zh: Optional[str] = None
    slug: str
    description: str
    description_zh: Optional[str] = None
    author: str
    category: str
    tags: Optional[list[str]] = None
    stars: int
    forks: int
    view_count: int
    favorite_count: int
    is_official: bool
    created_at: str

    class Config:
        from_attributes = True


class SkillDetailResponse(BaseModel):
    """技能详情响应"""

    id: int
    name: str
    name_zh: Optional[str] = None
    slug: str
    description: str
    description_zh: Optional[str] = None
    author: str
    github_url: str
    github_repo: Optional[str] = None
    category: str
    tags: Optional[list[str]] = None
    content: str
    content_zh: Optional[str] = None
    skill_md: Optional[str] = None  # 完整的 SKILL.md 原文
    skill_md_zh: Optional[str] = None  # 完整的 SKILL.md 中文翻译
    install_command: str
    stars: int
    forks: int
    view_count: int
    favorite_count: int
    share_count: int
    is_official: bool
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """分页响应"""

    total: int
    page: int
    page_size: int
    items: list


# ==================== API Routes ====================


@router.get("/", response_model=PaginatedResponse)
async def list_skills(
    category: Optional[str] = Query(None, description="技能分类"),
    is_official: Optional[bool] = Query(None, description="是否官方技能"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    order_by: str = Query("created_at", description="排序字段"),
    order_desc: bool = Query(True, description="是否降序"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
):
    """
    获取技能列表

    支持分类筛选、搜索、排序和分页
    """
    try:
        # 转换分类
        category_enum = None
        if category:
            try:
                category_enum = SkillCategory(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"无效的分类: {category}")

        offset = (page - 1) * page_size

        async with get_session() as session:
            repo = SkillRepository(session)

            skills, total = await repo.list(
                category=category_enum,
                status=SkillStatus.ACTIVE,
                is_official=is_official,
                search_keyword=search,
                order_by=order_by,
                order_desc=order_desc,
                offset=offset,
                limit=page_size,
            )

            # 转换为响应模型
            items = [
                SkillListResponse(
                    id=skill.id,
                    name=skill.name,
                    name_zh=skill.name_zh,
                    slug=skill.slug,
                    description=skill.description,
                    description_zh=skill.description_zh,
                    author=skill.author,
                    category=skill.category.value,
                    tags=skill.tags if isinstance(skill.tags, list) else [],
                    stars=skill.stars,
                    forks=skill.forks,
                    view_count=skill.view_count,
                    favorite_count=skill.favorite_count,
                    is_official=skill.is_official,
                    created_at=skill.created_at.isoformat(),
                )
                for skill in skills
            ]

            return PaginatedResponse(
                total=total, page=page, page_size=page_size, items=items
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/{skill_id}", response_model=SkillDetailResponse)
async def get_skill_detail(skill_id: int):
    """
    获取技能详情

    自动增加浏览次数
    """
    try:
        async with get_session() as session:
            repo = SkillRepository(session)
            stats_repo = SkillStatsRepository(session)

            skill = await repo.get_by_id(skill_id)

            if not skill:
                raise HTTPException(status_code=404, detail="技能不存在")

            # 增加浏览次数
            await repo.increment_view_count(skill_id)
            await stats_repo.increment_view_count(skill_id, date.today())

            return SkillDetailResponse(
                id=skill.id,
                name=skill.name,
                name_zh=skill.name_zh,
                slug=skill.slug,
                description=skill.description,
                description_zh=skill.description_zh,
                author=skill.author,
                github_url=skill.github_url,
                github_repo=skill.github_repo,
                category=skill.category.value,
                tags=skill.tags if isinstance(skill.tags, list) else [],
                content=skill.content,
                content_zh=skill.content_zh,
                skill_md=skill.skill_md,  # 完整的 SKILL.md 原文
                skill_md_zh=skill.skill_md_zh,  # 完整的 SKILL.md 中文翻译
                install_command=skill.install_command,
                stars=skill.stars,
                forks=skill.forks,
                view_count=skill.view_count + 1,  # 返回更新后的计数
                favorite_count=skill.favorite_count,
                share_count=skill.share_count,
                is_official=skill.is_official,
                status=skill.status.value,
                created_at=skill.created_at.isoformat(),
                updated_at=skill.updated_at.isoformat(),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.post("/{skill_id}/share")
async def share_skill(skill_id: int):
    """记录技能分享"""
    try:
        async with get_session() as session:
            repo = SkillRepository(session)
            stats_repo = SkillStatsRepository(session)

            skill = await repo.get_by_id(skill_id)

            if not skill:
                raise HTTPException(status_code=404, detail="技能不存在")

            # 增加分享次数
            await repo.increment_share_count(skill_id)
            await stats_repo.increment_share_count(skill_id, date.today())

            return {"success": True, "message": "分享记录成功"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/categories/list")
async def list_categories():
    """获取所有分类"""
    return {
        "categories": [
            {"value": cat.value, "label": cat.value.replace("_", " ").title()}
            for cat in SkillCategory
        ]
    }

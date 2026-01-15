"""
认证相关 API 路由
"""
import hashlib
import time
import httpx
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...config import get_settings
from ...storage.database import get_session, UserRepository
from ...storage.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


# ==================== Pydantic Models ====================


class WechatLoginRequest(BaseModel):
    """微信登录请求"""
    code: str = Field(..., description="微信登录临时凭证")
    nickname: Optional[str] = Field(None, description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="用户头像")
    gender: Optional[int] = Field(0, description="性别")
    city: Optional[str] = Field(None, description="城市")
    province: Optional[str] = Field(None, description="省份")


class LoginResponse(BaseModel):
    """登录响应"""
    user_id: int
    openid: str
    nickname: Optional[str]
    avatar_url: Optional[str]
    token: str
    is_new_user: bool


# ==================== Helper Functions ====================


async def get_wechat_openid(code: str) -> dict:
    """
    通过 code 换取 openid

    微信接口文档：
    https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
    """
    settings = get_settings()

    if not settings.wechat_appid or settings.wechat_appid == "your_wechat_appid":
        raise HTTPException(
            status_code=500,
            detail="微信小程序 AppID 未配置，请在 .env 文件中设置 WECHAT_APPID"
        )

    if not settings.wechat_secret or settings.wechat_secret == "your_wechat_secret":
        raise HTTPException(
            status_code=500,
            detail="微信小程序 AppSecret 未配置，请在 .env 文件中设置 WECHAT_SECRET"
        )

    url = "https://api.weixin.qq.com/sns/jscode2session"
    params = {
        "appid": settings.wechat_appid,
        "secret": settings.wechat_secret,
        "js_code": code,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params)
            data = response.json()

            # 检查错误
            if "errcode" in data and data["errcode"] != 0:
                error_msg = data.get("errmsg", "未知错误")
                raise HTTPException(
                    status_code=400,
                    detail=f"微信登录失败: {error_msg} (错误码: {data['errcode']})"
                )

            # 返回 openid 和 session_key
            return {
                "openid": data.get("openid"),
                "session_key": data.get("session_key"),
                "unionid": data.get("unionid"),  # 可能为空
            }
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"请求微信服务器失败: {str(e)}"
            )


def generate_token(openid: str, user_id: int) -> str:
    """
    生成简单的 token（实际项目应该使用 JWT）
    格式：md5(openid + user_id + timestamp + secret)
    """
    settings = get_settings()
    timestamp = str(int(time.time()))
    raw = f"{openid}{user_id}{timestamp}{settings.wechat_secret}"
    token = hashlib.md5(raw.encode()).hexdigest()
    return f"{token}:{timestamp}"


# ==================== API Routes ====================


@router.post("/login", response_model=LoginResponse)
async def wechat_login(request: WechatLoginRequest):
    """
    微信小程序登录

    流程：
    1. 前端调用 wx.login() 获取 code
    2. 将 code 发送到后端
    3. 后端用 code 换取 openid
    4. 查询或创建用户记录
    5. 返回用户信息和 token
    """
    try:
        # 1. 用 code 换取 openid
        wechat_data = await get_wechat_openid(request.code)
        openid = wechat_data["openid"]
        session_key = wechat_data["session_key"]
        unionid = wechat_data.get("unionid")

        if not openid:
            raise HTTPException(status_code=400, detail="获取 openid 失败")

        # 2. 查询或创建用户
        async with get_session() as session:
            repo = UserRepository(session)

            # 尝试查找现有用户
            user = await repo.get_by_openid(openid)
            is_new_user = user is None

            if user:
                # 更新用户信息
                if request.nickname:
                    user.nickname = request.nickname
                if request.avatar_url:
                    user.avatar_url = request.avatar_url
                if request.gender:
                    user.gender = request.gender
                if request.city:
                    user.city = request.city
                if request.province:
                    user.province = request.province

                user.session_key = session_key
                if unionid:
                    user.unionid = unionid

                await repo.update(user)
            else:
                # 创建新用户
                user = await repo.create(
                    openid=openid,
                    session_key=session_key,
                    unionid=unionid,
                    nickname=request.nickname or f"用户{openid[:8]}",
                    avatar_url=request.avatar_url,
                    gender=request.gender or 0,
                    city=request.city,
                    province=request.province,
                )

        # 3. 生成 token
        token = generate_token(openid, user.id)

        # 4. 返回登录结果
        return LoginResponse(
            user_id=user.id,
            openid=user.openid,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            token=token,
            is_new_user=is_new_user,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")


@router.get("/user/{user_id}")
async def get_user_info(user_id: int):
    """获取用户信息"""
    try:
        async with get_session() as session:
            repo = UserRepository(session)
            user = await repo.get_by_id(user_id)

            if not user:
                raise HTTPException(status_code=404, detail="用户不存在")

            return {
                "id": user.id,
                "openid": user.openid,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "gender": user.gender,
                "city": user.city,
                "province": user.province,
                "created_at": user.created_at.isoformat(),
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户信息失败: {str(e)}")

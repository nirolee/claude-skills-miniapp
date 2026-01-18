# 头像昵称更新说明

## 问题

微信小程序从基础库 2.21.2 开始废弃了 `getUserProfile()` API，导致登录时无法自动获取用户头像和昵称。

## 解决方案

采用微信推荐的**头像昵称填写组件**，让用户登录后主动设置个人信息。

## 改动内容

### 1. 前端 - profile.vue

#### 模板变更
- **头像**：改为 `<button open-type="chooseAvatar">` 包裹头像，点击可选择
- **昵称**：改为 `<input type="nickname">` 输入框，可直接编辑

#### 新增方法
- `onChooseAvatar(e)` - 处理头像选择
- `onNicknameBlur(e)` - 处理昵称修改

#### 样式新增
- `.avatar-wrapper` - 移除button默认样式
- `.user-name-input` - 输入框样式与原文本一致

### 2. 前端 - login.js

#### 简化登录流程
- 移除 `getUserProfile()` 调用（已废弃）
- 登录时只传 `code`，不传用户信息
- 后端自动生成默认昵称（如：用户oR1Fm12i）

### 3. 用户体验

**登录后的流程**：
1. 用户点击"点击登录"
2. 完成微信授权，获得默认头像和昵称
3. 在个人中心，点击头像 → 选择新头像
4. 点击昵称 → 输入新昵称
5. 自动保存到本地（TODO: 需后端API支持同步到服务器）

## 后续工作

### 需要添加后端API

在 `backend/src/api/routers/auth.py` 或新建 `users.py` 添加：

```python
@router.put("/user/{user_id}/profile")
async def update_user_profile(
    user_id: int,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None
):
    """更新用户资料"""
    async with get_session() as session:
        repo = UserRepository(session)
        update_data = {}
        if nickname:
            update_data["nickname"] = nickname
        if avatar_url:
            update_data["avatar_url"] = avatar_url

        user = await repo.update(user_id, update_data)
        return {"success": True, "user": user}
```

### 前端调用API

在 `frontend/utils/api.js` 添加：

```javascript
export async function updateUserProfile(userId, data) {
  return await put(`/user/${userId}/profile`, data)
}
```

在 `profile.vue` 中取消注释并调用：

```javascript
// 选择头像
async onChooseAvatar(e) {
  const { avatarUrl } = e.detail
  try {
    this.userInfo.avatar_url = avatarUrl
    uni.setStorageSync('user', this.userInfo)

    // 调用后端API
    await updateUserProfile(this.userInfo.user_id, { avatar_url: avatarUrl })

    uni.showToast({ title: '头像已更新', icon: 'success' })
  } catch (error) {
    console.error('更新头像失败', error)
  }
}
```

## 测试步骤

1. 退出登录（如已登录）
2. 重新登录
3. 查看个人中心，应显示默认头像和默认昵称
4. 点击头像，选择新头像 ✅
5. 点击昵称，输入新昵称 ✅
6. 切换页面后返回，信息已保存（本地）✅

## 参考文档

- [微信官方：头像昵称填写](https://developers.weixin.qq.com/miniprogram/dev/framework/open-ability/userProfile.html)
- [getUserProfile 接口调整说明](https://developers.weixin.qq.com/community/develop/doc/000cacfa20ce88df04cb468bc52801)

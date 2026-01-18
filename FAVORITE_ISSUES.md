# 收藏功能问题报告

## 🐛 发现的问题

### 1️⃣ **前端 - 首页收藏功能缺陷（严重）**

**位置**: `frontend/pages/index/index.vue`

**问题**:
```javascript
// 第151行：硬编码用户ID
userId: 1,  // 临时用户ID（实际应从微信登录获取）

// 第250行：收藏状态写死
isFavorited: false, // TODO: 从API获取收藏状态

// 第294-320行：没有检查登录状态
async toggleFavorite(skillId) {
  // ❌ 直接使用this.userId，没有检查登录
  await addFavorite(this.userId, skillId)
}
```

**影响**:
- ❌ 未登录用户也能点击收藏（但会失败）
- ❌ 所有收藏都记录到user_id=1
- ❌ 无法显示真实的收藏状态
- ❌ 用户体验差，没有登录提示

---

### 2️⃣ **后端 - 缺少用户验证（中等）**

**位置**: `backend/src/api/routers/favorites.py`

**问题**:
```python
@router.post("/", response_model=FavoriteResponse)
async def add_favorite(request: FavoriteRequest):
    # ❌ 没有验证user_id是否存在
    # ❌ 可以传入任何user_id，包括不存在的用户
    favorite = await fav_repo.create(request.user_id, request.skill_id)
```

**影响**:
- ⚠️ 可以为不存在的用户创建收藏记录
- ⚠️ 数据库中可能存在孤立的收藏记录
- ⚠️ 外键约束如果设置不当可能导致数据库错误

---

### 3️⃣ **详情页 - 实现正确（参考）**

**位置**: `frontend/pages/detail/detail.vue`

**正确实现**:
```javascript
async toggleFavorite() {
  // ✅ 检查登录状态
  const isLoggedIn = await requireLogin()
  if (!isLoggedIn) return

  // ✅ 获取真实用户ID
  const userId = getCurrentUserId()

  // ✅ 乐观更新UI + 错误回滚
  const previousState = this.skill.isFavorited
  try {
    this.skill.isFavorited = !this.skill.isFavorited
    if (this.skill.isFavorited) {
      await addFavorite(userId, this.skill.id)
    } else {
      await removeFavorite(userId, this.skill.id)
    }
  } catch (error) {
    this.skill.isFavorited = previousState // 回滚
  }
}
```

---

## 🔧 修复方案

### 方案A：快速修复（推荐）

修改 `frontend/pages/index/index.vue`：

```javascript
import { getCurrentUserId, requireLogin } from '../../utils/login.js'

// 1. 移除硬编码的userId
data() {
  return {
    // userId: 1,  // ❌ 删除这一行
    // ...其他数据
  }
},

// 2. 修复toggleFavorite方法
async toggleFavorite(skillId) {
  // 检查登录状态
  const isLoggedIn = await requireLogin()
  if (!isLoggedIn) return

  const userId = getCurrentUserId()
  const skill = this.skills.find((s) => s.id === skillId)
  if (!skill) return

  try {
    if (skill.isFavorited) {
      await removeFavorite(userId, skillId)
      skill.isFavorited = false
      uni.showToast({ title: '取消收藏', icon: 'none' })
    } else {
      await addFavorite(userId, skillId)
      skill.isFavorited = true
      uni.showToast({ title: '已收藏', icon: 'success' })
    }
  } catch (error) {
    console.error('收藏操作失败:', error)
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
},

// 3. 在mounted中加载收藏状态（可选）
async mounted() {
  await this.loadCategories()
  await this.loadSkills(true)

  // 如果已登录，加载收藏状态
  const userId = getCurrentUserId()
  if (userId) {
    await this.loadFavoriteStatus()
  }
},

// 4. 新增方法：加载收藏状态
async loadFavoriteStatus() {
  const userId = getCurrentUserId()
  if (!userId || this.skills.length === 0) return

  try {
    // 批量检查收藏状态
    for (const skill of this.skills) {
      const res = await checkFavorite(userId, skill.id)
      skill.isFavorited = res.is_favorited || false
    }
  } catch (error) {
    console.error('加载收藏状态失败', error)
  }
}
```

### 方案B：后端验证用户（推荐）

修改 `backend/src/api/routers/favorites.py`：

```python
@router.post("/", response_model=FavoriteResponse)
async def add_favorite(request: FavoriteRequest):
    """添加收藏"""
    try:
        async with get_session() as session:
            fav_repo = FavoriteRepository(session)
            skill_repo = SkillRepository(session)
            user_repo = UserRepository(session)  # 新增
            stats_repo = SkillStatsRepository(session)

            # ✅ 验证用户是否存在
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
            # ...后续逻辑
```

---

## ⚠️ 风险评估

| 问题 | 严重程度 | 影响范围 | 修复优先级 |
|------|---------|---------|-----------|
| 首页硬编码userId | 🔴 高 | 所有首页收藏操作 | P0 立即修复 |
| 首页没有登录检查 | 🔴 高 | 用户体验 | P0 立即修复 |
| 后端缺少用户验证 | 🟡 中 | 数据完整性 | P1 尽快修复 |
| 首页没有显示收藏状态 | 🟢 低 | 用户体验 | P2 可选优化 |

---

## ✅ 测试计划

### 前端测试
1. **未登录状态**：
   - 点击收藏 → 应跳转到登录页

2. **已登录状态**：
   - 点击收藏 → 成功收藏，显示❤️
   - 再次点击 → 取消收藏，显示🤍
   - 刷新页面 → 收藏状态保持

3. **错误处理**：
   - 网络错误 → 显示"操作失败"
   - 重复收藏 → 显示"已经收藏过该技能"

### 后端测试
```bash
# 测试无效用户ID
curl -X POST https://api.liguoqi.site/api/favorites/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 99999, "skill_id": 1}'
# 应返回 404: 用户不存在
```

---

## 📝 相关文件

- ✅ 详情页（正确）：`frontend/pages/detail/detail.vue:275-309`
- ❌ 首页（需修复）：`frontend/pages/index/index.vue:151,250,294-320`
- ⚠️ 后端API（需增强）：`backend/src/api/routers/favorites.py:56-96`
- 📖 登录工具：`frontend/utils/login.js:116-140`

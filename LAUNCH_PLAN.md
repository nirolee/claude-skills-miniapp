# Claude Skills 小程序上线规划清单

## 📋 当前项目状态

### ✅ 已完成
- [x] 前端三大页面（首页、详情页、搜索页）
- [x] 后端 API 完整实现
- [x] 首页接入真实 API
- [x] 数据库连接正常
- [x] 已导入 20 个技能数据
- [x] Terminal Cyberpunk 设计风格完成

### ❌ 待完成
- [ ] 详情页接入真实 API
- [ ] 搜索页接入真实 API
- [ ] 个人中心页开发
- [ ] 微信登录功能
- [ ] 收藏功能完整实现
- [ ] 域名购买 + ICP 备案
- [ ] HTTPS 部署
- [ ] 数据量补充（目标 100+ 技能）

---

## 🚨 上线必须完成项（无法跳过）

### 1. 域名和备案 ⏰ 15-20 天
**当前状态**：使用 IP 地址 `223.109.140.233`，小程序不允许

**必须操作**：
1. **购买域名**
   - 推荐：`claudeskills.com` 或 `claude-skills.cn`
   - 平台：阿里云、腾讯云、GoDaddy
   - 费用：约 50-100 元/年

2. **ICP 备案**（中国大陆必须）
   - 在域名服务商处提交备案申请
   - 准备资料：身份证、营业执照（如有）、域名证书
   - 等待审核：15-20 天
   - 费用：免费（部分服务商收取幕布费 20-30 元）

3. **小程序备案**（新规定）
   - 2023 年 9 月后，小程序也需要单独备案
   - 在微信公众平台提交
   - 等待审核：3-7 天
   - 依赖：必须先完成 ICP 备案

**时间线**：
- 第 1 天：购买域名
- 第 1-3 天：提交 ICP 备案
- 第 3-20 天：等待审核
- 第 20-25 天：通过后提交小程序备案
- 第 25-30 天：小程序备案通过

**⚠️ 风险**：这是上线的最长路径，建议立即开始！

---

### 2. HTTPS 部署 ⏰ 1-2 天
**当前状态**：HTTP 服务，小程序要求必须 HTTPS

**必须操作**：
1. **申请 SSL 证书**
   - 免费方案：Let's Encrypt（90 天需续期）
   - 付费方案：阿里云/腾讯云 SSL 证书（1 年，约 200-500 元）
   - 推荐：阿里云免费 SSL（1 年，需每年续期）

2. **配置 Nginx 反向代理**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location /api {
           proxy_pass http://127.0.0.1:8081;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **更新前端 API 配置**
   - 修改 `frontend/config/api.js`
   - 生产环境改为：`https://your-domain.com`

4. **小程序后台配置服务器域名**
   - 登录微信公众平台
   - 开发 → 开发管理 → 服务器域名
   - 添加：`https://your-domain.com`

---

### 3. 核心功能开发 ⏰ 5-7 天

#### 3.1 详情页接入 API ⏰ 1 天
**文件**：`frontend/pages/detail/detail.vue`

**修改要点**：
```javascript
// 替换 onLoad 中的数据加载
import { getSkillDetail, shareSkill, addFavorite, removeFavorite } from '../../utils/api.js'

async loadSkill(id) {
  try {
    const skill = await getSkillDetail(id)
    this.skill = {
      ...skill,
      authorAvatar: `https://avatars.githubusercontent.com/u/${skill.id}`,
      stars: this.formatNumber(skill.stars),
      forks: this.formatNumber(skill.forks),
      downloads: this.formatNumber(skill.view_count),
    }
  } catch (error) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  }
}
```

#### 3.2 搜索页接入 API ⏰ 1 天
**文件**：`frontend/pages/search/search.vue`

**修改要点**：
```javascript
import { getSkillsList } from '../../utils/api.js'

async performSearch() {
  try {
    const res = await getSkillsList({
      search: this.searchQuery,
      category: this.selectedCategory,
      order_by: this.sortBy === 'stars' ? 'stars' : 'view_count',
      page: 1,
      page_size: 50,
    })
    this.skills = res.items.map(skill => ({
      // ... 数据转换
    }))
  } catch (error) {
    uni.showToast({ title: '搜索失败', icon: 'none' })
  }
}
```

#### 3.3 个人中心页开发 ⏰ 2-3 天
**文件**：`frontend/pages/profile/profile.vue`

**必须功能**：
- [ ] 用户信息展示（头像、昵称）
- [ ] 收藏列表（带分页）
- [ ] 浏览历史（可选）
- [ ] 设置选项（清除缓存、关于我们）
- [ ] 退出登录

#### 3.4 微信登录功能 ⏰ 1-2 天

**前端实现**：
```javascript
// utils/login.js
export async function wxLogin() {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success: async (loginRes) => {
        // 发送 code 到后端
        const res = await uni.request({
          url: `${API_BASE_URL}/auth/login`,
          method: 'POST',
          data: { code: loginRes.code }
        })
        // 保存 session_key/token
        uni.setStorageSync('user', res.data)
        resolve(res.data)
      },
      fail: reject
    })
  })
}
```

**后端实现**：
- [ ] 创建 `/api/auth/login` 接口
- [ ] 用 code 换取 openid/session_key
- [ ] 创建或更新用户记录
- [ ] 返回自定义 token

**配置**：
- [ ] 获取微信小程序 AppSecret
- [ ] 更新 `backend/.env` 中的 `WECHAT_SECRET`

---

### 4. 数据准备 ⏰ 2-3 天

#### 4.1 导入更多技能数据
**当前**：20 个技能（远远不够）
**目标**：至少 100-200 个技能

**操作**：
```bash
# 导入 10 页（约 120 个技能）
cd backend
python scripts/import_skills.py --source skillsmp --pages 10

# 或导入更多
python scripts/import_skills.py --source skillsmp --pages 20
```

#### 4.2 数据质量优化
- [ ] 人工审核技能内容
- [ ] 补充中文描述
- [ ] 验证 GitHub 链接有效性
- [ ] 标记官方技能（anthropics 仓库）
- [ ] 分类优化（确保每个分类都有技能）

---

### 5. 补充必要页面 ⏰ 1 天

#### 5.1 隐私政策页面
**文件**：`frontend/pages/privacy/privacy.vue`

**内容要点**：
- 收集哪些信息（昵称、头像、openid）
- 信息用途（收藏功能、用户识别）
- 不会分享给第三方
- 用户权利（删除数据）

#### 5.2 用户协议页面
**文件**：`frontend/pages/agreement/agreement.vue`

**内容要点**：
- 服务说明
- 用户行为规范
- 免责声明
- 知识产权说明

#### 5.3 关于我们页面
**文件**：添加到个人中心

**内容**：
- 小程序简介
- 开发者信息
- 联系方式
- 版本号

---

### 6. 用户体验优化 ⏰ 2-3 天

#### 6.1 加载状态优化
- [ ] 添加骨架屏（首页、详情页）
- [ ] 统一 Loading 样式
- [ ] 网络错误提示优化
- [ ] 空状态优化（带引导）

#### 6.2 性能优化
- [ ] 首页数据缓存（避免每次重新加载）
- [ ] 图片懒加载
- [ ] 分页优化（虚拟滚动）
- [ ] 接口防抖节流

#### 6.3 交互优化
- [ ] 下拉刷新反馈
- [ ] 点击反馈动画
- [ ] 错误重试机制
- [ ] Toast 提示统一

---

## 🎯 上线时间规划

### 阶段一：立即开始（第 1-3 天）
**优先级：🔴 最高**
- [ ] 购买域名
- [ ] 提交 ICP 备案
- [ ] 并行：开始核心功能开发
- [ ] 并行：导入更多数据（10-20 页）

### 阶段二：功能开发（第 4-10 天）
**优先级：🔴 高**
- [ ] 详情页接入 API
- [ ] 搜索页接入 API
- [ ] 个人中心页开发
- [ ] 微信登录功能
- [ ] 补充必要页面

### 阶段三：等待备案（第 11-25 天）
**优先级：🟡 中**
- [ ] 用户体验优化
- [ ] 数据质量优化
- [ ] 补充协议文档
- [ ] 内部测试

### 阶段四：部署上线（第 26-30 天）
**优先级：🔴 最高**
- [ ] 备案通过后配置 HTTPS
- [ ] 部署到生产服务器
- [ ] 配置小程序服务器域名
- [ ] 全面测试

### 阶段五：提交审核（第 31-35 天）
**优先级：🔴 最高**
- [ ] 提交小程序备案
- [ ] 小程序备案通过后提交代码审核
- [ ] 等待微信审核（1-7 天）
- [ ] 审核通过后发布

---

## 📅 最快上线时间

**乐观估计**：约 35-40 天（约 5-6 周）
**保守估计**：约 45-60 天（约 6-8 周）

**关键路径**：
1. ICP 备案（15-20 天）← 最长，无法加速
2. 核心功能开发（5-7 天）
3. 部署 + HTTPS（1-2 天）
4. 小程序备案（3-7 天）
5. 微信审核（1-7 天）

---

## ⚠️ 重要提醒

### 必须立即处理
1. **域名备案**：时间最长，立即开始！
2. **获取微信 AppSecret**：登录微信公众平台获取
3. **确定小程序类目**：建议选择"工具 > 开发者工具"

### 可以后续迭代
- 分享功能（微信分享卡片）
- 评论功能（需要内容安全审核）
- 数据统计和推荐算法
- 更多筛选和排序选项

### 个人小程序限制
- ❌ 不能做社交功能（评论、论坛、聊天）
- ❌ 不能做支付功能
- ✅ 可以做工具类功能（浏览、搜索、收藏）

---

## 💰 预估费用

| 项目 | 费用 | 说明 |
|------|------|------|
| 域名 | 50-100 元/年 | .com/.cn 域名 |
| SSL 证书 | 0-500 元/年 | 免费或付费 |
| ICP 备案 | 0-30 元 | 幕布费（如需） |
| 服务器 | 已有 | 223.109.140.233 |
| 小程序认证 | 300 元/年 | 企业认证（可选） |
| **总计** | **50-630 元** | 首年费用 |

---

## 📞 需要准备的资料

### ICP 备案
- [ ] 身份证正反面照片
- [ ] 手机号码
- [ ] 邮箱
- [ ] 幕布照片（部分地区需要）

### 小程序备案
- [ ] 营业执照（企业）或身份证（个人）
- [ ] ICP 备案号
- [ ] 小程序信息（名称、简介、类目）

### 微信审核
- [ ] 小程序隐私政策
- [ ] 用户协议
- [ ] 测试账号（如需要）

---

## 🎉 总结

### 最快上线路线
1. **今天**：立即购买域名并提交 ICP 备案
2. **本周内**：完成核心功能开发（详情、搜索、个人中心）
3. **下周**：导入 100+ 技能数据，优化用户体验
4. **3-4 周后**：备案通过，配置 HTTPS 并部署
5. **5 周后**：提交小程序审核
6. **6 周后**：审核通过，正式上线！

### 建议策略
- 🚀 **MVP 优先**：先上线核心功能，后续迭代优化
- ⏰ **并行工作**：备案和开发同时进行
- 📊 **数据优先**：用户体验依赖内容质量
- 🛡️ **合规第一**：确保符合微信审核规范

---

**准备好开始了吗？** 建议从购买域名和提交备案开始！

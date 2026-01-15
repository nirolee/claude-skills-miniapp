# Claude Skills 小程序 - 前端项目

## 🎨 设计理念

**Terminal Cyberpunk × Developer Tools**

将终端命令行的极客美学与赛博朋克的霓虹色彩相结合，打造独特的技术感界面。

### 核心设计元素

- **配色方案**: 深空背景 + 霓虹蓝/紫色强调 + 终端绿色
- **字体**: 等宽字体（SF Mono, Cascadia Code）营造代码编辑器氛围
- **视觉效果**: 扫描线、终端光标、渐变光晕、卡片悬浮
- **交互动效**: 打字机效果、脉冲动画、滑动高亮

## 📱 功能页面

### 1. 首页 (`pages/index/index.vue`)
- 技能列表展示（卡片式布局）
- 分类筛选（可横向滚动）
- 实时统计（总技能数、在线用户）
- 下拉刷新 + 上拉加载更多
- 收藏/取消收藏
- 浮动按钮快速返回顶部

### 2. 技能详情页 (`pages/detail/detail.vue`)
- 技能完整信息展示
- 统计数据卡片（Stars, Forks, Downloads）
- 一键复制安装命令
- Markdown 文档渲染
- 标签展示
- 相关技能推荐
- 分享 + 收藏功能

### 3. 搜索页 (`pages/search/search.vue`)
- 实时搜索（300ms 防抖）
- 快速筛选（全部/官方/热门/最新）
- 高级筛选（可折叠）
  - 排序方式（Stars/更新时间/下载量/名称）
  - 多分类选择
  - Stars 范围滑块
- 搜索结果高亮
- 热门搜索推荐
- 最近搜索历史

### 4. 个人中心页 (`pages/profile/profile.vue`)
- 用户信息展示
- 微信登录/退出
- 统计卡片（收藏/浏览历史/已安装）
- 最近收藏列表
- 功能菜单
- 设置（深色模式、清除缓存、关于）

## 🎨 主题系统

### CSS 变量 (`uni.scss`)

```scss
/* 背景色 */
--bg-primary: #0a0e1a;     // 主背景
--bg-secondary: #0f1729;   // 次要背景
--bg-card: #141b2b;        // 卡片背景

/* 霓虹强调色 */
--neon-cyan: #00d9ff;      // 青色
--neon-purple: #a855f7;    // 紫色
--neon-pink: #ff006e;      // 粉色
--neon-green: #00ff88;     // 绿色

/* 文本色 */
--text-primary: #e2e8f0;   // 主要文本
--text-secondary: #94a3b8; // 次要文本
--text-tertiary: #64748b;  // 辅助文本
```

### 动画效果

- `fadeInUp`: 从下向上淡入
- `slideInLeft`: 从左向右滑入
- `pulse`: 脉冲呼吸效果
- `blink`: 光标闪烁
- `scan`: 扫描线效果
- `spin`: 加载旋转

## 🚀 快速开始

### 环境要求

- Node.js >= 16.0.0
- HBuilderX 或 VSCode + uni-app 插件
- 微信开发者工具（用于小程序预览）

### 安装依赖

```bash
cd frontend
npm install
```

### 开发运行

**微信小程序**
```bash
npm run dev:mp-weixin
```
然后用微信开发者工具打开 `dist/dev/mp-weixin` 目录

**H5 网页版**
```bash
npm run dev:h5
```
浏览器访问 http://localhost:8080

### 生产构建

```bash
# 微信小程序
npm run build:mp-weixin

# H5 网页版
npm run build:h5
```

## 📂 项目结构

```
frontend/
├── pages/              # 页面目录
│   ├── index/         # 首页
│   ├── detail/        # 详情页
│   ├── search/        # 搜索页
│   └── profile/       # 个人中心
├── static/            # 静态资源
│   └── icons/         # 图标资源
├── components/        # 组件（待添加）
├── utils/             # 工具函数（待添加）
├── App.vue            # 应用入口
├── uni.scss           # 全局样式
├── pages.json         # 页面配置
├── manifest.json      # 应用配置
└── package.json       # 依赖配置
```

## 🎯 后续开发计划

### 待实现功能

1. **API 集成**
   - 连接后端 FastAPI 接口
   - 实现数据获取和更新
   - 添加请求拦截器和错误处理

2. **状态管理**
   - 使用 Pinia 管理全局状态
   - 用户登录状态持久化
   - 收藏和浏览历史本地缓存

3. **组件封装**
   - SkillCard 技能卡片组件
   - CategoryChip 分类标签组件
   - LoadingSpinner 加载动画组件
   - EmptyState 空状态组件

4. **性能优化**
   - 图片懒加载
   - 列表虚拟滚动
   - 路由缓存
   - 骨架屏加载

5. **增强功能**
   - Markdown 内容渲染（使用 uParse 或 mp-html）
   - 代码高亮显示
   - 分享海报生成
   - 二维码生成

## 📱 微信小程序配置

### 申请 AppID

1. 登录微信公众平台：https://mp.weixin.qq.com
2. 注册小程序账号
3. 获取 AppID
4. 在 `manifest.json` 中填入 AppID

### 服务器域名配置

在微信公众平台后台配置合法域名：

- `request` 合法域名：你的后端 API 域名
- `uploadFile` 合法域名：图片上传域名
- `downloadFile` 合法域名：文件下载域名

### 注意事项

- 小程序必须使用 HTTPS 协议
- 域名必须经过 ICP 备案
- 测试阶段可在开发者工具中关闭域名校验

## 🎨 设计资源

### 图标来源

- TabBar 图标：需要放置在 `static/icons/` 目录
- 尺寸要求：81px × 81px (普通) / 162px × 162px (高清)

### 推荐字体

- **等宽字体**: SF Mono, Cascadia Code, Fira Code, JetBrains Mono
- **显示字体**: 思源黑体, PingFang SC

## 🤝 开发规范

### 命名约定

- 组件：PascalCase (`SkillCard.vue`)
- 页面：kebab-case (`skill-detail.vue`)
- 样式类：kebab-case (`.skill-card`)
- CSS 变量：kebab-case (`--neon-cyan`)

### 代码风格

- 使用 Vue 3 Composition API
- 使用 `<script setup>` 语法
- 样式使用 SCSS
- 遵循 ESLint 规则

### Git 提交规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
perf: 性能优化
test: 测试相关
chore: 构建工具或辅助工具的变动
```

## 📄 许可证

MIT License

---

**Built with 💙 using uni-app & Vue 3**

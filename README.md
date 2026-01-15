# Claude Skills 小程序市场

**为 Claude Code 初学者提供最便捷的技能发现和安装体验**

## 🎯 项目概述

Claude Skills 是一个基于微信小程序的 Claude Code 技能市场，帮助用户轻松浏览、搜索、收藏和安装 Claude Code 技能。

### 核心特性

- 🔍 **智能搜索**: 实时搜索、高级筛选、热门推荐
- 💫 **精美界面**: Terminal Cyberpunk 设计风格，独特的技术感
- 📱 **便捷分享**: 微信生态内一键分享，社交裂变传播
- ❤️ **个性收藏**: 收藏喜欢的技能，本地持久化存储
- 📦 **一键安装**: 复制安装命令，快速集成到 Claude Code

### 目标用户

- Claude Code 初学者
- 寻找高质量技能的开发者
- 技能创作者和分享者

## 📂 项目结构

```
claude-skills-miniapp/
├── frontend/              # uni-app 小程序前端
│   ├── pages/            # 页面目录
│   │   ├── index/       # 首页（技能列表）
│   │   ├── detail/      # 技能详情
│   │   ├── search/      # 搜索页
│   │   └── profile/     # 个人中心
│   ├── static/          # 静态资源
│   ├── uni.scss         # 全局样式
│   ├── App.vue          # 应用入口
│   ├── pages.json       # 页面配置
│   └── README.md        # 前端文档
│
├── backend/              # FastAPI 后端 ✅
│   ├── src/
│   │   ├── api/         # API 路由
│   │   ├── crawler/     # 爬虫模块
│   │   ├── storage/     # 数据层
│   │   └── config.py    # 配置
│   ├── scripts/         # 工具脚本
│   │   ├── init_db.py   # 初始化数据库
│   │   └── import_skills.py # 导入技能数据
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
└── docs/                 # 文档（待实现）
    ├── API.md           # API 文档
    └── DEPLOY.md        # 部署文档
```

## 🚀 快速开始

### 前端开发

```bash
cd frontend
npm install
npm run dev:mp-weixin
```

用微信开发者工具打开 `frontend/dist/dev/mp-weixin` 目录

详细说明见 [frontend/README.md](frontend/README.md)

### 后端开发

```bash
cd backend

# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium

# 配置环境变量
copy .env.example .env
# 编辑 .env 文件填入 MySQL 配置

# 初始化数据库
python scripts\init_db.py

# 导入技能数据
python scripts\import_skills.py

# 启动 API 服务
python src\api\main.py
```

访问 API 文档：http://localhost:8000/docs

详细说明见 [backend/README.md](backend/README.md)

## 🎨 设计特色

### Terminal Cyberpunk 美学

- 深空背景 + 霓虹色彩
- 等宽字体营造终端氛围
- 扫描线、光标闪烁等特效
- 渐变光晕、悬浮卡片

### 核心配色

- **霓虹青**: #00d9ff
- **霓虹紫**: #a855f7
- **终端绿**: #00ff88
- **深空背景**: #0a0e1a

## 📱 功能页面

### 1. 首页
- 技能列表（卡片式布局）
- 分类筛选
- 实时统计
- 下拉刷新 + 上拉加载

### 2. 技能详情
- 完整技能信息
- 一键复制安装命令
- Markdown 文档渲染
- 相关技能推荐

### 3. 搜索页
- 实时搜索（300ms 防抖）
- 快速筛选 + 高级筛选
- 热门搜索 + 历史记录

### 4. 个人中心
- 用户信息 + 微信登录
- 收藏/浏览历史
- 功能菜单 + 设置

## 🛠️ 技术栈

### 前端
- **框架**: uni-app (Vue 3)
- **语言**: Vue 3 + Composition API
- **样式**: SCSS + CSS 变量
- **平台**: 微信小程序 + H5

### 后端
- **框架**: FastAPI (Python)
- **数据库**: MySQL + Redis
- **爬虫**: Playwright + GitHub API
- **ORM**: SQLAlchemy 2.0 (异步)

## 📋 开发计划

### Phase 1: MVP 核心功能 (Week 1-2) ✅
- [x] 创建项目结构
- [x] 设计 UI 界面
- [x] 实现四个核心页面
- [x] 集成全局主题系统

### Phase 2: 后端开发 (Week 3-4) ✅
- [x] 搭建 FastAPI 项目
- [x] 实现 GitHub 技能爬虫
- [x] 设计数据库表结构
- [x] 开发 REST API

### Phase 3: 前后端对接 (Week 5)
- [ ] API 集成
- [ ] 状态管理（Pinia）
- [ ] 数据持久化
- [ ] 错误处理

### Phase 4: 功能完善 (Week 6)
- [ ] Markdown 渲染
- [ ] 分享海报生成
- [ ] 性能优化
- [ ] Bug 修复

### Phase 5: 测试上线 (Week 7-8)
- [ ] 内测 + 反馈收集
- [ ] 微信小程序审核
- [ ] 正式上线
- [ ] 宣传推广

## 🎯 成功指标

### 用户数据（MVP 阶段）
- 上线第一个月 DAU > 100
- 用户留存率（次日留存 > 30%）
- 分享率 > 10%

### 内容数据
- 收录技能数 > 50
- 热门技能浏览量 > 1000/周
- 技能收藏数 > 500

## 💡 商业化方向

### 短期（MVP 验证后）
- 技能推荐广告位
- 付费技能上架服务

### 长期
- 企业定制技能开发
- 技能培训课程
- 技能开发者社区

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

MIT License

---

**Built with 💙 for Claude Code Community**

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Claude Skills 是一个 Claude Code 技能市场小程序，包含 uni-app 前端和 FastAPI 后端。帮助用户浏览、搜索、收藏和安装 Claude Code 技能。

## 常用开发命令

### ⚠️ 重要提示：前端启动问题

**此项目前端使用 uni-app 3.x alpha 版本，依赖包不完整，无法通过 npm 命令直接启动。**

**推荐使用 HBuilderX 开发工具启动项目。详细步骤见 [START.md](START.md)**

### 前端开发 (frontend/) - 仅供参考

```bash
# ❌ 以下命令目前无法工作，因为 @dcloudio 依赖缺失关键文件
cd frontend
npm install

# ❌ 这些命令会报错：ENOENT: no such file or directory
npm run dev:mp-weixin
npm run dev:h5

# ✅ 请使用 HBuilderX 替代
# 下载地址: https://www.dcloud.io/hbuilderx.html
# 操作: 文件 → 导入 → 选择 frontend 目录 → 运行到小程序模拟器
```

### 后端开发 (backend/)

```bash
# 环境准备
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
playwright install chromium  # 安装浏览器

# 配置数据库
copy .env.example .env       # 配置 MySQL 连接信息

# 数据库操作
python scripts\init_db.py              # 初始化数据库表
python scripts\init_db.py --force      # 强制重建表（危险）
python scripts\import_skills.py        # 爬取导入技能数据

# 启动 API 服务
python src\api\main.py       # 开发模式，自动重载
# 访问 http://localhost:8000/docs (API 文档)

# 或使用 uvicorn
uvicorn src.api.main:app --reload --port 8000
```

## 核心架构

### 前端架构 (uni-app + Vue 3)

**页面结构**:
- `pages/index/` - 首页技能列表，分类筛选，下拉刷新，收藏功能
- `pages/detail/` - 技能详情，安装命令复制，Markdown 渲染，相关推荐
- `pages/search/` - 实时搜索（300ms 防抖），快速筛选，高级筛选
- `pages/profile/` - 个人中心，用户信息，收藏历史

**设计系统 - Terminal Cyberpunk**:
- 使用 `uni.scss` 全局样式和 CSS 变量
- 核心配色: 深空背景 (#0a0e1a)，霓虹青 (#00d9ff)，霓虹紫 (#a855f7)，终端绿 (#00ff88)
- 等宽字体营造终端氛围
- 组件使用 Vue 3 Composition API + `<script setup>` 语法

**配置文件**:
- `pages.json` - 页面路由和 TabBar 配置
- `manifest.json` - 应用配置和小程序 AppID

### 后端架构 (FastAPI + SQLAlchemy 2.0)

**分层设计**:
```
src/
├── api/              # API 层
│   ├── main.py       # FastAPI 应用入口，CORS 配置，路由注册
│   └── routers/      # 路由模块
│       ├── skills.py      # 技能 CRUD，列表查询，分类筛选
│       └── favorites.py   # 收藏管理，用户收藏列表
├── storage/          # 数据层
│   ├── models.py     # SQLAlchemy 模型定义
│   └── database.py   # 数据库连接，Repository 模式
├── crawler/          # 爬虫层
│   ├── base_crawler.py         # Playwright 基础爬虫封装
│   └── github_skill_crawler.py # 从 anthropics/skills 抓取
└── config.py         # 配置管理 (Pydantic Settings)
```

**数据模型关系** (storage/models.py):
- `Skill` - 技能核心模型
  - 基础信息: name, slug (唯一), description, author
  - GitHub 信息: github_url, stars, forks
  - 分类: category (SkillCategory 枚举), tags (JSON)
  - 内容: content (完整 Markdown), install_command
  - 统计: view_count, favorite_count, share_count (冗余字段，快速查询)
  - 状态: status (active/archived/pending), is_official

- `User` - 用户模型
  - 微信信息: openid (唯一), unionid, session_key
  - 用户资料: nickname, avatar_url, gender, city, province

- `Favorite` - 收藏关联表
  - 外键: user_id, skill_id
  - 唯一约束: (user_id, skill_id)

- `SkillStats` - 技能统计 (按日)
  - 外键: skill_id
  - 统计数据: view_count, favorite_count, share_count
  - 唯一约束: (skill_id, date)

**Repository 模式** (database.py):
```python
async with get_session() as session:
    repo = SkillRepository(session)
    skills, total = await repo.list(
        category=SkillCategory.DEBUGGING,
        search_query="test",
        limit=20, offset=0
    )
```

**API 路由** (基于 FastAPI):
- `GET /api/skills` - 技能列表，支持分类、搜索、分页、排序
- `GET /api/skills/{skill_id}` - 技能详情
- `POST /api/skills/{skill_id}/share` - 记录分享
- `GET /api/skills/categories/list` - 分类列表
- `POST /api/favorites` - 添加收藏
- `DELETE /api/favorites` - 取消收藏
- `GET /api/favorites/user/{user_id}` - 用户收藏列表

**爬虫系统** (crawler/):
- `BaseCrawler` - Playwright 异步上下文管理器
- `GitHubSkillCrawler` - 从 anthropics/skills 仓库抓取
  - 智能分类推断: 从路径和内容提取 category
  - 标签提取: 识别技术关键词 (react, python, playwright...)
  - 安装命令生成: `claude plugin install {github_url}`

## 开发规范

### 前端
- 使用 Vue 3 Composition API + `<script setup>`
- 样式使用 SCSS，遵循全局 CSS 变量 (uni.scss)
- 命名约定: 组件 PascalCase，页面 kebab-case，样式类 kebab-case
- 提交规范: feat/fix/docs/style/refactor/perf/test/chore

### 后端
- 使用 SQLAlchemy 2.0 异步 API
- 数据访问必须通过 Repository 层，禁止直接操作 ORM
- Pydantic 模型用于请求/响应验证
- 日志记录使用 logging 模块
- 爬虫需设置合理间隔 (asyncio.sleep)，避免被封

## 环境要求

- 前端: Node.js >= 16.0.0
- 后端: Python >= 3.10, MySQL >= 5.7 (utf8mb4), Playwright
- 开发工具: 微信开发者工具 (小程序预览)

## 重要提示

- MySQL 字符集必须是 utf8mb4
- 后端使用 Windows 路径分隔符 `\`
- 小程序正式环境需配置合法域名 (HTTPS + ICP 备案)
- 爬虫抓取 GitHub 需注意反爬限制，建议配置 GitHub Token
- 统计字段 (view_count, favorite_count) 是冗余设计，用于快速查询，需保持同步
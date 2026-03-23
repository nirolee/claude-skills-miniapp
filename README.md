# skill技能助手 · Claude Code Skills 小程序

> 收录 **13万+** Claude Code Skills，微信小程序内直接搜索、收藏、一键复制安装命令。

微信搜索「**skill技能助手**」立即体验 👆

---

## 为什么做这个

Claude Code 的 skills 生态发展很快，但分散在 GitHub 各处，没有统一的地方搜索和管理。这个小程序把 GitHub 上的 SKILL.md 全部爬取收录，按分类整理，方便查找和使用。

## 功能

- 🔍 **搜索** — 13万+ skills 全文检索
- 📂 **分类浏览** — 26个分类，覆盖开发、写作、分析等场景
- ⭐ **收藏** — 收藏常用 skills，随时查看
- 📋 **一键复制** — 直接复制安装命令到 Claude Code

## 数据规模

| 指标 | 数量 |
|------|------|
| 收录 Skills | 130,000+ |
| 分类 | 26 |
| GitHub Stars 总计 | 162,000,000+ |

## 技术栈

**后端** — FastAPI + SQLAlchemy + MySQL  
**爬虫** — GitHub API + Playwright  
**前端** — uni-app (Vue 3) · 微信小程序  

## 本地运行

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# 填入 MySQL 配置和 GitHub Token

python scripts/init_db.py
python src/api/main.py
```

API 文档：http://localhost:8000/docs

## 环境变量

参考 `backend/.env.example`，需要配置：
- MySQL 数据库连接
- GitHub Token（用于爬虫限流）

## 使用小程序

微信扫码或搜索「**skill技能助手**」

<!-- 这里可以放小程序码图片 -->

## License

MIT

# Claude Skills 小程序 - 后端

基于 FastAPI 的高性能后端服务，提供技能数据管理、用户认证和数据统计功能。

## 技术栈

- **FastAPI**: 现代异步 Web 框架
- **SQLAlchemy 2.0**: 异步 ORM
- **MySQL 5.7+**: 关系型数据库
- **Playwright**: 网页爬虫
- **Pydantic**: 数据验证

## 项目结构

```
backend/
├── src/
│   ├── api/              # API 路由
│   │   ├── routers/
│   │   │   ├── skills.py      # 技能相关接口
│   │   │   └── favorites.py   # 收藏相关接口
│   │   └── main.py       # FastAPI 应用入口
│   ├── crawler/          # 爬虫模块
│   │   ├── base_crawler.py    # Playwright 基础爬虫
│   │   └── github_skill_crawler.py  # GitHub 技能爬虫
│   ├── storage/          # 数据层
│   │   ├── models.py     # SQLAlchemy 模型
│   │   └── database.py   # 数据库连接和 Repository
│   └── config.py         # 配置管理
├── scripts/              # 工具脚本
│   ├── init_db.py        # 初始化数据库
│   └── import_skills.py  # 导入技能数据
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 环境准备

```powershell
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 配置环境变量

```powershell
# 复制配置模板
copy .env.example .env

# 编辑 .env 文件，填入 MySQL 配置
notepad .env
```

必须配置的变量：
- `MYSQL_HOST`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

### 3. 初始化数据库

```powershell
# 创建数据库表结构
python scripts\init_db.py

# 如果需要重建所有表（危险！）
python scripts\init_db.py --force
```

### 4. 导入技能数据

```powershell
# 从 GitHub 抓取技能数据
python scripts\import_skills.py
```

### 5. 启动服务

```powershell
# 开发模式（自动重载）
python src\api\main.py

# 或使用 uvicorn
uvicorn src.api.main:app --reload --port 8000
```

访问 API 文档：http://localhost:8000/docs

## API 接口

### 技能相关

- `GET /api/skills` - 获取技能列表（支持分类、搜索、分页）
- `GET /api/skills/{skill_id}` - 获取技能详情
- `POST /api/skills/{skill_id}/share` - 记录分享
- `GET /api/skills/categories/list` - 获取分类列表

### 收藏相关

- `POST /api/favorites` - 添加收藏
- `DELETE /api/favorites` - 取消收藏
- `GET /api/favorites/user/{user_id}` - 获取用户收藏列表
- `GET /api/favorites/check` - 检查收藏状态

## 数据模型

### Skill (技能)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| name | str | 技能名称 |
| slug | str | URL slug（唯一） |
| description | str | 简短描述 |
| author | str | 作者 |
| github_url | str | GitHub 链接 |
| category | enum | 分类 |
| tags | json | 标签数组 |
| content | text | 完整 Markdown 内容 |
| install_command | str | 安装命令 |
| stars | int | GitHub stars |
| forks | int | GitHub forks |
| view_count | int | 浏览次数 |
| favorite_count | int | 收藏次数 |
| is_official | bool | 是否官方技能 |

### User (用户)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| openid | str | 微信 openid（唯一） |
| nickname | str | 昵称 |
| avatar_url | str | 头像 URL |

### Favorite (收藏)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| user_id | int | 用户 ID |
| skill_id | int | 技能 ID |
| created_at | datetime | 创建时间 |

## 开发指南

### Repository 模式

所有数据访问通过 Repository 类：

```python
from src.storage.database import get_session, SkillRepository

async with get_session() as session:
    repo = SkillRepository(session)
    skills, total = await repo.list(
        category=SkillCategory.DEBUGGING,
        limit=20
    )
```

### 添加新的 API 路由

1. 在 `src/api/routers/` 创建新的路由文件
2. 定义 Pydantic 模型（请求/响应）
3. 实现路由处理函数
4. 在 `src/api/main.py` 注册路由

### 添加新的爬虫

1. 在 `src/crawler/` 创建爬虫类
2. 继承 `BaseCrawler` 或独立实现
3. 实现数据提取和保存逻辑
4. 创建对应的 scripts/ 脚本

## 注意事项

### Windows 环境

- 使用 PowerShell 或 CMD
- 路径分隔符使用 `\` 或 `/`
- 日志文件编码使用 UTF-8

### 数据库

- MySQL 版本 >= 5.7
- 字符集必须是 utf8mb4
- 建议开启 SQL 慢查询日志

### 爬虫

- GitHub 可能有反爬虫限制
- 建议配置 GitHub Token 提高 API 限额
- 合理设置爬取间隔，避免被封禁

## 故障排查

### 数据库连接失败

```powershell
# 测试 MySQL 连接
mysql -h localhost -u root -p

# 检查防火墙设置
```

### Playwright 浏览器启动失败

```powershell
# 重新安装浏览器
playwright install chromium --force
```

### 依赖安装失败

```powershell
# 清理 pip 缓存
pip cache purge

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 部署建议

### 生产环境

1. 使用 Gunicorn/Uvicorn workers
2. 配置 Nginx 反向代理
3. 启用 HTTPS
4. 配置日志轮转
5. 设置定时任务（爬虫更新）

### Docker 部署（待实现）

```dockerfile
# Dockerfile 示例
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "src/api/main.py"]
```

## 许可证

MIT License

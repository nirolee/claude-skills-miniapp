# GitHub Actions 部署配置说明

本项目使用 GitHub Actions 自动部署到 223 服务器。

## 配置步骤

### 1. 在 GitHub 仓库设置 Secrets

进入仓库 Settings → Secrets and variables → Actions，添加以下 secrets：

| Secret 名称 | 说明 | 示例值 |
|------------|------|--------|
| `SERVER_HOST` | 服务器 IP 地址 | `223.109.140.233` |
| `SERVER_USER` | SSH 用户名 | `root` 或 `ubuntu` |
| `SSH_PRIVATE_KEY` | SSH 私钥 | 完整的私钥内容 |
| `SERVER_PORT` | SSH 端口（可选） | `22`（默认） |

### 2. 生成 SSH 密钥对（如果没有）

在本地执行：
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions_key
```

- 将公钥 `~/.ssh/github_actions_key.pub` 添加到服务器的 `~/.ssh/authorized_keys`
- 将私钥 `~/.ssh/github_actions_key` 的完整内容复制到 GitHub Secret `SSH_PRIVATE_KEY`

### 3. 服务器准备

#### 创建项目目录
```bash
sudo mkdir -p /var/www/claude-skills-miniapp
sudo chown $USER:$USER /var/www/claude-skills-miniapp
```

#### 配置 Supervisor（管理 API 服务）

创建配置文件 `/etc/supervisor/conf.d/claude-skills-api.conf`：
```ini
[program:claude-skills-api]
command=/var/www/claude-skills-miniapp/backend/venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
directory=/var/www/claude-skills-miniapp/backend
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/claude-skills-api.log
environment=PATH="/var/www/claude-skills-miniapp/backend/venv/bin"
```

重启 Supervisor：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start claude-skills-api
```

#### 配置 Nginx（反向代理）

创建配置 `/etc/nginx/sites-available/claude-skills`：
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为实际域名

    # API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 前端静态资源（如果使用 H5）
    location / {
        root /var/www/claude-skills-miniapp/frontend;
        try_files $uri $uri/ /index.html;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/claude-skills /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. 设置定时任务（爬虫）

编辑 crontab：
```bash
crontab -e
```

添加：
```bash
# 每天凌晨 3 点运行爬虫更新技能数据
0 3 * * * cd /var/www/claude-skills-miniapp/backend && /var/www/claude-skills-miniapp/backend/venv/bin/python scripts/browser_api_crawler.py >> /var/log/skillsmp_crawler.log 2>&1
```

## 部署流程

### 自动部署（推荐）

1. 提交代码到 `main` 或 `master` 分支
2. GitHub Actions 自动触发部署
3. 后端自动更新、安装依赖、重启服务
4. 前端代码更新（需手动构建小程序）

### 手动运行爬虫

在 GitHub 仓库页面：
1. 进入 Actions 标签
2. 选择 "部署到 223 服务器" workflow
3. 点击 "Run workflow"
4. 勾选运行爬虫选项

## 部署后检查

### 检查 API 服务
```bash
# SSH 登录服务器
ssh user@223.109.140.233

# 检查服务状态
supervisorctl status claude-skills-api

# 查看日志
tail -f /var/log/claude-skills-api.log

# 测试 API
curl http://localhost:8000/api/skills?page=1&limit=10
```

### 检查数据库
```bash
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python scripts/count_skills.py
```

## 故障排查

### API 服务无法启动
```bash
# 查看详细日志
tail -100 /var/log/claude-skills-api.log

# 手动启动测试
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### 数据库连接失败
检查 `backend/.env` 文件配置：
```ini
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/claude_skills?charset=utf8mb4
```

### 爬虫失败
```bash
# 手动运行爬虫测试
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python scripts/browser_api_crawler.py
```

## 小程序部署

由于 uni-app 项目需要专门的构建工具，小程序部署需要：

### 方案 A：使用 HBuilderX
1. 在 HBuilderX 中导入 `frontend` 目录
2. 运行 → 运行到小程序模拟器 → 微信开发者工具
3. 发行 → 小程序-微信 → 上传到微信平台

### 方案 B：使用 CLI（如果支持）
```bash
cd frontend
npm run build:mp-weixin
# 将 dist/build/mp-weixin 上传到微信开发者工具
```

## 参考资料

- [GitHub Actions SSH 部署](https://github.com/appleboy/ssh-action)
- [Supervisor 文档](http://supervisord.org/)
- [Nginx 反向代理配置](https://nginx.org/en/docs/)
- [uni-app 发行文档](https://uniapp.dcloud.net.cn/tutorial/build/)

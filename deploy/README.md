# 部署配置文件说明

本目录包含服务器部署所需的配置文件。

## 文件列表

- `claude-skills-api.conf` - Supervisor 进程管理配置
- `nginx-claude-skills.conf` - Nginx 反向代理配置

## 使用方法

### 1. Supervisor 配置

将配置文件复制到 Supervisor 配置目录：

```bash
sudo cp deploy/claude-skills-api.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start claude-skills-api
```

查看服务状态：

```bash
sudo supervisorctl status claude-skills-api
```

查看日志：

```bash
tail -f /var/log/claude-skills-api.log
```

### 2. Nginx 配置

将配置文件复制到 Nginx 配置目录：

```bash
sudo cp deploy/nginx-claude-skills.conf /etc/nginx/sites-available/claude-skills
sudo ln -s /etc/nginx/sites-available/claude-skills /etc/nginx/sites-enabled/
```

修改配置中的域名：

```bash
sudo nano /etc/nginx/sites-available/claude-skills
# 将 server_name 修改为实际域名或 IP
```

测试配置并重启：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 3. 环境变量配置

复制并编辑环境变量文件：

```bash
cd /var/www/claude-skills-miniapp/backend
cp .env.example .env
nano .env
```

必须配置的项：
- `MYSQL_PASSWORD` - MySQL 数据库密码
- `WECHAT_APPID` - 微信小程序 AppID
- `WECHAT_SECRET` - 微信小程序 AppSecret

可选配置：
- `GITHUB_TOKEN` - GitHub API Token（用于获取 stars/forks）
- `DEBUG=False` - 生产环境建议设置为 False

### 4. 定时任务（爬虫）

添加 crontab 定时任务：

```bash
crontab -e
```

添加以下内容（每天凌晨 3 点运行爬虫）：

```bash
0 3 * * * cd /var/www/claude-skills-miniapp/backend && /var/www/claude-skills-miniapp/backend/venv/bin/python scripts/browser_api_crawler.py >> /var/log/skillsmp_crawler.log 2>&1
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

检查 `.env` 文件中的数据库配置：

```bash
cd /var/www/claude-skills-miniapp/backend
cat .env | grep MYSQL
```

测试数据库连接：

```bash
mysql -u root -p -e "SHOW DATABASES;" | grep claude_skills
```

### Nginx 502 错误

检查 API 服务是否运行：

```bash
sudo supervisorctl status claude-skills-api
curl http://127.0.0.1:8000/api/skills?page=1&limit=10
```

检查 Nginx 错误日志：

```bash
tail -f /var/log/nginx/error.log
```

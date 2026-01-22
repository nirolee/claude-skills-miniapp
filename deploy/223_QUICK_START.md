# 223 服务器部署 - 快速开始

## 📦 部署内容

✅ **API 服务** (已有) - 后端 API
🆕 **内容更新任务** (新增) - 从 GitHub 获取完整 SKILL.md
🆕 **翻译任务** (新增) - AI 翻译，**每天上午 10 点运行**（白天运行）

---

## 🚀 一键部署

在 223 服务器上运行：

```bash
cd /var/www/claude-skills-miniapp
git pull  # 获取最新代码

# 一键部署
bash deploy/deploy_to_223.sh
```

这个脚本会自动：
1. ✅ 更新代码
2. ✅ 安装依赖 (aiohttp)
3. ✅ 配置 Supervisor（内容更新任务）
4. ✅ 配置 Crontab（翻译任务 - 上午 10 点）
5. ✅ 启动所有服务
6. ✅ 运行验证检查

---

## ✅ 部署后验证

运行验证脚本：

```bash
bash /var/www/claude-skills-miniapp/deploy/verify_deployment.sh
```

**验证内容**:
- ✅ Supervisor 服务状态
- ✅ Crontab 配置
- ✅ API 服务响应
- ✅ 数据库连接
- ✅ 日志文件
- ✅ 内容更新进度
- ✅ 数据库统计

---

## 📊 查看运行状态

### 查看所有服务
```bash
sudo supervisorctl status
```

**预期输出**:
```
claude-skills-api                RUNNING   pid 12345, uptime 1:23:45
claude-skills-content-update     RUNNING   pid 12346, uptime 0:00:10
```

### 查看实时日志

```bash
# 内容更新日志
tail -f /var/log/claude-skills-content-update.log

# API 日志
tail -f /var/log/claude-skills-api.log

# 翻译日志（定时任务运行后才有）
tail -f /var/log/claude-skills-translate.log
```

### 查看内容更新进度

```bash
cd /var/www/claude-skills-miniapp/backend
cat logs/content_update_progress.json | python -m json.tool
```

---

## ⚙️ 管理命令

### Supervisor 管理

```bash
# 查看状态
sudo supervisorctl status

# 停止内容更新
sudo supervisorctl stop claude-skills-content-update

# 启动内容更新
sudo supervisorctl start claude-skills-content-update

# 重启 API
sudo supervisorctl restart claude-skills-api

# 查看所有日志
sudo supervisorctl tail -f claude-skills-content-update
```

### Crontab 管理

```bash
# 查看定时任务
crontab -l

# 编辑定时任务
crontab -e
```

**当前配置**:
- 爬虫: 每天凌晨 3 点
- **翻译: 每天上午 10 点**（白天运行）

---

## 📈 预期效果

### 内容更新任务（持续运行）
- **处理速度**: 每秒 1 个 skill
- **预计时间**: 3-4 小时完成 12,000+ skills
- **自动跳过**: 已更新的 skills
- **断点续传**: 中断后继续

### 翻译任务（每天上午 10 点）
- **运行时间**: 上午 10 点（白天，避免影响晚上使用）
- **自动跳过**: 已翻译的 skills
- **默认行为**: 翻译所有未翻译的

如果想限制每天翻译数量，修改 crontab:
```bash
crontab -e
# 改为: 0 10 * * * ... scripts/translate_skills.py --limit 100 ...
```

---

## ⚠️ 重要提示

### 1. API Key 配置
翻译功能需要 Anthropic API Key：

```bash
nano /var/www/claude-skills-miniapp/backend/.env
# 添加: ANTHROPIC_API_KEY=your_key_here
```

### 2. 翻译时间改为白天
✅ 已配置为**每天上午 10 点运行**，避免晚上占用资源

### 3. 不会重复处理
- ✅ 内容更新：自动跳过已更新的 skills
- ✅ 翻译任务：自动跳过已翻译的 skills

---

## 🔧 故障排查

### 问题：内容更新任务未运行

```bash
# 查看状态
sudo supervisorctl status claude-skills-content-update

# 查看错误日志
tail -50 /var/log/claude-skills-content-update.log

# 手动测试
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python scripts/continuous_update_content.py
```

### 问题：翻译任务未执行

```bash
# 检查 crontab
crontab -l | grep translate

# 检查 API Key
cat /var/www/claude-skills-miniapp/backend/.env | grep ANTHROPIC_API_KEY

# 手动测试
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python scripts/translate_skills.py --limit 5
```

---

## 📞 需要帮助？

详细文档: `deploy/SERVER_223_DEPLOYMENT.md`

快速检查: `bash deploy/verify_deployment.sh`

# 223 服务器部署和任务管理指南

## 📋 当前运行的任务

### 1. API 服务（Supervisor 守护进程）
- **程序**: `claude-skills-api`
- **功能**: FastAPI 后端服务
- **端口**: 8000
- **状态**: 常驻运行
- **日志**: `/var/log/claude-skills-api.log`

### 2. 爬虫任务（Crontab 定时任务）
- **程序**: `browser_api_crawler.py`
- **功能**: 从 SkillsMP 抓取新 skills
- **运行时间**: 每天凌晨 3 点
- **日志**: `/var/log/skillsmp_crawler.log`

---

## 🆕 新增任务

### 3. 内容更新任务（Supervisor 守护进程）⭐ 新增
- **程序**: `continuous_update_content.py`
- **功能**: 从 GitHub 获取完整 SKILL.md 内容
- **特性**:
  - ✅ 断点续传（中断后继续运行）
  - ✅ 自动跳过已处理的 skills
  - ✅ 进度保存到 `logs/content_update_progress.json`
  - ✅ 完成后自动停止
- **日志**: `/var/log/claude-skills-content-update.log`

### 4. 翻译任务（Crontab 定时任务）⭐ 新增
- **程序**: `translate_skills.py`
- **功能**: AI 翻译 skill 的 name、description、content
- **运行时间**: 每天上午 10 点（白天运行，避免晚上占用资源）
- **日志**: `/var/log/claude-skills-translate.log`

---

## 🚀 部署步骤

### 步骤 1: 上传新文件到服务器

```bash
# 在本地打包需要上传的文件
cd D:\niro\claude-skills-miniapp\backend

# 上传到服务器
scp scripts/continuous_update_content.py root@223.109.140.233:/var/www/claude-skills-miniapp/backend/scripts/
scp -r src/services/ai_translation.py root@223.109.140.233:/var/www/claude-skills-miniapp/backend/src/services/
scp deploy/claude-skills-supervisor.conf root@223.109.140.233:/tmp/
```

或者在服务器上直接 `git pull`（如果配置了 git）。

### 步骤 2: 配置 Supervisor（内容更新任务）

```bash
# 1. 备份旧配置
sudo cp /etc/supervisor/conf.d/claude-skills-api.conf /etc/supervisor/conf.d/claude-skills-api.conf.bak

# 2. 更新配置
sudo cp /tmp/claude-skills-supervisor.conf /etc/supervisor/conf.d/claude-skills.conf

# 3. 重新加载配置
sudo supervisorctl reread
sudo supervisorctl update

# 4. 查看所有任务状态
sudo supervisorctl status

# 应该看到:
# claude-skills-api                RUNNING   pid 12345, uptime 1:23:45
# claude-skills-content-update     RUNNING   pid 12346, uptime 0:00:10
```

### 步骤 3: 配置 Crontab（翻译任务）

```bash
# 编辑 crontab
crontab -e

# 添加以下内容（如果已有爬虫任务，在下面添加）:

# 每天凌晨 3 点运行爬虫（已有）
0 3 * * * cd /var/www/claude-skills-miniapp/backend && /var/www/claude-skills-miniapp/backend/venv/bin/python scripts/smart_crawler.py >> /var/log/skillsmp_crawler.log 2>&1

# 每天上午 10 点运行翻译（新增）⭐ 白天运行，避免晚上占用资源
0 10 * * * cd /var/www/claude-skills-miniapp/backend && /var/www/claude-skills-miniapp/backend/venv/bin/python scripts/translate_skills.py >> /var/log/claude-skills-translate.log 2>&1
0 2 * * * cd /var/www/claude-skills-miniapp/backend && /var/www/claude-skills-miniapp/backend/venv/bin/python scripts/translate_skills.py >> /var/log/claude-skills-translate.log 2>&1

# 保存退出（ESC + :wq）
```

### 步骤 4: 配置 API Key（翻译需要）

```bash
# 编辑环境变量
cd /var/www/claude-skills-miniapp/backend
nano .env

# 添加 Anthropic API Key（如果还没有）
ANTHROPIC_API_KEY=your_api_key_here

# 保存退出（Ctrl+X, Y, Enter）

# 重启 API 服务以加载新环境变量
sudo supervisorctl restart claude-skills-api
```

---

## 📊 监控和管理

### 查看任务状态

```bash
# 查看所有 supervisor 任务
sudo supervisorctl status

# 查看内容更新任务
sudo supervisorctl status claude-skills-content-update

# 查看 crontab 任务
crontab -l
```

### 查看日志

```bash
# API 服务日志
tail -f /var/log/claude-skills-api.log

# 内容更新日志
tail -f /var/log/claude-skills-content-update.log

# 翻译任务日志
tail -f /var/log/claude-skills-translate.log

# 爬虫日志
tail -f /var/log/skillsmp_crawler.log
```

### 查看内容更新进度

```bash
cd /var/www/claude-skills-miniapp/backend

# 查看进度文件
cat logs/content_update_progress.json

# 或者用 Python 格式化查看
python3 << 'EOF'
import json
with open('logs/content_update_progress.json', 'r') as f:
    data = json.load(f)
    print(f"开始时间: {data['started_at']}")
    print(f"上次更新: {data['last_update']}")
    print(f"已处理: {len(data['processed_ids'])} 个")
    print(f"成功: {data['success_count']}")
    print(f"失败: {data['failed_count']}")
    print(f"跳过: {data['skipped_count']}")
EOF
```

### 手动控制任务

```bash
# 停止内容更新任务
sudo supervisorctl stop claude-skills-content-update

# 启动内容更新任务
sudo supervisorctl start claude-skills-content-update

# 重启内容更新任务
sudo supervisorctl restart claude-skills-content-update

# 手动运行翻译（不等定时任务）
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python scripts/translate_skills.py --limit 10  # 测试翻译 10 个
```

---

## 🔍 验证部署结果

### 1. 验证内容更新任务是否运行

```bash
# 方法 1: 检查进程
ps aux | grep continuous_update_content

# 方法 2: 检查日志（应该有更新记录）
tail -20 /var/log/claude-skills-content-update.log

# 方法 3: 检查数据库
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python << 'EOF'
import asyncio
from sqlalchemy import text
from src.storage.database import get_session

async def check():
    async with get_session() as session:
        query = text("SELECT AVG(LENGTH(content)) as avg_len, MAX(LENGTH(content)) as max_len FROM skills")
        result = await session.execute(query)
        row = result.fetchone()
        print(f"平均内容长度: {row.avg_len:.0f} 字符")
        print(f"最长内容: {row.max_len} 字符")

asyncio.run(check())
EOF
```

### 2. 验证翻译任务配置

```bash
# 检查 crontab 是否配置
crontab -l | grep translate

# 手动测试翻译（小规模）
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python scripts/translate_skills.py --limit 5
```

---

## ⚠️ 注意事项

### 1. 资源使用
- **内容更新任务**: 每秒 1 个请求，对 GitHub 友好
- **翻译任务**: 消耗 API tokens，建议只翻译未翻译的

### 2. 任务优先级
建议执行顺序：
1. 先让内容更新任务运�� 1-2 天（获取完整内容）
2. 再启用翻译任务（翻译完整内容）

### 3. 成本控制
- 翻译任务会消耗 Anthropic API tokens
- 可以通过 `--limit` 参数控制每次翻译数量
- 建议在 crontab 中设置每天翻译上限

修改 crontab 翻译任务为每次翻译 100 个（上午 10 点运行）：
```bash
0 10 * * * cd /var/www/claude-skills-miniapp/backend && /var/www/claude-skills-miniapp/backend/venv/bin/python scripts/translate_skills.py --limit 100 >> /var/log/claude-skills-translate.log 2>&1
```

### 4. 断点续传
- 内容更新任务支持断点续传
- 如果中途停止（如服务器重启），下次会自动从中断处继续
- 进度保存在 `logs/content_update_progress.json`

---

## 🐛 故障排查

### 问题 1: 内容更新任务没有运行

**检查步骤**:
```bash
# 1. 检查 supervisor 状态
sudo supervisorctl status claude-skills-content-update

# 2. 查看错误日志
tail -50 /var/log/claude-skills-content-update.log

# 3. 手动测试
cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate
python scripts/continuous_update_content.py
```

**常见原因**:
- 虚拟环境路径不对
- Python 依赖缺失：`pip install aiohttp`
- 数据库连接失败

### 问题 2: 翻译任务报错

**检查步骤**:
```bash
# 1. 检查 API Key
cd /var/www/claude-skills-miniapp/backend
cat .env | grep ANTHROPIC_API_KEY

# 2. 手动测试翻译
source venv/bin/activate
python scripts/translate_skills.py --limit 1

# 3. 查看翻译日志
tail -50 /var/log/claude-skills-translate.log
```

**常见原因**:
- API Key 未配置或无效
- API 余额不足
- 网络连接问题

### 问题 3: 内容更新很慢

这是正常的！因为：
- 12,000+ skills 需要逐个从 GitHub 获取
- 每个请求间隔 1 秒（避免限流）
- 预计需要 3-4 小时完成

**加速方法**（不推荐，可能被 GitHub 限流）:
```bash
# 修改延迟参数（需要修改代码）
# 在 continuous_update_content.py 中修改:
# delay_between_requests=0.5  # 改为 0.5 秒
```

---

## 📈 预期效果

完成部署并运行 1-2 天后：

1. **内容更新完成**:
   - 平均 content 长度: 200 字符 → 2000+ 字符
   - 长内容 skills: 0 个 → 8000+ 个

2. **翻译完成**:
   - 已翻译 content_zh: 4400 个 → 12000+ 个
   - 用户可查看完整中文 SKILL.md

3. **用户体验提升**:
   - 技能详情页显示完整内容
   - 支持中英文切换
   - Markdown 格式完整保留

---

## 🎯 快速部署命令总结

```bash
# 1. 上传文件（git pull 或 scp）
cd /var/www/claude-skills-miniapp
git pull

# 2. 安装依赖
cd backend
source venv/bin/activate
pip install aiohttp

# 3. 配置 API Key
nano .env
# 添加: ANTHROPIC_API_KEY=your_key

# 4. 配置 Supervisor
sudo cp deploy/claude-skills-supervisor.conf /etc/supervisor/conf.d/claude-skills.conf
sudo supervisorctl reread
sudo supervisorctl update

# 5. 配置 Crontab
crontab -e
# 添加翻译任务（上午 10 点）: 0 10 * * * cd /var/www/claude-skills-miniapp/backend && venv/bin/python scripts/translate_skills.py >> /var/log/claude-skills-translate.log 2>&1

# 6. 验证
sudo supervisorctl status
tail -f /var/log/claude-skills-content-update.log
```

完成！🎉

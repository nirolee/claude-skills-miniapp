# 定时任务配置指南

## 1. 翻译 API 配置

### 方案A: 百度翻译（推荐，免费额度5万字符/月）

1. 访问 https://fanyi-api.baidu.com/ 注册账号
2. 创建应用获取 APP ID 和密钥
3. 在 `.env` 文件中配置：

```bash
BAIDU_TRANSLATE_APP_ID=你的APP_ID
BAIDU_TRANSLATE_SECRET=你的密钥
```

### 方案B: Anthropic Claude API

在 `.env` 文件中配置：

```bash
ANTHROPIC_API_KEY=sk-ant-xxx
```

**注意**: Claude API 按 token 计费，适合高质量长文本翻译

## 2. 本地测试

### 测试爬虫（幂等机制）

```bash
cd backend
python scripts/browser_api_crawler.py
```

第二次运行应该显示大量"跳过(无变化)"，证明幂等机制生效。

### 测试翻译（翻译前10个）

```bash
python scripts/translate_skills.py --limit 10
```

### 测试完整定时任务

```bash
python scripts/scheduled_task.py --translate-limit 5
```

## 3. 部署到223服务器

### 步骤1: 上传代码

```bash
# 推送到 GitHub
git add .
git commit -m "添加定时任务和翻译功能"
git push origin main

# SSH 到服务器
ssh root@223.109.140.233

# 拉取最新代码
cd /var/www/claude-skills-miniapp
git pull origin main
```

### 步骤2: 安装依赖

```bash
cd backend
source venv/bin/activate
pip install httpx anthropic
```

### 步骤3: 配置翻译 API

```bash
# 编辑 .env 文件
nano .env

# 添加百度翻译配置
BAIDU_TRANSLATE_APP_ID=你的APP_ID
BAIDU_TRANSLATE_SECRET=你的密钥
```

### 步骤4: 数据库迁移

```bash
python scripts/add_chinese_fields.py
```

### 步骤5: 测试运行

```bash
# 测试翻译1个技能
python scripts/translate_skills.py --limit 1

# 测试完整任务
python scripts/scheduled_task.py --translate-limit 5 --skip-crawler
```

### 步骤6: 配置 Cron 定时任务

```bash
# 编辑 crontab
crontab -e

# 添加以下任务（推荐配置）：

# 每天凌晨2点：爬虫 + 翻译50个
0 2 * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --translate-limit 50 >> /var/log/claude-skills-cron.log 2>&1

# 每天上午10点和下午4点：仅爬虫（更新数据）
0 10,16 * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --skip-translation >> /var/log/claude-skills-cron.log 2>&1

# 每3小时：翻译5个未翻译的技能
0 */3 * * * /var/www/claude-skills-miniapp/backend/venv/bin/python /var/www/claude-skills-miniapp/backend/scripts/scheduled_task.py --skip-crawler --translate-limit 5 >> /var/log/claude-skills-cron.log 2>&1
```

### 步骤7: 配置日志轮转

```bash
# 创建日志轮转配置
sudo nano /etc/logrotate.d/claude-skills

# 添加以下内容：
/var/log/claude-skills-cron.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 root root
}
```

## 4. 监控和维护

### 查看任务执行日志

```bash
tail -f /var/log/claude-skills-cron.log
```

### 查看 Cron 任务

```bash
crontab -l
```

### 检查数据库翻译进度

```bash
python -c "
import asyncio
from src.storage.database import get_session
from sqlalchemy import text

async def check():
    async with get_session() as s:
        result = await s.execute(text('''
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN name_zh IS NOT NULL AND name_zh != '' THEN 1 ELSE 0 END) as translated
            FROM skills
        '''))
        row = result.fetchone()
        print(f'总技能数: {row.total}')
        print(f'已翻译: {row.translated}')
        print(f'进度: {row.translated/row.total*100:.1f}%')

asyncio.run(check())
"
```

### 手动触发任务

```bash
# 仅爬虫
python scripts/scheduled_task.py --skip-translation

# 仅翻译10个
python scripts/scheduled_task.py --skip-crawler --translate-limit 10

# 完整任务
python scripts/scheduled_task.py --translate-limit 50
```

## 5. 翻译额度管理

### 百度翻译免费额度

- **5万字符/月**
- 平均每个技能约 1000 字符（name + description + content）
- 可翻译约 50 个技能/月
- 建议配置：每3小时翻译5个 = 每天40个 = 每月约1200个

**超出免费额度**:
- 降低翻译频率（每6小时翻译5个）
- 或申请付费版（0.01元/万字符）

### 翻译优先级策略

当前脚本已按 stars 降序翻译，优先翻译热门技能。

如需自定义优先级：

```bash
# 修改 translate_skills.py 中的 ORDER BY 子句
ORDER BY stars DESC  # 按热度
ORDER BY created_at DESC  # 按最新
ORDER BY RAND() LIMIT 50  # 随机翻译50个
```

## 6. 幂等机制验证

运行两次爬虫，第二次应该显示：

```
保存结果:
  新增: 0
  更新: 0
  跳过(无变化): 2904
  失败: 0
```

证明幂等机制生效，不会重复更新未变化的数据。

## 7. 故障排查

### 问题1: 翻译失败

```bash
# 检查翻译 API 配置
grep BAIDU .env

# 测试翻译服务
python -c "
import asyncio
from src.services.translation import translate_text

async def test():
    result = await translate_text('Hello World')
    print(f'翻译结果: {result}')

asyncio.run(test())
"
```

### 问题2: Cron 任务不执行

```bash
# 检查 cron 服务
systemctl status cron

# 查看 cron 日志
grep CRON /var/log/syslog

# 确保 Python 路径正确
which python  # 应该是虚拟环境的 python
```

### 问题3: 权限问题

```bash
# 确保日志文件可写
sudo touch /var/log/claude-skills-cron.log
sudo chmod 644 /var/log/claude-skills-cron.log
```

## 8. 性能优化建议

- **爬虫**: 每天运行3次足够（凌晨、上午、下午）
- **翻译**: 根据免费额度调整频率，避免超额
- **日志**: 定期清理，避免占用磁盘空间
- **数据库**: 定期检查索引和查询性能

## 9. 扩展功能

### 添加通知（可选）

当翻译完成或出错时发送通知：

```python
# 在 scheduled_task.py 中添加
import requests

def send_notification(message):
    # 使用企业微信/钉钉/邮件等发送通知
    pass
```

### 增量爬取（可选）

只爬取新增的技能，减少 API 请求：

```python
# 在 browser_api_crawler.py 中添加
last_crawl_time = get_last_crawl_time()
if skill.created_at <= last_crawl_time:
    break  # 跳过已爬取的
```

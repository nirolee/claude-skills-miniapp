# 定时任务配置说明

## ✅ 已配置的定时任务

### 1. Skill_md 内容更新任务

**执行时间**: 每小时整点（00 分）
**运行时长**: 30 分钟（自动停止）
**脚本路径**: `/root/claude-skills-api/scripts/run_scheduled_update.sh`

**Crontab 配置**:
```bash
0 * * * * /root/claude-skills-api/scripts/run_scheduled_update.sh
```

## ⚙️ 运行参数

| 参数 | 值 | 说明 |
|------|---|------|
| 并发数 | 5 | 稳定运行，避免限流 |
| 超时时间 | 20 秒 | 增加容错性 |
| 批次延迟 | 2 秒 | 避免 GitHub 限流 |
| 运行时长 | 30 分钟 | timeout 自动停止 |
| GitHub Token | 已配置 | 限流 5000/小时 |

## 📊 预期效果

**每次运行（30 分钟）**:
- 处理约 300-600 条记录
- 成功率约 85-90%
- 自动跳过已处理的记录

**每天累计（24 小时）**:
- 运行 24 次
- 处理约 7,200-14,400 条记录
- 预计 5-10 天完成剩余 71,735 条

## 📁 日志文件

**定时任务日志**:
```bash
/root/claude-skills-api/logs/scheduled_update_YYYYMMDD.log
```

**脚本详细日志**:
```bash
/root/claude-skills-api/logs/fast_update_YYYYMMDD.log
```

**进度文件**:
```bash
/root/claude-skills-api/logs/fast_update_progress.json
```

## 🔍 监控命令

### 查看定时任务状态
```bash
# 查看所有定时任务
crontab -l

# 查看定时任务日志
tail -f /root/claude-skills-api/logs/scheduled_update_$(date +%Y%m%d).log

# 查看详细运行日志
tail -f /root/claude-skills-api/logs/fast_update_$(date +%Y%m%d).log
```

### 查看进程
```bash
# 检查是否在运行
ps aux | grep fast_concurrent_update | grep python
```

### 查看进度统计
```bash
cd /root/claude-skills-api
source venv/bin/activate
python -c "
import json
with open('logs/fast_update_progress.json') as f:
    data = json.load(f)
print(f'总处理: {len(data[\"processed_ids\"])}')
print(f'成功: {data[\"success_count\"]}')
print(f'失败: {data[\"failed_count\"]}')
print(f'成功率: {data[\"success_count\"]/len(data[\"processed_ids\"])*100:.1f}%')
"
```

### 查看数据库实际数据
```bash
cd /root/claude-skills-api
source venv/bin/activate
python -c "
import asyncio
from sqlalchemy import text
import sys
sys.path.insert(0, '.')
from src.storage.database import get_engine

async def check():
    engine = get_engine()
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT COUNT(*) FROM skills WHERE skill_md IS NOT NULL AND skill_md != \"\"'))
        count = result.fetchone()[0]
        print(f'已抓取 skill_md: {count:,} 条')
    await engine.dispose()

asyncio.run(check())
"
```

## 🛠️ 管理命令

### 手动运行一次
```bash
cd /root/claude-skills-api
bash scripts/run_scheduled_update.sh
```

### 停止��前运行
```bash
# 查找进程
ps aux | grep fast_concurrent_update | grep python

# 停止进程（替换 PID）
kill <PID>
```

### 暂停定时任务
```bash
# 编辑 crontab
crontab -e

# 注释掉这一行（在行首添加 #）
# 0 * * * * /root/claude-skills-api/scripts/run_scheduled_update.sh
```

### 恢复定时任务
```bash
# 编辑 crontab
crontab -e

# 取消注释（删除行首的 #）
0 * * * * /root/claude-skills-api/scripts/run_scheduled_update.sh
```

## 📈 当前状态

**已完成**:
- ✅ 脚本优化（并发 5，超时 20s）
- ✅ GitHub Token 认证
- ✅ 定时任务配置
- ✅ 自动日志清理（保留 7 天）
- ✅ 断点续传功能

**数据统计**:
- 总记录: 93,601 条
- 已抓取: 20,245 条（21.6%）
- 待抓取: 71,735 条

**运行计划**:
- 每小时运行 30 分钟
- 每天 24 次
- 预计 5-10 天完成全部

## ⚠️ 注意事项

1. **日志文件清理**: 自动删除 7 天前的日志
2. **断点续传**: 脚本会自动跳过已处理的记录
3. **限流保护**: 如果连续失败，脚本会继续尝试下一批
4. **进度保存**: 每 100 条记录保存一次进度

## 🔗 相关文件

- 主脚本: `scripts/fast_concurrent_update.py`
- 定时任务脚本: `scripts/run_scheduled_update.sh`
- 测试脚本: `scripts/test_github_token.py`
- GitHub Token 配置: `.env` 文件

#!/bin/bash
# 定时任务：每小时运行 30 分钟的技能内容更新脚本
# 使用 timeout 限制运行时间为 30 分钟

cd /root/claude-skills-api

# 激活虚拟环境
source venv/bin/activate

# 设置日志文件
LOG_DIR="/root/claude-skills-api/logs"
LOG_FILE="$LOG_DIR/scheduled_update_$(date +%Y%m%d).log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 运行脚本，限时 30 分钟（1800 秒）
timeout 1800 python scripts/fast_concurrent_update.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

# 记录结束时间和状态
echo "----------------------------------------" >> "$LOG_FILE"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"

if [ $EXIT_CODE -eq 124 ]; then
    echo "状态: 已达到 30 分钟限制，正常停止" >> "$LOG_FILE"
elif [ $EXIT_CODE -eq 0 ]; then
    echo "状态: 脚本正常完成" >> "$LOG_FILE"
else
    echo "状态: 脚本异常退出 (退出码: $EXIT_CODE)" >> "$LOG_FILE"
fi

echo "========================================" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 清理超过 7 天的日志文件
find "$LOG_DIR" -name "scheduled_update_*.log" -mtime +7 -delete

#!/bin/bash
# 部署验证脚本 - 检查所有服务是否正常运行

echo "========================================"
echo "223 服务器 - Claude Skills 部署验证"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
}

check_warn() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# 1. 检查 Supervisor 服务
echo "1️⃣ 检查 Supervisor 服务"
echo "----------------------------------------"

if command -v supervisorctl &> /dev/null; then
    check_pass "Supervisor 已安装"

    # 检查 API 服务
    if supervisorctl status claude-skills-api | grep -q "RUNNING"; then
        check_pass "API 服务运行中"
        supervisorctl status claude-skills-api | head -1
    else
        check_fail "API 服务未运行"
        supervisorctl status claude-skills-api 2>&1
    fi

    echo ""

    # 检查内容更新服务
    if supervisorctl status claude-skills-content-update 2>/dev/null | grep -q "RUNNING"; then
        check_pass "内容更新任务运行中"
        supervisorctl status claude-skills-content-update | head -1
    elif supervisorctl status claude-skills-content-update 2>/dev/null | grep -q "EXITED"; then
        check_warn "内容更新任务已完成（正常退出）"
        supervisorctl status claude-skills-content-update | head -1
    else
        check_fail "内容更新任务未配置或未运行"
        echo "请检查配置: sudo supervisorctl status"
    fi
else
    check_fail "Supervisor 未安装"
fi

echo ""
echo ""

# 2. 检查 Crontab 配置
echo "2️⃣ 检查 Crontab 定时任务"
echo "----------------------------------------"

if crontab -l &> /dev/null; then
    # 检查爬虫任务
    if crontab -l | grep -q "smart_crawler.py"; then
        check_pass "爬虫任务已配置"
        crontab -l | grep "smart_crawler.py"
    else
        check_warn "爬虫任务未配置"
    fi

    echo ""

    # 检查翻译任务
    if crontab -l | grep -q "translate_skills.py"; then
        check_pass "翻译任务已配置"
        crontab -l | grep "translate_skills.py"
    else
        check_fail "翻译任务未配置"
        echo "请运行: crontab -e"
        echo "添加: 0 10 * * * cd /var/www/claude-skills-miniapp/backend && venv/bin/python scripts/translate_skills.py >> /var/log/claude-skills-translate.log 2>&1"
    fi
else
    check_warn "没有 crontab 配置"
fi

echo ""
echo ""

# 3. 检查 API 服务响应
echo "3️⃣ 检查 API 服务响应"
echo "----------------------------------------"

if curl -s http://127.0.0.1:8000/api/skills?page=1&limit=1 > /dev/null; then
    check_pass "API 服务响应正常"
    echo "测试 URL: http://127.0.0.1:8000/api/skills?page=1&limit=1"
else
    check_fail "API 服务无响应"
    echo "请检查: curl http://127.0.0.1:8000/api/skills?page=1&limit=1"
fi

echo ""
echo ""

# 4. 检查数据库连接
echo "4️⃣ 检查数据库"
echo "----------------------------------------"

cd /var/www/claude-skills-miniapp/backend

if [ -f ".env" ]; then
    check_pass ".env 文件存在"

    if grep -q "ANTHROPIC_API_KEY" .env && [ "$(grep ANTHROPIC_API_KEY .env | cut -d'=' -f2)" != "" ]; then
        check_pass "Anthropic API Key 已配置"
    else
        check_fail "Anthropic API Key 未配置"
        echo "请编辑 .env 文件添加: ANTHROPIC_API_KEY=your_key"
    fi
else
    check_fail ".env 文件不存在"
fi

echo ""

# 简单测试数据库连接
if source venv/bin/activate && python -c "from src.storage.database import get_session; import asyncio; asyncio.run(get_session().__aenter__())" 2>/dev/null; then
    check_pass "数据库连接正常"
else
    check_fail "数据库连接失败"
    echo "请检查 .env 中的数据库配置"
fi

echo ""
echo ""

# 5. 检查日志文件
echo "5️⃣ 检查日志文件"
echo "----------------------------------------"

# API 日志
if [ -f "/var/log/claude-skills-api.log" ]; then
    check_pass "API 日志存在"
    LOG_SIZE=$(stat -f%z "/var/log/claude-skills-api.log" 2>/dev/null || stat -c%s "/var/log/claude-skills-api.log" 2>/dev/null)
    echo "  文件大小: $(numfmt --to=iec $LOG_SIZE 2>/dev/null || echo "$LOG_SIZE bytes")"
    echo "  最后 3 行:"
    tail -3 /var/log/claude-skills-api.log | sed 's/^/    /'
else
    check_warn "API 日志不存在"
fi

echo ""

# 内容更新日志
if [ -f "/var/log/claude-skills-content-update.log" ]; then
    check_pass "内容更新日志存在"
    LOG_SIZE=$(stat -f%z "/var/log/claude-skills-content-update.log" 2>/dev/null || stat -c%s "/var/log/claude-skills-content-update.log" 2>/dev/null)
    echo "  文件大小: $(numfmt --to=iec $LOG_SIZE 2>/dev/null || echo "$LOG_SIZE bytes")"
    echo "  最后 3 行:"
    tail -3 /var/log/claude-skills-content-update.log | sed 's/^/    /'
else
    check_warn "内容更新日志不存在（可能还未运行）"
fi

echo ""
echo ""

# 6. 检查内容更新进度
echo "6️⃣ 检查内容更新进度"
echo "----------------------------------------"

PROGRESS_FILE="/var/www/claude-skills-miniapp/backend/logs/content_update_progress.json"

if [ -f "$PROGRESS_FILE" ]; then
    check_pass "进度文件存在"

    cd /var/www/claude-skills-miniapp/backend
    source venv/bin/activate

    python3 << 'EOF'
import json
import sys

try:
    with open('/var/www/claude-skills-miniapp/backend/logs/content_update_progress.json', 'r') as f:
        data = json.load(f)

    print(f"  开始时间: {data['started_at']}")
    print(f"  上次更新: {data['last_update']}")
    print(f"  已处理: {len(data['processed_ids'])} 个")
    print(f"  成功: {data['success_count']}")
    print(f"  失败: {data['failed_count']}")
    print(f"  跳过: {data['skipped_count']}")

    # 计算进度百分比（假设总共 12000 个需要更新）
    total_to_update = 12000
    progress = (len(data['processed_ids']) / total_to_update) * 100
    print(f"  预计进度: {progress:.1f}%")

except Exception as e:
    print(f"读取进度文件失败: {e}")
    sys.exit(1)
EOF

else
    check_warn "进度文件不存在（任务可能还未开始）"
fi

echo ""
echo ""

# 7. 检查数据库统计
echo "7️⃣ 检查数据库内容统计"
echo "----------------------------------------"

cd /var/www/claude-skills-miniapp/backend
source venv/bin/activate

python3 << 'EOF'
import asyncio
from sqlalchemy import text
from src.storage.database import get_session

async def check():
    try:
        async with get_session() as session:
            # 检查 content 长度
            query = text("""
                SELECT
                    COUNT(*) as total,
                    AVG(LENGTH(content)) as avg_len,
                    MAX(LENGTH(content)) as max_len,
                    SUM(CASE WHEN LENGTH(content) > 1000 THEN 1 ELSE 0 END) as long_content
                FROM skills
            """)
            result = await session.execute(query)
            row = result.fetchone()

            print(f"  总 Skills: {row.total}")
            print(f"  平均内容长度: {row.avg_len:.0f} 字符")
            print(f"  最长内容: {row.max_len} 字符")
            print(f"  长内容 (>1000字符): {row.long_content}")

            print("")

            # 检查翻译进度
            query2 = text("""
                SELECT
                    SUM(CASE WHEN content_zh IS NOT NULL AND content_zh != '' THEN 1 ELSE 0 END) as translated,
                    COUNT(*) as total
                FROM skills
            """)
            result2 = await session.execute(query2)
            row2 = result2.fetchone()

            print(f"  已翻译: {row2.translated}/{row2.total} ({row2.translated/row2.total*100:.1f}%)")

    except Exception as e:
        print(f"数据库查询失败: {e}")

asyncio.run(check())
EOF

echo ""
echo ""

# 8. 总结
echo "========================================"
echo "验证完成"
echo "========================================"
echo ""
echo "📝 后续操作建议："
echo ""
echo "1. 查看实时日志:"
echo "   tail -f /var/log/claude-skills-content-update.log"
echo ""
echo "2. 查看所有服务状态:"
echo "   sudo supervisorctl status"
echo ""
echo "3. 手动测试翻译:"
echo "   cd /var/www/claude-skills-miniapp/backend"
echo "   source venv/bin/activate"
echo "   python scripts/translate_skills.py --limit 5"
echo ""
echo "4. 查看 crontab 配置:"
echo "   crontab -l"
echo ""

#!/bin/bash
# 一键部署到 223 服务器

echo "========================================"
echo "223 服务器 - Claude Skills 一键部署"
echo "========================================"
echo ""

set -e  # 遇到错误立即退出

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

step() {
    echo -e "${GREEN}▶ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# 1. 检查目录
step "1. 检查项目目录"
cd /var/www/claude-skills-miniapp/backend || {
    echo "❌ 项目目录不存在"
    exit 1
}
echo "✅ 项目目录: $(pwd)"

# 2. 更新代码
step "2. 更新代码"
cd /var/www/claude-skills-miniapp
git pull || warn "Git pull 失败，使用现有代码"

# 3. 安装依赖
step "3. 安装 Python 依赖"
cd backend
source venv/bin/activate
pip install aiohttp -q
echo "✅ 依赖安装完成"

# 4. 检查 API Key
step "4. 检查 Anthropic API Key"
if grep -q "ANTHROPIC_API_KEY" .env && [ "$(grep ANTHROPIC_API_KEY .env | cut -d'=' -f2)" != "" ]; then
    echo "✅ API Key 已配置"
else
    echo ""
    warn "未找到 API Key，请手动配置"
    echo "编辑文件: nano /var/www/claude-skills-miniapp/backend/.env"
    echo "添加行: ANTHROPIC_API_KEY=your_key_here"
    echo ""
    read -p "是否现在配置？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        nano .env
    else
        echo "⏭️ 跳过 API Key 配置（稍后手动配置）"
    fi
fi

# 5. 配置 Supervisor
step "5. 配置 Supervisor"
sudo cp ../deploy/claude-skills-supervisor.conf /etc/supervisor/conf.d/claude-skills.conf
sudo supervisorctl reread
sudo supervisorctl update
echo "✅ Supervisor 配置完成"

# 6. 启动服务
step "6. 启动/重启服务"
sudo supervisorctl restart claude-skills-api
sudo supervisorctl start claude-skills-content-update 2>/dev/null || echo "内容更新任务已启动"
echo "✅ 服务已启动"

# 7. 配置 Crontab
step "7. 配置 Crontab（翻译任务）"
CRON_CMD='0 10 * * * cd /var/www/claude-skills-miniapp/backend && /var/www/claude-skills-miniapp/backend/venv/bin/python scripts/translate_skills.py >> /var/log/claude-skills-translate.log 2>&1'

# 检查是否已存在
if crontab -l 2>/dev/null | grep -q "translate_skills.py"; then
    echo "✅ 翻译任务已在 crontab 中"
else
    echo ""
    echo "需要添加翻译任务到 crontab"
    echo "命令: $CRON_CMD"
    echo ""
    read -p "是否现在添加？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
        echo "✅ 翻译任务已添加"
    else
        echo "⏭️ 跳过 crontab 配置（稍后手动添加）"
        echo "手动添加: crontab -e"
        echo "添加行: $CRON_CMD"
    fi
fi

echo ""
echo "========================================"
echo "🎉 部署完成！"
echo "========================================"
echo ""
echo "正在验证部署..."
echo ""

# 运行验证脚本
bash ../deploy/verify_deployment.sh

#!/bin/bash
# Claude Skills - SSL 证书自动申请脚本
# 使用 Let's Encrypt 免费证书

set -e

echo "=========================================="
echo "Claude Skills API - SSL 证书申请"
echo "=========================================="
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 root 用户运行此脚本"
    echo "   sudo bash setup-ssl.sh"
    exit 1
fi

# 1. 安装 certbot
echo "📦 步骤 1/4: 安装 certbot..."
if ! command -v certbot &> /dev/null; then
    apt update
    apt install -y certbot python3-certbot-nginx
    echo "✅ certbot 安装完成"
else
    echo "✅ certbot 已安装"
fi

# 2. 检查域名解析
echo ""
echo "🔍 步骤 2/4: 检查域名解析..."
DOMAIN="api.oppohunter.com"
CURRENT_IP=$(dig +short $DOMAIN | tail -n1)
SERVER_IP="223.109.140.233"

if [ "$CURRENT_IP" != "$SERVER_IP" ]; then
    echo "⚠️  域名解析异常:"
    echo "   域名: $DOMAIN"
    echo "   当前解析: $CURRENT_IP"
    echo "   应该解析: $SERVER_IP"
    echo ""
    echo "请先在域名管理面板添加 A 记录:"
    echo "   记录类型: A"
    echo "   主机记录: api"
    echo "   记录值: $SERVER_IP"
    echo "   TTL: 600"
    echo ""
    read -p "域名已配置好？按回车继续，或 Ctrl+C 退出..."
else
    echo "✅ 域名解析正确: $DOMAIN → $SERVER_IP"
fi

# 3. 停止 Nginx（避免端口占用）
echo ""
echo "🔧 步骤 3/4: 临时停止 Nginx..."
systemctl stop nginx
echo "✅ Nginx 已停止"

# 4. 申请证书
echo ""
echo "🔐 步骤 4/4: 申请 SSL 证书..."
certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email niro@oppohunter.com \
    --domains $DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ SSL 证书申请成功！"
    echo ""
    echo "证书位置:"
    echo "  fullchain.pem: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo "  privkey.pem:   /etc/letsencrypt/live/$DOMAIN/privkey.pem"
    echo "  chain.pem:     /etc/letsencrypt/live/$DOMAIN/chain.pem"
else
    echo "❌ SSL 证书申请失败"
    systemctl start nginx
    exit 1
fi

# 5. 配置自动续期
echo ""
echo "🔄 配置自动续期..."
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
echo "✅ 自动续期配置完成（每天凌晨3点检查）"

# 6. 启动 Nginx
echo ""
echo "🚀 启动 Nginx..."
systemctl start nginx
systemctl status nginx | head -5
echo ""

echo "=========================================="
echo "✅ SSL 证书配置完成！"
echo "=========================================="
echo ""
echo "下一步:"
echo "1. 部署 Nginx 配置:"
echo "   scp deploy/nginx-claude-skills.conf root@223.109.140.233:/etc/nginx/sites-available/claude-skills"
echo "   ssh root@223.109.140.233 'ln -sf /etc/nginx/sites-available/claude-skills /etc/nginx/sites-enabled/'"
echo "   ssh root@223.109.140.233 'nginx -t && systemctl reload nginx'"
echo ""
echo "2. 测试 HTTPS 访问:"
echo "   curl https://api.oppohunter.com/health"
echo ""
echo "3. 更新前端配置:"
echo "   修改 frontend/config/api.js 中的 production 地址"
echo ""

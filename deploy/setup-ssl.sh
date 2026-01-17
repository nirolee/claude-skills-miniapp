#!/bin/bash
# SSL 证书自动申请脚本 - api.liguoqi.site
# 使用 Let's Encrypt 免费证书（3个月自动续期）

set -e

DOMAIN="api.liguoqi.site"
EMAIL="admin@liguoqi.site"  # 修改为你的邮箱

echo "================================================"
echo "SSL 证书申请脚本"
echo "域名: $DOMAIN"
echo "================================================"
echo ""

# 1. 检查是否已安装 certbot
echo "步骤 1: 检查 certbot..."
if ! command -v certbot &> /dev/null; then
    echo "  ⏳ certbot 未安装，正在安装..."
    apt-get update -qq
    apt-get install -y certbot python3-certbot-nginx -qq
    echo "  ✅ certbot 安装完成"
else
    echo "  ✅ certbot 已安装"
fi

echo ""

# 2. 检查 80 端口是否被占用
echo "步骤 2: 检查 80 端口..."
if netstat -tuln | grep -q ":80 "; then
    echo "  ⚠️  80 端口被占用，需要临时关闭 Nginx"
    systemctl stop nginx
    NGINX_WAS_RUNNING=1
else
    echo "  ✅ 80 端口空闲"
    NGINX_WAS_RUNNING=0
fi

echo ""

# 3. 申请证书
echo "步骤 3: 申请 SSL 证书..."
echo "  域名: $DOMAIN"
echo "  邮箱: $EMAIL"
echo ""

certbot certonly \
    --standalone \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    -d "$DOMAIN" \
    --preferred-challenges http

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SSL 证书申请成功！"
    echo ""
    echo "证书位置："
    echo "  fullchain: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
    echo "  privkey:   /etc/letsencrypt/live/$DOMAIN/privkey.pem"
    echo "  chain:     /etc/letsencrypt/live/$DOMAIN/chain.pem"
    echo ""
else
    echo "❌ SSL 证书申请失败"
    exit 1
fi

# 4. 重启 Nginx（如果之前在运行）
if [ $NGINX_WAS_RUNNING -eq 1 ]; then
    echo "步骤 4: 重启 Nginx..."
    systemctl start nginx
    echo "  ✅ Nginx 已重启"
fi

echo ""

# 5. 配置自动续期
echo "步骤 5: 配置自动续期..."
if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | crontab -
    echo "  ✅ 自动续期已配置（每天凌晨3点检查）"
else
    echo "  ✅ 自动续期已存在"
fi

echo ""
echo "================================================"
echo "✅ 全部完成！"
echo "================================================"
echo ""
echo "下一步："
echo "1. 配置 Nginx HTTPS"
echo "2. 重载 Nginx: systemctl reload nginx"
echo "3. 测试访问: https://$DOMAIN/health"
echo ""

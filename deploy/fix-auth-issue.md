# 修复登录404问题

## 问题原因

1. **端口配置不匹配**：Supervisor运行在8000端口，但Nginx转发到8081端口
2. **微信AppID/Secret未配置**：.env文件中还是占位符

## 修复步骤

### 步骤1：SSH连接服务器

```bash
ssh root@223.109.140.233
```

### 步骤2：检查后端服务状态

```bash
# 查看后端进程
ps aux | grep uvicorn

# 查看正在监听的端口
netstat -tlnp | grep python
```

### 步骤3：修复端口配置（方案A - 推荐）

**修改Supervisor配置，统一使用8081端口**

```bash
# 编辑supervisor配置
vi /etc/supervisor/conf.d/claude-skills-api.conf

# 修改这一行：
# 从：--port 8000
# 改为：--port 8081
command=/var/www/claude-skills-miniapp/backend/venv/bin/python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8081

# 保存退出后，重启服务
supervisorctl reread
supervisorctl update
supervisorctl restart claude-skills-api

# 验证端口
netstat -tlnp | grep 8081
```

### 步骤4：配置微信AppID和Secret

```bash
# 编辑.env文件
cd /var/www/claude-skills-miniapp/backend
vi .env

# 修改以下两行（替换为真实值）：
WECHAT_APPID=wxea85c78af2ac2e2e
WECHAT_SECRET=你的微信小程序Secret

# 保存退出后，重启服务
supervisorctl restart claude-skills-api
```

**获取微信Secret的方法：**

1. 登录微信公众平台：https://mp.weixin.qq.com/
2. 开发 → 开发管理 → 开发设置
3. 找到"AppSecret(小程序密钥)"
4. 点击"重置"（如果之前没有保存）
5. 使用管理员微信扫码确认
6. 复制Secret立即保存（只显示一次）

### 步骤5：测试API

```bash
# 测试健康检查
curl http://localhost:8081/health

# 测试技能列表
curl http://localhost:8081/api/skills/?page=1&page_size=5

# 测试登录接口（会提示需要code）
curl -X POST http://localhost:8081/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"code":"test"}'
```

### 步骤6：测试HTTPS访问

```bash
# 退出SSH，在本地测试
curl https://api.liguoqi.site/health
curl https://api.liguoqi.site/api/skills/?page=1&page_size=5
```

## 快速验证脚本

在服务器上运行以下脚本一键检查：

```bash
cat > /tmp/check-claude-api.sh << 'EOF'
#!/bin/bash

echo "=== Claude Skills API 诊断脚本 ==="
echo ""

echo "1. 检查后端进程"
ps aux | grep uvicorn | grep -v grep
echo ""

echo "2. 检查监听端口"
netstat -tlnp | grep python
echo ""

echo "3. 检查Nginx配置中的端口"
grep "proxy_pass" /etc/nginx/sites-available/claude-skills
echo ""

echo "4. 检查微信配置"
cd /var/www/claude-skills-miniapp/backend
grep "WECHAT_APPID" .env
grep "WECHAT_SECRET" .env | sed 's/WECHAT_SECRET=.*/WECHAT_SECRET=***已隐藏***/'
echo ""

echo "5. 测试本地API"
curl -s http://localhost:8081/health && echo "" || echo "端口8081无响应"
curl -s http://localhost:8000/health && echo "" || echo "端口8000无响应"
echo ""

echo "6. 测试HTTPS API"
curl -s https://api.liguoqi.site/health
echo ""

echo "=== 诊断完成 ==="
EOF

chmod +x /tmp/check-claude-api.sh
/tmp/check-claude-api.sh
```

## 预期结果

### 修复前
```
❌ netstat显示监听8000端口
❌ Nginx转发到8081端口
❌ curl localhost:8081 失败
❌ 登录接口404错误
```

### 修复后
```
✅ netstat显示监听8081端口
✅ Nginx转发到8081端口
✅ curl localhost:8081 成功
✅ 登录接口返回错误（但不是404，说明路由正常）
```

## 备选方案B：修改Nginx配置

如果不想修改后端端口，也可以修改Nginx配置：

```bash
# 编辑Nginx配置
vi /etc/nginx/sites-available/claude-skills

# 修改第45行：
# 从：proxy_pass http://127.0.0.1:8081;
# 改为：proxy_pass http://127.0.0.1:8000;

# 重载Nginx
nginx -t
systemctl reload nginx
```

## 验证微信登录

修复后，在小程序中测试登录，应该看到以下错误之一：

1. **错误码-1**："微信小程序 AppID 未配置" → 说明需要配置WECHAT_APPID
2. **错误码40029**："code已被使用" → 说明路由和配置都正常了
3. **登录成功** → 一切正常

## 注意事项

- ⚠️ 修改配置后必须重启服务
- ⚠️ WECHAT_SECRET只显示一次，务必保存好
- ⚠️ 生产环境记得备份.env文件
- ⚠️ 不要把SECRET提交到Git仓库

## 后续步骤

登录功能修复后，继续按照 `deploy/LAUNCH_GUIDE.md` 完成小程序上线流程。

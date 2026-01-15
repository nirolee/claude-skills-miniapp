# Claude Skills 小程序上线部署指南

## 📋 部署清单

### ✅ 已完成
- [x] 前端代码（uni-app 小程序）
- [x] 后端 API（FastAPI，运行在 223:8081）
- [x] 数据库（MySQL，2904 个技能 + 自动翻译）
- [x] 小程序 AppID（wxea85c78af2ac2e2e）

### 🔄 待完成
- [ ] DNS A 记录配置
- [ ] SSL 证书申请
- [ ] Nginx HTTPS 配置
- [ ] 前端 API 地址更新
- [ ] 小程序后台配置
- [ ] 打包上传审核

---

## 🚀 部署步骤

### 步骤 1: 配置 DNS A 记录

**在域名管理面板（阿里云/腾讯云）添加：**

| 记录类型 | 主机记录 | 记录值 | TTL |
|---------|---------|--------|-----|
| A | api | 223.109.140.233 | 600 |

**验证：**
```bash
# 等待 5-10 分钟后执行
ping api.oppohunter.com
# 应该显示: 223.109.140.233
```

---

### 步骤 2: 申请 SSL 证书

**在 223 服务器上执行：**

```bash
# 1. 上传脚本
scp deploy/setup-ssl.sh root@223.109.140.233:/root/

# 2. 连接服务器
ssh root@223.109.140.233

# 3. 运行脚本
cd /root
chmod +x setup-ssl.sh
./setup-ssl.sh
```

**脚本会自动：**
- ✅ 安装 certbot
- ✅ 申请 Let's Encrypt 证书（免费，3个月自动续期）
- ✅ 配置自动续期（每天凌晨3点）

**预期输出：**
```
✅ SSL 证书申请成功！
证书位置:
  fullchain.pem: /etc/letsencrypt/live/api.oppohunter.com/fullchain.pem
  privkey.pem:   /etc/letsencrypt/live/api.oppohunter.com/privkey.pem
```

---

### 步骤 3: 部署 Nginx 配置

**在本地执行：**

```bash
# 1. 上传 Nginx 配置
scp deploy/nginx-claude-skills.conf root@223.109.140.233:/etc/nginx/sites-available/claude-skills

# 2. 启用配置
ssh root@223.109.140.233 "ln -sf /etc/nginx/sites-available/claude-skills /etc/nginx/sites-enabled/"

# 3. 测试配置
ssh root@223.109.140.233 "nginx -t"

# 4. 重载 Nginx
ssh root@223.109.140.233 "systemctl reload nginx"
```

---

### 步骤 4: 测试 HTTPS API

**测试健康检查：**
```bash
curl https://api.oppohunter.com/health
# 预期输出: OK

curl https://api.oppohunter.com/api/skills/categories/list
# 预期输出: JSON 分类列表
```

**浏览器测试：**
- 打开: https://api.oppohunter.com/api/skills/?page=1&page_size=10
- 应该看到技能列表 JSON 数据

---

### 步骤 5: 更新前端 API 配置

**修改 `frontend/config/api.js`：**

```javascript
// 生产环境 - 使用 HTTPS 域名
production: 'https://api.oppohunter.com'
```

**完整修改：**
```javascript
const ENV = {
  development: 'http://localhost:8000',
  production: 'https://api.oppohunter.com'  // ← 修改这里
}
```

---

### 步骤 6: 小程序后台配置

**登录微信公众平台：**
1. 访问：https://mp.weixin.qq.com/
2. 开发 → 开发管理 → 开发设置 → 服务器域名

**配置服务器域名：**
| 类型 | 域名 |
|------|------|
| request合法域名 | https://api.oppohunter.com |
| uploadFile合法域名 | https://api.oppohunter.com |
| downloadFile合法域名 | https://api.oppohunter.com |

**注意：**
- ✅ 必须是 HTTPS
- ✅ 必须已备案
- ✅ 域名需要通过 ICP 备案（oppohunter.com 已备案）

---

### 步骤 7: 打包并提交审核

**使用 HBuilderX：**

1. **打开项目**
   - 文件 → 导入 → 选择 `frontend` 目录

2. **配置小程序信息**
   - 检查 `manifest.json` 中的 appid：`wxea85c78af2ac2e2e`

3. **发行**
   - 点击菜单：发行 → 小程序-微信
   - 选择：微信开发者工具
   - 等待编译完成

4. **上传代码**
   - 在微信开发者工具中点击"上传"
   - 填写版本号：`1.0.0`
   - 填写版本描述：`Claude Skills 技能市场首次上线`

5. **提交审核**
   - 登录微信公众平台
   - 版本管理 → 开发版本 → 提交审核
   - 填写审核信息：
     - **功能描述**：Claude Code 技能浏览、搜索、收藏、安装
     - **测试账号**：（无需登录可直接使用）
     - **隐私说明**：不涉及用户隐私数据收集

6. **等待审核**
   - 一般 1-3 个工作日
   - 审核通过后，点击"发布"即可上线

---

## 🔍 验证清单

### DNS 验证
```bash
nslookup api.oppohunter.com
# 应该返回: 223.109.140.233
```

### SSL 证书验证
```bash
curl -I https://api.oppohunter.com/health
# 应该看到: HTTP/2 200
```

### API 功能验证
```bash
# 技能列表
curl https://api.oppohunter.com/api/skills/?page=1&page_size=5

# 分类列表
curl https://api.oppohunter.com/api/skills/categories/list

# 技能详情
curl https://api.oppohunter.com/api/skills/1
```

### 前端配置验证
```bash
# 检查生产环境配置
grep "production:" frontend/config/api.js
# 应该显示: production: 'https://api.oppohunter.com'
```

---

## 📞 故障排查

### 问题 1: DNS 不生效
**症状：** `ping api.oppohunter.com` 无法解析

**解决：**
1. 等待 5-10 分钟（DNS 生效时间）
2. 清除本地 DNS 缓存：`ipconfig /flushdns` (Windows)
3. 使用 `nslookup api.oppohunter.com 8.8.8.8` 测试

### 问题 2: SSL 证书申请失败
**症状：** certbot 报错 "Connection refused"

**解决：**
1. 确认 DNS 已生效
2. 确认 80 端口已开放
3. 临时关闭 Nginx：`systemctl stop nginx`
4. 重新运行：`./setup-ssl.sh`

### 问题 3: Nginx 配置错误
**症状：** `nginx -t` 报错

**解决：**
1. 检查证书路径是否正确
2. 检查配置文件语法
3. 查看错误日志：`tail -f /var/log/nginx/error.log`

### 问题 4: API 请求失败
**症状：** 小程序提示"网络请求失败"

**解决：**
1. 确认服务器域名已配置
2. 检查后端服务运行状态：`systemctl status xxx`
3. 查看 Nginx 日志：`tail -f /var/log/nginx/claude-skills-error.log`

---

## 📊 监控和维护

### SSL 证书自动续期
- 每天凌晨 3:00 自动检查续期
- 查看 cron 日志：`grep certbot /var/log/syslog`

### API 服务监控
```bash
# 检查服务状态
ssh root@223.109.140.233 "ps aux | grep uvicorn"

# 查看 API 日志
ssh root@223.109.140.233 "tail -f /var/log/nginx/claude-skills-access.log"
```

### 翻译进度监控
```bash
# 查看翻译进度
ssh root@223.109.140.233 "
mysql -u claude_user -p'Claude2024!Skill' claude_skills -e '
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN name_zh IS NOT NULL THEN 1 ELSE 0 END) as translated
FROM skills;
' 2>/dev/null
"
```

---

## 🎉 上线成功标志

- ✅ `https://api.oppohunter.com/health` 返回 200
- ✅ `https://api.oppohunter.com/api/skills/` 返回技能列表
- ✅ 小程序开发工具可以正常请求 API
- ✅ 小程序审核通过并发布
- ✅ 用户可以在微信搜索并使用小程序

---

## 📝 备注

- 域名：api.oppohunter.com
- 服务器：223.109.140.233
- 端口：8081（内部），443（外部 HTTPS）
- 证书类型：Let's Encrypt（免费，3个月自动续期）
- 后端 API 文档：https://api.oppohunter.com/docs（部署后可访问）

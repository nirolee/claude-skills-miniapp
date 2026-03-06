# GitHub Token 配置指南

## 🔑 获取 GitHub Personal Access Token

### 步骤 1: 访问 GitHub Token 设置页面
打开浏览器访问：
```
https://github.com/settings/tokens
```

或者：
1. 登录 GitHub
2. 点击右上角头像 → Settings
3. 左侧菜单最底部 → Developer settings
4. Personal access tokens → Tokens (classic)

### 步骤 2: 生成新 Token
1. 点击 **"Generate new token"** → **"Generate new token (classic)"**
2. 填写信息：
   - **Note**: `Claude Skills Crawler`（备注名称）
   - **Expiration**: `No expiration`（永不过期）或选择时间
   - **Scopes**: **不需要选择任何权限**（留空即可）
     - 我们只是用来提高 API 限流，不需要访问仓库

3. 点击底部 **"Generate token"** 按钮
4. **重要**：复制生成的 token（形如 `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`）
   - ⚠️ Token 只显示一次，离开页面后无法再查看！

## 🔧 配置到服务器

### 方法 1: 临时环境变量（推荐测试）
```bash
# SSH 连接到服务器
ssh root@223.109.140.233

# 导出环境变量
export GITHUB_TOKEN="ghp_你的token"

# 运行脚本测试
cd ~/claude-skills-api
source venv/bin/activate
python scripts/fast_concurrent_update.py
```

### 方法 2: 添加到 .env 文件（推荐生产）
```bash
# SSH 连接到服务器
ssh root@223.109.140.233

# 编辑 .env 文件
cd ~/claude-skills-api
echo "GITHUB_TOKEN=ghp_你的token" >> .env

# 验证
cat .env | grep GITHUB_TOKEN
```

### 方法 3: 添加到系统环境变量（永久）
```bash
# 编辑 bashrc
echo 'export GITHUB_TOKEN="ghp_你的token"' >> ~/.bashrc
source ~/.bashrc

# 验证
echo $GITHUB_TOKEN
```

## ✅ 验证配置

运行脚本，查看日志开头：
```bash
cd ~/claude-skills-api
source venv/bin/activate
python scripts/fast_concurrent_update.py
```

**有 Token**：
```
============================================================
快速并发更新 - 并发数: 10
✅ GitHub Token 已配置（限流: 5000/小时）
============================================================
```

**无 Token**：
```
============================================================
快速并发更新 - 并发数: 10
⚠️ 未配置 GitHub Token（限流: 60/小时）
============================================================
```

## 📊 限流对比

| 认证方式 | 限流 | 并发推荐 | 完成时间 |
|---------|------|---------|----------|
| 无 Token | 60/小时 | 1-2 | 8-10 小时 |
| 有 Token | 5000/小时 | 10-20 | 1-2 小时 |

## 🔒 安全提示

1. **不要将 Token 提交到 Git 仓库**
   - .env 文件已在 .gitignore 中
2. **Token 泄露处理**
   - 如果 Token 泄露，立即到 GitHub 删除该 Token
   - 重新生成新的 Token
3. **定期轮换**
   - 建议每 3-6 个月更换一次 Token

## 🚀 启动抓取

配置好 Token 后，运行：
```bash
cd ~/claude-skills-api
source venv/bin/activate

# 后台运行
nohup python scripts/fast_concurrent_update.py > logs/crawler.log 2>&1 &

# 查看实时日志
tail -f logs/fast_update_$(date +%Y%m%d).log
```

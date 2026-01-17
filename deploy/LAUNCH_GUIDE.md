# 小程序上线操作指南

## ✅ 已完成部分

- [x] DNS 解析：api.liguoqi.site → 223.109.140.233
- [x] SSL 证书：Let's Encrypt（有效期至 2026-04-17，自动续期）
- [x] Nginx HTTPS：已配置并测试通过
- [x] 前端配置：已更新为 https://api.liguoqi.site
- [x] 后端服务：运行在 223:8081，Nginx 反向代理
- [x] 数据库：2904 个技能，自动翻译中

## 📋 待完成步骤

### 步骤 1：配置小程序服务器域名

1. **登录微信公众平台**
   - 访问：https://mp.weixin.qq.com/
   - 使用小程序管理员账号扫码登录

2. **进入开发设置**
   - 左侧菜单：开发 → 开发管理 → 开发设置
   - 找到"服务器域名"部分

3. **配置域名**

| 类型 | 域名 | 说明 |
|------|------|------|
| request合法域名 | https://api.liguoqi.site | API 请求域名 |
| uploadFile合法域名 | https://api.liguoqi.site | （如需上传文件） |
| downloadFile合法域名 | https://api.liguoqi.site | （如需下载文件） |

**注意事项：**
- ✅ 必须是 HTTPS 协议
- ✅ 域名必须已备案（liguoqi.site 已备案）
- ✅ 每月只能修改 5 次，谨慎操作
- ❌ 不能使用 IP 地址

4. **保存配置**
   - 点击"保存并提交"
   - 等待几分钟生效

---

### 步骤 2：使用 HBuilderX 打包小程序

#### 2.1 安装 HBuilderX

如果还没安装：
- 下载地址：https://www.dcloud.io/hbuilderx.html
- 选择"正式版" → "标准版"即可

#### 2.2 导入项目

1. 打开 HBuilderX
2. 文件 → 导入 → 从本地目录导入
3. 选择：`D:\niro\claude-skills-miniapp\frontend`
4. 项目导入成功

#### 2.3 检查配置

打开 `manifest.json`，确认：
- **AppID**: `wxea85c78af2ac2e2e`（已配置）
- **小程序名称**: Claude Skills
- **版本号**: 1.0.0

#### 2.4 编译运行（可选测试）

1. 点击菜单：运行 → 运行到小程序模拟器 → 微信开发者工具
2. 会自动打开微信开发者工具
3. 测试功能是否正常：
   - ✅ 首页技能列表加载
   - ✅ 搜索功能
   - ✅ 技能详情页
   - ✅ 收藏功能

#### 2.5 发行打包

1. 点击菜单：发行 → 小程序-微信
2. 选择：微信开发者工具
3. 等待编译完成（约 1-2 分钟）

---

### 步骤 3：上传代码到微信后台

#### 3.1 在微信开发者工具中上传

1. 编译完成后会自动打开微信开发者工具
2. 点击右上角"上传"按钮
3. 填写版本信息：
   - **版本号**：`1.0.0`
   - **项目备注**：
     ```
     Claude Skills 技能市场首版上线
     - 浏览 2900+ Claude Code 技能
     - 支持分类筛选和搜索
     - 收藏和分享功能
     - 中文翻译自动更新
     ```

4. 点击"上传"

#### 3.2 确认上传成功

- 上传成功后，开发者工具会提示
- 可以在微信公众平台看到"开发版本"

---

### 步骤 4：提交审核

#### 4.1 登录微信公众平台

1. 访问：https://mp.weixin.qq.com/
2. 进入：版本管理 → 开发版本

#### 4.2 提交审核

1. 找到刚上传的版本（1.0.0）
2. 点击"提交审核"
3. 填写审核信息：

**基本信息：**
- **小程序类别**：工具 → 开发者工具
- **标签**：开发工具、技能市场、Claude

**功能页面：**

| 页面路径 | 页面标题 | 页面功能描述 |
|---------|---------|------------|
| pages/index/index | 技能列表 | 浏览和搜索 Claude Code 技能 |
| pages/detail/detail | 技能详情 | 查看技能详细信息和安装命令 |
| pages/search/search | 搜索 | 搜索技能 |
| pages/profile/profile | 个人中心 | 查看收藏的技能 |

**测试账号：**
- 无需测试账号（小程序无需登录即可使用）
- 勾选"无需账号密码"

**补充说明：**
```
Claude Skills 是一个 Claude Code 技能市场小程序，帮助用户：

1. 浏览和搜索 2900+ 个 Claude Code 官方和社区技能
2. 按分类筛选（调试、测试、自动化等9个分类）
3. 查看技能详情、GitHub 链接、安装命令
4. 收藏感兴趣的技能
5. 支持中英文双语展示

数据来源：
- 技能数据从 skillsmp.com 和 GitHub anthropics/skills 仓库爬取
- 每日自动更新 stars 和 forks 数据
- 使用 Claude AI 自动翻译为中文

技术实现：
- 前端：uni-app + Vue 3
- 后端：FastAPI + MySQL
- 服务器：已备案域名 api.liguoqi.site

无用户隐私数据收集，无需登录即可使用全部功能。
```

4. 点击"提交审核"

---

### 步骤 5：等待审核

#### 审核时间
- 通常：1-3 个工作日
- 周末/节假日可能延长

#### 审核状态查看
- 微信公众平台 → 版本管理 → 审核版本
- 状态：审核中 → 审核通过/审核失败

#### 常见审核失败原因
1. ❌ 服务器域名未配置
   - 确保已在步骤 1 配置服务器域名

2. ❌ 域名未备案
   - 确认 liguoqi.site 备案状态

3. ❌ 功能描述不清
   - 按照上面的模板填写即可

4. ❌ 类目不符
   - 确保选择"工具 → 开发者工具"

---

### 步骤 6：发布上线

#### 审核通过后

1. 登录微信公众平台
2. 版本管理 → 审核版本
3. 审核通过的版本，点击"发布"
4. 确认发布

#### 发布成功

- 用户可以在微信搜索"Claude Skills"找到小程序
- 也可以扫描小程序码直接访问

---

## 📊 上线后监控

### API 监控
```bash
# 查看 Nginx 访问日志
ssh root@223.109.140.233 "tail -f /var/log/nginx/claude-skills-access.log"

# 查看 Nginx 错误日志
ssh root@223.109.140.233 "tail -f /var/log/nginx/claude-skills-error.log"

# 查看后端服务状态
ssh root@223.109.140.233 "ps aux | grep uvicorn"
```

### 数据库监控
```bash
# 查看技能总数和翻译进度
ssh root@223.109.140.233 "mysql -u claude_user -p'Claude2024!Skill' claude_skills -e '
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN name_zh IS NOT NULL THEN 1 ELSE 0 END) as translated
FROM skills;
' 2>/dev/null"
```

### SSL 证书监控
```bash
# 查看证书有效期
ssh root@223.109.140.233 "certbot certificates"

# 手动续期（如需要）
ssh root@223.109.140.233 "certbot renew"
```

---

## 🆘 常见问题

### Q1: 小程序请求失败
**A:** 检查：
1. 服务器域名是否已配置
2. API 服务是否运行：`ps aux | grep uvicorn`
3. Nginx 是否运行：`systemctl status nginx`
4. 查看错误日志

### Q2: 审核被拒
**A:** 根据拒绝原因修改：
- 服务类目不符 → 更换为"工具 → 开发者工具"
- 域名问题 → 确认备案状态
- 功能描述不清 → 参考上面的模板重新填写

### Q3: 数据不更新
**A:** 检查定时任务：
```bash
ssh root@223.109.140.233 "crontab -l"
ssh root@223.109.140.233 "tail -100 /var/log/claude-skills-cron.log"
```

---

## 📞 联系方式

如遇到技术问题，可以查看：
- 部署指南：`deploy/DEPLOYMENT_GUIDE.md`
- 项目文档：`README.md`
- 后端 API 文档：https://api.liguoqi.site/docs

祝上线顺利！ 🎉

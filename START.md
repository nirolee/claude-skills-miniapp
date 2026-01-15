# 🚀 HBuilderX 启动指南（已修复配置）

## ✅ 问题已解决

通过对比你的可运行项目 `simplylifeminiprogram`，我已经修复了以下关键配置：

### 已添加/修复的文件
- ✅ `manifest.json` - 添加 `"vueVersion": "3"` 和完整配置
- ✅ `.hbuilderx/launch.json` - HBuilderX 启动配置
- ✅ `index.html` - 应用入口 HTML
- ✅ `main.js` - Vue 3 应用入口

现在你的项目应该可以在 HBuilderX 中正常运行了！

---

## 📋 使用步骤

### 第一步：打开 HBuilderX

如果你已经安装了 HBuilderX，直接启动它。

如果还没安装：
1. 访问：https://www.dcloud.io/hbuilderx.html
2. 下载并解压（无需安装）
3. 运行 `HBuilderX.exe`

### 第二步：导入项目

#### 方法一：通过菜单导入（推荐）
1. 点击菜单栏：**文件 → 导入 → 从本地目录导入**
2. 选择项目目录：`D:\niro\claude-skills-miniapp\frontend`
3. 点击 **选择文件夹**
4. 项目会出现在左侧项目管理器中

#### 方法二：直接拖拽
1. 打开文件资源管理器
2. 找到 `D:\niro\claude-skills-miniapp\frontend` 文件夹
3. 将整个文件夹拖到 HBuilderX 窗口中

### 第三步：配置微信开发者工具路径

1. 打开 HBuilderX 设置
   - 方式1：菜单栏 **工具 → 设置**
   - 方式2：快捷键 `Ctrl + ,`

2. 找到 **运行配置 → 小程序运行配置**

3. 配置 **微信开发者工具路径**
   - Windows 默认路径：
     ```
     C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat
     ```
   - 或点击 **浏览** 按钮手动选择

4. 确保 **微信开发者工具已安装**
   - 下载地址：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html
   - 安装后打开一次，登录微信账号

### 第四步：配置微信小程序 AppID（可选）

如果你有微信小程序 AppID：

1. 打开 `manifest.json` 文件
2. 找到 `"mp-weixin"` 节点
3. 修改 `"appid": ""` 为你的 AppID
4. 保存文件

**如果没有 AppID**：可以暂时不填，使用测试 AppID 运行。

### 第五步：运行项目 🎯

1. 在 HBuilderX 项目管理器中，右键点击项目根目录（`frontend`）

2. 选择：**运行 → 运行到小程序模拟器 → 微信开发者工具**

3. **首次运行**会自动：
   - ✅ 安装依赖（`npm install`）
   - ✅ 编译项目
   - ✅ 启动微信开发者工具
   - ✅ 自动导入项目到微信开发者工具

4. 等待编译完成（查看 HBuilderX 底部控制台）

5. 微信开发者工具会自动打开并显示小程序

---

## 🎨 HBuilderX 快捷操作

### 常用快捷键
- `Ctrl + R` - 运行项目（重新编译）
- `Ctrl + Shift + R` - 停止运行
- `Ctrl + B` - 编译项目（不运行）
- `Ctrl + Shift + F` - 全局搜索
- `Ctrl + P` - 快速打开文件
- `Ctrl + /` - 注释/取消注释

### 运行到不同平台
右键项目 → 运行 → 选择平台：
- **微信小程序** - 运行到小程序模拟器 → 微信开发者工具
- **H5** - 运行到浏览器 → Chrome
- **支付宝小程序** - 运行到小程序模拟器 → 支付宝开发者工具

### 查看编译输出
- 底部控制台 → **控制台** 标签：查看编译日志
- 底部控制台 → **终端** 标签：查看命令行输出

---

## 🔧 常见问题

### Q1: 点击运行后没有反应？
**A:** 检查以下项：
1. 微信开发者工具路径是否正确配置
2. 微信开发者工具是否已登录
3. 查看 HBuilderX 控制台是否有错误信息
4. 尝试关闭微信开发者工具后重新运行

### Q2: 编译报错 "Cannot find module '@dcloudio/xxx'"？
**A:** 依赖安装不完整，手动安装：
```bash
cd D:\niro\claude-skills-miniapp\frontend
npm install --legacy-peer-deps
```

### Q3: 微信开发者工具显示 "代码包过大"？
**A:** 开发环境正常，生产环境需要：
1. 使用分包加载
2. 压缩图片资源
3. 移除未使用的依赖

### Q4: 想用 VSCode 编辑代码？
**A:** 可以！工作流程：
1. 用 VSCode 打开项目并编辑代码
2. 用 HBuilderX 运行和预览
3. 两个工具可以同时打开项目，互不干扰

### Q5: 修改代码后没有生效？
**A:** 尝试：
1. 保存文件（`Ctrl + S`）
2. 等待自动编译（查看控制台）
3. 如果还没生效，按 `Ctrl + R` 重新运行

---

## 📂 项目结构（HBuilderX 风格）

```
frontend/
├── .hbuilderx/          # HBuilderX 配置（已添加✅）
│   └── launch.json      # 启动配置
├── pages/               # 页面目录
│   ├── index/           # 首页
│   ├── detail/          # 详情页
│   ├── search/          # 搜索页
│   └── profile/         # 个人中心
├── static/              # 静态资源（图片、图标）
├── App.vue              # 应用入口（Vue 3 Composition API）
├── index.html           # HTML 入口（已添加✅）
├── main.js              # JS 入口（已添加✅）
├── manifest.json        # 应用配置（已修复✅）
├── pages.json           # 页面路由配置
├── uni.scss             # 全局样式
├── vite.config.js       # Vite 构建配置
└── package.json         # 依赖配置
```

---

## 🎯 下一步

项目运行成功后，你可以：

1. **修改页面**：编辑 `pages/` 目录下的 `.vue` 文件
2. **调整样式**：修改 `uni.scss` 全局样式
3. **添加页面**：在 `pages.json` 中注册新页面
4. **配置 TabBar**：在 `pages.json` 中配置底部导航栏

---

## 🎯 后端启动（独立）

后端不受前端问题影响，可以正常启动：

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# 配置 .env 文件
copy .env.example .env
# 编辑 .env 填入 MySQL 配置

# 初始化数据库
python scripts\init_db.py

# 导入技能数据
python scripts\import_skills.py

# 启动 API 服务
python src\api\main.py
# 访问 http://localhost:8000/docs
```

---

**最后更新**: 2026-01-10
**状态**: 配置已修复 ✅ 应该可以运行了！

如果还有问题，请检查 HBuilderX 控制台的错误信息。

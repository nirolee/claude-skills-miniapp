# Skill Terminal Logo 使用说明

## 快速开始

### 1. 生成Logo文件

1. **打开生成器**
   ```powershell
   # 在浏览器中打开
   start D:/niro/claude-skills-miniapp/logo-generator.html
   ```

2. **生成所需文件**

   页面会自动显示 144×144 的小程序头像Logo，点击对应按钮下载：

   | 按钮 | 用途 | 尺寸 | 保存位置 |
   |------|------|------|----------|
   | 下载正方形Logo | 微信小程序头像 | 144×144 | `frontend/static/images/logo-square.png` |
   | 生成大尺寸 → 下载 | 启动页/海报 | 512×512 | `frontend/static/images/logo-large.png` |
   | 生成TabBar图标 | 首页图标（选中） | 81×81 | `frontend/static/tabbar/home-active.png` |

### 2. 所需图标清单

需要手动移动下载的文件到以下位置：

#### 微信小程序头像
- ✅ `skill-terminal-logo-144.png` → 上传到微信公众平台

#### 启动页
- ✅ `skill-terminal-logo-512.png` → `frontend/static/images/splash.png`

#### TabBar图标（需要生成多个版本）

**首页图标**
- `frontend/static/tabbar/home.png` - 未选中（灰色版）
- `frontend/static/tabbar/home-active.png` - 选中（霓虹青色） ✅

**搜索图标**
- `frontend/static/tabbar/search.png` - 放大镜（灰色）
- `frontend/static/tabbar/search-active.png` - 放大镜（霓虹青色）

**个人图标**
- `frontend/static/tabbar/profile.png` - 用户头像（灰色）
- `frontend/static/tabbar/profile-active.png` - 用户头像（霓虹紫色）

### 3. 生成灰色版本图标

TabBar未选中状态需要灰色图标，有两种方法：

**方法1：在生成器中修改颜色**
1. 打开 `logo-generator.html`
2. 找到 `generateTabbarIcon()` 函数
3. 将 `ctx.fillStyle = '#00d9ff';` 改为 `ctx.fillStyle = '#64748b';`（灰色）
4. 重新生成并保存为 `home.png`

**方法2：用图片编辑工具**
1. 用Photoshop/GIMP打开 `home-active.png`
2. 去色：图像 → 调整 → 去色
3. 调整亮度到灰色（#64748b）
4. 保存为 `home.png`

### 4. 创建其他图标

**搜索图标** (使用Emoji或字符)：
```javascript
// 在生成器中添加新函数
function generateSearchIcon(active = false) {
    const size = 81;
    canvas.width = size;
    canvas.height = size;
    ctx.clearRect(0, 0, size, size);

    const color = active ? '#00d9ff' : '#64748b';

    // 绘制放大镜
    ctx.strokeStyle = color;
    ctx.lineWidth = 4;
    ctx.shadowColor = active ? color : 'transparent';
    ctx.shadowBlur = active ? 10 : 0;

    // 圆圈
    ctx.beginPath();
    ctx.arc(32, 32, 20, 0, Math.PI * 2);
    ctx.stroke();

    // 手柄
    ctx.beginPath();
    ctx.moveTo(45, 45);
    ctx.lineTo(58, 58);
    ctx.stroke();
}
```

**个人图标** (使用Emoji或字符)：
```javascript
function generateProfileIcon(active = false) {
    const size = 81;
    canvas.width = size;
    canvas.height = size;
    ctx.clearRect(0, 0, size, size);

    const color = active ? '#a855f7' : '#64748b';

    ctx.font = `${size * 0.6}px 'Courier New'`;
    ctx.fillStyle = color;
    ctx.shadowColor = active ? color : 'transparent';
    ctx.shadowBlur = active ? 10 : 0;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('👤', size/2, size/2);
}
```

## 设计规范

### 配色方案

| 颜色名称 | 十六进制 | RGB | 用途 |
|---------|---------|-----|------|
| 霓虹青 | `#00d9ff` | rgb(0, 217, 255) | 主色调、边框、首页图标 |
| 霓虹紫 | `#a855f7` | rgb(168, 85, 247) | 强调色、SKILL文字、个人图标 |
| 终端绿 | `#00ff88` | rgb(0, 255, 136) | 辅助色、成功状态 |
| 深空蓝 | `#0a0e1a` | rgb(10, 14, 26) | 背景色 |
| 灰色 | `#64748b` | rgb(100, 116, 139) | 未选中状态 |

### 发光效果

所有霓虹色图标都应有发光效果：
```css
box-shadow: 0 0 15px rgba(0, 217, 255, 0.8);
```

或在Canvas中：
```javascript
ctx.shadowColor = '#00d9ff';
ctx.shadowBlur = 15;
```

## 品牌资源

### Logo变体

1. **正方形版本** (144×144) - 微信小程序头像
   - 包含：`>_` + ⚡ + "SKILL"
   - 有星空背景和霓虹边框

2. **大尺寸版本** (512×512) - 宣传海报、启动页
   - 相同设计，更高分辨率

3. **简化图标** (81×81) - TabBar、按钮
   - 只保留核心图形（`>_` 或 ⚡）
   - 无边框，透明背景

4. **横版Banner** (750×300) - 分享海报
   - 可在生成器中添加横版布局

### 使用场景

| 场景 | 推荐版本 | 尺寸 |
|------|----------|------|
| 微信小程序头像 | 正方形Logo | 144×144 |
| 启动页 | 大尺寸Logo | 512×512 |
| 分享海报 | 横版Banner | 750×300 |
| TabBar图标 | 简化图标 | 81×81 |
| 文章配图 | 大尺寸Logo | 512×512 |

## 微信小程序配置

### 1. 上传头像

登录微信公众平台 → 设置 → 小程序信息 → 上传头像
- 使用 `skill-terminal-logo-144.png`

### 2. 更新pages.json

确认TabBar配置正确：
```json
{
  "tabBar": {
    "color": "#64748b",
    "selectedColor": "#00d9ff",
    "backgroundColor": "#0a0e1a",
    "list": [
      {
        "pagePath": "pages/index/index",
        "text": "首页",
        "iconPath": "static/tabbar/home.png",
        "selectedIconPath": "static/tabbar/home-active.png"
      },
      {
        "pagePath": "pages/search/search",
        "text": "搜索",
        "iconPath": "static/tabbar/search.png",
        "selectedIconPath": "static/tabbar/search-active.png"
      },
      {
        "pagePath": "pages/profile/profile",
        "text": "我的",
        "iconPath": "static/tabbar/profile.png",
        "selectedIconPath": "static/tabbar/profile-active.png"
      }
    ]
  }
}
```

## 生成完整图标包

### 自动化脚本（可选）

创建 `generate-all-icons.js`：
```javascript
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  await page.goto('file:///D:/niro/claude-skills-miniapp/logo-generator.html');

  // 生成并保存所有图标
  const icons = [
    { name: 'logo-square', size: 144 },
    { name: 'logo-large', size: 512 },
    { name: 'home-active', size: 81 },
    // ... 更多图标
  ];

  for (const icon of icons) {
    await page.evaluate((size) => {
      // 调用生成函数
      if (size === 144) generateSquareLogo();
      if (size === 512) generateLargeLogo();
      if (size === 81) generateTabbarIcon();
    }, icon.size);

    await page.screenshot({
      path: `frontend/static/images/${icon.name}.png`,
      clip: { x: 0, y: 0, width: icon.size, height: icon.size }
    });
  }

  await browser.close();
})();
```

## 常见问题

### Q: 图标在小程序中显示模糊？
A: 确保使用2倍图（81×81对应162×162），微信会自动缩放。

### Q: 如何批量生成图标？
A: 使用上面的Puppeteer脚本，或者手动在生成器中逐个下载。

### Q: 可以修改颜色方案吗？
A: 可以，编辑 `logo-generator.html` 中的颜色变量：
```javascript
const colors = {
    neonCyan: '#00d9ff',    // 霓虹青
    neonPurple: '#a855f7',  // 霓虹紫
    terminalGreen: '#00ff88' // 终端绿
};
```

### Q: 如何生成透明背景版本？
A: 在绘制函数开头使用：
```javascript
ctx.clearRect(0, 0, canvas.width, canvas.height); // 而不是 drawStarField()
```

## 下一步

- [ ] 在浏览器中打开 `logo-generator.html`
- [ ] 下载 144×144 Logo并上传到微信公众平台
- [ ] 生成并保存所有TabBar图标
- [ ] 更新 `pages.json` 的图标路径
- [ ] 测试小程序中TabBar图标显示效果

---

**提示**：所有图标都已设计为高对比度的霓虹风格，确保在深色背景下清晰可见。如果需要调整，直接编辑HTML文件中的Canvas绘制代码即可。

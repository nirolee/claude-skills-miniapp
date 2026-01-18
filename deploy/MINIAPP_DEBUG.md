# 小程序调试指南

## 问题：小程序运行失败，H5 正常

### 检查步骤

#### 步骤 1：微信开发者工具配置

1. 打开微信开发者工具
2. 点击右上角"详情"
3. 切换到"本地设置"标签
4. **必须勾选**：
   - ✅ 不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书
   - ✅ 启用调试
   - ✅ 不校验安全域名

**截图示例**：
```
┌─────────────────────────────────────┐
│ 详情                                │
├─────────────────────────────────────┤
│ 本地设置 | 项目配置 | 域名信息      │
├─────────────────────────────────────┤
│ ☑ 不校验合法域名...                 │
│ ☑ 启用调试                          │
│ ☑ 不校验安全域名                    │
└─────────────────────────────────────┘
```

#### 步骤 2：查看控制台错误

在微信开发者工具中：

1. 点击底部"Console"标签
2. 查看是否有红色错误
3. 常见错误类型：

**错误 A：域名不在合法域名列表**
```
request:fail url not in domain list
不在以下 request 合法域名列表中
```
**解决**：勾选"不校验合法域名"（开发阶段）

**错误 B：TLS 版本不支持**
```
request:fail ssl hand shake error
```
**解决**：检查服务器 SSL/TLS 配置

**错误 C：跨域问题**
```
Access-Control-Allow-Origin
```
**解决**：检查服务器 CORS 配置

**错误 D：网络请求失败**
```
request:fail
```
**解决**：检查网络连接，API 服务是否正常

#### 步骤 3：检查网络面板

1. 点击"Network"标签
2. 刷新小程序（Ctrl+R）
3. 查看网络请求：
   - ✅ 绿色 - 请求成功
   - ❌ 红色 - 请求失败

#### 步骤 4：检查 AppID 配置

确认 `manifest.json` 中的 AppID：
```json
"mp-weixin": {
  "appid": "wxea85c78af2ac2e2e"  // 必须是你的小程序 AppID
}
```

如果用的是测试号，AppID 可能不同。

#### 步骤 5：清除缓存重新编译

1. HBuilderX 中：
   - 运行 → 停止运行
   - 删除 `unpackage/dist/dev/mp-weixin` 目录
   - 重新运行

2. 微信开发者工具中：
   - 工具 → 清除缓存 → 全部清除
   - 重新编译

---

## 常见问题对照表

| 现象 | 可能原因 | 解决方案 |
|------|---------|---------|
| 白屏，无任何显示 | 编译错误/页面路径错误 | 查看 Console 错误，检查 pages.json |
| 显示页面但无数据 | API 请求失败 | 查看 Network，检查域名配置 |
| 报"不在合法域名列表" | 未配置服务器域名 | 勾选"不校验合法域名"（开发）|
| 样式混乱 | 样式编译问题 | 清除缓存重新编译 |
| 点击无响应 | JS 错误 | 查看 Console，检查事件绑定 |

---

## 调试技巧

### 1. 添加调试日志

在 `utils/request.js` 中添加：

```javascript
export function request(options = {}) {
  const fullUrl = `${API_BASE_URL}${url}`

  // 添加调试日志
  console.log('[API 请求]', method, fullUrl, data)

  return new Promise((resolve, reject) => {
    uni.request({
      url: fullUrl,
      // ...
      success: (res) => {
        console.log('[API 成功]', fullUrl, res.data)  // 添加
        // ...
      },
      fail: (err) => {
        console.error('[API 失败]', fullUrl, err)  // 添加
        // ...
      }
    })
  })
}
```

### 2. 使用真机调试

1. 微信开发者工具 → 点击"预览"
2. 用微信扫码
3. 在手机上查看真实效果
4. 可以在开发者工具中查看手机的 Console 输出

### 3. 检查 API 基础地址

在首页 `mounted` 中添加：

```javascript
async mounted() {
  console.log('API_BASE_URL:', API_BASE_URL)  // 检查 API 地址
  await this.loadCategories()
  await this.loadSkills(true)
}
```

确保输出是：`https://api.liguoqi.site/api`

---

## H5 和小程序差异

| 特性 | H5 | 小程序 |
|------|----|----|
| 网络请求 | fetch/axios | uni.request |
| 域名限制 | CORS | 合法域名列表 |
| 本地存储 | localStorage | uni.setStorage |
| 路由方式 | hash/history | 小程序路由 |
| 样式单位 | px/rem | rpx |

---

## 生产环境配置

上线前必须：

1. **配置服务器域名**
   - 登录微信公众平台
   - 开发 → 开发设置 → 服务器域名
   - 添加：`https://api.liguoqi.site`

2. **关闭调试选项**
   - `manifest.json` → `"urlCheck": true`
   - 移除所有 `console.log`

3. **提交审核**
   - 确保所有 API 请求都在合法域名内
   - 测试所有功能正常

---

## 紧急联系

如果还是无法解决：

1. 截图发送：
   - 微信开发者工具 Console 错误
   - Network 面板请求状态
   - 本地设置配置

2. 提供信息：
   - 微信开发者工具版本
   - uni-app 版本
   - HBuilderX 版本
   - 具体错误提示

---

祝调试顺利！

# Skill 内容和翻译改进说明

## 🔍 发现的问题

### 1. 数据库现状
通过检查发现：
- **总技能数**: 12,346 个
- **平均 content 长度**: 只有 203 字符（太短！）
- **最长 content**: 949 字符
- **超过 1000 字符的**: 0 个

**问题原因**: 爬虫只抓取了 description，而不是完整的 SKILL.md 文件内容！

### 2. 翻译限制
- AI 翻译服务在翻译 content 时只翻译前 2000 字符
- 对于完整的 SKILL.md 文件来说太短了

### 3. 已翻译进度
- 已翻译 content_zh: 4,400 个
- 未翻译: 7,946 个

---

## ✅ 已完成的改进

### 1. ✅ 数据库字段
- 数据库已有 `content_zh` 字段（无需修改）

### 2. ✅ 修改 AI 翻译服务 (`backend/src/services/ai_translation.py`)

**改进内容**:
- ✅ 移除了 `[:500]` 和 `[:2000]` 的内容截断
- ✅ 增加 max_tokens 到 16384（支持更长内容）
- ✅ 如果 content 超过 3000 字符，分开翻译以获得更好质量
- ✅ 使用 JSON 转义避免格式问题
- ✅ 完整保持 Markdown 格式

### 3. ✅ 修改爬虫 (`backend/scripts/smart_crawler.py`)

**新增功能**:
- ✅ 添加 `fetch_skill_content_from_github()` 函数
  - 从 GitHub 仓库获取完整的 SKILL.md 文件
  - 支持各种 GitHub URL 格式
  - 自动转换为 raw content URL

**修改逻辑**:
- ✅ 保存 skill 时，从 GitHub 获取完整内容
- ✅ 如果获取失败，使用 description 作为后备
- ✅ 更新现有 skill 时，如果新 content 更长，也会更新

### 4. ✅ 新增更新脚本 (`backend/scripts/update_skill_content.py`)

**功能**:
- ✅ 批量更新现有 skills 的完整内容
- ✅ 自动跳过 content 已经够长的 skills
- ✅ 支持限制更新数量（测试用）

---

## 🚀 使用方法

### 步骤 1: 更新现有 Skills 的完整内容

首先，更新数据库中现有的 skills，获取它们的完整 SKILL.md 内容。

```bash
cd backend

# 测试更新 10 个 skill
python scripts/update_skill_content.py --limit 10

# 查看结果，如果正常，更新所有 skills
python scripts/update_skill_content.py

# 只更新 content 长度小于 200 的
python scripts/update_skill_content.py --min-length 200
```

**预期结果**:
- 成功: 从 GitHub 获取到完整内容的 skill 数量
- 失败: GitHub 上没有 SKILL.md 或获取失败的
- 跳过: 新内容不比旧内容长的

### 步骤 2: 翻译 Skills 内容

更新完整内容后，运行翻译脚本来翻译 content_zh 字段。

```bash
# 测试翻译 5 个 skill（确保 API 正常）
python scripts/translate_skills.py --limit 5

# 如果测试成功，翻译所有未翻译的 skills
python scripts/translate_skills.py

# 强制重新翻译所有（包括已翻译的）
python scripts/translate_skills.py --all
```

**注意事项**:
- ✅ 翻译会自动跳过已翻译的 skills（除非使用 --all）
- ✅ 现在会翻译完整的 content，不再截断
- ⚠️ 长内容会分开翻译，需要更多 API 调用
- ⚠️ 每个 skill 间隔 2 秒，避免请求过快

### 步骤 3: 验证结果

检查更新和翻译是否成功：

```bash
# 运行检查脚本
python -c "
import asyncio
from sqlalchemy import text
from src.storage.database import get_session

async def check():
    async with get_session() as session:
        # 检查 content 长度
        query = text('''
            SELECT
                AVG(LENGTH(content)) as avg_len,
                MAX(LENGTH(content)) as max_len,
                SUM(CASE WHEN LENGTH(content) > 1000 THEN 1 ELSE 0 END) as long_content
            FROM skills
        ''')
        result = await session.execute(query)
        row = result.fetchone()
        print('Content 统计:')
        print(f'  平均长度: {row.avg_len:.0f} 字符')
        print(f'  最长: {row.max_len} 字符')
        print(f'  长内容(>1000字符): {row.long_content}')

        # 检查翻译进度
        query2 = text('''
            SELECT
                SUM(CASE WHEN content_zh IS NOT NULL AND content_zh != '' THEN 1 ELSE 0 END) as translated,
                COUNT(*) as total
            FROM skills
        ''')
        result2 = await session.execute(query2)
        row2 = result2.fetchone()
        print(f'\\n翻译进度:')
        print(f'  已翻译: {row2.translated}/{row2.total}')
        print(f'  进度: {row2.translated/row2.total*100:.1f}%')

asyncio.run(check())
"
```

### 步骤 4: 未来的爬虫使用

以后运行爬虫时，会自动获取完整内容：

```bash
# 爬取新的 skills（现在会自动获取完整内容）
python scripts/smart_crawler.py
```

---

## 📊 预期改进效果

### 更新内容后:
- ✅ 平均 content 长度: **203 字符 → 2000+ 字符**
- ✅ 长内容 skill (>1000 字符): **0 个 → 数千个**
- ✅ 用户点击技能详情页，能看到完整的 SKILL.md 内容

### 翻译后:
- ✅ content_zh 包含完整的中文版 SKILL.md
- ✅ 保持 Markdown 格式（标题、列表、代码块等）
- ✅ 前端可以正确显示中英文双语内容

---

## ⚠️ 注意事项

### 1. GitHub 限流
- 更新脚本每个请求间隔 1 秒
- 如果遇到 403 错误，说明被限流了，稍后再试

### 2. API 成本
- 翻译完整内容会消耗更多 API tokens
- 建议先用 `--limit` 参数测试
- 长内容会自动分开翻译

### 3. 内容质量
- 有些 GitHub 仓库可能没有 SKILL.md 文件
- 脚本会自动使用 description 作为后备
- 可以查看日志了解哪些 skill 获取失败

---

## 🔄 推荐执行顺序

```bash
# 1. 测试更新内容（10 个）
python scripts/update_skill_content.py --limit 10

# 2. 检查结果
# 查看数据库，确认 content 长度增加了

# 3. 如果测试成功，更新所有
python scripts/update_skill_content.py

# 4. 等待更新完成（可能需要几小时，因为有 12000+ skills）

# 5. 测试翻译（5 个）
python scripts/translate_skills.py --limit 5

# 6. 如果测试成功，翻译所有
python scripts/translate_skills.py

# 7. 验证结果
# 在前端查看技能详情页，应该能看到完整内容
```

---

## 🐛 故障排查

### 问题 1: 更新脚本获取内容失败

**原因**: GitHub URL 格式不对或仓库不存在

**解决**: 查看日志，找出哪些 skill 失败了，手动检查 GitHub URL

### 问题 2: 翻译脚本报错

**原因**:
- API key 未配置
- 内容格式问题
- JSON 解析失败

**解决**:
- 检查 .env 文件中的 ANTHROPIC_API_KEY
- 查看日志，找出失败的 skill
- 降级模式会自动启用（逐个字段翻译）

### 问题 3: 前端显示空白

**原因**: content_zh 为空或 Markdown 渲染问题

**解决**:
- 检查数据库，确认 content_zh 有值
- 检查前端 Markdown 渲染组件
- 查看浏览器控制台错误

---

## 📝 总结

完成以上步骤后，你的 Skill 市场将会：
- ✅ 每个 skill 都有完整的 SKILL.md 内容
- ✅ 支持中英文双语显示
- ✅ 用户可以查看详细的技能说明
- ✅ 未来爬取的新 skills 自动包含完整内容

需要帮助可以随时问我！

"""详细检查 SkillsMP 网站结构，找到所有 63295 个技能"""
from playwright.sync_api import sync_playwright
import time
import json

def analyze_skillsmp():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 使用有头模式
        page = browser.new_page()

        print("访问 SkillsMP...")
        page.goto('https://skillsmp.com/zh', wait_until='networkidle', timeout=60000)
        time.sleep(8)

        print(f"页面标题: {page.title()}")

        # 查找所有可能包含技能总数的元素
        print("\n=== 搜索技能总数 ===")
        text_with_numbers = page.locator('text=/\\d{3,}/').all()
        for elem in text_with_numbers[:20]:
            try:
                text = elem.text_content()
                if text and any(char.isdigit() for char in text):
                    print(f"  - {text}")
            except:
                pass

        # 查找分页或筛选器
        print("\n=== 查找分页/筛选 ===")

        # 检查分类筛选
        categories = page.locator('[class*="category"], [class*="filter"], [class*="tag"]').all()
        print(f"找到 {len(categories)} 个可能的分类/筛选元素")

        # 检查搜索框
        search_inputs = page.locator('input[type="search"], input[placeholder*="搜索"], input[placeholder*="search"]').all()
        print(f"找到 {len(search_inputs)} 个搜索框")

        # 检查下拉菜单或选项卡
        selects = page.locator('select, [role="combobox"], [class*="dropdown"]').all()
        print(f"找到 {len(selects)} 个下拉菜单")

        # 查看页面 URL 结构
        print(f"\n当前 URL: {page.url}")

        # 检查是否有 API 请求
        print("\n=== 监听网络请求（等待 10 秒）===")
        api_requests = []

        def handle_request(request):
            if 'api' in request.url or 'skills' in request.url:
                api_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'headers': dict(request.headers)
                })
                print(f"  API: {request.method} {request.url}")

        page.on('request', handle_request)

        # 滚动触发更多请求
        for i in range(3):
            page.evaluate("window.scrollBy(0, 500)")
            time.sleep(2)

        print(f"\n捕获到 {len(api_requests)} 个 API 请求")

        # 保存 API 请求信息
        if api_requests:
            with open('D:/niro/claude-skills-miniapp/backend/scripts/api_requests.json', 'w', encoding='utf-8') as f:
                json.dump(api_requests, f, indent=2, ensure_ascii=False)
            print("已保存 API 请求到: api_requests.json")

        # 检查页面的 JavaScript 变量
        print("\n=== 检查 JavaScript 全局变量 ===")
        try:
            js_data = page.evaluate("""
                () => {
                    return {
                        windowKeys: Object.keys(window).filter(k => k.includes('skill') || k.includes('data')),
                        hasReact: typeof window.React !== 'undefined',
                        hasVue: typeof window.Vue !== 'undefined',
                        hasNext: typeof window.__NEXT_DATA__ !== 'undefined',
                    }
                }
            """)
            print(f"  React: {js_data.get('hasReact')}")
            print(f"  Vue: {js_data.get('hasVue')}")
            print(f"  Next.js: {js_data.get('hasNext')}")
            print(f"  相关变量: {js_data.get('windowKeys')}")
        except Exception as e:
            print(f"  无法检查 JS 变量: {e}")

        # 截图
        page.screenshot(path='D:/niro/claude-skills-miniapp/backend/scripts/analyze_full.png', full_page=True)
        print("\n已保存截图: analyze_full.png")

        # 保存完整 HTML
        html = page.content()
        with open('D:/niro/claude-skills-miniapp/backend/scripts/analyze_full.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("已保存 HTML: analyze_full.html")

        print("\n按 Enter 继续，我会尝试查找具体的技能列表结构...")
        input()

        # 详细分析技能卡片结构
        print("\n=== 分析技能卡片结构 ===")

        # 获取第一个技能链接的详细信息
        first_skill = page.locator('a[href*="/skills/"]').first
        if first_skill:
            print("第一个技能链接的 HTML:")
            html = first_skill.evaluate("el => el.outerHTML")
            print(html[:500])

            # 获取父元素
            parent = first_skill.locator('xpath=..').first
            print("\n父元素 HTML:")
            parent_html = parent.evaluate("el => el.outerHTML")
            print(parent_html[:500])

        input("\n按 Enter 关闭浏览器...")
        browser.close()

if __name__ == "__main__":
    analyze_skillsmp()

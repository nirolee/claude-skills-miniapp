"""寻找 SkillsMP 的技能列表 API 端点"""
from playwright.sync_api import sync_playwright
import time
import json
import re

def find_skills_api():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # 存储所有 API 请求
        api_calls = []

        def handle_request(request):
            url = request.url
            # 记录所有可能相关的 API 请求
            if any(keyword in url for keyword in ['skill', 'api', 'search', 'list', '_rsc']):
                api_calls.append({
                    'url': url,
                    'method': request.method,
                    'type': request.resource_type
                })
                print(f"[API] {request.method} {url}")

        def handle_response(response):
            url = response.url
            # 记录响应内容
            if any(keyword in url for keyword in ['skill', 'api', 'search', 'list']):
                try:
                    if response.status == 200 and 'json' in response.headers.get('content-type', '').lower():
                        body = response.text()
                        # 检查是否包含技能列表
                        if 'skills' in body.lower() or 'items' in body.lower():
                            print(f"\n✅ 找到可能的列表 API: {url}")
                            print(f"   响应长度: {len(body)} 字符")
                            # 尝试解析 JSON
                            try:
                                data = json.loads(body)
                                print(f"   JSON 结构: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                            except:
                                pass
                except Exception as e:
                    pass

        page.on('request', handle_request)
        page.on('response', handle_response)

        print("=== 测试 1: 访问首页并滚动 ===")
        page.goto('https://skillsmp.com/zh', wait_until='networkidle', timeout=60000)
        time.sleep(5)

        # 滚动加载更多
        for i in range(5):
            print(f"滚动 {i+1}/5...")
            page.evaluate("window.scrollBy(0, 800)")
            time.sleep(2)

        print("\n=== 测试 2: 尝试搜索功能 ===")
        # 查找搜索框
        search_selectors = [
            'input[type="search"]',
            'input[placeholder*="搜索"]',
            'input[placeholder*="Search"]',
            'input[name*="search"]',
            '[role="searchbox"]'
        ]

        search_found = False
        for selector in search_selectors:
            try:
                if page.locator(selector).count() > 0:
                    print(f"找到搜索框: {selector}")
                    page.locator(selector).first.fill("test")
                    time.sleep(3)
                    search_found = True
                    break
            except:
                pass

        if not search_found:
            print("未找到搜索框，尝试导航到搜索页...")
            # 尝试直接访问搜索页
            try:
                page.goto('https://skillsmp.com/zh/search', timeout=30000)
                time.sleep(5)
            except:
                print("无法访问 /zh/search")

        print("\n=== 测试 3: 检查分类页面 ===")
        # 查找分类链接
        category_links = page.locator('a[href*="/category"], a[href*="/categories"]').all()
        if category_links:
            print(f"找到 {len(category_links)} 个分类链接")
            try:
                category_links[0].click()
                time.sleep(5)
            except:
                pass

        print("\n=== 测试 4: 检查页面 JavaScript 变量 ===")
        try:
            js_data = page.evaluate("""
                () => {
                    // 检查 Next.js 数据
                    const nextData = window.__NEXT_DATA__;
                    if (nextData) {
                        return {
                            hasNextData: true,
                            pageProps: Object.keys(nextData.props?.pageProps || {})
                        };
                    }

                    // 检查其他全局变量
                    const skillsData = [];
                    for (let key in window) {
                        if (key.includes('skill') || key.includes('data')) {
                            skillsData.push(key);
                        }
                    }

                    return {
                        hasNextData: false,
                        skillsVariables: skillsData
                    };
                }
            """)
            print(f"JavaScript 变量: {json.dumps(js_data, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"无法检查 JS 变量: {e}")

        print("\n=== 收集到的 API 请求 ===")
        # 分析 API 模式
        unique_patterns = set()
        for call in api_calls:
            url = call['url']
            # 提取 URL 模式
            pattern = re.sub(r'\?.*', '', url)  # 移除查询参数
            pattern = re.sub(r'/[a-f0-9-]{36}', '/:id', pattern)  # 替换 UUID
            pattern = re.sub(r'/\d+', '/:id', pattern)  # 替换数字 ID
            unique_patterns.add(pattern)

        print("\nAPI 模式:")
        for pattern in sorted(unique_patterns):
            print(f"  - {pattern}")

        # 保存所有请求
        with open('D:/niro/claude-skills-miniapp/backend/scripts/all_api_calls.json', 'w', encoding='utf-8') as f:
            json.dump(api_calls, f, indent=2, ensure_ascii=False)
        print(f"\n已保存 {len(api_calls)} 个 API 请求到: all_api_calls.json")

        print("\n按 Enter 关闭浏览器...")
        input()
        browser.close()

if __name__ == "__main__":
    find_skills_api()

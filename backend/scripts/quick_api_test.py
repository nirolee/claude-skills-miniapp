"""快速测试 API 响应格式"""
import asyncio
import aiohttp
from playwright.async_api import async_playwright
import json


async def quick_test():
    """快速测试 API 格式"""
    async with async_playwright() as p:
        print("启动浏览器...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        print("访问首页...")
        await page.goto('https://skillsmp.com/zh', timeout=60000)
        await asyncio.sleep(8)

        cookies = await context.cookies()
        cookie_dict = {c['name']: c['value'] for c in cookies}
        print(f"获取到 {len(cookies)} 个 cookies")

        await browser.close()

        # 测试 API
        print("\n测试 API 请求...")
        url = "https://skillsmp.com/api/skills"
        params = {'page': 1, 'limit': 5, 'sortBy': 'stars', 'marketplaceOnly': 'false'}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://skillsmp.com/zh',
        }

        async with aiohttp.ClientSession(cookies=cookie_dict, headers=headers) as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=30)) as response:
                print(f"状态码: {response.status}")
                data = await response.json()
                print(f"\n响应结构:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:1000])

                # 保存完整响应
                with open('D:/niro/claude-skills-miniapp/backend/scripts/api_response_sample.json', 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print("\n已保存完整响应到: api_response_sample.json")


if __name__ == "__main__":
    asyncio.run(quick_test())

"""深度扫描 SkillsMP，检查是否有更多技能"""
from playwright.sync_api import sync_playwright
import time

def deep_scan():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 使用有头模式观察
        page = browser.new_page()

        print("访问 SkillsMP...")
        page.goto('https://skillsmp.com/zh', wait_until='networkidle', timeout=60000)

        # 等待 Cloudflare
        time.sleep(8)

        print(f"页面标题: {page.title()}")

        # 连续滚动 20 次，看看能加载多少内容
        for i in range(20):
            print(f"\n第 {i + 1} 次滚动...")

            # 滚动前的技能数量
            before_count = len(page.locator('a[href*="/skills/"]').all())
            print(f"  滚动前: {before_count} 个技能")

            # 滚动到底部
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)

            # 滚动后的技能数量
            after_count = len(page.locator('a[href*="/skills/"]').all())
            print(f"  滚动后: {after_count} 个技能")

            if after_count == before_count:
                print("  没有新内容加载，停止滚动")
                break

        # 最终统计
        all_links = page.locator('a[href*="/skills/"]').all()
        print(f"\n最终找到 {len(all_links)} 个技能链接")

        # 检查是否有 "加载更多" 或 "下一页" 按钮
        load_more_selectors = [
            'text=/加载更多|load more|show more|next/i',
            'button:has-text("更多")',
            '[aria-label*="more"]',
            '[class*="load-more"]',
        ]

        for selector in load_more_selectors:
            try:
                button = page.locator(selector).first
                if button.is_visible():
                    print(f"\n找到加载更多按钮: {selector}")
                    break
            except:
                pass

        # 截图保存
        page.screenshot(path='D:/niro/claude-skills-miniapp/backend/scripts/deep_scan.png', full_page=True)
        print("\n已保存截图: deep_scan.png")

        input("\n按 Enter 键关闭浏览器...")
        browser.close()

if __name__ == "__main__":
    deep_scan()

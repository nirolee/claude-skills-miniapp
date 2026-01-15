"""检查 SkillsMP 网站的技能数据"""
from playwright.sync_api import sync_playwright
import json

def check_skillsmp():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("访问 SkillsMP 首页...")
        page.goto('https://skillsmp.com/', timeout=60000)
        page.wait_for_load_state('networkidle')

        # 截图查看页面
        page.screenshot(path='D:/niro/claude-skills-miniapp/backend/scripts/skillsmp_home.png', full_page=True)
        print("已保存首页截图: skillsmp_home.png")

        # 检查页面标题
        title = page.title()
        print(f"页面标题: {title}")

        # 检查所有链接
        links = page.locator('a').all()
        print(f"\n找到 {len(links)} 个链接")

        # 查找技能卡片或列表
        skill_cards = page.locator('[class*="skill"], [class*="card"], [class*="item"]').all()
        print(f"找到 {len(skill_cards)} 个可能的技能元素")

        # 查找分页信息
        pagination = page.locator('[class*="page"], [class*="pagination"]').all()
        print(f"找到 {len(pagination)} 个分页元素")

        # 检查是否有 "查看更多" 或 "下一页" 按钮
        more_buttons = page.locator('text=/更多|next|下一页|load more/i').all()
        print(f"找到 {len(more_buttons)} 个加载更多按钮")

        # 尝试获取所有技能链接
        skill_links = []
        for link in links:
            try:
                href = link.get_attribute('href')
                text = link.text_content()
                if href and ('skill' in href.lower() or 'claude' in href.lower()):
                    skill_links.append({
                        'href': href,
                        'text': text.strip() if text else ''
                    })
            except:
                pass

        print(f"\n找到 {len(skill_links)} 个可能的技能链接:")
        for i, link in enumerate(skill_links[:20], 1):  # 只显示前20个
            print(f"  {i}. {link['text'][:50]} - {link['href']}")

        # 保存完整的 HTML 用于分析
        html = page.content()
        with open('D:/niro/claude-skills-miniapp/backend/scripts/skillsmp_home.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\n已保存完整 HTML: skillsmp_home.html")

        # 尝试访问中文版
        print("\n\n尝试访问中文版...")
        page.goto('https://skillsmp.com/zh', timeout=60000)
        page.wait_for_load_state('networkidle')

        page.screenshot(path='D:/niro/claude-skills-miniapp/backend/scripts/skillsmp_zh.png', full_page=True)
        print("已保存中文版截图: skillsmp_zh.png")

        # 重新检查中文版的技能数量
        skill_cards_zh = page.locator('[class*="skill"], [class*="card"], [class*="item"]').all()
        print(f"中文版找到 {len(skill_cards_zh)} 个可能的技能元素")

        # 查找技能标题
        titles = page.locator('h2, h3, h4, [class*="title"]').all()
        print(f"找到 {len(titles)} 个标题元素")

        skill_titles = []
        for title in titles[:50]:  # 检查前50个标题
            try:
                text = title.text_content()
                if text and len(text.strip()) > 3:
                    skill_titles.append(text.strip())
            except:
                pass

        print(f"\n找到的标题:")
        for i, title in enumerate(skill_titles[:20], 1):
            print(f"  {i}. {title[:80]}")

        browser.close()

if __name__ == "__main__":
    check_skillsmp()

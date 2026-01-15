"""
基础爬虫类
基于 Playwright 实现，支持 JavaScript 渲染和异步操作
"""
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

from ..config import get_settings

logger = logging.getLogger(__name__)


class BaseCrawler:
    """异步爬虫基类，使用 Playwright 进行网页抓取"""

    def __init__(
        self,
        headless: bool = True,
        user_agent: Optional[str] = None,
        timeout: int = 30000,
    ):
        """
        初始化爬虫

        Args:
            headless: 是否无头模式
            user_agent: 自定义 User-Agent
            timeout: 请求超时时间（毫秒）
        """
        settings = get_settings()
        self.headless = headless
        self.user_agent = user_agent or settings.crawler_user_agent
        self.timeout = timeout

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def start(self):
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport={"width": 1920, "height": 1080},
                locale='zh-CN',  # 设置语言
                timezone_id='Asia/Shanghai',  # 设置时区
            )

            # 注入反检测脚本
            await self.context.add_init_script("""
                // 覆盖 webdriver 属性
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // 覆盖 plugins 和 languages
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });

                // 覆盖 chrome 属性
                window.chrome = {
                    runtime: {}
                };
            """)
            self.page = await self.context.new_page()
            self.page.set_default_timeout(self.timeout)
            logger.info("浏览器启动成功")
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            raise

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("浏览器关闭成功")
        except Exception as e:
            logger.error(f"浏览器关闭失败: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()

    async def fetch_page(
        self,
        url: str,
        wait_selector: Optional[str] = None,
        wait_timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        抓取页面内容

        Args:
            url: 目标 URL
            wait_selector: 等待的 CSS 选择器（确保页面加载完成）
            wait_timeout: 等待超时时间（毫秒），默认使用 self.timeout

        Returns:
            包含页面信息的字典：
            {
                "url": 当前页面 URL,
                "html": 页面 HTML,
                "text": 页面文本内容,
                "title": 页面标题,
                "screenshot": 页面截图（base64）
            }
        """
        if not self.page:
            raise RuntimeError("浏览器未启动，请先调用 start() 方法")

        try:
            logger.info(f"开始抓取: {url}")

            # 访问页面
            response = await self.page.goto(url, wait_until="domcontentloaded")

            if response and response.status >= 400:
                logger.warning(f"HTTP 状态码: {response.status}")

            # 等待特定元素加载
            if wait_selector:
                timeout = wait_timeout or self.timeout
                await self.page.wait_for_selector(
                    wait_selector, timeout=timeout, state="visible"
                )
                logger.debug(f"元素 {wait_selector} 加载完成")

            # 提取页面信息
            html = await self.page.content()
            text = await self.page.inner_text("body")
            title = await self.page.title()
            current_url = self.page.url

            # 可选：截图用于调试
            screenshot = await self.page.screenshot(type="png", full_page=False)

            logger.info(f"抓取成功: {current_url}")

            return {
                "url": current_url,
                "html": html,
                "text": text,
                "title": title,
                "screenshot": screenshot,
            }

        except Exception as e:
            logger.error(f"抓取失败 {url}: {e}")
            raise

    async def extract_elements(
        self,
        selector: str,
        extract_type: str = "text",
        attribute: Optional[str] = None,
    ) -> list:
        """
        提取页面元素

        Args:
            selector: CSS 选择器
            extract_type: 提取类型 (text/html/attribute)
            attribute: 当 extract_type 为 attribute 时，指定属性名

        Returns:
            提取结果列表
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            elements = await self.page.query_selector_all(selector)

            if extract_type == "text":
                return [await el.inner_text() for el in elements]
            elif extract_type == "html":
                return [await el.inner_html() for el in elements]
            elif extract_type == "attribute" and attribute:
                return [await el.get_attribute(attribute) for el in elements]
            else:
                return []

        except Exception as e:
            logger.error(f"元素提取失败 {selector}: {e}")
            return []

    async def click_and_wait(
        self,
        selector: str,
        wait_selector: Optional[str] = None,
        wait_time: int = 1000,
    ):
        """
        点击元素并等待

        Args:
            selector: 要点击的元素选择器
            wait_selector: 点击后等待出现的元素选择器
            wait_time: 等待时间（毫秒）
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            await self.page.click(selector)
            logger.debug(f"点击元素: {selector}")

            if wait_selector:
                await self.page.wait_for_selector(wait_selector, timeout=self.timeout)
            else:
                await self.page.wait_for_timeout(wait_time)

        except Exception as e:
            logger.error(f"点击操作失败 {selector}: {e}")
            raise

    async def scroll_to_bottom(self, pause_time: int = 500):
        """
        滚动到页面底部（用于加载懒加载内容）

        Args:
            pause_time: 每次滚动后的暂停时间（毫秒）
        """
        if not self.page:
            raise RuntimeError("浏览器未启动")

        try:
            await self.page.evaluate(
                """
                async () => {
                    const distance = 100;
                    const delay = %d;
                    while (document.scrollingElement.scrollTop + window.innerHeight < document.scrollingElement.scrollHeight) {
                        document.scrollingElement.scrollBy(0, distance);
                        await new Promise(resolve => setTimeout(resolve, delay));
                    }
                }
            """
                % pause_time
            )
            logger.debug("滚动到页面底部")
        except Exception as e:
            logger.error(f"滚动操作失败: {e}")
            raise

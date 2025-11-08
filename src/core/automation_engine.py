#!/usr/bin/env python3
"""
自动化引擎核心模块
Automation Engine Core Module

基于 Playwright 的现代化 Web 自动化引擎
支持 Chromium、Firefox、WebKit 浏览器

主要特性:
- 异步操作支持
- 智能等待机制
- 丰富的元素交互方法
- 工作流自动化
- 截图和调试功能

使用示例:
    config = {'headless': False, 'timeout': 10}
    engine = AutomationEngine(config)
    await engine.initialize_browser()
    await engine.navigate_to_url('https://example.com')
    await engine.input_text('#search', 'query')
    await engine.click_element('#submit')
    await engine.cleanup()
"""

import asyncio
import os
import platform
import time
from typing import Any

from loguru import logger
from playwright.async_api import (
    Browser,
    BrowserContext,
    ElementHandle,
    Page,
    Playwright,
    async_playwright,
)

from ..utils.browser_checker import BrowserChecker


class AutomationEngine:
    """
    自动化引擎类
    基于 Playwright 的现代化 Web 自动化引擎
    """

    def __init__(self, config: dict[str, Any]):
        """
        初始化自动化引擎

        Args:
            config: 配置字典
        """
        self.config = config
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None
        self.is_running = False
        self._browser_disconnected = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_future: asyncio.Future | None = None

    def _get_fallback_browser_paths(self) -> dict:
        """获取备选浏览器路径，用于打包环境下的最后尝试"""
        fallback_paths = {}

        system = platform.system()
        if system == "Windows":
            fallback_paths = {
                "Microsoft Edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                "Google Chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                "Google Chrome (x86)": r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                "Firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            }
        elif system == "Darwin":  # macOS
            fallback_paths = {
                "Google Chrome": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "Microsoft Edge": "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                "Firefox": "/Applications/Firefox.app/Contents/MacOS/firefox",
                "Safari": "/Applications/Safari.app/Contents/MacOS/Safari",
            }
        elif system == "Linux":
            fallback_paths = {
                "Google Chrome": "/usr/bin/google-chrome",
                "Chromium": "/usr/bin/chromium-browser",
                "Firefox": "/usr/bin/firefox",
            }

        return fallback_paths

    def _setup_playwright_environment(self):
        """设置 Playwright 环境变量，在打包环境下优先使用系统浏览器"""
        try:
            import sys

            # 检查是否在 PyInstaller 打包环境中
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # PyInstaller 环境 - 不设置 Playwright 的浏览器路径，让它使用系统浏览器
                logger.info("PyInstaller 打包环境检测到，将使用系统浏览器")

                # 清除可能影响的环境变量，确保使用系统浏览器
                env_vars_to_clear = [
                    'PLAYWRIGHT_BROWSERS_PATH',
                    'PLAYWRIGHT_DRIVER_PATH',
                    'PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'
                ]

                for env_var in env_vars_to_clear:
                    if env_var in os.environ:
                        del os.environ[env_var]
                        logger.debug(f"清除环境变量: {env_var}")
            else:
                # 开发环境
                logger.debug("开发环境，使用默认 Playwright 配置")

        except Exception as e:
            logger.warning(f"设置 Playwright 环境时出错: {e}")
            # 不抛出异常，继续使用默认配置

    async def initialize_browser(self) -> bool:
        """
        异步初始化 Playwright 浏览器

        Returns:
            bool: 初始化是否成功
        """
        try:
            self._loop = asyncio.get_running_loop()
            self._browser_disconnected = False
            # 检查是否在 PyInstaller 打包环境中
            self._setup_playwright_environment()

            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 获取浏览器配置
            headless = self.config.get("headless", False)
            browser_config = self.config.get("browser", None)  # 可能是名称或路径
            browser_path = self.config.get("browser_path", None)  # 浏览器可执行文件路径

            # 检查是否在打包环境中
            import sys
            is_packaged = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

            # 在打包环境下，优先使用系统浏览器
            if is_packaged or (browser_config is None and browser_path is None):
                logger.info("搜索系统浏览器...")
                browser_checker = BrowserChecker()
                auto_path = browser_checker.get_best_browser()
                if auto_path:
                    browser_path = auto_path
                    browser_config = None  # 清除配置，使用路径
                    logger.info(f"使用系统浏览器: {browser_path}")
                else:
                    if is_packaged:
                        # 打包环境下没找到系统浏览器，尝试 Edge 或 Chrome 的常见位置
                        logger.warning("未找到系统浏览器，尝试常见浏览器位置...")
                        fallback_browsers = self._get_fallback_browser_paths()
                        for fb_name, fb_path in fallback_browsers.items():
                            if os.path.exists(fb_path):
                                browser_path = fb_path
                                browser_config = None
                                logger.info(f"使用备选浏览器: {fb_name} ({fb_path})")
                                break
                        else:
                            raise Exception("打包环境下未找到可用的系统浏览器。请确保已安装 Chrome、Edge 或 Firefox。")
                    else:
                        # 开发环境，使用默认chromium
                        browser_config = "chromium"
                        logger.warning("未找到系统浏览器，尝试默认Chromium")

            # 选择浏览器
            if browser_config == "firefox":
                browser = self.playwright.firefox
            elif browser_config == "webkit":
                browser = self.playwright.webkit
            else:
                browser = self.playwright.chromium

            # 基础启动参数 - 添加反检测参数
            browser_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",  # 关键：隐藏 webdriver 标志
                "--disable-extensions",
                "--disable-geolocation",
                "--disable-permissions-api",
                "--disable-features=VizDisplayCompositor",
                "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",  # 模拟真实浏览器
            ]

            # 自动打开开发者工具（默认启用，方便调试）
            if self.config.get("open_devtools", True):  # 默认改为 True
                browser_args.append("--auto-open-devtools-for-tabs")
                logger.info("已启用自动打开开发者工具")

            # 基础启动选项
            window_size = self.config.get("window_size", "1566,900")
            width, height = map(int, window_size.split(","))

            launch_options = {
                "headless": headless,
                "args": browser_args + [f"--window-size={width},{height}"],
            }

            # 如果指定了浏览器路径，使用该路径
            if browser_path:
                launch_options["executable_path"] = browser_path
                # 为国产浏览器添加特殊启动参数
                browser_name = os.path.basename(browser_path).lower()
                if "360" in browser_name or "qq" in browser_name:
                    # 为360浏览器和QQ浏览器添加额外的兼容性参数
                    launch_options["args"].extend([
                        "--disable-web-security",
                        "--disable-background-timer-throttling",
                        "--disable-backgrounding-occluded-windows",
                        "--disable-renderer-backgrounding",
                        "--disable-field-trial-config",
                        "--disable-ipc-flooding-protection",
                    ])
                logger.info(f"使用指定浏览器路径: {browser_path}")
            else:
                # 使用指定的浏览器引擎
                logger.info(f"使用指定浏览器引擎: {browser_config}")

            self.browser = await browser.launch(**launch_options)

            # 监听浏览器断开事件
            self.browser.on('disconnected', self._on_browser_disconnected)

            # 创建上下文
            self.context = await self.browser.new_context(
                viewport={"width": width, "height": height},
                screen={"width": width, "height": height},
                permissions=[]  # 禁用所有权限请求
            )

            # 创建页面
            self.page = await self.context.new_page()

            # 隐藏 WebDriver 特征（关键反检测措施）
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                // 覆盖 chrome 对象
                window.chrome = {
                    runtime: {}
                };

                // 覆盖 permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // 覆盖 plugins 长度
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // 覆盖 languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en']
                });
            """)

            # 明确设置页面视窗尺寸，确保与浏览器窗口一致
            await self.page.set_viewport_size({"width": width, "height": height})

            # 设置超时 - 恢复原来的默认10秒
            timeout = self.config.get("timeout", 10) * 1000  # Playwright 使用毫秒
            self.page.set_default_timeout(timeout)

            browser_info = browser_path if browser_path else browser_config or "auto"
            logger.info(f"Playwright 浏览器初始化成功: {browser_info}")

            # 设置运行状态为True
            self.is_running = True
            self._browser_disconnected = False  # 确保标志正确
            logger.info(f"自动化引擎状态已设置 - is_running: {self.is_running}, browser_disconnected: {self._browser_disconnected}")

            # 预热：访问一个简单页面，建立"信任"
            try:
                logger.info("预热浏览器：访问简单页面建立信任...")
                await self.page.goto("about:blank", wait_until="domcontentloaded")
                await asyncio.sleep(1)
                logger.info("预热完成")
            except Exception as e:
                logger.warning(f"预热失败（不影响后续操作）: {e}")

            return True

        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False

    async def navigate_to_url(self, url: str) -> bool:
        """
        异步导航到指定URL

        Args:
            url: 目标URL

        Returns:
            bool: 导航是否成功
        """
        logger.debug(f"navigate_to_url 调用 - should_continue: {self.should_continue()}, is_running: {self.is_running}, browser_disconnected: {self._browser_disconnected}")

        if not self.should_continue():
            logger.warning(f"任务已停止，跳过导航 - is_running: {self.is_running}, browser_disconnected: {self._browser_disconnected}")
            return False

        if not self.page:
            logger.error("导航失败: 浏览器未初始化")
            return False

        try:
            logger.info(f"导航到: {url}")
            # 使用 domcontentloaded 等待策略，避免因网络资源加载缓慢导致超时
            # 设置较长的超时时间（60秒），适应网络波动
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            logger.info(f"页面导航成功: {url}")
            return True

        except Exception as e:
            logger.error(f"导航失败: {e}")
            import traceback
            logger.error(f"错误详情:\n{traceback.format_exc()}")
            return False

    async def find_element(
        self, selector: str, timeout: int | None = None
    ) -> ElementHandle | None:
        """
        异步查找页面元素

        Args:
            selector: CSS选择器或XPath表达式
            timeout: 超时时间(秒)

        Returns:
            ElementHandle或None
        """
        if not self.should_continue():
            logger.debug("任务已停止，跳过元素查找")
            return None

        if not self.page:
            logger.warning("元素查找失败: 浏览器未初始化")
            return None


        try:
            # 设置超时 - 恢复原来的默认10秒
            timeout_ms = (timeout or self.config.get("timeout", 10)) * 1000

            # 查找元素
            element = await self.page.wait_for_selector(selector, timeout=timeout_ms)
            return element

        except Exception as e:
            logger.warning(f"元素查找失败 {selector}: {e}")
            # 只有在元素找不到时才等待5分钟
            return None

    async def input_text(self, selector: str, text: str) -> bool:
        """
        异步在元素中输入文本

        Args:
            selector: CSS选择器或XPath表达式
            text: 要输入的文本

        Returns:
            bool: 输入是否成功
        """
        if not self.should_continue():
            logger.debug("任务已停止，跳过文本输入")
            return False

        try:
            element = await self.find_element(selector)
            if element and self.page:
                await self.page.fill(selector, text)
                return True
            return False

        except Exception as e:
            logger.error(f"文本输入失败: {e}")
            return False

    async def clear_input(self, selector: str) -> bool:
        """
        异步清空输入框内容

        Args:
            selector: CSS选择器或XPath表达式

        Returns:
            bool: 清空是否成功
        """
        try:
            element = await self.find_element(selector)
            if element and self.page:
                # 使用fill方法清空输入框
                await self.page.fill(selector, "")
                return True
            return False

        except Exception as e:
            logger.error(f"清空输入框失败: {e}")
            return False

    async def click_element(self, selector: str) -> bool:
        """
        异步点击元素

        Args:
            selector: CSS选择器或XPath表达式

        Returns:
            bool: 点击是否成功
        """
        if not self.should_continue():
            logger.debug("任务已停止，跳过元素点击")
            return False

        try:
            element = await self.find_element(selector)
            if element and self.page:
                await self.page.click(selector)
                return True
            return False

        except Exception as e:
            logger.error(f"元素点击失败: {e}")
            return False

    async def double_click_element(self, selector: str) -> bool:
        """
        异步双击元素

        Args:
            selector: CSS选择器或XPath表达式

        Returns:
            bool: 双击是否成功
        """

        try:
            element = await self.find_element(selector)
            if element and self.page:
                await self.page.dblclick(selector)
                return True
            return False

        except Exception as e:
            logger.error(f"元素双击失败: {e}")
            return False

    async def safe_double_click_element(self, selector: str, timeout: int = 10) -> bool:
        """
        安全双击元素：等待元素存在，滚动到可见位置，然后双击

        Args:
            selector: 元素选择器
            timeout: 等待超时时间(秒)

        Returns:
            bool: 双击是否成功
        """
        try:
            # 先等待并滚动到元素
            if await self.wait_and_scroll_to_element(selector, timeout):
                # 再双击元素
                await self.page.dblclick(selector)
                logger.info(f"成功双击元素: {selector}")
                return True
            else:
                logger.error(f"无法双击元素，元素不存在或不可见: {selector}")
                return False
        except Exception as e:
            logger.error(f"安全双击元素失败 {selector}: {e}")
            return False

    async def wait_for_element(self, selector: str, timeout: int | None = None) -> bool:
        """
        异步等待元素出现

        Args:
            selector: CSS选择器或XPath表达式
            timeout: 超时时间(秒)

        Returns:
            bool: 元素是否出现
        """
        element = await self.find_element(selector, timeout)
        return element is not None

    async def get_text(self, selector: str) -> str | None:
        """
        异步获取元素文本

        Args:
            selector: CSS选择器或XPath表达式

        Returns:
            str: 元素文本或None
        """
        try:
            element = await self.find_element(selector)
            if element and self.page:
                text = await self.page.text_content(selector)
                return text
            return None

        except Exception as e:
            logger.error(f"获取文本失败: {e}")
            return None

    async def hover(self, selector: str, timeout: int = 5) -> bool:
        """
        异步鼠标悬停在元素上

        Args:
            selector: CSS选择器或XPath表达式
            timeout: 等待超时时间(秒)

        Returns:
            bool: 悬停是否成功
        """
        try:
            if self.page:
                timeout_ms = timeout * 1000
                await self.page.hover(selector, timeout=timeout_ms)
                return True
            return False
        except Exception as e:
            logger.error(f"鼠标悬停失败: {e}")
            return False

    async def select_option(self, selector: str, value: str) -> bool:
        """
        异步选择下拉框选项

        Args:
            selector: 下拉框选择器
            value: 选项值

        Returns:
            bool: 选择是否成功
        """
        try:
            if self.page:
                await self.page.select_option(selector, value)
                return True
            return False
        except Exception as e:
            logger.error(f"选择选项失败: {e}")
            return False

    async def press_key(self, key: str) -> bool:
        """
        异步模拟按键操作

        Args:
            key: 按键名称（如 'Enter', 'Tab', 'Escape'）

        Returns:
            bool: 按键是否成功
        """
        try:
            if self.page:
                await self.page.keyboard.press(key)
                return True
            return False
        except Exception as e:
            logger.error(f"按键操作失败: {e}")
            return False

    async def scroll_to_element(self, selector: str) -> bool:
        """
        异步滚动到元素位置

        Args:
            selector: 元素选择器

        Returns:
            bool: 滚动是否成功
        """
        try:
            if self.page:
                await self.page.locator(selector).scroll_into_view_if_needed()
                return True
            return False
        except Exception as e:
            logger.error(f"滚动到元素失败: {e}")
            return False

    async def wait_and_scroll_to_element(self, selector: str, timeout: int = 10) -> bool:
        """
        等待元素存在并滚动到可见位置的通用方法

        Args:
            selector: 元素选择器
            timeout: 等待超时时间(秒)

        Returns:
            bool: 操作是否成功
        """
        try:
            if not self.page:
                logger.error("等待并滚动到元素失败: 浏览器未初始化")
                return False

            logger.info(f"等待元素出现: {selector}")

            # 等待元素存在
            timeout_ms = timeout * 1000
            element = await self.page.wait_for_selector(selector, timeout=timeout_ms)

            if element:
                logger.info(f"元素已找到，滚动到可见位置: {selector}")

                try:
                    # 滚动到元素位置 - 添加超时保护
                    locator = self.page.locator(selector)
                    # 使用 asyncio.wait_for 添加超时保护（最多等待5秒）
                    await asyncio.wait_for(
                        locator.scroll_into_view_if_needed(),
                        timeout=5.0
                    )

                    # 等待一小段时间确保滚动完成
                    await asyncio.sleep(0.5)

                    logger.info(f"成功滚动到元素: {selector}")
                    return True

                except asyncio.TimeoutError:
                    logger.warning(f"滚动到元素超时，但元素存在，尝试继续: {selector}")
                    # 即使滚动超时，元素仍然存在，可以尝试继续
                    return True

            else:
                logger.warning(f"元素未找到: {selector}")
                return False

        except Exception as e:
            logger.error(f"等待并滚动到元素失败 {selector}: {e}")
            return False



    async def safe_click_element(self, selector: str, timeout: int = 10) -> bool:
        """
        安全点击元素：等待元素存在，滚动到可见位置，然后点击

        Args:
            selector: 元素选择器
            timeout: 等待超时时间(秒)

        Returns:
            bool: 点击是否成功
        """
        try:
            # 先等待并滚动到元素
            if await self.wait_and_scroll_to_element(selector, timeout):
                # 再点击元素 - 添加超时保护，防止点击操作卡死
                try:
                    # 使用双重超时保护：
                    # 1. page.click 内部超时（timeout * 1000 毫秒）
                    # 2. asyncio.wait_for 外部超时（timeout + 5 秒，更宽松）
                    await asyncio.wait_for(
                        self.page.click(selector, timeout=timeout * 1000),
                        timeout=timeout + 5.0  # 额外5秒缓冲，确保不会误判
                    )
                    logger.info(f"成功点击元素: {selector}")
                    return True
                except asyncio.TimeoutError:
                    logger.error(f"点击元素超时（{timeout + 5}秒）: {selector}")
                    return False
            else:
                logger.error(f"无法点击元素，元素不存在或不可见: {selector}")
                return False
        except Exception as e:
            logger.error(f"安全点击元素失败 {selector}: {e}")
            return False

    async def safe_input_text(self, selector: str, text: str, clear_first: bool = True, timeout: int = 10) -> bool:
        """
        安全输入文本：等待元素存在，滚动到可见位置，然后输入

        Args:
            selector: 元素选择器
            text: 要输入的文本
            clear_first: 是否先清空输入框
            timeout: 等待超时时间(秒)

        Returns:
            bool: 输入是否成功
        """
        try:
            # 先等待并滚动到元素
            if await self.wait_and_scroll_to_element(selector, timeout):
                if clear_first:
                    # 先清空输入框，然后输入文本
                    await self.page.fill(selector, text)
                else:
                    # 直接在现有内容后追加文本
                    await self.page.type(selector, text)
                logger.info(f"成功输入文本到元素: {selector}")
                return True
            else:
                logger.error(f"无法输入文本，元素不存在或不可见: {selector}")
                return False
        except Exception as e:
            logger.error(f"安全输入文本失败 {selector}: {e}")
            return False

    async def wait_for_selector_visible(
        self, selector: str, timeout: int | None = None
    ) -> bool:
        """
        异步等待元素变为可见

        Args:
            selector: 元素选择器
            timeout: 超时时间(秒)

        Returns:
            bool: 元素是否可见
        """
        try:
            if self.page:
                timeout_ms = (timeout or self.config.get("timeout", 10)) * 1000
                await self.page.wait_for_selector(
                    selector, state="visible", timeout=timeout_ms
                )
                return True
            return False
        except Exception as e:
            logger.warning(f"等待元素可见失败 {selector}: {e}")
            return False

    async def get_attribute(self, selector: str, attribute: str) -> str | None:
        """
        异步获取元素属性值

        Args:
            selector: 元素选择器
            attribute: 属性名

        Returns:
            str: 属性值或None
        """
        try:
            if self.page:
                value = await self.page.get_attribute(selector, attribute)
                return value
            return None
        except Exception as e:
            logger.error(f"获取属性失败: {e}")
            return None

    async def is_element_visible(self, selector: str) -> bool:
        """
        异步检查元素是否可见

        Args:
            selector: 元素选择器

        Returns:
            bool: 元素是否可见
        """
        try:
            if self.page:
                return await self.page.is_visible(selector)
            return False
        except Exception as e:
            logger.warning(f"检查元素可见性失败: {e}")
            return False

    async def wait_for_page_load(self, timeout: int | None = None) -> bool:
        """
        异步等待页面加载完成

        Args:
            timeout: 超时时间(秒)

        Returns:
            bool: 页面是否加载完成
        """
        try:
            if self.page:
                timeout_ms = (timeout or 30) * 1000
                # 使用domcontentloaded而不是networkidle，避免因持续网络请求导致超时
                await self.page.wait_for_load_state("domcontentloaded", timeout=timeout_ms)
                return True
            return False
        except Exception as e:
            logger.warning(f"等待页面加载失败: {e}")
            return False

    async def take_screenshot(self, filepath: str | None = None) -> str | None:
        """
        异步截取屏幕截图

        Args:
            filepath: 保存路径，如果为None则自动生成

        Returns:
            str: 截图文件路径或None
        """
        if not self.page:
            logger.error("截图失败: 浏览器未初始化")
            return None

        try:
            if filepath is None:
                timestamp = int(time.time())
                filepath = f"screenshot_{timestamp}.png"

            await self.page.screenshot(path=filepath)
            logger.info(f"截图已保存: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None

    async def execute_workflow(self, steps: list[dict[str, Any]]) -> bool:
        """
        异步执行自动化工作流

        Args:
            steps: 工作流步骤列表

        Returns:
            bool: 执行是否成功
        """
        try:
            self.is_running = True

            for i, step in enumerate(steps):
                if not self.should_continue():
                    logger.info("收到停止信号，停止工作流执行")
                    return False

                logger.info(f"执行步骤 {i + 1}: {step.get('description', '未知步骤')}")

                action = step.get("action")

                if action == "navigate":
                    if not await self.navigate_to_url(step["url"]):
                        return False

                elif action == "click":
                    selector = step["selector"]
                    if not await self.click_element(selector):
                        return False

                elif action == "input":
                    selector = step["selector"]
                    if not await self.input_text(selector, step["text"]):
                        return False

                elif action == "wait":
                    duration = step.get("duration", 1)
                    await asyncio.sleep(duration)

                elif action == "wait_for_selector":
                    selector = step["selector"]
                    timeout = step.get("timeout", 10)
                    if not await self.wait_for_element(selector, timeout):
                        return False

                elif action == "wait_for_visible":
                    selector = step["selector"]
                    timeout = step.get("timeout", 10)
                    if not await self.wait_for_selector_visible(selector, timeout):
                        return False

                elif action == "hover":
                    selector = step["selector"]
                    if not await self.hover(selector):
                        return False

                elif action == "select_option":
                    selector = step["selector"]
                    value = step["value"]
                    if not await self.select_option(selector, value):
                        return False

                elif action == "press_key":
                    key = step["key"]
                    if not await self.press_key(key):
                        return False

                elif action == "screenshot":
                    filename = step.get("filename")
                    await self.take_screenshot(filename)

                elif action == "scroll_to":
                    selector = step["selector"]
                    if not await self.scroll_to_element(selector):
                        return False

                else:
                    logger.warning(f"未知动作: {action}")

                # 步骤间延迟
                step_delay = self.config.get("step_delay", 0.5)
                if step_delay > 0:
                    await asyncio.sleep(step_delay)

            return True

        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            return False
        finally:
            self.is_running = False

    async def cleanup(self):
        """
        异步清理资源
        """
        try:
            await self._close_browser()

        except Exception as e:
            logger.error(f"清理资源失败: {e}")

    # 同步包装器方法 - 专为UI调用设计
    def initialize_driver(self) -> bool:
        """
        同步方式初始化浏览器（为UI调用提供的包装器）

        Returns:
            bool: 初始化是否成功
        """
        try:
            return asyncio.run(self.initialize_browser())
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # 如果在事件循环中，创建新的线程来运行
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.initialize_browser())
                    return future.result()
            raise e

    async def evaluate_js(self, javascript_code: str) -> Any:
        """
        执行JavaScript代码并返回结果

        Args:
            javascript_code: 要执行的JavaScript代码

        Returns:
            Any: JavaScript执行结果
        """
        if not self.should_continue() or not self.page:
            logger.debug("跳过 evaluate_js，当前浏览器不可用或任务已停止")
            return None

        try:
            result = await self.page.evaluate(javascript_code)
            return result
        except Exception as e:
            if self._browser_disconnected or not self.should_continue():
                logger.debug(f"evaluate_js 在停止状态下忽略异常: {e}")
                return None
            logger.error(f"JavaScript执行失败: {e}")
            return None

    async def get_current_url(self) -> str | None:
        """
        获取当前页面URL

        Returns:
            str: 当前页面URL或None
        """
        if not self.should_continue() or not self.page:
            logger.debug("跳过 get_current_url，当前浏览器不可用或任务已停止")
            return None

        try:
            current_url = self.page.url
            return current_url
        except Exception as e:
            if self._browser_disconnected or not self.should_continue():
                logger.debug(f"get_current_url 在停止状态下忽略异常: {e}")
                return None
            logger.error(f"获取当前URL失败: {e}")
            return None

    async def is_browser_alive(self) -> bool:
        """
        检查浏览器是否仍然活跃

        Returns:
            bool: 浏览器是否活跃
        """
        if self._browser_disconnected:
            return False

        try:
            return (
                self.browser is not None and
                self.browser.is_connected() and
                self.context is not None and
                self.page is not None
            )
        except Exception:
            return False

    def set_stop_flag(self):
        """
        设置停止标志，用于外部停止任务
        """
        self.is_running = False
        logger.info("自动化引擎收到停止信号")

        if self._loop and self._loop.is_running():
            try:
                if self._stop_future is None or self._stop_future.done():
                    self._stop_future = asyncio.run_coroutine_threadsafe(self._close_browser(), self._loop)
            except RuntimeError as exc:
                logger.warning(f"发送停止信号时无法调度关闭操作: {exc}")

    def should_continue(self) -> bool:
        """
        检查是否应该继续执行任务

        Returns:
            bool: 是否应该继续
        """
        return self.is_running and not self._browser_disconnected

    def _on_browser_disconnected(self):
        """浏览器断开连接时的回调函数"""
        logger.warning("检测到浏览器已断开连接")
        self._browser_disconnected = True
        self.is_running = False

    async def _close_browser(self):
        """统一关闭浏览器及上下文资源"""

        self._browser_disconnected = True
        try:
            if self.page:
                try:
                    if hasattr(self.page, "is_closed"):
                        if not self.page.is_closed():
                            await self.page.close()
                    else:
                        await self.page.close()
                except Exception as page_error:
                    logger.debug(f"关闭页面时出现异常: {page_error}")
            if self.context:
                try:
                    await self.context.close()
                except Exception as ctx_error:
                    logger.debug(f"关闭上下文时出现异常: {ctx_error}")
            if self.browser:
                try:
                    await self.browser.close()
                except Exception as browser_error:
                    logger.debug(f"关闭浏览器时出现异常: {browser_error}")
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception as pw_error:
                    logger.debug(f"停止Playwright时出现异常: {pw_error}")
        finally:
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None
            self.is_running = False
            self._browser_disconnected = True
            self._loop = None

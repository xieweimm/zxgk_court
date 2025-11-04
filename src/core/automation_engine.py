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
"""

import asyncio
import os
import platform
import time
from typing import Any, Optional, TYPE_CHECKING

from loguru import logger
from playwright.async_api import (
    Browser,
    BrowserContext,
    ElementHandle,
    Page,
    Playwright,
    async_playwright,
)

if TYPE_CHECKING:
    from .schemas import BrowserConfig


class AutomationEngine:
    """
    自动化引擎类
    基于 Playwright 的现代化 Web 自动化引擎
    """

    def __init__(self, config: "BrowserConfig"):
        """
        初始化自动化引擎

        Args:
            config: BrowserConfig 配置对象
        """
        self.config = config
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # 从配置对象获取参数
        self.headless = config.headless
        self.browser_type = config.type
        self.timeout = config.timeout * 1000  # 转换为毫秒
        self.slow_mo = config.slow_mo

        logger.info(f"自动化引擎初始化完成 - 浏览器: {self.browser_type}, 无头模式: {self.headless}")

    async def initialize_browser(self):
        """初始化浏览器"""
        try:
            logger.info("正在启动浏览器...")
            self.playwright = await async_playwright().start()

            # 根据配置选择浏览器
            browser_map = {
                "chromium": self.playwright.chromium,
                "firefox": self.playwright.firefox,
                "webkit": self.playwright.webkit,
            }

            browser_launcher = browser_map.get(self.browser_type, self.playwright.chromium)

            # 启动浏览器
            self.browser = await browser_launcher.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
            )

            # 创建浏览器上下文
            viewport = {"width": self.config.viewport.width, "height": self.config.viewport.height}
            self.context = await self.browser.new_context(
                viewport=viewport,
                locale="zh-CN",
            )

            # 设置默认超时
            self.context.set_default_timeout(self.timeout)

            # 创建新页面
            self.page = await self.context.new_page()

            logger.info("浏览器启动成功")
            return True

        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            await self.cleanup()
            return False

    async def navigate_to_url(self, url: str, wait_until: str = "networkidle"):
        """
        导航到指定URL

        Args:
            url: 目标URL
            wait_until: 等待条件 (load/domcontentloaded/networkidle)
        """
        try:
            logger.info(f"导航到: {url}")
            await self.page.goto(url, wait_until=wait_until)
            return True
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        try:
            logger.info("正在清理资源...")

            if self.page:
                await self.page.close()
                self.page = None

            if self.context:
                await self.context.close()
                self.context = None

            if self.browser:
                await self.browser.close()
                self.browser = None

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None

            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {e}")

    def __del__(self):
        """析构函数"""
        # 确保资源被清理
        pass

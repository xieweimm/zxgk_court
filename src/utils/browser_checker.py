#!/usr/bin/env python3
"""
浏览器检查工具
Browser Checker Utility

检查系统中可用的浏览器
"""

import platform
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger


class BrowserChecker:
    """浏览器检查器"""

    @staticmethod
    def is_chromium_available() -> bool:
        """检查Chromium是否可用"""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                browser.close()
                return True
        except Exception as e:
            logger.warning(f"Chromium不可用: {e}")
            return False

    @staticmethod
    def is_firefox_available() -> bool:
        """检查Firefox是否可用"""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.firefox.launch(headless=True)
                browser.close()
                return True
        except Exception as e:
            logger.warning(f"Firefox不可用: {e}")
            return False

    @staticmethod
    def is_webkit_available() -> bool:
        """检查WebKit是否可用"""
        try:
            from playwright.sync_api import sync_playwright

            with sync_playwright() as p:
                browser = p.webkit.launch(headless=True)
                browser.close()
                return True
        except Exception as e:
            logger.warning(f"WebKit不可用: {e}")
            return False

    @staticmethod
    def get_available_browsers() -> list[str]:
        """获取所有可用的浏览器"""
        browsers = []

        if BrowserChecker.is_chromium_available():
            browsers.append("chromium")

        if BrowserChecker.is_firefox_available():
            browsers.append("firefox")

        if BrowserChecker.is_webkit_available():
            browsers.append("webkit")

        return browsers

    @staticmethod
    def get_recommended_browser() -> Optional[str]:
        """获取推荐的浏览器"""
        available = BrowserChecker.get_available_browsers()

        if not available:
            return None

        # 优先推荐chromium
        if "chromium" in available:
            return "chromium"

        return available[0]

#!/usr/bin/env python3
"""
测试自动化引擎
"""

import asyncio
import pytest

from src.core.automation_engine import AutomationEngine
from src.core.schemas import BrowserConfig


@pytest.mark.asyncio
async def test_automation_engine_init():
    """测试自动化引擎初始化"""
    config = BrowserConfig(
        headless=True,
        type="chromium",
        timeout=30
    )
    engine = AutomationEngine(config)

    assert engine is not None
    assert engine.headless is True
    assert engine.browser_type == "chromium"


@pytest.mark.asyncio
async def test_browser_launch():
    """测试浏览器启动"""
    config = BrowserConfig(
        headless=True,
        type="chromium"
    )
    engine = AutomationEngine(config)

    result = await engine.initialize_browser()
    assert result is True
    assert engine.browser is not None
    assert engine.page is not None

    await engine.cleanup()


@pytest.mark.asyncio
async def test_navigation():
    """测试页面导航"""
    config = BrowserConfig(
        headless=True,
        type="chromium"
    )
    engine = AutomationEngine(config)

    await engine.initialize_browser()
    result = await engine.navigate_to_url("https://www.example.com")
    assert result is True

    await engine.cleanup()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

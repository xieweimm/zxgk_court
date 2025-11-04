#!/usr/bin/env python3
"""
配置模式测试
Configuration Schemas Tests
"""

import pytest
from src.core.schemas import (
    Config,
    BrowserConfig,
    LoggingConfig,
    TaskConfig,
    AppConfig,
    StepConfig,
    RetryConfig,
    ViewportConfig
)


def test_viewport_config_default():
    """测试视口配置默认值"""
    viewport = ViewportConfig()
    assert viewport.width == 1280
    assert viewport.height == 720


def test_browser_config_default():
    """测试浏览器配置默认值"""
    browser = BrowserConfig()
    assert browser.type == "chromium"
    assert browser.headless is False
    assert browser.timeout == 30
    assert browser.viewport.width == 1280


def test_browser_config_from_dict():
    """测试从字典创建浏览器配置"""
    data = {
        "type": "firefox",
        "headless": True,
        "timeout": 60,
        "viewport": {"width": 1920, "height": 1080}
    }
    browser = BrowserConfig.from_dict(data)
    assert browser.type == "firefox"
    assert browser.headless is True
    assert browser.timeout == 60
    assert browser.viewport.width == 1920
    assert browser.viewport.height == 1080


def test_logging_config_from_dict():
    """测试从字典创建日志配置"""
    data = {"level": "DEBUG", "console": False}
    logging = LoggingConfig.from_dict(data)
    assert logging.level == "DEBUG"
    assert logging.console is False
    assert logging.file is True  # 默认值


def test_task_config_from_dict():
    """测试从字典创建任务配置"""
    data = {"max_retries": 5, "retry_delay": 3.0}
    task = TaskConfig.from_dict(data)
    assert task.max_retries == 5
    assert task.retry_delay == 3.0
    assert task.concurrent_limit == 5  # 默认值


def test_config_full():
    """测试完整配置"""
    data = {
        "browser": {"type": "chromium", "headless": False},
        "logging": {"level": "INFO"},
        "task": {"max_retries": 3},
        "app": {"name": "Test App"}
    }
    config = Config.from_dict(data)
    assert config.browser.type == "chromium"
    assert config.logging.level == "INFO"
    assert config.task.max_retries == 3
    assert config.app.name == "Test App"


def test_retry_config():
    """测试重试配置"""
    retry = RetryConfig(max_retries=5, retry_delay=3.0)
    assert retry.max_retries == 5
    assert retry.retry_delay == 3.0


def test_step_config_from_dict():
    """测试从字典创建步骤配置"""
    data = {
        "step_id": "nav_01",
        "name": "导航到页面",
        "handler": "navigation_handler",
        "method": "navigate_to_page",
        "args": ["https://example.com"],
        "kwargs": {"wait": True},
        "retry_config": {"max_retries": 3, "retry_delay": 2.0},
        "description": "导航测试"
    }
    step = StepConfig.from_dict(data)
    assert step.step_id == "nav_01"
    assert step.name == "导航到页面"
    assert step.handler == "navigation_handler"
    assert step.method == "navigate_to_page"
    assert step.args == ["https://example.com"]
    assert step.kwargs == {"wait": True}
    assert step.retry_config.max_retries == 3
    assert step.description == "导航测试"


def test_step_config_missing_required_field():
    """测试缺少必需字段时抛出异常"""
    data = {
        "step_id": "nav_01",
        "name": "导航到页面",
        # 缺少 handler 和 method
    }
    with pytest.raises(KeyError) as exc_info:
        StepConfig.from_dict(data)
    assert "必需字段" in str(exc_info.value)


def test_step_config_to_dict():
    """测试步骤配置转换为字典"""
    step = StepConfig(
        step_id="test_01",
        name="测试步骤",
        handler="test_handler",
        method="test_method",
        args=[1, 2],
        kwargs={"key": "value"}
    )
    data = step.to_dict()
    assert data["step_id"] == "test_01"
    assert data["name"] == "测试步骤"
    assert data["args"] == [1, 2]
    assert data["kwargs"] == {"key": "value"}


def test_config_empty_dict():
    """测试空字典使用默认配置"""
    config = Config.from_dict({})
    assert config.browser.type == "chromium"
    assert config.logging.level == "INFO"
    assert config.task.max_retries == 3
    assert config.app.name == "ZXGK Court Automation Tool"

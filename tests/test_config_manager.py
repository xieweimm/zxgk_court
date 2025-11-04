#!/usr/bin/env python3
"""
配置管理器测试
"""

import pytest
from pathlib import Path
from src.core.config_manager import ConfigManager
from src.core.schemas import Config


def test_config_manager_init():
    """测试配置管理器初始化"""
    config_manager = ConfigManager()
    assert config_manager.config_dir.exists()
    assert config_manager.config_dir.name == "config"


def test_get_config():
    """测试获取类型化配置"""
    config_manager = ConfigManager()
    config = config_manager.get_config()

    # 验证返回的是 Config 对象
    assert isinstance(config, Config)

    # 验证默认值
    assert config.browser.type == "chromium"
    assert config.browser.headless is False
    assert config.browser.timeout == 30
    assert config.logging.level == "INFO"
    assert config.task.max_retries == 3


def test_get_config_caching():
    """测试配置缓存"""
    config_manager = ConfigManager()
    config1 = config_manager.get_config()
    config2 = config_manager.get_config()

    # 应该返回同一个对象（缓存）
    assert config1 is config2


def test_load_step_config():
    """测试加载步骤配置"""
    config_manager = ConfigManager()

    step_data = {
        "step_id": "test_01",
        "name": "测试步骤",
        "handler": "test_handler",
        "method": "test_method"
    }

    step_config = config_manager.load_step_config(step_data)
    assert step_config.step_id == "test_01"
    assert step_config.name == "测试步骤"
    assert step_config.handler == "test_handler"
    assert step_config.method == "test_method"


def test_load_step_config_missing_field():
    """测试缺少必需字段时抛出异常"""
    config_manager = ConfigManager()

    invalid_step_data = {
        "step_id": "test_01",
        "name": "测试步骤"
        # 缺少 handler 和 method
    }

    with pytest.raises(KeyError):
        config_manager.load_step_config(invalid_step_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

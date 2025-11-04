#!/usr/bin/env python3
"""
配置验证使用示例
Configuration Validation Usage Examples

演示如何使用新的类型化配置系统
"""

from src.core.config_manager import ConfigManager
from src.core.schemas import Config, StepConfig


def example_1_load_typed_config():
    """示例1: 加载类型化配置"""
    print("=" * 60)
    print("示例1: 加载类型化配置")
    print("=" * 60)

    config_manager = ConfigManager()
    config = config_manager.get_config()

    # ✅ IDE 自动提示，类型安全
    print(f"浏览器类型: {config.browser.type}")
    print(f"浏览器超时: {config.browser.timeout}秒")
    print(f"视口大小: {config.browser.viewport.width}x{config.browser.viewport.height}")
    print(f"日志级别: {config.logging.level}")
    print(f"最大重试: {config.task.max_retries}次")
    print(f"应用名称: {config.app.name}")
    print()


def example_2_validate_step_config():
    """示例2: 验证步骤配置"""
    print("=" * 60)
    print("示例2: 验证步骤配置（正确配置）")
    print("=" * 60)

    config_manager = ConfigManager()

    # 正确的配置
    step_data = {
        "step_id": "nav_01",
        "name": "导航到页面",
        "handler": "navigation_handler",
        "method": "navigate_to_page",
        "args": ["https://example.com"],
        "kwargs": {"timeout": 30}
    }

    try:
        step_config = config_manager.load_step_config(step_data)
        print(f"✅ 步骤配置验证成功:")
        print(f"   步骤ID: {step_config.step_id}")
        print(f"   步骤名称: {step_config.name}")
        print(f"   处理器: {step_config.handler}")
        print(f"   方法: {step_config.method}")
        print(f"   参数: {step_config.args}")
        print(f"   关键字参数: {step_config.kwargs}")
        print()
    except Exception as e:
        print(f"❌ 错误: {e}")


def example_3_invalid_step_config():
    """示例3: 捕获无效配置错误"""
    print("=" * 60)
    print("示例3: 捕获无效配置（缺少必需字段）")
    print("=" * 60)

    config_manager = ConfigManager()

    # ❌ 错误的配置 - 缺少 handler 和 method
    invalid_step_data = {
        "step_id": "nav_01",
        "name": "导航到页面",
        # 缺少 handler 和 method
    }

    try:
        step_config = config_manager.load_step_config(invalid_step_data)
        print(f"步骤配置: {step_config}")
    except KeyError as e:
        print(f"✅ 成功捕获配置错误:")
        print(f"   错误信息: {e}")
        print(f"   启动时就发现问题，不用等到运行时！")
        print()


def example_4_compare_old_vs_new():
    """示例4: 对比旧方法 vs 新方法"""
    print("=" * 60)
    print("示例4: 新方法使用示例")
    print("=" * 60)

    config_manager = ConfigManager()
    config = config_manager.get_config()

    print("【类型化对象访问】:")
    # ✅ IDE 自动提示，类型安全
    print(f"   浏览器类型: {config.browser.type} (简洁，有类型提示)")
    print(f"   超时时间: {config.browser.timeout}")
    print(f"   视口大小: {config.browser.viewport.width}x{config.browser.viewport.height}")
    print()


def example_5_step_config_usage():
    """示例5: 步骤配置的实际使用"""
    print("=" * 60)
    print("示例5: 步骤配置的实际使用")
    print("=" * 60)

    # 创建步骤配置
    step_data = {
        "step_id": "form_01",
        "name": "填写表单",
        "handler": "form_handler",
        "method": "fill_form",
        "args": [],
        "kwargs": {
            "username": "test_user",
            "password": "test_pass"
        },
        "retry_config": {
            "max_retries": 5,
            "retry_delay": 3.0
        },
        "description": "填写登录表单"
    }

    step = StepConfig.from_dict(step_data)

    print(f"步骤信息:")
    print(f"  ID: {step.step_id}")
    print(f"  名称: {step.name}")
    print(f"  重试次数: {step.retry_config.max_retries}")
    print(f"  重试延迟: {step.retry_config.retry_delay}秒")
    print(f"  描述: {step.description}")
    print()

    # 转换回字典（用于保存或传输）
    step_dict = step.to_dict()
    print(f"转换回字典: {step_dict}")
    print()


if __name__ == "__main__":
    print("\n🎯 配置验证优化 - 使用示例\n")

    try:
        example_1_load_typed_config()
        example_2_validate_step_config()
        example_3_invalid_step_config()
        example_4_compare_old_vs_new()
        example_5_step_config_usage()

        print("=" * 60)
        print("✅ 所有示例运行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()

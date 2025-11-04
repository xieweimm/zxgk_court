#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZXGK Court Automation Tool - 主程序入口
架构: 用户 → GUI窗口 → Playwright → 目标网站

创建时间: 2025年
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入版本信息
try:
    from version import get_version_string, get_version, get_build
except ImportError:
    def get_version_string():
        return "v1.0.0+0"
    def get_version():
        return "1.0.0"
    def get_build():
        return 0


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    return True


def check_gui_environment():
    """检查GUI环境"""
    import os

    try:
        # 检查是否有DISPLAY环境变量（Linux/macOS）
        if sys.platform.startswith('linux') and not os.environ.get('DISPLAY'):
            print("警告: 未检测到DISPLAY环境变量，可能无法显示GUI")
            return False

        # 测试tkinter
        print("测试tkinter可用性...")
        import tkinter as tk
        print("正在创建测试窗口...")
        test_root = tk.Tk()
        test_root.withdraw()  # 隐藏测试窗口
        test_root.destroy()
        print("tkinter测试成功")

        return True
    except Exception as e:
        print(f"GUI环境检查失败: {e}")
        return False


def check_dependencies():
    """检查必要的依赖"""
    missing_deps = []

    try:
        import tkinter
        print("✓ tkinter 可用")
    except ImportError:
        missing_deps.append("tkinter")
        print("✗ tkinter 不可用")

    try:
        import playwright
        print("✓ playwright 可用")
    except ImportError:
        missing_deps.append("playwright")
        print("✗ playwright 不可用")

    if missing_deps:
        print("错误: 缺少必要的依赖包:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\n请运行以下命令安装依赖:")
        print("pip install playwright")
        print("playwright install chromium")
        return False

    return True


def setup_environment():
    """设置运行环境"""
    try:
        # 确保必要的目录存在
        required_dirs = ["logs", "config", "assets"]
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)

        return True
    except Exception as e:
        print(f"环境设置失败: {e}")
        return False


def main():
    """
    主程序入口函数
    """
    print("="*50)
    print(f"ZXGK Court Automation Tool {get_version_string()}")
    print("架构: 用户 → GUI → Playwright → 网站")
    print("="*50)

    # 初始化日志系统
    try:
        from src.utils.logger import setup_logger
        setup_logger()
        print("✓ 日志系统已初始化")
    except Exception as e:
        print(f"⚠ 日志系统初始化失败: {e}")
        # 不影响程序继续运行

    # 设置环境变量以抑制tkinter弃用警告
    os.environ['TK_SILENCE_DEPRECATION'] = '1'
    if not check_python_version():
        input("按回车键退出...")
        return 1

    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...")
        return 1

    # 检查GUI环境
    if not check_gui_environment():
        input("按回车键退出...")
        return 1

    # 设置环境
    if not setup_environment():
        input("按回车键退出...")
        return 1

    try:
        # 导入并启动GUI应用
        print("正在启动GUI界面...")
        from src.ui.gui import ZXGKCourtAutomationGUI

        app = ZXGKCourtAutomationGUI()
        app.run()

        print("程序正常退出")
        return 0

    except ImportError as e:
        print(f"导入模块失败: {e}")
        print("请检查项目文件是否完整")
        input("按回车键退出...")
        return 1

    except Exception as e:
        print(f"程序启动失败: {e}")
        import traceback
        traceback.print_exc()
        input("按回车键退出...")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

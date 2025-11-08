#!/usr/bin/env python3
"""
ZXGK 模块处理器
ZXGK Module Handlers
"""

from .excel_handler import ExcelHandler
from .navigation_handler import NavigationHandler
from .captcha_handler import CaptchaHandler
from .form_handler import FormHandler

__all__ = [
    "ExcelHandler",
    "NavigationHandler",
    "CaptchaHandler",
    "FormHandler",
]

#!/usr/bin/env python3
"""
异常类定义
Custom Exceptions
"""


class AutomationException(Exception):
    """自动化异常基类"""
    pass


class BrowserException(AutomationException):
    """浏览器异常"""
    pass


class ElementNotFoundException(AutomationException):
    """元素未找到异常"""
    pass


class TimeoutException(AutomationException):
    """超时异常"""
    pass


class ConfigException(AutomationException):
    """配置异常"""
    pass


class TaskException(AutomationException):
    """任务执行异常"""
    pass

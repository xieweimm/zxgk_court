#!/usr/bin/env python3
"""
辅助工具函数
Helper Utilities
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable


def retry_async(max_retries: int = 3, delay: float = 1.0):
    """
    异步函数重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试延迟（秒）
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay)
            return None
        return wrapper
    return decorator


def measure_time(func: Callable):
    """
    测量函数执行时间的装饰器
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} 执行耗时: {duration:.2f}秒")
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__} 执行耗时: {duration:.2f}秒")
        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def format_duration(seconds: float) -> str:
    """
    格式化时长

    Args:
        seconds: 秒数

    Returns:
        格式化的时长字符串
    """
    if seconds < 60:
        return f"{seconds:.2f}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.2f}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}小时{minutes}分{secs:.2f}秒"

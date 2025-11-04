#!/usr/bin/env python3
"""
重试管理器
Retry Manager

提供统一的重试逻辑
"""

import asyncio
from typing import Any, Callable, Optional
from loguru import logger


class RetryManager:
    """重试管理器"""

    @staticmethod
    async def retry_async(
        func: Callable,
        *args,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        **kwargs
    ) -> Any:
        """
        异步重试函数

        Args:
            func: 要重试的异步函数
            *args: 函数参数
            max_retries: 最大重试次数
            delay: 初始延迟时间（秒）
            backoff: 退避系数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        last_exception: Optional[Exception] = None
        current_delay = delay

        for attempt in range(max_retries):
            try:
                result = await func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"重试成功 (第{attempt + 1}次尝试)")
                return result

            except Exception as e:
                last_exception = e
                logger.warning(f"执行失败 (第{attempt + 1}次尝试): {e}")

                if attempt < max_retries - 1:
                    logger.info(f"等待 {current_delay:.1f}秒后重试...")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

        logger.error(f"重试失败，已达到最大重试次数 ({max_retries})")
        raise last_exception

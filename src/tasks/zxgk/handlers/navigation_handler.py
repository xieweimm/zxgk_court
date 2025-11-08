#!/usr/bin/env python3
"""
页面导航处理器
Navigation Handler

负责页面导航和 502 错误处理
"""

import asyncio
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from src.core.automation_engine import AutomationEngine


class NavigationHandler:
    """页面导航处理器"""

    def __init__(self, max_retries: int = 5, retry_delay: float = 3.0):
        """
        初始化导航处理器

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.page_load_status = None  # 记录页面加载的HTTP状态
        self.captcha_status = None  # 记录验证码接口的HTTP状态

    async def navigate_with_retry(
        self, automation_engine: "AutomationEngine", url: str
    ) -> bool:
        """
        导航到指定 URL 并处理 502 错误和首次加载失败

        Args:
            automation_engine: 自动化引擎
            url: 目标 URL

        Returns:
            是否成功加载页面
        """
        # 设置网络监听器（同时监听主页面和验证码接口）
        await self._setup_network_listener(automation_engine, url)

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"尝试导航到页面 (第 {attempt}/{self.max_retries} 次): {url}")

                # 重置状态
                self.page_load_status = None

                # 导航到页面
                success = await automation_engine.navigate_to_url(url)

                if not success:
                    logger.warning(f"导航失败 (第 {attempt}/{self.max_retries} 次)")
                    if attempt < self.max_retries:
                        logger.info(f"等待 {self.retry_delay} 秒后重试...")
                        await asyncio.sleep(self.retry_delay)
                        continue
                    else:
                        logger.error("达到最大重试次数，导航失败")
                        return False

                # 等待页面加载和HTTP响应
                logger.info("等待页面加载和HTTP响应...")
                await asyncio.sleep(2)

                # 等待页面主请求的响应（最多等待5秒）
                for _ in range(50):  # 50次 * 0.1秒 = 5秒
                    if self.page_load_status is not None:
                        logger.debug(f"检测到页面HTTP响应状态: {self.page_load_status}")
                        break
                    await asyncio.sleep(0.1)

                # 获取当前 URL
                current_url = await automation_engine.get_current_url()
                logger.info(f"当前页面 URL: {current_url}")

                # 检查HTTP状态码
                if self.page_load_status == 200:
                    logger.info(f"页面HTTP状态: {self.page_load_status} - 加载成功")

                    # 额外等待页面渲染
                    await asyncio.sleep(1)

                    # 验证关键元素是否存在
                    page_content = await automation_engine.page.content()
                    if "captchaImg" in page_content or "pCardNum" in page_content:
                        logger.info("页面关键元素已加载")
                        return True
                    else:
                        logger.warning("页面HTTP状态200但关键元素未加载，尝试刷新")

                        # 重置页面状态，准备监听reload后的请求
                        self.page_load_status = None

                        await automation_engine.page.reload(wait_until="domcontentloaded", timeout=60000)
                        await asyncio.sleep(2)

                        page_content = await automation_engine.page.content()
                        if "captchaImg" in page_content or "pCardNum" in page_content:
                            logger.info("刷新后页面加载成功")
                            return True

                elif self.page_load_status == 502:
                    logger.warning(f"检测到 502 错误")
                else:
                    logger.warning(f"页面HTTP状态异常: {self.page_load_status}")

                # 加载失败，准备重试
                if attempt < self.max_retries:
                    logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("达到最大重试次数")
                    return False

            except Exception as e:
                logger.error(f"导航失败 (第 {attempt}/{self.max_retries} 次): {e}")

                if attempt < self.max_retries:
                    logger.info(f"等待 {self.retry_delay} 秒后重试...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error("达到最大重试次数，导航失败")
                    return False

        logger.error("页面加载失败，所有重试均失败")
        return False

    async def _setup_network_listener(
        self, automation_engine: "AutomationEngine", target_url: str
    ) -> None:
        """
        设置网络监听器，同时监听主页面和验证码接口

        Args:
            automation_engine: 自动化引擎
            target_url: 目标URL
        """
        try:
            # 提取目标URL的路径部分用于匹配
            target_path = target_url.split("?")[0]  # 移除查询参数

            async def handle_response(response):
                # 监听主页面请求
                response_url = response.url.split("?")[0]
                if target_path in response_url:
                    self.page_load_status = response.status
                    logger.debug(f"页面主请求响应: {response.url} - 状态码: {response.status}")

                # 同时监听验证码接口
                if "captcha.do" in response.url:
                    self.captcha_status = response.status
                    logger.debug(f"验证码接口响应: {response.url} - 状态码: {response.status}")

            # 注册响应监听器
            automation_engine.page.on("response", handle_response)
            logger.debug("页面导航和验证码网络监听器已设置")

        except Exception as e:
            logger.warning(f"设置网络监听器失败: {e}")

    async def _check_502_error(self, automation_engine: "AutomationEngine") -> bool:
        """
        检查页面是否为 502 错误

        Args:
            automation_engine: 自动化引擎

        Returns:
            是否为 502 错误页面
        """
        try:
            # 检查页面标题是否包含 "502"
            title = await automation_engine.page.title()
            if "502" in title:
                logger.debug(f"检测到 502 错误 - 页面标题: {title}")
                return True

            # 检查页面内容是否包含 502 错误提示
            page_content = await automation_engine.page.content()
            error_indicators = [
                "502 Bad Gateway",
                "502错误",
                "服务器错误",
                "Bad Gateway",
            ]

            for indicator in error_indicators:
                if indicator in page_content:
                    logger.debug(f"检测到 502 错误 - 包含关键字: {indicator}")
                    return True

            # 不再检查表单元素是否存在，避免误判
            # 页面正常加载时元素可能还未渲染完成
            return False

        except Exception as e:
            logger.error(f"检查 502 错误时出错: {e}")
            return True  # 出错时视为需要重试

    async def wait_for_page_ready(
        self, automation_engine: "AutomationEngine", timeout: float = 30.0
    ) -> bool:
        """
        等待页面完全加载

        Args:
            automation_engine: 自动化引擎
            timeout: 超时时间（秒）

        Returns:
            是否加载成功
        """
        try:
            # 等待关键元素出现
            result = await automation_engine.wait_for_element(
                "//input[@id='pCardNum']", timeout=int(timeout)
            )
            if result:
                logger.info("页面关键元素已加载")
                return True
            else:
                logger.error("页面关键元素加载超时")
                return False

        except Exception as e:
            logger.error(f"等待页面加载失败: {e}")
            return False

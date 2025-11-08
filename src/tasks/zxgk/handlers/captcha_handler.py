#!/usr/bin/env python3
"""
验证码识别处理器
Captcha Handler

负责验证码图片下载和 OCR 识别
"""

import asyncio
import base64
import random
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from loguru import logger

# Pillow兼容性补丁：为新版本Pillow添加ANTIALIAS别名
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
except Exception as e:
    logger.warning(f"Pillow兼容性补丁失败: {e}")

try:
    import ddddocr
    DDDDOCR_AVAILABLE = True
except ImportError:
    DDDDOCR_AVAILABLE = False
    logger.warning("ddddocr 未安装，验证码识别功能不可用")

if TYPE_CHECKING:
    from src.core.automation_engine import AutomationEngine


class CaptchaHandler:
    """验证码识别处理器"""

    def __init__(self, max_attempts: int = 100, ocr_engine: str = "ddddocr", navigation_handler=None):
        """
        初始化验证码处理器

        Args:
            max_attempts: 最大识别尝试次数（默认100次）
            ocr_engine: OCR 引擎类型（目前仅支持 ddddocr）
            navigation_handler: 导航处理器（用于共享验证码状态）
        """
        self.max_attempts = max_attempts
        self.ocr_engine = ocr_engine
        self.ocr = None
        self.navigation_handler = navigation_handler  # 引用导航处理器获取验证码状态

        # 初始化 OCR 引擎
        if ocr_engine == "ddddocr" and DDDDOCR_AVAILABLE:
            try:
                self.ocr = ddddocr.DdddOcr()
                logger.info("ddddocr 初始化成功")
            except Exception as e:
                logger.error(f"ddddocr 初始化失败: {e}")
        else:
            logger.warning(f"OCR 引擎 {ocr_engine} 不可用")

    async def recognize_captcha(
        self,
        automation_engine: "AutomationEngine",
        captcha_img_xpath: str = "//img[@id='captchaImg']",
    ) -> Optional[str]:
        """
        识别验证码

        Args:
            automation_engine: 自动化引擎
            captcha_img_xpath: 验证码图片的 XPath

        Returns:
            识别结果，失败返回 None
        """
        if not self.ocr:
            logger.error("OCR 引擎未初始化")
            return None

        # 不再设置监听器，使用navigation_handler已设置的监听器
        logger.debug("使用navigation_handler的验证码状态监听")

        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(f"开始识别验证码 (第 {attempt}/{self.max_attempts} 次)")

                # 获取验证码图片（bytes格式）
                captcha_image_bytes = await self._get_captcha_image(
                    automation_engine, captcha_img_xpath
                )

                if not captcha_image_bytes:
                    logger.warning(f"获取验证码图片失败 (第 {attempt}/{self.max_attempts} 次)")

                    # 刷新验证码
                    await self._refresh_captcha(automation_engine, captcha_img_xpath)
                    continue

                # 转换为base64编码
                captcha_base64 = base64.b64encode(captcha_image_bytes).decode('utf-8')
                logger.info(f"验证码截图已转换为base64 (长度: {len(captcha_base64)} 字符)")
                logger.debug(f"验证码base64前100字符: {captcha_base64[:100]}...")

                # OCR 识别（ddddocr可以直接识别bytes）
                result = self.ocr.classification(captcha_image_bytes)
                logger.info(f"OCR识别原始结果: '{result}'")

                # 清理识别结果
                result = self._clean_captcha_result(result)
                logger.info(f"OCR识别清理后结果: '{result}'")

                if result and len(result) >= 4:  # 假设验证码至少4位
                    logger.info(f"✓ 验证码识别成功: {result}")
                    return result
                else:
                    logger.warning(f"✗ 验证码识别结果无效: '{result}' (长度: {len(result) if result else 0}, 要求至少4位) (第 {attempt}/{self.max_attempts} 次)")

                    # 刷新验证码
                    await self._refresh_captcha(automation_engine, captcha_img_xpath)

            except Exception as e:
                logger.error(f"验证码识别失败 (第 {attempt}/{self.max_attempts} 次): {e}")

                if attempt < self.max_attempts:
                    await self._refresh_captcha(automation_engine, captcha_img_xpath)

        logger.error("验证码识别失败，已达最大尝试次数")
        return None

    async def _get_captcha_image(
        self,
        automation_engine: "AutomationEngine",
        captcha_img_xpath: str,
    ) -> Optional[bytes]:
        """
        获取验证码图片数据

        Args:
            automation_engine: 自动化引擎
            captcha_img_xpath: 验证码图片 XPath

        Returns:
            图片字节数据
        """
        try:
            # 等待验证码图片元素存在
            result = await automation_engine.wait_for_element(captcha_img_xpath, timeout=10)
            if not result:
                logger.error("验证码图片元素加载超时")
                return None

            # 获取图片元素
            img_element = automation_engine.page.locator(captcha_img_xpath).first

            # 等待一下让网络监听器有机会捕获验证码接口响应
            if self.navigation_handler and self.navigation_handler.captcha_status is None:
                logger.debug("等待验证码接口响应...")
                for _ in range(20):  # 最多等待2秒
                    if self.navigation_handler.captcha_status is not None:
                        break
                    await asyncio.sleep(0.1)

            # 检查验证码是否已加载成功
            is_loaded = await self._check_captcha_loaded(automation_engine, img_element)

            if is_loaded:
                logger.debug("验证码已加载，直接截取")
            else:
                logger.warning(f"验证码未加载成功 (HTTP状态: {self.navigation_handler.captcha_status if self.navigation_handler else 'N/A'})，点击刷新")

                # 重置状态
                if self.navigation_handler:
                    self.navigation_handler.captcha_status = None

                # 点击刷新验证码
                await img_element.click()

                # 随机等待时间（2秒到5秒之间）
                random_delay = random.uniform(2.0, 5.0)
                logger.debug(f"等待验证码加载，随机延迟: {random_delay:.2f}秒")
                await asyncio.sleep(random_delay)

                # 等待新的验证码接口响应（最多等待3秒）
                for _ in range(30):  # 30次 * 0.1秒 = 3秒
                    if self.navigation_handler and self.navigation_handler.captcha_status == 200:
                        logger.debug("检测到新验证码接口返回200")
                        break
                    await asyncio.sleep(0.1)

                # 再次检查是否加载成功
                is_loaded = await self._check_captcha_loaded(automation_engine, img_element)
                if not is_loaded:
                    logger.error(f"验证码刷新后仍未加载成功 (HTTP状态: {self.navigation_handler.captcha_status if self.navigation_handler else 'N/A'})")
                    return None

            # 截取验证码图片
            screenshot = await img_element.screenshot()

            logger.debug(f"验证码图片已截取，大小: {len(screenshot)} 字节")
            return screenshot

        except Exception as e:
            logger.error(f"获取验证码图片失败: {e}")
            return None

    async def _check_captcha_loaded(
        self,
        automation_engine: "AutomationEngine",
        img_element,
    ) -> bool:
        """
        检查验证码是否加载成功
        只通过HTTP状态码判断（从navigation_handler获取）

        Args:
            automation_engine: 自动化引擎
            img_element: 验证码图片元素

        Returns:
            是否加载成功
        """
        try:
            # 从navigation_handler获取验证码状态
            if not self.navigation_handler:
                logger.warning("navigation_handler未设置，无法检查验证码状态")
                return False

            captcha_status = self.navigation_handler.captcha_status

            # 只检查验证码接口的HTTP状态码
            if captcha_status == 200:
                logger.debug(f"验证码接口HTTP状态: 200 - 加载成功")
                return True
            else:
                logger.debug(f"验证码接口HTTP状态: {captcha_status} - 未加载或加载失败")
                return False

        except Exception as e:
            logger.warning(f"检查验证码加载状态失败: {e}")
            return False

    async def _refresh_captcha(
        self,
        automation_engine: "AutomationEngine",
        captcha_img_xpath: str,
    ) -> None:
        """
        刷新验证码

        Args:
            automation_engine: 自动化引擎
            captcha_img_xpath: 验证码图片 XPath
        """
        try:
            logger.info("刷新验证码...")

            # 重置状态
            if self.navigation_handler:
                self.navigation_handler.captcha_status = None

            # 点击验证码图片刷新
            img_element = automation_engine.page.locator(captcha_img_xpath).first
            await img_element.click()

            # 随机等待时间（2秒到5秒之间）
            random_delay = random.uniform(2.0, 5.0)
            logger.debug(f"等待新验证码加载，随机延迟: {random_delay:.2f}秒")
            await asyncio.sleep(random_delay)

            # 等待新的验证码接口响应（最多等待3秒）
            for _ in range(30):  # 30次 * 0.1秒 = 3秒
                if self.navigation_handler and self.navigation_handler.captcha_status == 200:
                    logger.debug("检测到新验证码接口返回200")
                    break
                await asyncio.sleep(0.1)

            if not self.navigation_handler or self.navigation_handler.captcha_status != 200:
                logger.warning(f"验证码刷新后未检测到200状态 (当前状态: {self.navigation_handler.captcha_status if self.navigation_handler else 'N/A'})")
            else:
                logger.debug("验证码已刷新")

        except Exception as e:
            logger.error(f"刷新验证码失败: {e}")

    def _clean_captcha_result(self, result: str) -> str:
        """
        清理验证码识别结果

        Args:
            result: 原始识别结果

        Returns:
            清理后的结果
        """
        if not result:
            return ""

        # 移除空格和特殊字符
        result = result.strip()
        result = "".join(c for c in result if c.isalnum())

        return result

    async def manual_input_captcha(
        self, automation_engine: "AutomationEngine"
    ) -> Optional[str]:
        """
        人工输入验证码（备用方案）

        Args:
            automation_engine: 自动化引擎

        Returns:
            用户输入的验证码
        """
        logger.warning("自动识别失败，需要人工输入验证码")

        # TODO: 实现人工输入界面（可以通过 GUI 弹窗实现）
        # 这里暂时返回 None，后续集成 GUI 时实现

        return None

#!/usr/bin/env python3
"""
表单处理器
Form Handler

负责表单填写和提交
"""

import asyncio
from typing import TYPE_CHECKING, Optional, Dict, Any

from loguru import logger

if TYPE_CHECKING:
    from src.core.automation_engine import AutomationEngine


class FormHandler:
    """表单处理器"""

    def __init__(
        self,
        id_input_xpath: str = "//input[@id='pCardNum']",
        captcha_input_xpath: str = "//input[@id='yzm']",
        submit_btn_xpath: str = "//button[contains(.,'查询')]",
    ):
        """
        初始化表单处理器

        Args:
            id_input_xpath: 身份证号输入框 XPath
            captcha_input_xpath: 验证码输入框 XPath
            submit_btn_xpath: 提交按钮 XPath
        """
        self.id_input_xpath = id_input_xpath
        self.captcha_input_xpath = captcha_input_xpath
        self.submit_btn_xpath = submit_btn_xpath

    async def fill_and_submit(
        self,
        automation_engine: "AutomationEngine",
        id_number: str,
        captcha: str,
        name: Optional[str] = None,
    ) -> bool:
        """
        填写表单并提交

        Args:
            automation_engine: 自动化引擎
            id_number: 身份证号
            captcha: 验证码
            name: 姓名（可选，某些页面可能需要）

        Returns:
            是否提交成功
        """
        try:
            logger.info(f"开始填写表单 - 身份证号: {id_number[:6]}****{id_number[-4:]}")

            # 填写身份证号
            success = await self._fill_id_number(automation_engine, id_number)
            if not success:
                logger.error("填写身份证号失败")
                return False

            # 填写验证码
            success = await self._fill_captcha(automation_engine, captcha)
            if not success:
                logger.error("填写验证码失败")
                return False

            # 等待一小段时间，模拟人工操作
            await asyncio.sleep(0.5)

            # 点击提交按钮
            success = await self._click_submit(automation_engine)
            if not success:
                logger.error("点击提交按钮失败")
                return False

            logger.info("表单提交成功")
            return True

        except Exception as e:
            logger.error(f"填写表单失败: {e}")
            return False

    async def _fill_id_number(
        self, automation_engine: "AutomationEngine", id_number: str
    ) -> bool:
        """
        填写身份证号

        Args:
            automation_engine: 自动化引擎
            id_number: 身份证号

        Returns:
            是否成功
        """
        try:
            # 等待输入框出现
            result = await automation_engine.wait_for_element(
                self.id_input_xpath, timeout=10
            )
            if not result:
                logger.error("身份证号输入框加载超时")
                return False

            # 清空输入框
            await automation_engine.page.locator(self.id_input_xpath).first.fill("")

            # 输入身份证号
            await automation_engine.page.locator(self.id_input_xpath).first.fill(
                id_number
            )

            # 验证输入
            input_value = await automation_engine.page.locator(
                self.id_input_xpath
            ).first.input_value()

            if input_value != id_number:
                logger.error(f"身份证号输入验证失败: 期望 {id_number}, 实际 {input_value}")
                return False

            logger.debug("身份证号填写成功")
            return True

        except Exception as e:
            logger.error(f"填写身份证号失败: {e}")
            return False

    async def _fill_captcha(
        self, automation_engine: "AutomationEngine", captcha: str
    ) -> bool:
        """
        填写验证码

        Args:
            automation_engine: 自动化引擎
            captcha: 验证码

        Returns:
            是否成功
        """
        try:
            # 等待输入框出现
            result = await automation_engine.wait_for_element(
                self.captcha_input_xpath, timeout=10
            )
            if not result:
                logger.error("验证码输入框加载超时")
                return False

            # 清空输入框
            await automation_engine.page.locator(self.captcha_input_xpath).first.fill(
                ""
            )

            # 输入验证码
            await automation_engine.page.locator(self.captcha_input_xpath).first.fill(
                captcha
            )

            # 验证输入
            input_value = await automation_engine.page.locator(
                self.captcha_input_xpath
            ).first.input_value()

            if input_value != captcha:
                logger.error(f"验证码输入验证失败: 期望 {captcha}, 实际 {input_value}")
                return False

            logger.debug("验证码填写成功")
            return True

        except Exception as e:
            logger.error(f"填写验证码失败: {e}")
            return False

    async def _click_submit(self, automation_engine: "AutomationEngine") -> bool:
        """
        点击提交按钮

        Args:
            automation_engine: 自动化引擎

        Returns:
            是否成功
        """
        try:
            # 等待按钮出现
            result = await automation_engine.wait_for_element(
                self.submit_btn_xpath, timeout=10
            )
            if not result:
                logger.error("提交按钮加载超时")
                return False

            # 点击按钮
            await automation_engine.page.locator(self.submit_btn_xpath).first.click()

            logger.debug("提交按钮点击成功")
            return True

        except Exception as e:
            logger.error(f"点击提交按钮失败: {e}")
            return False

    async def extract_result(
        self, automation_engine: "AutomationEngine", timeout: float = 10.0
    ) -> Dict[str, Any]:
        """
        提取查询结果

        Args:
            automation_engine: 自动化引擎
            timeout: 等待结果的超时时间（秒）

        Returns:
            查询结果字典
        """
        try:
            logger.info("等待查询结果...")

            # 等待结果加载
            await asyncio.sleep(2)

            # 检查是否有错误提示
            error_message = await self._check_error_message(automation_engine)
            if error_message:
                logger.warning(f"查询返回错误: {error_message}")
                return {
                    "success": False,
                    "error": error_message,
                    "case_count": 0,
                    "details": None,
                }

            # 提取结果数据
            result_data = await self._extract_result_data(automation_engine)

            logger.info(f"查询结果提取完成: {result_data}")
            return result_data

        except Exception as e:
            logger.error(f"提取查询结果失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "case_count": 0,
                "details": None,
            }

    async def _check_error_message(
        self, automation_engine: "AutomationEngine"
    ) -> Optional[str]:
        """
        检查是否有错误提示

        Args:
            automation_engine: 自动化引擎

        Returns:
            错误信息，没有错误返回 None
        """
        try:
            # 常见错误提示的选择器
            error_selectors = [
                "//div[contains(@class, 'error')]",
                "//div[contains(@class, 'alert')]",
                "//span[contains(@class, 'error')]",
                "//div[contains(., '验证码错误')]",
                "//div[contains(., '查询失败')]",
            ]

            for selector in error_selectors:
                error_element = automation_engine.page.locator(selector).first
                if await error_element.count() > 0:
                    error_text = await error_element.text_content()
                    if error_text and error_text.strip():
                        return error_text.strip()

            return None

        except Exception as e:
            logger.debug(f"检查错误信息时出错: {e}")
            return None

    async def _extract_result_data(
        self, automation_engine: "AutomationEngine"
    ) -> Dict[str, Any]:
        """
        提取结果数据

        Args:
            automation_engine: 自动化引擎

        Returns:
            结果数据字典
        """
        try:
            # TODO: 根据实际页面结构提取数据
            # 这里提供一个基础实现，需要根据实际情况调整

            # 检查是否有结果表格
            result_table_xpath = "//table[contains(@class, 'result')]"
            table_count = await automation_engine.page.locator(
                result_table_xpath
            ).count()

            if table_count > 0:
                # 有结果
                # 提取案件数量（示例）
                case_count_text = await automation_engine.page.locator(
                    "//span[contains(., '案件')]"
                ).first.text_content()

                return {
                    "success": True,
                    "error": None,
                    "case_count": self._extract_number(case_count_text),
                    "details": "查询成功，存在执行记录",
                }
            else:
                # 无结果
                return {
                    "success": True,
                    "error": None,
                    "case_count": 0,
                    "details": "查询成功，暂无执行记录",
                }

        except Exception as e:
            logger.error(f"提取结果数据失败: {e}")
            return {
                "success": False,
                "error": f"数据提取失败: {e}",
                "case_count": 0,
                "details": None,
            }

    def _extract_number(self, text: str) -> int:
        """
        从文本中提取数字

        Args:
            text: 文本

        Returns:
            提取的数字
        """
        import re

        if not text:
            return 0

        numbers = re.findall(r"\d+", text)
        return int(numbers[0]) if numbers else 0

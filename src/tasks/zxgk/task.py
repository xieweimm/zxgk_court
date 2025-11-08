#!/usr/bin/env python3
"""
ZXGK 被执行人查询任务
ZXGK Query Task

负责执行批量被执行人查询
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from loguru import logger

from src.tasks.base_task import BaseTask, TaskStatus, TaskResult
from .handlers.excel_handler import ExcelHandler
from .handlers.navigation_handler import NavigationHandler
from .handlers.captcha_handler import CaptchaHandler
from .handlers.form_handler import FormHandler

if TYPE_CHECKING:
    from src.core.automation_engine import AutomationEngine


class ZXGKQueryTask(BaseTask):
    """ZXGK 被执行人查询任务"""

    def __init__(
        self,
        task_id: str,
        config: dict,
        excel_path: str,
        output_path: Optional[str] = None,
    ):
        """
        初始化任务

        Args:
            task_id: 任务ID
            config: 配置字典
            excel_path: Excel 文件路径
            output_path: 结果输出路径（可选）
        """
        super().__init__(task_id, "ZXGK 被执行人查询", config)

        self.excel_path = excel_path
        self.output_path = output_path or self._generate_output_path()

        # 从配置中获取参数
        zxgk_config = config.get("zxgk", {})
        self.url = zxgk_config.get("url", "https://zxgk.court.gov.cn/zhzxgk/")

        # 初始化处理器
        excel_config = zxgk_config.get("excel", {})
        self.excel_handler = ExcelHandler(
            id_column=excel_config.get("id_column", "身份证号码"),
            name_column=excel_config.get("name_column", "姓名"),
        )

        retry_config = zxgk_config.get("retry", {})
        self.navigation_handler = NavigationHandler(
            max_retries=retry_config.get("max_retries", 5),
            retry_delay=retry_config.get("retry_delay", 3.0),
        )

        captcha_config = zxgk_config.get("captcha", {})
        self.captcha_handler = CaptchaHandler(
            max_attempts=captcha_config.get("max_attempts", 100),
            ocr_engine=captcha_config.get("ocr_engine", "ddddocr"),
            navigation_handler=self.navigation_handler,  # 传入navigation_handler以共享验证码状态
        )

        selectors = zxgk_config.get("selectors", {})
        self.form_handler = FormHandler(
            id_input_xpath=selectors.get("id_input", "//input[@id='pCardNum']"),
            captcha_input_xpath=selectors.get("captcha_input", "//input[@id='yzm']"),
            submit_btn_xpath=selectors.get("submit_btn", "//button[contains(.,'查询')]"),
        )

        # 任务状态
        self.query_data: List[Dict[str, str]] = []
        self.results: List[Dict[str, Any]] = []
        self.current_index: int = 0
        self.total_count: int = 0

    def _generate_output_path(self) -> str:
        """生成输出文件路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(__file__).parent.parent.parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        return str(output_dir / f"zxgk_result_{timestamp}.xlsx")

    async def execute(self, automation_engine: "AutomationEngine") -> TaskResult:
        """
        执行任务

        Args:
            automation_engine: 自动化引擎

        Returns:
            任务执行结果
        """
        try:
            logger.info(f"开始执行 ZXGK 查询任务 - Excel: {self.excel_path}")

            # 检查自动化引擎状态
            if not automation_engine:
                logger.error("自动化引擎为 None")
                return TaskResult(TaskStatus.FAILED, "自动化引擎未初始化")

            if not automation_engine.page:
                logger.error("自动化引擎页面对象为 None")
                return TaskResult(TaskStatus.FAILED, "浏览器页面未创建")

            logger.info(f"自动化引擎状态正常 - is_running: {automation_engine.is_running}")

            # 步骤 1: 解析 Excel
            logger.info("步骤 1/4: 解析 Excel 文件")
            self.query_data = self.excel_handler.parse_excel(self.excel_path)
            self.total_count = len(self.query_data)

            if self.total_count == 0:
                return TaskResult(
                    TaskStatus.FAILED,
                    "Excel 文件中没有有效数据",
                )

            logger.info(f"成功解析 {self.total_count} 条查询数据")

            # 步骤 2: 导航到查询页面
            logger.info(f"步骤 2/4: 导航到查询页面 - {self.url}")
            success = await self.navigation_handler.navigate_with_retry(
                automation_engine, self.url
            )

            if not success:
                return TaskResult(
                    TaskStatus.FAILED,
                    "无法访问查询页面（多次 502 错误）",
                )

            # 等待页面准备就绪
            success = await self.navigation_handler.wait_for_page_ready(
                automation_engine
            )

            if not success:
                return TaskResult(
                    TaskStatus.FAILED,
                    "页面加载超时",
                )

            # 步骤 3: 循环查询
            for index, data in enumerate(self.query_data, start=1):
                # 检查是否应该停止
                if not self.should_continue():
                    logger.warning("任务被停止，终止查询")
                    break

                self.current_index = index

                logger.info(
                    f"开始查询 ({index}/{self.total_count}): "
                    f"{data['name']} - {data['id_number'][:6]}****{data['id_number'][-4:]}"
                )

                # 查询单条数据
                result = await self._query_single(automation_engine, data)

                # 保存结果
                self.results.append(result)

                # 更新进度
                self._update_progress(index, self.total_count)

                # 添加延迟，避免请求过快
                if index < self.total_count:
                    # 分段等待，以便能够快速响应停止信号
                    for _ in range(6):  # 6次 * 0.5秒 = 3秒
                        if not self.should_continue():
                            logger.warning("任务被停止，终止查询")
                            break
                        await asyncio.sleep(0.5)

            # 步骤 4: 导出结果
            self._export_results()

            # 判断任务是否被停止
            if not self.should_continue():
                logger.info(f"查询任务被停止 - 已完成: {len(self.results)}/{self.total_count}")
                return TaskResult(
                    TaskStatus.CANCELLED,
                    f"任务已停止: 已完成 {len(self.results)}/{self.total_count} 条查询",
                    data={
                        "total": self.total_count,
                        "completed": len(self.results),
                        "success": self._count_success(),
                        "failed": len(self.results) - self._count_success(),
                        "output_path": self.output_path,
                    },
                )

            logger.info(f"查询任务完成 - 成功: {self._count_success()}/{self.total_count}")

            return TaskResult(
                TaskStatus.SUCCESS,
                f"查询完成: {self._count_success()}/{self.total_count} 成功",
                data={
                    "total": self.total_count,
                    "success": self._count_success(),
                    "failed": self.total_count - self._count_success(),
                    "output_path": self.output_path,
                },
            )

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            return TaskResult(TaskStatus.FAILED, str(e), error=e)

    async def _query_single(
        self, automation_engine: "AutomationEngine", data: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        查询单条数据

        Args:
            automation_engine: 自动化引擎
            data: 查询数据

        Returns:
            查询结果
        """
        result = {
            "姓名": data["name"],
            "身份证号": data["id_number"],
            "查询时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "状态": "失败",
            "案件数量": 0,
            "详情": None,
        }

        try:
            # 检查是否应该停止
            if not self.should_continue():
                result["详情"] = "任务已停止"
                return result

            # 识别验证码
            captcha = await self.captcha_handler.recognize_captcha(
                automation_engine,
                self.form_handler.captcha_input_xpath.replace(
                    "//input[@id='yzm']", "//img[@id='captchaImg']"
                ),
            )

            if not captcha:
                result["详情"] = "验证码识别失败"
                return result

            # 再次检查是否应该停止
            if not self.should_continue():
                result["详情"] = "任务已停止"
                return result

            # 填写并提交表单
            success = await self.form_handler.fill_and_submit(
                automation_engine, data["id_number"], captcha, data["name"]
            )

            if not success:
                result["详情"] = "表单提交失败"
                return result

            # 检查是否应该停止
            if not self.should_continue():
                result["详情"] = "任务已停止"
                return result

            # 提取查询结果
            query_result = await self.form_handler.extract_result(automation_engine)

            if query_result["success"]:
                result["状态"] = "成功"
                result["案件数量"] = query_result["case_count"]
                result["详情"] = query_result["details"]
            else:
                result["详情"] = query_result["error"]

        except Exception as e:
            logger.error(f"查询失败: {e}")
            result["详情"] = f"查询异常: {str(e)}"

        return result

    def _export_results(self) -> None:
        """导出查询结果"""
        try:
            logger.info(f"导出结果到: {self.output_path}")

            self.excel_handler.export_results(
                self.results,
                self.output_path,
                columns=["姓名", "身份证号", "查询时间", "状态", "案件数量", "详情"],
            )

            logger.info("结果导出成功")

        except Exception as e:
            logger.error(f"导出结果失败: {e}")

    def _count_success(self) -> int:
        """统计成功数量"""
        return sum(1 for r in self.results if r["状态"] == "成功")

    def _update_progress(self, current: int, total: int) -> None:
        """
        更新进度

        Args:
            current: 当前进度
            total: 总数
        """
        progress = (current / total) * 100
        logger.info(f"进度: {current}/{total} ({progress:.1f}%)")

        # TODO: 通过回调函数更新 GUI 进度条

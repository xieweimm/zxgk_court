#!/usr/bin/env python3
"""
步骤执行器
Step Executor

执行配置化的任务步骤
"""

from typing import Any, Dict
from loguru import logger

from ...core.schemas import StepConfig


class StepExecutor:
    """步骤执行器"""

    def __init__(self):
        """初始化步骤执行器"""
        logger.info("步骤执行器初始化完成")

    async def execute_step(
        self,
        step_config: StepConfig,
        automation_engine: Any,
        handler: Any
    ) -> dict[str, Any]:
        """
        执行单个步骤

        Args:
            step_config: 步骤配置（StepConfig 对象）
            automation_engine: 自动化引擎实例
            handler: 处理器实例

        Returns:
            执行结果

        Raises:
            AttributeError: 如果处理器没有指定的方法
        """
        step_name = step_config.name
        logger.info(f"执行步骤: {step_name} (ID: {step_config.step_id})")

        try:
            # 获取处理方法
            method_name = step_config.method
            if not hasattr(handler, method_name):
                raise AttributeError(f"处理器 {handler.__class__.__name__} 没有方法: {method_name}")

            method = getattr(handler, method_name)

            # 执行方法
            result = await method(*step_config.args, **step_config.kwargs)

            logger.info(f"步骤执行成功: {step_name}")
            return {"success": True, "data": result}

        except Exception as e:
            logger.error(f"步骤执行失败: {step_name}, 错误: {e}")
            return {"success": False, "error": str(e)}

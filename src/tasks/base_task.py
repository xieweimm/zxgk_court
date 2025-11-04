#!/usr/bin/env python3
"""
任务基类
Base Task Class

所有自动化任务的基类，定义统一的任务接口
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from ..core.automation_engine import AutomationEngine
    from ..core.schemas import Config


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    SUCCESS = "success"  # 执行成功
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消
    TIMEOUT = "timeout"  # 超时


class TaskResult:
    """任务执行结果"""

    def __init__(
        self,
        status: TaskStatus,
        message: str = "",
        data: Optional[dict[str, Any]] = None,
        error: Optional[Exception] = None,
    ):
        self.status = status
        self.message = message
        self.data = data or {}
        self.error = error
        self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "error": str(self.error) if self.error else None,
            "timestamp": self.timestamp.isoformat(),
        }

    @property
    def success(self) -> bool:
        """是否成功"""
        return self.status == TaskStatus.SUCCESS


class BaseTask(ABC):
    """任务基类"""

    def __init__(
        self,
        task_id: str,
        task_name: str,
        config: "Config"
    ):
        """
        初始化任务

        Args:
            task_id: 任务ID
            task_name: 任务名称
            config: 任务配置（Config 对象）
        """
        self.task_id = task_id
        self.task_name = task_name
        self.config = config
        self.status = TaskStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        logger.info(f"任务初始化: {self.task_name} (ID: {self.task_id})")

    @abstractmethod
    async def execute(self, automation_engine: "AutomationEngine") -> TaskResult:
        """
        执行任务（抽象方法，由子类实现）

        Args:
            automation_engine: 自动化引擎实例

        Returns:
            任务执行结果
        """
        pass

    async def run(self, automation_engine: "AutomationEngine") -> TaskResult:
        """
        运行任务（包含状态管理和异常处理）

        Args:
            automation_engine: 自动化引擎实例

        Returns:
            任务执行结果
        """
        self.start_time = datetime.now()
        self.status = TaskStatus.RUNNING

        logger.info(f"开始执行任务: {self.task_name}")

        try:
            result = await self.execute(automation_engine)
            self.status = result.status
            self.end_time = datetime.now()

            duration = (self.end_time - self.start_time).total_seconds()
            logger.info(f"任务执行完成: {self.task_name}, 状态: {result.status.value}, 耗时: {duration:.2f}秒")

            return result

        except asyncio.TimeoutError:
            self.status = TaskStatus.TIMEOUT
            self.end_time = datetime.now()
            logger.error(f"任务超时: {self.task_name}")
            return TaskResult(TaskStatus.TIMEOUT, "任务执行超时")

        except Exception as e:
            self.status = TaskStatus.FAILED
            self.end_time = datetime.now()
            logger.error(f"任务执行失败: {self.task_name}, 错误: {e}")
            return TaskResult(TaskStatus.FAILED, f"任务执行失败: {str(e)}", error=e)

    def get_duration(self) -> float:
        """获取任务执行时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration(),
        }

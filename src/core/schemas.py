#!/usr/bin/env python3
"""
配置模式定义
Configuration Schemas

使用 dataclass 定义配置结构，提供类型安全和自动验证
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ViewportConfig:
    """视口配置"""
    width: int = 1280
    height: int = 720


@dataclass
class BrowserConfig:
    """浏览器配置"""
    type: str = "chromium"  # chromium, firefox, webkit
    headless: bool = False
    timeout: int = 30  # 默认超时时间（秒）
    slow_mo: int = 0  # 慢动作延迟（毫秒）
    viewport: ViewportConfig = field(default_factory=ViewportConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "BrowserConfig":
        """从字典创建配置对象"""
        viewport_data = data.get("viewport", {})
        viewport = ViewportConfig(**viewport_data) if viewport_data else ViewportConfig()

        return cls(
            type=data.get("type", "chromium"),
            headless=data.get("headless", False),
            timeout=data.get("timeout", 30),
            slow_mo=data.get("slow_mo", 0),
            viewport=viewport
        )


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    console: bool = True
    file: bool = True
    rotation: str = "00:00"  # 日志轮转时间
    retention: str = "30 days"  # 日志保留时间

    @classmethod
    def from_dict(cls, data: dict) -> "LoggingConfig":
        """从字典创建配置对象"""
        return cls(
            level=data.get("level", "INFO"),
            console=data.get("console", True),
            file=data.get("file", True),
            rotation=data.get("rotation", "00:00"),
            retention=data.get("retention", "30 days")
        )


@dataclass
class TaskConfig:
    """任务配置"""
    max_retries: int = 3
    retry_delay: float = 2.0
    concurrent_limit: int = 5

    @classmethod
    def from_dict(cls, data: dict) -> "TaskConfig":
        """从字典创建配置对象"""
        return cls(
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 2.0),
            concurrent_limit=data.get("concurrent_limit", 5)
        )


@dataclass
class AppConfig:
    """应用配置"""
    name: str = "ZXGK Court Automation Tool"
    version: str = "1.0.0"
    build: int = 1
    theme: str = "default"

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        """从字典创建配置对象"""
        return cls(
            name=data.get("name", "ZXGK Court Automation Tool"),
            version=data.get("version", "1.0.0"),
            build=data.get("build", 1),
            theme=data.get("theme", "default")
        )


@dataclass
class Config:
    """总配置"""
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    task: TaskConfig = field(default_factory=TaskConfig)
    app: AppConfig = field(default_factory=AppConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """从字典创建配置对象"""
        return cls(
            browser=BrowserConfig.from_dict(data.get("browser", {})),
            logging=LoggingConfig.from_dict(data.get("logging", {})),
            task=TaskConfig.from_dict(data.get("task", {})),
            app=AppConfig.from_dict(data.get("app", {}))
        )


# ==================== 步骤配置 ====================


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    retry_delay: float = 2.0

    @classmethod
    def from_dict(cls, data: dict) -> "RetryConfig":
        """从字典创建配置对象"""
        return cls(
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 2.0)
        )


@dataclass
class StepConfig:
    """步骤配置"""
    step_id: str
    name: str
    handler: str
    method: str
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    success_criteria: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "StepConfig":
        """
        从字典创建步骤配置对象

        Args:
            data: 步骤配置字典

        Returns:
            StepConfig 对象

        Raises:
            KeyError: 如果缺少必需字段
            TypeError: 如果字段类型不正确
        """
        # 验证必需字段
        required_fields = ["step_id", "name", "handler", "method"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise KeyError(f"步骤配置缺少必需字段: {', '.join(missing_fields)}")

        # 解析重试配置
        retry_data = data.get("retry_config", {})
        retry_config = RetryConfig.from_dict(retry_data) if retry_data else RetryConfig()

        return cls(
            step_id=data["step_id"],
            name=data["name"],
            handler=data["handler"],
            method=data["method"],
            args=data.get("args", []),
            kwargs=data.get("kwargs", {}),
            retry_config=retry_config,
            success_criteria=data.get("success_criteria", {}),
            description=data.get("description", "")
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "handler": self.handler,
            "method": self.method,
            "args": self.args,
            "kwargs": self.kwargs,
            "retry_config": {
                "max_retries": self.retry_config.max_retries,
                "retry_delay": self.retry_config.retry_delay
            },
            "success_criteria": self.success_criteria,
            "description": self.description
        }

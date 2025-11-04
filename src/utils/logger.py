#!/usr/bin/env python3
"""
日志工具
Logger Utility

基于loguru的日志配置
"""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: Path = None, log_level: str = "INFO"):
    """
    配置日志系统

    Args:
        log_dir: 日志文件目录
        log_level: 日志级别
    """
    if log_dir is None:
        # 默认使用项目根目录下的logs目录
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"

    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)

    # 移除默认的handler
    logger.remove()

    # 添加控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # 添加文件输出
    logger.add(
        log_dir / "{time:YYYY-MM-DD}_gui_system.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="00:00",  # 每天轮转
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
        encoding="utf-8",
    )

    logger.info("日志系统初始化完成")

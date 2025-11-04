#!/usr/bin/env python3
"""
配置管理器
Configuration Manager

负责加载和管理应用程序配置
"""

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from loguru import logger

from .schemas import Config, StepConfig


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化配置管理器

        Args:
            config_dir: 配置文件目录路径
        """
        if config_dir is None:
            # 默认使用项目根目录下的config目录
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"

        self.config_dir = Path(config_dir)
        self._typed_config: Optional[Config] = None  # 缓存类型化配置

        logger.info(f"配置管理器初始化 - 配置目录: {self.config_dir}")

    def _load_yaml(self, config_name: str) -> dict[str, Any]:
        """
        加载 YAML 配置文件（内部方法）

        Args:
            config_name: 配置文件名（不含扩展名）或完整路径

        Returns:
            配置字典
        """
        try:
            # 检查是否是完整路径
            if os.path.isabs(config_name):
                config_path = Path(config_name)
            else:
                # 尝试加载.yaml或.yml文件
                config_path = self.config_dir / f"{config_name}.yaml"
                if not config_path.exists():
                    config_path = self.config_dir / f"{config_name}.yml"

            if not config_path.exists():
                logger.warning(f"配置文件不存在: {config_path}")
                return {}

            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            logger.info(f"成功加载配置: {config_path}")
            return config

        except Exception as e:
            logger.error(f"加载配置失败 {config_name}: {e}")
            return {}

    def get_config(self) -> Config:
        """
        获取类型化的配置对象（主配置文件）

        Returns:
            Config 对象，包含类型安全的配置访问

        Raises:
            ValueError: 如果配置加载或解析失败
        """
        if self._typed_config is not None:
            return self._typed_config

        try:
            # 加载主配置文件
            config_dict = self._load_yaml("config")
            if not config_dict:
                logger.warning("配置文件为空，使用默认配置")
                self._typed_config = Config()
                return self._typed_config

            # 转换为类型化配置
            self._typed_config = Config.from_dict(config_dict)
            logger.info("类型化配置加载成功")
            return self._typed_config

        except Exception as e:
            logger.error(f"加载类型化配置失败: {e}")
            raise ValueError(f"配置解析失败: {e}") from e

    def save_config(self, config_name: str, config: dict[str, Any]):
        """
        保存配置文件

        Args:
            config_name: 配置文件名
            config: 配置字典
        """
        try:
            config_path = self.config_dir / f"{config_name}.yaml"

            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

            logger.info(f"配置已保存: {config_path}")

        except Exception as e:
            logger.error(f"保存配置失败 {config_name}: {e}")

    def load_step_config(self, step_data: dict) -> StepConfig:
        """
        加载并验证步骤配置

        Args:
            step_data: 步骤配置字典

        Returns:
            StepConfig 对象

        Raises:
            KeyError: 如果缺少必需字段
            TypeError: 如果字段类型不正确
        """
        try:
            return StepConfig.from_dict(step_data)
        except Exception as e:
            logger.error(f"步骤配置解析失败: {e}")
            raise

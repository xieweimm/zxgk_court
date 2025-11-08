#!/usr/bin/env python3
"""
Excel 数据处理器
Excel Handler

负责解析和验证 Excel 配置文件
"""

import re
from pathlib import Path
from typing import List, Dict, Optional

import pandas as pd
from loguru import logger


class ExcelHandler:
    """Excel 数据处理器"""

    def __init__(self, id_column: str = "身份证号码", name_column: str = "姓名"):
        """
        初始化 Excel 处理器

        Args:
            id_column: 身份证号码列名
            name_column: 姓名列名
        """
        self.id_column = id_column
        self.name_column = name_column

    def parse_excel(self, file_path: str) -> List[Dict[str, str]]:
        """
        解析 Excel 文件

        Args:
            file_path: Excel 文件路径

        Returns:
            包含身份证号和姓名的字典列表

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或缺少必需列
        """
        try:
            # 检查文件是否存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")

            # 读取 Excel 文件
            logger.info(f"开始解析 Excel 文件: {file_path}")
            df = pd.read_excel(file_path)

            # 验证必需列
            missing_columns = []
            if self.id_column not in df.columns:
                missing_columns.append(self.id_column)
            if self.name_column not in df.columns:
                missing_columns.append(self.name_column)

            if missing_columns:
                raise ValueError(f"Excel 文件缺少必需列: {', '.join(missing_columns)}")

            # 提取数据并过滤空行
            data = []
            for index, row in df.iterrows():
                id_number = str(row[self.id_column]).strip()
                name = str(row[self.name_column]).strip()

                # 跳过空行
                if not id_number or id_number == "nan" or not name or name == "nan":
                    logger.debug(f"跳过空行: 行{index + 2}")
                    continue

                # 验证身份证号格式
                if not self._validate_id_number(id_number):
                    logger.warning(f"身份证号格式错误: 行{index + 2}, 身份证号: {id_number}")
                    continue

                data.append({
                    "id_number": id_number,
                    "name": name,
                    "row_index": index + 2,  # Excel 行号（从1开始，标题行为1）
                })

            logger.info(f"成功解析 {len(data)} 条有效数据")
            return data

        except FileNotFoundError:
            raise
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"解析 Excel 文件失败: {e}")
            raise ValueError(f"Excel 文件解析失败: {e}") from e

    def _validate_id_number(self, id_number: str) -> bool:
        """
        验证身份证号格式

        Args:
            id_number: 身份证号

        Returns:
            是否有效
        """
        # 18位身份证号格式：6位地区码 + 8位出生日期 + 3位顺序码 + 1位校验码
        pattern = r"^\d{17}[\dXx]$"
        return bool(re.match(pattern, id_number))

    def export_results(
        self,
        results: List[Dict],
        output_path: str,
        columns: Optional[List[str]] = None
    ) -> None:
        """
        导出查询结果到 Excel

        Args:
            results: 查询结果列表
            output_path: 输出文件路径
            columns: 导出的列名列表（默认全部导出）
        """
        try:
            if not results:
                logger.warning("没有结果可导出")
                return

            df = pd.DataFrame(results)

            # 如果指定了列，只导出这些列
            if columns:
                df = df[columns]

            # 导出到 Excel
            df.to_excel(output_path, index=False)
            logger.info(f"结果已导出到: {output_path}")

        except Exception as e:
            logger.error(f"导出结果失败: {e}")
            raise

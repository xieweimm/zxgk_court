#!/usr/bin/env python3
"""
ZXGK 模块步骤配置
ZXGK Module Configuration

定义查询任务的步骤配置
"""

from typing import List, Dict, Any


def get_steps() -> List[Dict[str, Any]]:
    """
    获取 ZXGK 查询步骤配置

    Returns:
        步骤配置列表
    """
    return [
        {
            "step_id": "nav_01_navigate",
            "name": "导航到查询页面",
            "handler": "navigation_handler",
            "method": "navigate_with_retry",
            "args": [],
            "kwargs": {"url": "https://zxgk.court.gov.cn/zhzxgk/"},
            "retry_config": {
                "max_retries": 5,
                "retry_delay": 3.0,
            },
            "success_criteria": {"wait_time": 2.0},
            "description": "导航到被执行人查询页面，自动处理 502 错误",
        },
        {
            "step_id": "nav_02_wait_ready",
            "name": "等待页面加载",
            "handler": "navigation_handler",
            "method": "wait_for_page_ready",
            "args": [],
            "kwargs": {},
            "retry_config": {
                "max_retries": 3,
                "retry_delay": 2.0,
            },
            "success_criteria": {"timeout": 30.0},
            "description": "等待页面关键元素加载完成",
        },
        {
            "step_id": "captcha_01_recognize",
            "name": "识别验证码",
            "handler": "captcha_handler",
            "method": "recognize_captcha",
            "args": [],
            "kwargs": {},
            "retry_config": {
                "max_retries": 3,
                "retry_delay": 1.0,
            },
            "success_criteria": {},
            "description": "使用 OCR 识别验证码图片",
        },
        {
            "step_id": "form_01_fill_submit",
            "name": "填写并提交表单",
            "handler": "form_handler",
            "method": "fill_and_submit",
            "args": [],
            "kwargs": {
                # id_number 和 captcha 在运行时注入
            },
            "retry_config": {
                "max_retries": 2,
                "retry_delay": 1.0,
            },
            "success_criteria": {},
            "description": "填写身份证号和验证码，提交查询表单",
        },
        {
            "step_id": "form_02_extract_result",
            "name": "提取查询结果",
            "handler": "form_handler",
            "method": "extract_result",
            "args": [],
            "kwargs": {},
            "retry_config": {
                "max_retries": 2,
                "retry_delay": 1.0,
            },
            "success_criteria": {"timeout": 10.0},
            "description": "提取查询结果数据",
        },
    ]


def get_config_template() -> Dict[str, Any]:
    """
    获取 ZXGK 模块配置模板

    Returns:
        配置模板字典
    """
    return {
        "zxgk": {
            "url": "https://zxgk.court.gov.cn/zhzxgk/",
            "captcha_url": "https://zxgk.court.gov.cn/zhzxgk/captcha.do",
            "retry": {
                "max_retries": 5,
                "retry_delay": 3.0,
            },
            "captcha": {
                "max_attempts": 3,
                "ocr_engine": "ddddocr",
            },
            "selectors": {
                "id_input": "//input[@id='pCardNum']",
                "captcha_img": "//img[@id='captchaImg']",
                "captcha_input": "//input[@id='yzm']",
                "submit_btn": "//button[contains(.,'查询')]",
                "result_table": "//table[contains(@class, 'result')]",
            },
            "excel": {
                "id_column": "身份证号码",
                "name_column": "姓名",
                "result_columns": [
                    "姓名",
                    "身份证号",
                    "查询时间",
                    "状态",
                    "案件数量",
                    "详情",
                ],
            },
        }
    }

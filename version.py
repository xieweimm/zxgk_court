#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本信息管理
"""

VERSION = "1.0.0"
BUILD = 1


def get_version():
    """获取版本号"""
    return VERSION


def get_build():
    """获取构建号"""
    return BUILD


def get_version_string():
    """获取完整版本字符串"""
    return f"v{VERSION}+{BUILD}"


if __name__ == "__main__":
    print(get_version_string())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZXGK Court Automation GUI
主界面应用程序
"""

import asyncio
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import Optional

from loguru import logger


class ZXGKCourtAutomationGUI:
    """ZXGK法院自动化工具主界面"""

    def __init__(self):
        """初始化GUI"""
        self.root = tk.Tk()
        self.root.title("ZXGK Court Automation Tool")
        self.root.geometry("1200x800")

        # 设置窗口图标（如果存在）
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
            if icon_path.exists():
                self.root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
        except Exception as e:
            logger.warning(f"无法加载图标: {e}")

        # 初始化UI组件
        self._setup_ui()

        # 配置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        logger.info("GUI界面初始化完成")

    def _setup_ui(self):
        """设置UI布局"""
        # 创建顶部标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(
            title_frame,
            text="ZXGK Court Automation Tool",
            font=("Arial", 20, "bold"),
        )
        title_label.pack()

        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建标签页容器
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 添加示例标签页
        self._create_home_tab()
        self._create_settings_tab()

        # 创建底部状态栏
        self._create_status_bar()

    def _create_home_tab(self):
        """创建主页标签页"""
        home_frame = ttk.Frame(self.notebook)
        self.notebook.add(home_frame, text="主页")

        # 欢迎信息
        welcome_label = ttk.Label(
            home_frame,
            text="欢迎使用 ZXGK Court Automation Tool",
            font=("Arial", 16),
        )
        welcome_label.pack(pady=50)

        info_label = ttk.Label(
            home_frame,
            text="请从上方标签页选择功能模块",
            font=("Arial", 12),
        )
        info_label.pack(pady=20)

    def _create_settings_tab(self):
        """创建设置标签页"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="设置")

        # 浏览器设置
        browser_frame = ttk.LabelFrame(settings_frame, text="浏览器设置", padding=10)
        browser_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(browser_frame, text="浏览器类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        browser_combo = ttk.Combobox(
            browser_frame,
            values=["chromium", "firefox", "webkit"],
            state="readonly",
        )
        browser_combo.set("chromium")
        browser_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(browser_frame, text="无头模式:").grid(row=1, column=0, sticky=tk.W, pady=5)
        headless_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(browser_frame, variable=headless_var).grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)

        # 保存按钮
        save_btn = ttk.Button(
            settings_frame,
            text="保存设置",
            command=lambda: messagebox.showinfo("提示", "设置已保存"),
        )
        save_btn.pack(pady=10)

    def _create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(
            status_frame,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W,
        )
        self.status_label.pack(fill=tk.X, padx=5, pady=2)

    def update_status(self, message: str):
        """更新状态栏信息"""
        self.status_label.config(text=message)
        self.root.update_idletasks()

    def _on_closing(self):
        """处理窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            logger.info("用户关闭程序")
            self.root.destroy()

    def run(self):
        """运行GUI应用"""
        logger.info("启动GUI主循环")
        self.root.mainloop()


if __name__ == "__main__":
    app = ZXGKCourtAutomationGUI()
    app.run()

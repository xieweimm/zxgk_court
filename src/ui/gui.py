#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZXGK Court Automation GUI
主界面应用程序
"""

import asyncio
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Optional
import shutil
import queue

from loguru import logger

from src.core.config_manager import ConfigManager
from src.core.automation_engine import AutomationEngine
from src.tasks.zxgk.task import ZXGKQueryTask
from src.tasks.base_task import TaskStatus
from src.ui.components.log_viewer import LogViewer


class ZXGKCourtAutomationGUI:
    """ZXGK法院自动化工具主界面"""

    def __init__(self):
        """初始化GUI"""
        # 加载配置
        config_manager = ConfigManager()
        config = config_manager.get_config()
        self.config = config

        # 获取版本信息
        version = config.app.version
        build = config.app.build
        title = f"{config.app.name} - v{version}+{build}"

        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("1200x800")

        # Excel 文件路径
        self.excel_path_var = tk.StringVar()

        # 任务执行状态
        self.is_running = False
        self.automation_engine: Optional[AutomationEngine] = None
        self.current_task: Optional[ZXGKQueryTask] = None  # 当前运行的任务

        # 消息队列用于线程间通信
        self.message_queue = queue.Queue()

        # 日志组件
        self.log_viewer: Optional[LogViewer] = None

        # 设置窗口图标（如果存在）
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
            if icon_path.exists():
                self.root.iconphoto(True, tk.PhotoImage(file=str(icon_path)))
        except Exception as e:
            logger.warning(f"无法加载图标: {e}")

        # 初始化UI组件
        self._setup_ui()

        # 启动消息处理器
        self._start_message_processor()

        # 设置日志拦截器
        self._setup_gui_log_handler()

        # 配置关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        logger.info("GUI界面初始化完成")

    def _setup_ui(self):
        """设置UI布局"""
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 配置网格权重
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(0, weight=3)
        main_container.rowconfigure(1, weight=1)

        # 创建标签页容器
        self.notebook = ttk.Notebook(main_container)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))

        # 添加示例标签页
        self._create_home_tab()
        self._create_settings_tab()

        # 创建日志查看器
        self.log_viewer = LogViewer(main_container)
        self.log_viewer.create_ui()

        # 创建底部状态栏
        self._create_status_bar()

    def _create_home_tab(self):
        """创建主页标签页"""
        home_frame = ttk.Frame(self.notebook)
        self.notebook.add(home_frame, text="综合查询被执行人")

        # 主容器
        container = ttk.Frame(home_frame, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Excel 配置区域
        excel_frame = ttk.LabelFrame(container, text="Excel 配置文件", padding=15)
        excel_frame.pack(fill=tk.X, pady=(0, 20))

        # 文件路径输入
        path_frame = ttk.Frame(excel_frame)
        path_frame.pack(fill=tk.X)

        ttk.Label(path_frame, text="文件路径:", width=10).pack(side=tk.LEFT)

        path_entry = ttk.Entry(
            path_frame, textvariable=self.excel_path_var, state="readonly"
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 浏览按钮
        browse_btn = ttk.Button(
            path_frame, text="浏览...", command=self._browse_excel, width=10
        )
        browse_btn.pack(side=tk.LEFT, padx=5)

        # 下载模板按钮
        template_btn = ttk.Button(
            path_frame, text="下载模板", command=self._download_template, width=10
        )
        template_btn.pack(side=tk.LEFT)

        # 控制按钮区域
        control_frame = ttk.Frame(container)
        control_frame.pack(pady=(0, 20))

        # 开始查询按钮
        self.start_btn = ttk.Button(
            control_frame,
            text="开始查询",
            command=self._start_query,
            width=20,
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        # 停止按钮（初始禁用）
        self.stop_btn = ttk.Button(
            control_frame,
            text="停止查询",
            command=self._stop_query,
            state=tk.DISABLED,
            width=20,
        )
        self.stop_btn.pack(side=tk.LEFT)

        # 进度区域
        progress_frame = ttk.LabelFrame(container, text="查询进度", padding=15)
        progress_frame.pack(fill=tk.BOTH, expand=True)

        # 进度条
        self.progress_bar = ttk.Progressbar(
            progress_frame, mode="determinate", length=600
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # 进度信息
        self.progress_label = ttk.Label(progress_frame, text="就绪")
        self.progress_label.pack()

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

    def _browse_excel(self):
        """浏览并选择 Excel 文件"""
        file_path = filedialog.askopenfilename(
            title="选择 Excel 文件",
            filetypes=[
                ("Excel 文件", "*.xlsx *.xls"),
                ("所有文件", "*.*"),
            ],
        )

        if file_path:
            self.excel_path_var.set(file_path)
            logger.info(f"选择 Excel 文件: {file_path}")
            self.update_status(f"已选择文件: {Path(file_path).name}")

    def _download_template(self):
        """下载 Excel 模板"""
        try:
            # 模板文件路径
            template_path = (
                Path(__file__).parent.parent.parent / "templates" / "excel模板.xls"
            )

            if not template_path.exists():
                messagebox.showerror("错误", "模板文件不存在")
                return

            # 让用户选择保存位置
            save_path = filedialog.asksaveasfilename(
                title="保存模板文件",
                defaultextension=".xls",
                initialfile="被执行人查询模板.xls",
                filetypes=[("Excel 文件", "*.xls"), ("所有文件", "*.*")],
            )

            if save_path:
                # 复制模板文件
                shutil.copy(template_path, save_path)
                messagebox.showinfo("成功", f"模板已保存到:\n{save_path}")
                logger.info(f"模板文件已保存: {save_path}")

        except Exception as e:
            logger.error(f"下载模板失败: {e}")
            messagebox.showerror("错误", f"下载模板失败:\n{str(e)}")

    def _start_query(self):
        """开始查询"""
        # 验证 Excel 文件
        excel_path = self.excel_path_var.get()

        if not excel_path:
            messagebox.showwarning("警告", "请先选择 Excel 配置文件")
            return

        if not Path(excel_path).exists():
            messagebox.showerror("错误", "选择的文件不存在")
            return

        # 禁用开始按钮，启用停止按钮
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_running = True

        # 在新线程中执行查询
        import threading

        thread = threading.Thread(target=self._run_query_task, args=(excel_path,))
        thread.daemon = True
        thread.start()

    def _run_query_task(self, excel_path: str):
        """运行查询任务（在线程中执行）"""
        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 执行任务
            loop.run_until_complete(self._execute_query(excel_path))

        except Exception as e:
            logger.error(f"任务执行失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"任务执行失败:\n{str(e)}"))

        finally:
            # 恢复按钮状态
            self.root.after(0, self._on_task_finished)

    async def _execute_query(self, excel_path: str):
        """执行查询任务"""
        try:
            # 更新状态
            self.root.after(0, lambda: self.update_status("正在初始化浏览器..."))
            self.root.after(0, lambda: self.progress_label.config(text="正在初始化浏览器..."))

            # 初始化自动化引擎
            engine_config = {
                "headless": self.config.browser.headless,
                "browser": self.config.browser.type,
                "timeout": self.config.browser.timeout,
                "window_size": f"{self.config.browser.viewport.width},{self.config.browser.viewport.height}",
                "open_devtools": True,  # 打开开发者工具便于调试
            }
            self.automation_engine = AutomationEngine(engine_config)
            init_success = await self.automation_engine.initialize_browser()

            if not init_success:
                raise Exception("浏览器初始化失败")

            logger.info(f"浏览器初始化成功 - 引擎状态: is_running={self.automation_engine.is_running}, page={self.automation_engine.page is not None}")

            # 创建任务（传递完整 config 的字典形式）
            config_dict = {
                "browser": {
                    "type": self.config.browser.type,
                    "headless": self.config.browser.headless,
                    "timeout": self.config.browser.timeout,
                    "slow_mo": self.config.browser.slow_mo,
                    "viewport": {
                        "width": self.config.browser.viewport.width,
                        "height": self.config.browser.viewport.height,
                    },
                },
                "logging": {
                    "level": self.config.logging.level,
                    "console": self.config.logging.console,
                    "file": self.config.logging.file,
                    "rotation": self.config.logging.rotation,
                    "retention": self.config.logging.retention,
                },
                "task": {
                    "max_retries": self.config.task.max_retries,
                    "retry_delay": self.config.task.retry_delay,
                    "concurrent_limit": self.config.task.concurrent_limit,
                },
                "app": {
                    "name": self.config.app.name,
                    "version": self.config.app.version,
                    "build": self.config.app.build,
                    "theme": self.config.app.theme,
                },
            }

            # 加载 zxgk 配置
            config_manager = ConfigManager()
            zxgk_config = config_manager._load_yaml("zxgk")
            config_dict.update(zxgk_config)

            task = ZXGKQueryTask(
                task_id="zxgk_query_001",
                config=config_dict,
                excel_path=excel_path,
            )

            # 保存当前任务引用
            self.current_task = task

            # 执行任务
            result = await task.execute(self.automation_engine)

            # 显示结果
            if result.status == TaskStatus.SUCCESS:
                self.root.after(
                    0,
                    lambda: messagebox.showinfo(
                        "完成",
                        f"查询完成!\n\n{result.message}\n\n结果已保存到:\n{result.data.get('output_path')}",
                    ),
                )
            elif result.status == TaskStatus.CANCELLED:
                self.root.after(
                    0,
                    lambda: messagebox.showwarning(
                        "已停止",
                        f"任务已停止\n\n{result.message}\n\n部分结果已保存到:\n{result.data.get('output_path')}",
                    ),
                )
            else:
                self.root.after(
                    0, lambda: messagebox.showerror("失败", f"查询失败:\n{result.message}")
                )

        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"查询执行失败:\n{str(e)}"))

        finally:
            # 清理资源
            if self.automation_engine:
                await self.automation_engine.cleanup()
                self.automation_engine = None

            # 清理任务引用
            self.current_task = None

    def _stop_query(self):
        """停止查询"""
        if not self.is_running:
            messagebox.showwarning("警告", "当前没有正在运行的任务")
            return

        if messagebox.askyesno("确认", "确定要停止当前查询吗？\n\n已完成的查询结果将会保存。"):
            logger.info("用户请求停止查询")
            self.update_status("正在停止任务...")

            # 停止任务
            if self.current_task:
                self.current_task.stop()
                logger.info("已发送停止信号给任务")

            # 停止自动化引擎
            if self.automation_engine:
                self.automation_engine.set_stop_flag()
                logger.info("已发送停止信号给自动化引擎")

            self.stop_btn.config(state=tk.DISABLED)
            self.update_status("正在停止，请稍候...")

    def _on_task_finished(self):
        """任务完成后的处理"""
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.is_running = False
        self.progress_bar["value"] = 0
        self.progress_label.config(text="就绪")
        self.update_status("就绪")

    def log_message(self, message: str, level: str = "INFO"):
        """添加日志消息

        Args:
            message: 日志消息
            level: 日志级别 (INFO, SUCCESS, WARNING, ERROR)
        """
        if self.log_viewer:
            self.log_viewer.add_log(message, level)

        # 写入外部日志文件
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "SUCCESS":
            logger.info(f"✅ {message}")
        else:
            logger.info(message)

    def _setup_gui_log_handler(self):
        """设置GUI日志处理器 - 拦截所有loguru日志并发送到GUI"""

        def gui_log_sink(message):
            """将loguru日志发送到GUI"""
            record = message.record
            level_name = record["level"].name

            # 映射loguru级别到GUI级别
            gui_level = level_name
            if level_name == "SUCCESS":
                gui_level = "SUCCESS"
            elif level_name == "WARNING":
                gui_level = "WARNING"
            elif level_name == "ERROR" or level_name == "CRITICAL":
                gui_level = "ERROR"
            else:
                gui_level = "INFO"

            msg = record["message"]
            self.message_queue.put(('log', msg, gui_level))

        logger.add(gui_log_sink, level="INFO", format="{message}")

    def _start_message_processor(self):
        """启动消息处理器"""

        def process_messages():
            try:
                while True:
                    try:
                        message_type, *args = self.message_queue.get_nowait()

                        if message_type == 'log':
                            message, level = args
                            if self.log_viewer:
                                self.log_viewer.add_log(message, level)

                        elif message_type == 'status':
                            status = args[0]
                            self.update_status(status)

                    except queue.Empty:
                        break

            except Exception as e:
                print(f"消息处理出错: {e}")

            if hasattr(self, 'root'):
                self.root.after(100, process_messages)

        self.root.after(100, process_messages)

    def _on_closing(self):
        """处理窗口关闭事件"""
        # 检查是否有任务正在运行
        if self.is_running:
            if not messagebox.askokcancel(
                "警告",
                "查询任务正在运行中！\n\n强制退出可能导致数据丢失。\n\n确定要退出吗？"
            ):
                return

            # 停止任务
            if self.current_task:
                self.current_task.stop()

            # 停止自动化引擎
            if self.automation_engine:
                self.automation_engine.set_stop_flag()

        elif not messagebox.askokcancel("退出", "确定要退出程序吗？"):
            return

        logger.info("用户关闭程序")
        self.root.destroy()

    def run(self):
        """运行GUI应用"""
        logger.info("启动GUI主循环")
        self.root.mainloop()


if __name__ == "__main__":
    app = ZXGKCourtAutomationGUI()
    app.run()

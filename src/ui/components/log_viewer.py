"""日志查看器组件"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import datetime


class LogViewer:
    """日志查看器组件"""

    def __init__(self, parent_frame):
        """初始化日志查看器

        Args:
            parent_frame: 父容器框架
        """
        self.parent_frame = parent_frame
        self.log_entries = []  # 存储所有日志条目
        self.log_text = None
        self.log_level_var = None

    def create_ui(self):
        """创建日志查看器UI"""
        # 日志框架
        log_frame = ttk.LabelFrame(self.parent_frame, text="日志信息")
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)

        # 日志控制按钮
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        # 日志级别筛选
        ttk.Label(log_control_frame, text="级别:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_level_var = tk.StringVar(value="所有")
        log_level_combo = ttk.Combobox(log_control_frame,
                                      textvariable=self.log_level_var,
                                      values=["所有", "INFO", "SUCCESS", "WARNING", "ERROR"],
                                      state="readonly", width=10)
        log_level_combo.pack(side=tk.LEFT, padx=(0, 10))
        log_level_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_logs())

        # 控制按钮
        ttk.Button(log_control_frame, text="筛选",
                  command=self.filter_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_control_frame, text="清空",
                  command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_control_frame, text="导出",
                  command=self.export_logs).pack(side=tk.LEFT)

        # 日志文本区域
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置日志颜色标签
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")

    def add_log(self, message, level="INFO"):
        """添加日志消息

        Args:
            message: 日志消息
            level: 日志级别 (INFO, SUCCESS, WARNING, ERROR)
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # 存储日志条目
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.log_entries.append(log_entry)

        # 显示日志
        self.display_log_entry(log_entry)

    def display_log_entry(self, log_entry):
        """显示单条日志"""
        if not self.log_text:
            return

        self.log_text.config(state=tk.NORMAL)
        formatted_message = f"[{log_entry['timestamp']}] [{log_entry['level']}] {log_entry['message']}\n"

        # 插入带颜色的日志
        start_index = self.log_text.index(tk.END + "-1c")
        self.log_text.insert(tk.END, formatted_message)
        end_index = self.log_text.index(tk.END + "-1c")

        # 应用颜色标签
        self.log_text.tag_add(log_entry['level'], start_index, end_index)

        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def filter_logs(self):
        """根据级别过滤日志"""
        selected_level = self.log_level_var.get()

        # 清空日志显示区域
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

        # 重新显示符合过滤条件的日志
        for log_entry in self.log_entries:
            if selected_level == "所有" or log_entry['level'] == selected_level:
                self.display_log_entry(log_entry)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        # 也清空日志存储
        self.log_entries.clear()

    def export_logs(self):
        """导出日志到文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存日志",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for log_entry in self.log_entries:
                        formatted_line = f"[{log_entry['timestamp']}] [{log_entry['level']}] {log_entry['message']}\n"
                        f.write(formatted_line)
                self.add_log("日志已导出到: " + file_path, "SUCCESS")
            except Exception as e:
                self.add_log(f"导出日志失败: {e}", "ERROR")

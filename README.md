# ZXGK Court Automation Tool

ZXGK法院自动化工具 - 基于Python的法院案件自动化处理桌面应用程序

## 架构

```
User → GUI (Tkinter) → Automation Engine (Playwright) → Court Website
```

## 项目结构

```
zxgk_court/
├── src/                         # 源代码目录
│   ├── core/                    # 核心模块
│   │   ├── automation_engine.py # Playwright自动化引擎
│   │   └── config_manager.py    # 配置管理器
│   ├── tasks/                   # 任务模块
│   │   ├── base_task.py         # 任务基类
│   │   └── common/              # 通用组件
│   │       ├── retry_manager.py # 重试管理器
│   │       └── step_executor.py # 步骤执行器
│   ├── ui/                      # 用户界面
│   │   ├── gui.py               # 主GUI界面
│   │   ├── components/          # UI组件
│   │   ├── managers/            # UI管理器
│   │   ├── panels/              # UI面板
│   │   └── tabs/                # UI标签页
│   └── utils/                   # 工具函数
│       ├── logger.py            # 日志工具
│       ├── exceptions.py        # 异常定义
│       ├── browser_checker.py   # 浏览器检查
│       └── helpers.py           # 辅助函数
├── config/                      # 配置文件
│   └── config.yaml              # 主配置文件
├── templates/                   # 模板文件
├── assets/                      # 资源文件
├── logs/                        # 日志文件
├── tests/                       # 测试文件
├── docs/                        # 文档
├── scripts/                     # 脚本工具
├── main.py                      # 主程序入口
├── version.py                   # 版本信息
├── requirements.txt             # 依赖包列表
├── pyproject.toml               # 项目配置
└── README.md                    # 项目说明
```

## 快速开始

### 环境要求

- Python 3.8+
- Playwright
- Tkinter (Python内置)

### 安装步骤

1. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows
```

2. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

3. 运行程序

```bash
python main.py
```

## 开发指南

### 添加新模块

1. 在 `src/tasks/` 目录下创建新模块文件夹
2. 继承 `BaseTask` 类实现任务逻辑
3. 在 `src/ui/tabs/` 创建对应的GUI标签页
4. 在 `config/` 添加模块配置文件

### 配置管理

所有配置文件位于 `config/` 目录，使用YAML格式。

主配置文件: `config/config.yaml`

### 日志管理

日志文件自动保存在 `logs/` 目录，按日期轮转。

日志级别可在配置文件中调整。

## 架构特性

- **配置驱动**: 基于YAML配置的步骤执行
- **模块化设计**: 清晰的模块划分和职责分离
- **异步支持**: 基于asyncio的异步任务执行
- **重试机制**: 内置智能重试管理
- **日志系统**: 完善的日志记录和管理

## 测试

```bash
pytest tests/ -v
```

## 打包

```bash
# 使用PyInstaller打包
pyinstaller main.spec
```

## 许可证

本项目为内部使用工具

## 联系方式

ZXGK Team

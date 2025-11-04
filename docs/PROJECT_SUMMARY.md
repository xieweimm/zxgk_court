# ZXGK Court Automation Tool - 项目架构摘要

## 项目信息

- **项目名称**: ZXGK Court Automation Tool
- **版本**: 1.0.0
- **创建日期**: 2025-11-04
- **技术栈**: Python 3.8+, Playwright, Tkinter

## 架构概览

```
User → GUI (Tkinter) → Automation Engine (Playwright) → Court Website
```

## 核心组件

### 1. Core (核心模块)
- `automation_engine.py`: Playwright自动化引擎
- `config_manager.py`: YAML配置管理器

### 2. Tasks (任务框架)
- `base_task.py`: 任务基类，定义统一接口
- `common/`: 通用组件
  - `retry_manager.py`: 重试管理器
  - `step_executor.py`: 步骤执行器

### 3. UI (用户界面)
- `gui.py`: Tkinter主界面
- `components/`: 可复用UI组件
- `managers/`: UI状态管理器
- `panels/`: 面板组件
- `tabs/`: 功能标签页

### 4. Utils (工具集)
- `logger.py`: 基于loguru的日志系统
- `exceptions.py`: 自定义异常类
- `browser_checker.py`: 浏览器可用性检查
- `helpers.py`: 辅助函数集合

## 设计模式

### 配置驱动
所有任务步骤通过YAML配置定义，支持灵活修改

### 处理器模式
业务逻辑分离到专门的Handler中：
- NavigationHandler: 页面导航
- FormHandler: 表单填写
- DocumentHandler: 文件上传
- WorkflowHandler: 工作流控制

### 异步优先
所有自动化操作基于asyncio实现

### 重试机制
内置智能重试管理，支持退避策略

## 目录结构

```
zxgk_court/
├── src/                    # 源代码
│   ├── core/              # 核心引擎
│   ├── tasks/             # 任务模块
│   ├── ui/                # 用户界面
│   └── utils/             # 工具函数
├── config/                # 配置文件
├── templates/             # 模板文件
├── assets/                # 资源文件
├── logs/                  # 日志目录
├── tests/                 # 测试文件
├── docs/                  # 文档
├── scripts/               # 脚本工具
├── main.py               # 主程序入口
├── version.py            # 版本管理
├── requirements.txt      # 依赖列表
├── pyproject.toml        # 项目配置
├── .gitignore           # Git忽略规则
├── README.md            # 项目说明
└── CLAUDE.md            # AI开发指南
```

## 快速命令

```bash
# 安装依赖
pip install -r requirements.txt
playwright install chromium

# 运行程序
python main.py

# 运行测试
pytest tests/ -v

# 代码格式化
./scripts/lint.sh
```

## 扩展指南

1. 在 `src/tasks/[module_name]/` 创建新模块
2. 继承 `BaseTask` 实现任务逻辑
3. 在 `src/ui/tabs/` 创建GUI标签页
4. 在 `config/` 添加模块配置
5. 参考 `docs/开发指南-添加新模块.md`

## 关键特性

- ✅ 完整的项目脚手架
- ✅ 配置驱动的任务执行
- ✅ 异步自动化引擎
- ✅ 模块化架构设计
- ✅ 日志和异常管理
- ✅ 测试框架
- ✅ 开发文档

## 对比原项目

本项目脚手架与 `court_automation` 保持相同的架构模式：
- 相同的目录结构和组织方式
- 相同的设计模式和最佳实践
- 相同的技术栈和依赖
- 清晰的扩展指南

可直接参考 `court_automation` 项目的实现细节进行功能开发。

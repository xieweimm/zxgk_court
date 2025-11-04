# CLAUDE.md

ZXGK Court Automation Tool - Python-based desktop application for legal case automation.

**Architecture**: `User → GUI (Tkinter) → Automation Engine (Playwright) → Court Website`

## Development Commands

### Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
playwright install chromium
```

### Running
```bash
python main.py
```

### Testing
```bash
python -m pytest tests/ -v
```

## Project Structure

```
src/
├── core/                    # Automation engine (Playwright)
│   ├── automation_engine.py # Browser automation core
│   └── config_manager.py    # Configuration management
├── tasks/                   # Task execution framework
│   ├── base_task.py         # Base task class
│   ├── common/              # Shared components
│   │   ├── retry_manager.py
│   │   └── step_executor.py
│   └── [module_name]/       # Module-specific tasks
├── ui/                      # Tkinter GUI
│   ├── gui.py               # Main GUI application
│   ├── components/          # Reusable UI components
│   ├── managers/            # UI state managers
│   ├── panels/              # Panel widgets
│   └── tabs/                # Tab implementations
└── utils/                   # Utilities
    ├── logger.py            # Logging setup
    ├── exceptions.py        # Custom exceptions
    ├── browser_checker.py   # Browser availability check
    └── helpers.py           # Helper functions
```

## Architecture Patterns

### Configuration-Driven Steps

**Step Configuration Format**:
```python
{
    "step_id": "nav_01_navigate",
    "name": "导航到页面",
    "handler": "navigation_handler",
    "method": "navigate_to_page",
    "args": [],
    "kwargs": {},
    "retry_config": {
        "max_retries": 3,
        "retry_delay": 2.0
    },
    "success_criteria": {"wait_time": 1.0},
    "description": "描述"
}
```

### Handler Pattern

Separate business logic into specialized handlers:
- `NavigationHandler`: Page navigation
- `FormHandler`: Form filling
- `DocumentHandler`: File uploads
- `WorkflowHandler`: Multi-step workflows

### Task Base Class

All tasks should inherit from `BaseTask`:

```python
from src.tasks.base_task import BaseTask, TaskStatus, TaskResult

class MyTask(BaseTask):
    def __init__(self, task_id: str, config: dict):
        super().__init__(task_id, "任务名称", config)

    async def execute(self, automation_engine) -> TaskResult:
        # Implement task logic
        try:
            # Your automation code here
            return TaskResult(TaskStatus.SUCCESS, "执行成功")
        except Exception as e:
            return TaskResult(TaskStatus.FAILED, str(e), error=e)
```

## Key Design Principles

1. **Separation of Concerns**: Core, Tasks, UI, and Utils are clearly separated
2. **Configuration Over Code**: Use YAML configs for behavior changes
3. **Async First**: All automation operations are async
4. **Fail-Fast**: Early validation and clear error messages
5. **Retry with Backoff**: Intelligent retry mechanisms for flaky operations
6. **Logging**: Comprehensive logging at all levels

## Adding New Modules

1. Create module directory under `src/tasks/[module_name]/`
2. Implement task class inheriting from `BaseTask`
3. Create handlers for business logic
4. Add GUI tab in `src/ui/tabs/`
5. Create configuration file in `config/`

## Common Patterns

### Async Execution
```python
async def execute(self, automation_engine):
    await automation_engine.navigate_to_url(url)
    await automation_engine.wait_for_selector(selector)
    await automation_engine.click_element(button)
```

### Retry Pattern
```python
from src.tasks.common.retry_manager import RetryManager

result = await RetryManager.retry_async(
    func=my_function,
    max_retries=3,
    delay=2.0
)
```

### Configuration Loading
```python
from src.core.config_manager import ConfigManager

config_manager = ConfigManager()
config = config_manager.load_config("config")
browser_type = config.get("browser", {}).get("type", "chromium")
```

## Important Notes

- **Don't modify common code** - extend instead
- **Use step_id prefixes** for categorization (nav_, form_, doc_, etc.)
- **Inject params into kwargs** before step execution
- **Initialize browser** before task execution
- **Clean up resources** in finally blocks
- **Log extensively** for debugging

# SEMDS 编码规范

**版本**: v1.0  
**语言**: Python 3.11+  
**强制执行**: 是

---

## 🎯 核心原则

### 1. 可读性 > 简洁性

```python
# ✅ 好的代码 - 清晰易懂
def calculate_fitness(code: str, test_cases: List[TestCase]) -> float:
    """计算代码适应度分数。

    Args:
        code: 待评估的Python代码
        test_cases: 测试用例列表

    Returns:
        0.0到1.0之间的适应度分数
    """
    passed = sum(1 for tc in test_cases if run_test(code, tc))
    return passed / len(test_cases)

# ❌ 坏的代码 - 过度简洁
def f(c,t):return sum(r(c,x)for x in t)/len(t)
```

### 2. 显式 > 隐式

```python
# ✅ 显式处理所有情况
if backend == "deepseek":
    return call_deepseek_api(prompt)
elif backend == "openai":
    return call_openai_api(prompt)
else:
    raise ValueError(f"Unknown backend: {backend}")

# ❌ 隐式假设
return api_callers[backend](prompt)  # 可能KeyError
```

### 3. 防御性编程

```python
# ✅ 始终验证输入
def safe_write(filepath: str, content: str) -> Result:
    if not isinstance(filepath, str) or not filepath:
        raise ValueError("filepath must be non-empty string")
    if not isinstance(content, str):
        raise TypeError("content must be string")
    # ... 实际写入逻辑

# ❌ 无验证
def unsafe_write(filepath, content):
    with open(filepath, 'w') as f:  # 可能任意路径
        f.write(content)
```

---

## 📐 代码结构

### 文件组织

```
evolution/
├── __init__.py           # 最小化，仅导出公共API
├── code_generator.py     # 单一职责：代码生成
├── test_runner.py        # 单一职责：测试执行
├── strategy_optimizer.py # 单一职责：策略优化
└── utils.py              # 共享工具函数（尽量少）
```

### 类设计

```python
# ✅ 单一职责
class CodeGenerator:
    """代码生成器 - 负责调用LLM API生成代码。"""

    def __init__(self, backend: str, api_key: str):
        self.backend = backend
        self.api_key = api_key
        self._validate_config()

    def generate(self, task_spec: dict) -> GenerationResult:
        """生成代码实现。"""
        # 实现...

# ❌ 职责混杂
class EvolutionSystem:
    """混杂了生成、测试、优化多个职责。"""
    pass
```

### 函数设计

```python
# ✅ 参数明确，有默认值
def run_tests(
    code: str,
    test_cases: List[TestCase],
    timeout: float = 30.0,
    verbose: bool = False
) -> TestResult:
    """运行测试用例。

    Args:
        code: 被测代码
        test_cases: 测试用例列表
        timeout: 超时时间（秒），默认30
        verbose: 是否输出详细信息，默认False

    Returns:
        TestResult包含通过数、失败数、执行时间
    """

# ❌ 参数模糊
def test(c, t, to=30, v=False):
    pass
```

---

## 📝 命名规范

### 变量命名

```python
# ✅ 自解释的命名
generation_count = 10
best_fitness_score = 0.95
mutation_strategy = "conservative"

# ❌ 缩写/模糊
gc = 10
best = 0.95
ms = "cons"
```

### 常量命名

```python
# ✅ 全大写+下划线
MAX_GENERATIONS = 50
DEFAULT_TIMEOUT = 30.0
SUCCESS_THRESHOLD = 0.95
```

### 类命名

```python
# ✅ PascalCase
class GenerationResult:
class StrategyOptimizer:
class EvolutionLogger:

# ❌ 下划线或小写
class generation_result:
class strategyoptimizer:
```

---

## 🔒 类型注解

### 强制使用类型注解

```python
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass

@dataclass
class GenerationResult:
    """代码生成结果。"""
    code: str
    success: bool
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0

def generate_code(
    task_spec: Dict[str, Any],
    previous_attempts: List[GenerationResult],
    temperature: float = 0.5
) -> GenerationResult:
    """生成代码。"""
    # 实现...
```

### 复杂类型使用TypeAlias

```python
from typing import TypeAlias

# ✅ 复杂类型定义别名
GenerationHistory: TypeAlias = List[GenerationResult]
StrategyConfig: TypeAlias = Dict[str, Union[str, float, int]]
TestSuite: TypeAlias = Dict[str, Callable[[], bool]]

def analyze_history(history: GenerationHistory) -> StrategyConfig:
    pass
```

---

## 🧪 错误处理

### 使用异常而非返回值

```python
# ✅ 使用异常
def safe_divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b

try:
    result = safe_divide(10, 0)
except ValueError as e:
    logger.error(f"Calculation failed: {e}")

# ❌ 使用返回值标识错误
def unsafe_divide(a, b):
    if b == 0:
        return None  # 调用者可能忘记检查
    return a / b
```

### 自定义异常

```python
class SEMDSError(Exception):
    """SEMDS基础异常。"""
    pass

class GenerationError(SEMDSError):
    """代码生成失败。"""
    def __init__(self, message: str, raw_response: Optional[str] = None):
        super().__init__(message)
        self.raw_response = raw_response

class SandboxError(SEMDSError):
    """沙盒执行失败。"""
    def __init__(self, message: str, exit_code: int = -1):
        super().__init__(message)
        self.exit_code = exit_code
```

---

## 📊 日志规范

### 使用结构化日志

```python
import logging
from pythonjsonlogger import jsonlogger  # 推荐

logger = logging.getLogger("semds.evolution")

# ✅ 结构化日志
logger.info(
    "Generation completed",
    extra={
        "generation": gen_number,
        "pass_rate": pass_rate,
        "strategy": strategy_name,
        "execution_time_ms": exec_time
    }
)

# ❌ 非结构化日志
logger.info(f"Gen {gen_number} done with rate {pass_rate}")
```

### 日志级别使用

```python
logger.debug("Detailed debug info")      # 调试信息
logger.info("Normal operation")          # 正常操作
logger.warning("Unexpected but handled") # 异常但已处理
logger.error("Error occurred")           # 错误
logger.critical("System failure")        # 系统级失败
```

---

## 🔄 异步编程

### 优先使用asyncio

```python
import asyncio
from typing import AsyncIterator

# ✅ 异步实现
async def generate_async(prompt: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json={"prompt": prompt}) as resp:
            return await resp.text()

# ✅ 批量处理
async def generate_batch(prompts: List[str]) -> List[str]:
    tasks = [generate_async(p) for p in prompts]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

---

## 📦 导入规范

### 导入顺序

```python
# 1. 标准库
import os
import sys
from pathlib import Path
from typing import List, Dict

# 2. 第三方库
import sqlalchemy
from pydantic import BaseModel

# 3. 项目内部
from semds.core.kernel import safe_write
from semds.evolution.generator import CodeGenerator
```

### 避免循环导入

```python
# ✅ 在函数内导入
def get_generator():
    from semds.evolution.generator import CodeGenerator
    return CodeGenerator()

# ❌ 顶部循环导入
# from semds.evolution.generator import CodeGenerator
# from semds.core.sandbox import Sandbox  # 如果sandbox也导入generator...
```

---

## 🎨 代码格式化

### 使用Black（强制）

```bash
# 格式化
black semds/

# 检查
black --check semds/
```

### 配置示例（pyproject.toml）

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### 使用isort排序导入

```bash
isort semds/
```

---

## 🔍 静态检查

### 强制使用mypy

```bash
# 使用项目配置（推荐）
mypy semds/

# 或严格模式
mypy semds/ --strict
```

> **注意**: 项目使用 pyproject.toml 中的 mypy 配置，详情见配置文件中的 `[tool.mypy]` 部分。

### 配置（pyproject.toml）

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

---

## 🧹 代码审查清单

### 提交前必须检查

- [ ] 所有函数都有类型注解
- [ ] 所有函数都有docstring
- [ ] 没有`print()`调试语句（使用logger）
- [ ] 异常处理完善
- [ ] 通过black格式化
- [ ] 通过mypy检查
- [ ] 通过单元测试

### AI生成代码审查要点

- [ ] 是否遵循单函数单一职责
- [ ] 是否有足够的防御性检查
- [ ] 命名是否自解释
- [ ] 是否有潜在的副作用

---

**违反本规范的代码不得合并到主分支**

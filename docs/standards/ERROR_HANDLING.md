# SEMDS 错误处理规范

**版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: 所有Python代码

---

## 🎯 核心原则

```
1. 快速失败 - 尽早暴露问题，不隐藏错误
2. 明确错误 - 异常类型具体，消息清晰
3. 优雅降级 - 有备用方案，不直接崩溃
4. 完整日志 - 记录足够信息用于诊断
```

---

## 📦 异常体系

### 异常层次结构

```python
# core/exceptions.py

class SEMDSError(Exception):
    """SEMDS基础异常。"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code or "UNKNOWN"
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class CoreKernelError(SEMDSError):
    """Layer 0 核心内核错误。"""
    pass

class SandboxError(CoreKernelError):
    """沙盒执行错误。"""
    
    def __init__(self, message: str, exit_code: int = -1, stderr: str = "", **kwargs):
        super().__init__(message, error_code="SANDBOX_ERROR", **kwargs)
        self.exit_code = exit_code
        self.stderr = stderr

class SecurityError(CoreKernelError):
    """安全违规错误。"""
    
    def __init__(self, message: str, violation_type: str = "", **kwargs):
        super().__init__(message, error_code="SECURITY_VIOLATION", **kwargs)
        self.violation_type = violation_type

class EvolutionError(SEMDSError):
    """进化引擎错误。"""
    pass

class GenerationError(EvolutionError):
    """代码生成错误。"""
    
    def __init__(self, message: str, raw_response: str = None, **kwargs):
        super().__init__(message, error_code="GENERATION_FAILED", **kwargs)
        self.raw_response = raw_response

class StrategyError(EvolutionError):
    """策略优化错误。"""
    pass

class EvaluationError(EvolutionError):
    """代码评估错误。"""
    pass

class StorageError(SEMDSError):
    """存储层错误。"""
    pass

class ValidationError(SEMDSError):
    """输入验证错误。"""
    pass
```

### 异常使用规范

```python
# ✅ 正确：使用具体异常类型
raise SandboxError(
    "代码执行超时", 
    exit_code=-1,
    details={"timeout": 30, "code_length": 1000}
)

# ❌ 错误：使用泛泛的Exception
raise Exception("出错了")  # 太笼统

# ❌ 错误：使用ValueError处理业务错误
raise ValueError("策略选择失败")  # 应该使用StrategyError
```

---

## 🛡️ 防御性编程

### 输入验证

```python
from typing import Any
import os
from pathlib import Path

# ✅ 正确的输入验证
def safe_write(filepath: str, content: str) -> Result:
    """安全写入文件。"""
    # 类型验证
    if not isinstance(filepath, str):
        raise TypeError(f"filepath must be str, got {type(filepath).__name__}")
    if not isinstance(content, str):
        raise TypeError(f"content must be str, got {type(content).__name__}")
    
    # 空值验证
    if not filepath:
        raise ValueError("filepath cannot be empty")
    
    # 路径安全验证
    resolved_path = Path(filepath).resolve()
    allowed_root = Path("/app/data").resolve()
    
    try:
        resolved_path.relative_to(allowed_root)
    except ValueError:
        raise SecurityError(
            f"Path traversal detected: {filepath}",
            violation_type="PATH_TRAVERSAL"
        )
    
    # 内容验证
    if len(content) > 10_000_000:  # 10MB限制
        raise ValueError("Content too large (>10MB)")
    
    # ... 实际写入逻辑

# ❌ 错误：无验证
def unsafe_write(filepath, content):
    with open(filepath, 'w') as f:
        f.write(content)
```

### 边界条件处理

```python
# ✅ 正确处理边界
def calculate_average(values: list[float]) -> float:
    """计算平均值。"""
    if not values:
        raise ValidationError(
            "Cannot calculate average of empty list",
            error_code="EMPTY_LIST"
        )
    
    if not all(isinstance(v, (int, float)) for v in values):
        non_numeric = [v for v in values if not isinstance(v, (int, float))]
        raise ValidationError(
            f"Non-numeric values found: {non_numeric}",
            error_code="INVALID_TYPE"
        )
    
    return sum(values) / len(values)

# ❌ 错误：不处理边界
def bad_average(values):
    return sum(values) / len(values)  # 可能ZeroDivisionError
```

---

## 🔄 错误恢复策略

### 重试机制

```python
import asyncio
from functools import wraps
from typing import Callable, TypeVar

T = TypeVar('T')

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """重试装饰器。"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt} failed: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
            raise RuntimeError("Should not reach here")
        
        return async_wrapper
    return decorator

# 使用示例
@retry(max_attempts=3, exceptions=(APIError, TimeoutError))
async def call_llm_api(prompt: str) -> str:
    """调用LLM API（带重试）。"""
    # ... 调用逻辑
```

### 降级策略

```python
class CodeGenerator:
    """代码生成器（带降级策略）。"""
    
    def __init__(self):
        self.primary_backend = ClaudeBackend()
        self.fallback_backend = OpenAIBackend()
    
    async def generate(self, task: Task) -> GenerationResult:
        """生成代码（主后端失败时降级）。"""
        try:
            # 尝试主后端
            return await self.primary_backend.generate(task)
        except (APIError, TimeoutError) as e:
            logger.warning(f"Primary backend failed: {e}. Using fallback...")
        
        try:
            # 降级到备用后端
            return await self.fallback_backend.generate(task)
        except APIError as e:
            # 备用也失败，使用本地模板
            logger.error(f"Fallback backend also failed: {e}")
            return self._generate_from_template(task)
    
    def _generate_from_template(self, task: Task) -> GenerationResult:
        """从模板生成（最后的保底）。"""
        # 使用预设模板，质量较低但至少可用
        template = self._select_template(task.task_type)
        code = template.fill(task.parameters)
        
        return GenerationResult(
            code=code,
            success=True,
            is_fallback=True,
            message="Generated from template due to API failure"
        )
```

---

## 📝 错误日志

### 结构化日志

```python
import logging
import json
from pythonjsonlogger import jsonlogger

# 配置JSON日志
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(timestamp)s %(level)s %(name)s %(message)s %(error_code)s %(details)s'
)
logHandler.setFormatter(formatter)
logger = logging.getLogger("semds")
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# ✅ 正确的错误日志
logger.error(
    "代码生成失败",
    extra={
        "error_code": "GENERATION_FAILED",
        "task_id": task.id,
        "generation": current_gen,
        "details": {
            "backend": "claude",
            "prompt_length": len(prompt),
            "error_type": type(e).__name__
        }
    }
)

# ❌ 错误的日志
logger.error(f"Failed: {e}")  # 无结构化信息
```

### 日志级别使用

```python
# DEBUG: 调试信息（开发时使用）
logger.debug(f"Processing generation {gen_number}")

# INFO: 正常操作信息
logger.info("Evolution completed", extra={"best_score": best_score})

# WARNING: 异常但已处理
logger.warning("API rate limit approaching", extra={"remaining": 10})

# ERROR: 错误需要关注
logger.error("Sandbox execution failed", extra={"exit_code": 1})

# CRITICAL: 系统级故障
logger.critical("Database connection lost")
```

---

## 🎯 错误处理模式

### 上下文管理器

```python
from contextlib import contextmanager

@contextmanager
def sandbox_context(timeout: float = 30.0):
    """沙盒执行上下文。"""
    sandbox = Sandbox()
    try:
        yield sandbox
    except TimeoutError:
        logger.error("Sandbox execution timeout")
        sandbox.force_stop()
        raise SandboxError("Execution timeout", exit_code=-1)
    except Exception as e:
        logger.exception("Sandbox unexpected error")
        raise SandboxError(f"Unexpected error: {e}")
    finally:
        sandbox.cleanup()

# 使用
with sandbox_context(timeout=10.0) as sb:
    result = sb.execute(code)
```

### 结果模式（替代异常）

```python
from dataclasses import dataclass
from typing import Generic, TypeVar, Union

T = TypeVar('T')

@dataclass
class Result(Generic[T]):
    """操作结果封装。"""
    success: bool
    value: T = None
    error: str = ""
    error_code: str = ""
    
    @staticmethod
    def ok(value: T) -> 'Result[T]':
        return Result(success=True, value=value)
    
    @staticmethod
    def err(error: str, code: str = "") -> 'Result[T]':
        return Result(success=False, error=error, error_code=code)
    
    def unwrap(self) -> T:
        if not self.success:
            raise RuntimeError(f"Unwrap failed: {self.error}")
        return self.value

# 使用示例
def safe_parse_json(data: str) -> Result[dict]:
    try:
        return Result.ok(json.loads(data))
    except json.JSONDecodeError as e:
        return Result.err(f"Invalid JSON: {e}", "JSON_ERROR")

result = safe_parse_json(raw_data)
if result.success:
    process(result.value)
else:
    logger.error(f"Parse failed: {result.error}")
```

---

## ✅ 错误处理检查清单

```markdown
## 错误处理检查清单

### 异常设计
- [ ] 自定义异常继承自SEMDSError
- [ ] 异常包含error_code
- [ ] 异常消息清晰有用
- [ ] 异常包含相关上下文

### 输入验证
- [ ] 所有公共函数验证输入
- [ ] 类型检查明确
- [ ] 边界条件检查
- [ ] 路径安全检查（防遍历）

### 错误恢复
- [ ] 外部调用有重试机制
- [ ] 有降级策略
- [ ] 资源正确释放
- [ ] 状态回滚机制（如需要）

### 日志记录
- [ ] 错误使用结构化日志
- [ ] 包含足够诊断信息
- [ ] 适当的日志级别
- [ ] 敏感信息已脱敏

### 测试覆盖
- [ ] 异常路径有测试
- [ ] 边界条件有测试
- [ ] 错误恢复逻辑有测试
```

---

**最后更新**: 2026-03-07  
**维护者**: 核心开发团队

# SEMDS 安全开发规范

**版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: 所有代码、配置、部署

---

## 🎯 安全原则

```
1. 最小权限 - 只给必要的权限
2. 纵深防御 - 多层安全机制
3. 默认安全 - 不安全的功能默认关闭
4. 安全失败 - 出错时进入安全状态
```

---

## 🔐 代码安全

### 输入验证

```python
import re
from pathlib import Path

# ✅ 严格的输入验证
def validate_task_id(task_id: str) -> str:
    """验证任务ID格式。"""
    if not isinstance(task_id, str):
        raise TypeError("task_id must be string")
    
    # 只允许字母、数字、连字符、下划线
    if not re.match(r'^[a-zA-Z0-9_-]+$', task_id):
        raise ValueError(f"Invalid task_id format: {task_id}")
    
    if len(task_id) > 64:
        raise ValueError("task_id too long (max 64)")
    
    return task_id

def sanitize_filename(filename: str) -> str:
    """清理文件名，防止路径遍历。"""
    # 移除路径分隔符
    filename = filename.replace('/', '').replace('\\', '')
    # 移除父目录引用
    filename = filename.replace('..', '')
    # 只允许安全字符
    if not re.match(r'^[\w\-. ]+$', filename):
        raise ValueError(f"Invalid filename: {filename}")
    return filename
```

### 路径安全

```python
from pathlib import Path

# ✅ 安全的文件操作
ALLOWED_ROOT = Path("/app/data").resolve()

def safe_read_file(filepath: str) -> str:
    """安全读取文件。"""
    # 解析路径
    path = (ALLOWED_ROOT / filepath).resolve()
    
    # 确保在允许的根目录内
    try:
        path.relative_to(ALLOWED_ROOT)
    except ValueError:
        raise SecurityError("Path traversal attempt detected")
    
    # 检查是否是文件
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    return path.read_text()

# ❌ 不安全的文件操作
def unsafe_read(filepath: str) -> str:
    return open(filepath).read()  # 可能读取/etc/passwd
```

### 命令注入防护

```python
import subprocess
import shlex

# ✅ 安全的命令执行
def safe_execute(command: list[str]) -> str:
    """使用列表形式执行命令（无shell注入）。"""
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30
    )
    return result.stdout

# 使用示例
safe_execute(["python", "-c", code])  # ✅ 安全

# ❌ 不安全的命令执行
def unsafe_execute(command: str) -> str:
    return subprocess.check_output(command, shell=True)  # 危险！

# 如果必须使用shell
safe_execute(shlex.quote(user_input))  # 转义用户输入
```

### SQL注入防护

```python
from sqlalchemy import text

# ✅ 使用参数化查询
def get_task(task_id: str):
    return session.execute(
        text("SELECT * FROM tasks WHERE id = :task_id"),
        {"task_id": task_id}
    ).fetchone()

# ❌ 不安全的查询（绝不使用）
def unsafe_get_task(task_id: str):
    return session.execute(
        f"SELECT * FROM tasks WHERE id = '{task_id}'"  # SQL注入！
    ).fetchone()
```

---

## 🧪 沙盒安全

### 代码执行隔离

```python
# ✅ 安全的代码执行
class SecureSandbox:
    """安全沙盒。"""
    
    FORBIDDEN_PATTERNS = [
        r'__import__\s*\(',
        r'import\s+os',
        r'import\s+subprocess',
        r'eval\s*\(',
        r'exec\s*\(',
        r'open\s*\(',
        r'file\s*\(',
    ]
    
    def validate_code(self, code: str) -> None:
        """验证代码安全性。"""
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, code):
                raise SecurityError(
                    f"Forbidden pattern detected: {pattern}",
                    violation_type="FORBIDDEN_PATTERN"
                )
    
    def execute(self, code: str) -> ExecutionResult:
        """在隔离环境执行代码。"""
        # 1. 静态检查
        self.validate_code(code)
        
        # 2. subprocess隔离执行
        return self._subprocess_execute(code)
    
    def _subprocess_execute(self, code: str) -> ExecutionResult:
        """subprocess临时目录中执行。"""
        import tempfile
        import subprocess
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入代码文件
            code_file = Path(tmpdir) / "code.py"
            code_file.write_text(code)
            
            # 在隔离环境中执行
            result = subprocess.run(
                ["python", str(code_file)],
                capture_output=True,
                text=True,
                timeout=30,           # 时间限制
                cwd=tmpdir,           # 工作目录隔离
            )
            
        return ExecutionResult(
            exit_code=result.returncode,
            output=result.stdout + result.stderr
        )
```

---

## 🔑 密钥管理

### 环境变量使用

```python
import os
from typing import Optional

# ✅ 从环境变量读取密钥
class Config:
    """配置类。"""
    
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    
    @classmethod
    def load(cls):
        """加载配置。"""
        cls.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        
        # 验证必需配置
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set")
    
    @classmethod
    def mask_key(cls, key: str) -> str:
        """脱敏显示密钥。"""
        if len(key) < 8:
            return "***"
        return key[:4] + "..." + key[-4:]

# 使用
print(f"Using API key: {Config.mask_key(Config.ANTHROPIC_API_KEY)}")
```

### 日志脱敏

```python
import re

def sanitize_log_message(message: str) -> str:
    """脱敏日志消息。"""
    # 脱敏API密钥
    patterns = [
        (r'sk-[a-zA-Z0-9]{48}', 'sk-***'),
        (r'api[_-]?key[=:]\s*\S+', 'api_key=***'),
        (r'password[=:]\s*\S+', 'password=***'),
        (r'token[=:]\s*\S+', 'token=***'),
    ]
    
    for pattern, replacement in patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)
    
    return message

# ✅ 安全的日志
logger.info(sanitize_log_message(f"API call with key: {api_key}"))
```

---

## 🛡️ 访问控制

### 权限检查

```python
from enum import Enum
from functools import wraps

class Permission(Enum):
    """权限枚举。"""
    READ_TASK = "read:task"
    WRITE_TASK = "write:task"
    EXECUTE_CODE = "execute:code"
    ADMIN = "admin"

def require_permission(permission: Permission):
    """权限检查装饰器。"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = get_current_user()
            if permission not in user.permissions:
                raise PermissionError(
                    f"Permission {permission.value} required"
                )
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# 使用
@require_permission(Permission.EXECUTE_CODE)
async def execute_in_sandbox(code: str):
    # 只有授权用户可以执行
    pass
```

---

## 🔍 安全扫描

### 依赖安全

```bash
# 扫描依赖漏洞
pip-audit
safety check

# 代码安全扫描
bandit -r . -f json -o bandit-report.json
```

### 配置检查

```python
# ✅ 安全的默认配置
class SecurityConfig:
    """安全配置。"""
    
    # 禁用危险功能
    ALLOW_EVAL = False
    ALLOW_EXEC = False
    ALLOW_IMPORT = False
    
    # 资源限制
    MAX_CODE_LENGTH = 10000
    MAX_EXECUTION_TIME = 30
    MAX_MEMORY_MB = 128
    
    # 网络限制
    ALLOW_NETWORK = False
    ALLOWED_HOSTS = []

# 生产环境配置覆盖
class ProductionConfig(SecurityConfig):
    """生产环境安全配置。"""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    ALLOWED_HOSTS = ["api.semds.io"]
```

---

## 🚨 安全事件响应

### 事件分类

| 级别 | 描述 | 响应时间 | 示例 |
|-----|------|---------|------|
| P0 | 系统入侵 | 立即 | 沙盒逃逸、未授权访问 |
| P1 | 数据泄露 | 1小时 | 密钥泄露、日志脱敏失败 |
| P2 | 配置错误 | 4小时 | 开放端口、弱权限 |
| P3 | 低危漏洞 | 24小时 | 依赖漏洞、信息泄露 |

### 响应流程

```
1. 发现/报告安全事件
2. 评估影响和级别
3. 遏制（隔离受影响系统）
4. 根除（修复漏洞）
5. 恢复（恢复服务）
6. 复盘（防止再发生）
```

---

## ✅ 安全检查清单

```markdown
## 安全开发检查清单

### 代码安全
- [ ] 所有用户输入经过验证
- [ ] 文件路径使用safe_join
- [ ] SQL使用参数化查询
- [ ] 无eval/exec使用
- [ ] 命令使用列表形式

### 密钥管理
- [ ] 密钥存储在环境变量
- [ ] 无硬编码密钥
- [ ] 日志脱敏处理
- [ ] 配置文件无敏感信息

### 沙盒安全
- [ ] 代码在隔离环境执行
- [ ] 资源限制已配置
- [ ] 网络已隔离
- [ ] 危险模式已拦截

### 访问控制
- [ ] 权限检查到位
- [ ] 敏感操作有审计日志
- [ ] 默认拒绝未授权访问
- [ ] 最小权限原则

### 部署安全
- [ ] 依赖已扫描
- [ ] 无调试信息泄露
- [ ] HTTPS强制
- [ ] 安全头已配置
```

---

**最后更新**: 2026-03-07  
**维护者**: 安全团队

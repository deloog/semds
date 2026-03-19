# Tool Design Principles
# 工具设计核心原则 - 强制遵循

> 这些原则通过代码审查强制执行，不是可选建议！

---

## 1. 极简主义 (Minimalism)

### 原则
用**最少代码**完成任务，去除一切冗余。

### 检查清单
- [ ] 没有未使用的导入
- [ ] 没有冗余变量
- [ ] 没有重复逻辑
- [ ] 单一职责：一个工具只做一件事
- [ ] 代码行数 < 100（复杂工具可放宽到 200）

### 反例
```python
# ❌ BAD: 过度工程
def fetch_data(url: str) -> dict:
    import json
    import requests
    from typing import Dict, Any
    
    class DataFetcher:
        def __init__(self, url):
            self.url = url
            self.session = requests.Session()
        
        def fetch(self) -> Dict[str, Any]:
            response = self.session.get(self.url)
            return json.loads(response.text)
    
    fetcher = DataFetcher(url)
    return fetcher.fetch()
```

### 正例
```python
# ✅ GOOD: 极简实现
def fetch_data(url: str) -> dict:
    import requests
    return requests.get(url, timeout=30).json()
```

---

## 2. 防御性编程 (Defensive Programming)

### 原则
**绝不信任输入**，假设所有输入都可能恶意或错误。

### 必须检查的边界条件

#### A. 输入验证
```python
def process(input_data: str) -> str:
    # 1. 类型检查
    if not isinstance(input_data, str):
        raise TypeError(f"Expected str, got {type(input_data).__name__}")
    
    # 2. 空值检查
    if not input_data or not input_data.strip():
        return ""  # 或抛出 ValueError，视场景而定
    
    # 3. 长度限制（防止内存攻击）
    if len(input_data) > 10_000_000:  # 10MB
        raise ValueError("Input too large")
    
    # 4. 危险字符检查（如适用）
    if ".." in input_data or input_data.startswith("/"):
        raise ValueError("Invalid path characters")
    
    # 主逻辑...
```

#### B. 外部调用保护
```python
def fetch_url(url: str, timeout: int = 30) -> str:
    import requests
    
    # 1. URL 验证
    if not url.startswith(("http://", "https://")):
        raise ValueError(f"Invalid URL scheme: {url}")
    
    # 2. 禁止内网/本地地址（防 SSRF）
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname in ("localhost", "127.0.0.1", "0.0.0.0"):
        raise ValueError("Local addresses not allowed")
    
    # 3. 超时控制
    # 4. 大小限制
    response = requests.get(url, timeout=timeout, stream=True)
    content = b""
    for chunk in response.iter_content(chunk_size=8192):
        content += chunk
        if len(content) > 10_000_000:  # 10MB limit
            raise ValueError("Response too large")
    
    return content.decode("utf-8", errors="replace")
```

#### C. 资源释放
```python
def read_file(path: str) -> str:
    # 使用上下文管理器确保资源释放
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
# 不要这样：f = open(...); return f.read()
```

---

## 3. 安全优先 (Security First)

### 禁止清单（绝对不允许）
- ❌ `eval()`, `exec()`, `compile()`
- ❌ `__import__()` 动态导入
- ❌ `pickle.loads()` 不可信数据
- ❌ `subprocess.call(shell=True)`
- ❌ `os.system()`
- ❌ 硬编码密钥/密码
- ❌ 不验证的文件路径操作

### 强制安全措施
```python
# ✅ 安全的文件操作
def safe_read_file(path: str, base_dir: str = "/allowed/path") -> str:
    import os
    
    # 1. 路径规范化
    abs_path = os.path.abspath(os.path.join(base_dir, path))
    
    # 2. 路径逃逸检查
    if not abs_path.startswith(os.path.abspath(base_dir)):
        raise ValueError("Path traversal detected")
    
    # 3. 存在性检查
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"File not found: {path}")
    
    # 4. 读取
    with open(abs_path, "r", encoding="utf-8") as f:
        return f.read()
```

---

## 4. 健壮性 (Robustness)

### 错误处理原则
1. **早失败，快失败** - 在入口处验证，不要传播错误
2. **具体异常** - 捕获具体异常，不要裸 except
3. **优雅降级** - 部分失败时返回可用结果

```python
# ✅ 好的错误处理
def parse_json(data: str) -> dict:
    import json
    
    if not isinstance(data, str):
        return {"error": "Input must be string", "data": None}
    
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}", "data": None}
    except Exception as e:
        # 意料之外的错误，记录但返回友好信息
        return {"error": "Unexpected error", "data": None}

# ❌ 裸 except 吞噬错误
def bad_parse(data):
    import json
    try:
        return json.loads(data)
    except:  # 不要这样做！
        return None
```

### 超时控制
```python
import signal
from functools import wraps

def timeout(seconds: int):
    """装饰器：强制超时"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"Function timed out after {seconds}s")
            
            # 设置超时
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        return wrapper
    return decorator

@timeout(30)
def long_running_task():
    pass
```

---

## 5. 可测试性 (Testability)

### 设计要点
- 纯函数优先（无副作用）
- 依赖注入（便于 mock）
- 单一职责（便于单元测试）

```python
# ✅ 易于测试
def extract_urls(html: str, base_url: str = "") -> list:
    """纯函数，无副作用，易于测试"""
    import re
    if not html:
        return []
    
    pattern = r'href=["\']([^"\']+)["\']'
    urls = re.findall(pattern, html)
    
    # 规范化
    return [u if u.startswith("http") else base_url + u for u in urls]

# 测试用例
def test_extract_urls():
    assert extract_urls('<a href="/test">') == ["/test"]
    assert extract_urls("") == []
    assert extract_urls(None) == []
```

---

## 6. 性能意识 (Performance)

### 必须考虑的点
- **大输入处理**：使用生成器/迭代器，不要一次性加载
- **正则优化**：复杂正则可能导致 ReDoS
- **循环效率**：避免在循环中进行重复计算

```python
# ✅ 处理大文件的正确方式
def process_large_file(path: str):
    with open(path, "r") as f:
        for line in f:  # 逐行读取，不占用大量内存
            yield process_line(line)

# ❌ 错误方式：一次性读取
def bad_process(path: str):
    with open(path, "r") as f:
        lines = f.readlines()  # 大文件会爆内存
    return [process_line(l) for l in lines]
```

---

## 代码审查清单

每个生成的工具必须通过以下检查：

| 类别 | 检查项 | 级别 |
|------|--------|------|
| 极简 | 代码行数 < 100 | 必须 |
| 极简 | 无未使用导入 | 必须 |
| 防御 | 输入类型检查 | 必须 |
| 防御 | 空值检查 | 必须 |
| 防御 | 长度/大小限制 | 必须 |
| 安全 | 无 eval/exec | 必须 |
| 安全 | 路径验证 | 必须 |
| 健壮 | 具体异常捕获 | 必须 |
| 健壮 | 超时控制 | 推荐 |
| 性能 | 支持大输入 | 推荐 |

---

## 模板示例

### 标准工具模板
```python
"""
Tool: {name}
Purpose: {description}
Author: Mother System
Created: {timestamp}
"""
import sys
sys.path.insert(0, r'D:\semds')
from mother.core.capability_registry import Capability


class {Name}Tool(Capability):
    """{description}"""
    
    # 常量配置
    MAX_INPUT_SIZE = 10_000_000  # 10MB
    TIMEOUT = 30  # seconds
    
    def __init__(self):
        super().__init__("{name}", "{description}")
    
    def execute(self, input_data: str) -> dict:
        """
        {description}
        
        Args:
            input_data: Description of input
        
        Returns:
            dict with keys:
                - success: bool
                - data: result data
                - error: error message if failed
        """
        try:
            # 1. 输入验证
            validated = self._validate_input(input_data)
            
            # 2. 核心逻辑
            result = self._process(validated)
            
            return {"success": True, "data": result, "error": None}
            
        except ValueError as e:
            return {"success": False, "data": None, "error": f"Invalid input: {e}"}
        except TimeoutError as e:
            return {"success": False, "data": None, "error": f"Operation timed out: {e}"}
        except Exception as e:
            # 未预料的错误，返回安全信息
            return {"success": False, "data": None, "error": "Internal error"}
    
    def _validate_input(self, data) -> str:
        """验证并返回清理后的输入"""
        # 类型检查
        if not isinstance(data, str):
            raise TypeError(f"Expected str, got {type(data).__name__}")
        
        # 空值检查
        if not data or not data.strip():
            raise ValueError("Input cannot be empty")
        
        # 大小限制
        if len(data) > self.MAX_INPUT_SIZE:
            raise ValueError(f"Input exceeds max size of {self.MAX_INPUT_SIZE} bytes")
        
        return data.strip()
    
    def _process(self, data: str):
        """核心处理逻辑（子类重写）"""
        raise NotImplementedError
```

---

> **记住**：简单是可靠的先决条件。
> 
> —— Edsger W. Dijkstra

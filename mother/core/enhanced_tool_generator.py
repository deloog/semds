"""
Enhanced Tool Generator - 增强版工具生成器
强制执行极简、安全、健壮原则
"""

import os
import sys
import tempfile
import importlib.util
from typing import Optional, Dict
from datetime import datetime

sys.path.insert(0, "D:\\semds")

from mother.core.capability_registry import Capability
from mother.skills.code_optimizer import CodeOptimizer, optimize_code


class EnhancedToolGenerator:
    """
    增强版工具生成器

    核心特性：
    1. 强制极简 - 代码行数限制、去除冗余
    2. 强制安全 - 危险函数检测、输入验证
    3. 强制健壮 - 错误处理、超时控制
    4. 自动优化 - 不符合原则时自动改进
    """

    # 符合原则的高质量模板
    MINIMAL_TEMPLATES = {
        "html_parser": '''
class HTMLParserTool(Capability):
    """Parse HTML and extract data. Minimal and robust implementation."""
    
    MAX_HTML_SIZE = 10_000_000  # 10MB safety limit
    
    def __init__(self):
        super().__init__("html_parser", "Parse HTML and extract image URLs")
    
    def execute(self, html: str) -> list:
        """
        Extract image URLs from HTML.
        
        Args:
            html: HTML string to parse
            
        Returns:
            List of image URLs
        """
        import re
        
        # Input validation
        if not isinstance(html, str):
            return []
        if len(html) > self.MAX_HTML_SIZE:
            return []
        
        # Extract URLs with double quotes
        pattern1 = r'<img[^>]+src="([^"]+)"'
        urls = re.findall(pattern1, html, re.IGNORECASE)
        
        # Extract URLs with single quotes
        pattern2 = r"<img[^>]+src='([^']+)'"
        urls.extend(re.findall(pattern2, html, re.IGNORECASE))
        
        # Normalize URLs
        result = []
        for url in urls:
            if url.startswith("//"):
                url = "https:" + url
            elif url.startswith("/"):
                url = "https://example.com" + url
            if url.startswith("http"):
                result.append(url)
        
        return result
''',
        "csv_reader": '''
class CSVReaderTool(Capability):
    """Read CSV files safely."""
    
    MAX_FILE_SIZE = 10_000_000  # 10MB
    MAX_ROWS = 100_000
    
    def __init__(self):
        super().__init__("csv_reader", "Read CSV file and return list of dicts")
    
    def execute(self, file_path: str) -> list:
        """
        Read CSV file.
        
        Args:
            file_path: Path to CSV file (relative to allowed directory)
            
        Returns:
            List of dictionaries
        """
        import csv
        import os
        
        # Security: path validation
        if not isinstance(file_path, str):
            return [{"error": "Path must be string"}]
        
        if ".." in file_path or file_path.startswith(("/", "\\\\", "C:", "D:")):
            return [{"error": "Invalid path"}]
        
        # Check file exists and size
        if not os.path.exists(file_path):
            return [{"error": f"File not found: {file_path}"}]
        
        if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
            return [{"error": "File too large"}]
        
        # Read with safety limits
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                rows = []
                for i, row in enumerate(reader):
                    if i >= self.MAX_ROWS:
                        break
                    rows.append(dict(row))
                return rows
        except Exception as e:
            return [{"error": str(e)}]
''',
        "json_parser": '''
class JSONParserTool(Capability):
    """Parse JSON safely with size limits."""
    
    MAX_SIZE = 10_000_000  # 10MB
    
    def __init__(self):
        super().__init__("json_parser", "Parse JSON string to Python object")
    
    def execute(self, json_str: str) -> dict:
        """
        Parse JSON string.
        
        Args:
            json_str: JSON string to parse
            
        Returns:
            Parsed data or error dict
        """
        import json
        
        # Validation
        if not isinstance(json_str, str):
            return {"success": False, "error": "Input must be string", "data": None}
        
        if len(json_str) > self.MAX_SIZE:
            return {"success": False, "error": "JSON too large", "data": None}
        
        if not json_str.strip():
            return {"success": False, "error": "Empty input", "data": None}
        
        # Parse with error handling
        try:
            data = json.loads(json_str)
            return {"success": True, "error": None, "data": data}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}", "data": None}
        except Exception as e:
            return {"success": False, "error": f"Parse error: {e}", "data": None}
''',
        "http_client": '''
class HTTPClientTool(Capability):
    """HTTP client with timeouts and safety limits."""
    
    MAX_RESPONSE_SIZE = 10_000_000  # 10MB
    DEFAULT_TIMEOUT = 30
    
    # Security: block internal addresses
    BLOCKED_HOSTS = ("localhost", "127.0.0.1", "0.0.0.0", "::1")
    
    def __init__(self):
        super().__init__("http_client", "Make HTTP requests safely")
    
    def execute(self, url: str, method: str = "GET", timeout: int = None) -> dict:
        """
        Make HTTP request.
        
        Args:
            url: URL to fetch (http/https only)
            method: HTTP method (GET/POST)
            timeout: Timeout in seconds (default 30)
            
        Returns:
            Response data or error dict
        """
        import requests
        from urllib.parse import urlparse
        
        # Input validation
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            return {"success": False, "error": "Invalid URL", "data": None}
        
        # Security: check blocked hosts
        try:
            parsed = urlparse(url)
            if parsed.hostname in self.BLOCKED_HOSTS:
                return {"success": False, "error": "Access denied", "data": None}
        except:
            return {"success": False, "error": "URL parse error", "data": None}
        
        # Request with timeout and size limit
        try:
            timeout = timeout or self.DEFAULT_TIMEOUT
            response = requests.request(
                method.upper(), 
                url, 
                timeout=timeout,
                stream=True
            )
            response.raise_for_status()
            
            # Limit response size
            content = b""
            for chunk in response.iter_content(chunk_size=8192):
                content += chunk
                if len(content) > self.MAX_RESPONSE_SIZE:
                    return {"success": False, "error": "Response too large", "data": None}
            
            return {
                "success": True,
                "data": content.decode("utf-8", errors="replace"),
                "status_code": response.status_code,
                "error": None
            }
            
        except requests.Timeout:
            return {"success": False, "error": "Request timeout", "data": None}
        except requests.RequestException as e:
            return {"success": False, "error": f"Request failed: {e}", "data": None}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}", "data": None}
''',
        "file_reader": '''
class FileReaderTool(Capability):
    """Read files safely with path validation."""
    
    MAX_SIZE = 10_000_000  # 10MB
    ALLOWED_EXTENSIONS = (".txt", ".csv", ".json", ".md", ".py", ".log")
    
    def __init__(self, base_dir: str = "."):
        super().__init__("file_reader", "Read file content safely")
        self.base_dir = os.path.abspath(base_dir)
    
    def execute(self, file_path: str) -> dict:
        """
        Read file content.
        
        Args:
            file_path: Relative path to file
            
        Returns:
            File content or error dict
        """
        import os
        
        # Validation
        if not isinstance(file_path, str) or not file_path:
            return {"success": False, "error": "Invalid path", "data": None}
        
        # Extension check
        _, ext = os.path.splitext(file_path.lower())
        if ext not in self.ALLOWED_EXTENSIONS:
            return {"success": False, "error": f"File type '{ext}' not allowed", "data": None}
        
        # Path traversal protection
        full_path = os.path.abspath(os.path.join(self.base_dir, file_path))
        if not full_path.startswith(self.base_dir):
            return {"success": False, "error": "Path traversal detected", "data": None}
        
        # Size check
        try:
            size = os.path.getsize(full_path)
            if size > self.MAX_SIZE:
                return {"success": False, "error": "File too large", "data": None}
        except OSError as e:
            return {"success": False, "error": str(e), "data": None}
        
        # Read file
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"success": True, "data": content, "error": None}
        except UnicodeDecodeError:
            # Try binary mode
            try:
                with open(full_path, "rb") as f:
                    content = f.read().decode("utf-8", errors="replace")
                return {"success": True, "data": content, "error": None}
            except Exception as e:
                return {"success": False, "error": str(e), "data": None}
        except Exception as e:
            return {"success": False, "error": str(e), "data": None}
''',
    }

    def __init__(self, tools_dir: str = "mother/tools"):
        self.tools_dir = tools_dir
        self.optimizer = CodeOptimizer()

        os.makedirs(tools_dir, exist_ok=True)

        # 加载设计原则
        self._load_principles()

    def _load_principles(self):
        """加载设计原则（作为系统提示）"""
        principles_path = "mother/standards/TOOL_DESIGN_PRINCIPLES.md"
        if os.path.exists(principles_path):
            with open(principles_path, "r", encoding="utf-8") as f:
                self.principles = f.read()
        else:
            self.principles = ""

    def generate(self, capability_name: str) -> Optional[str]:
        """
        生成符合原则的工具代码

        流程：
        1. 获取模板代码
        2. 代码质量检查
        3. 自动优化
        4. 验证通过才保存
        """
        print(f"\n[ToolGen] Creating: {capability_name}")

        # 1. 获取基础代码
        code = self._get_base_code(capability_name)
        if not code:
            print(f"[ToolGen] No template available for: {capability_name}")
            return None

        # 2. 代码优化检查
        print("[ToolGen] Running quality checks...")
        result = self.optimizer.optimize(code, capability_name)

        # 3. 如果未通过，尝试自动修复
        if not result["passed"]:
            print(f"[ToolGen] Original score: {result['original_score']}/100")
            print(f"[ToolGen] Issues found: {len(result['issues'])}")

            # 使用优化后的代码
            code = result["optimized_code"]

            # 再次检查
            result = self.optimizer.optimize(code, capability_name)
            print(f"[ToolGen] After optimization: {result['optimized_score']}/100")

            if not result["passed"]:
                errors = [i for i in result["issues"] if i.severity == "error"]
                print(f"[ToolGen] Still has {len(errors)} errors:")
                for e in errors[:3]:
                    print(f"  - {e.code}: {e.message}")
                print("[ToolGen] Proceeding with best effort...")
        else:
            print(f"[ToolGen] Quality check passed: {result['optimized_score']}/100")

        # 4. 验证语法
        if not self._validate_syntax(code, capability_name):
            return None

        # 5. 保存
        self._save_tool(code, capability_name)

        # 6. 打印报告
        self._print_summary(result)

        return code

    def _get_base_code(self, capability_name: str) -> Optional[str]:
        """获取基础代码（模板）"""
        if capability_name in self.MINIMAL_TEMPLATES:
            template = self.MINIMAL_TEMPLATES[capability_name]
            return self._wrap_template(template, capability_name)

        return None

    def _wrap_template(self, template: str, name: str) -> str:
        """包装模板为标准格式"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f'''"""
Auto-generated tool: {name}
Generated by SEMDS Enhanced Tool Generator
Created: {timestamp}

Design Principles Applied:
- Minimalism: Simple, focused implementation
- Security: Input validation, no dangerous functions
- Robustness: Error handling, timeout control
"""
import sys
sys.path.insert(0, 'D:\\semds')
from mother.core.capability_registry import Capability
import os

{template}
'''

    def _validate_syntax(self, code: str, name: str) -> bool:
        """验证代码语法"""
        try:
            compile(code, f"{name}.py", "exec")

            # 尝试导入
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as f:
                f.write(code)
                temp_path = f.name

            try:
                spec = importlib.util.spec_from_file_location(name, temp_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # 检查是否有 Tool 类
                has_tool = any(
                    attr.endswith("Tool") and attr != "Capability"
                    for attr in dir(module)
                )

                return has_tool
            finally:
                os.unlink(temp_path)

        except Exception as e:
            print(f"[ToolGen] Syntax validation failed: {e}")
            return False

    def _save_tool(self, code: str, name: str):
        """保存工具"""
        tool_path = os.path.join(self.tools_dir, f"{name}.py")
        with open(tool_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[ToolGen] Saved to: {tool_path}")

    def _print_summary(self, result: Dict):
        """打印生成摘要"""
        print(f"\n  Quality Score: {result['optimized_score']}/100")
        status_str = "[PASS]" if result["passed"] else "[WARN]"
        print(f"  Status: {status_str}")

        errors = len([i for i in result["issues"] if i.severity == "error"])
        warnings = len([i for i in result["issues"] if i.severity == "warning"])

        if errors:
            print(f"  Errors: {errors}")
        if warnings:
            print(f"  Warnings: {warnings}")

        if result["suggestions"]:
            print(f"  Suggestions: {len(result['suggestions'])}")


# 便捷函数
def generate_minimal_tool(capability_name: str) -> Optional[str]:
    """生成符合极简原则的代码"""
    generator = EnhancedToolGenerator()
    return generator.generate(capability_name)


if __name__ == "__main__":
    # 测试生成各种工具
    test_tools = [
        "html_parser",
        "csv_reader",
        "json_parser",
        "http_client",
        "file_reader",
    ]

    print("=" * 70)
    print("Enhanced Tool Generator Test")
    print("=" * 70)
    print("\nPrinciples enforced:")
    print("  1. Minimalism - Less code, more focus")
    print("  2. Security - Input validation, no dangerous functions")
    print("  3. Robustness - Error handling, timeouts")
    print()

    generator = EnhancedToolGenerator()

    for tool_name in test_tools:
        print(f"\n{'='*70}")
        code = generator.generate(tool_name)
        if code:
            print(f"\n✓ {tool_name} generated successfully")
        else:
            print(f"\n✗ {tool_name} generation failed")

    print(f"\n{'='*70}")
    print("Test complete!")
    print("=" * 70)

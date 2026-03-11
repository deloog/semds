"""
SEMDS Core Kernel - Layer 0

核心内核层，永远不被系统自动修改，只能由人类手动更新。
这是整个系统的信任锚点，类比DNA复制酶的保真机制。

本模块提供：
- safe_write: 四层防护的文件写入机制
- append_audit_log: 审计日志记录
"""

import ast
import hashlib
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 审计日志文件路径（相对于core目录）
AUDIT_LOG_PATH = Path(__file__).parent / "audit.log"


def _get_timestamp() -> str:
    """获取ISO格式时间戳。"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_python_syntax(content: str) -> tuple[bool, Optional[str]]:
    """
    验证Python代码语法是否合法。

    Args:
        content: 要验证的Python代码字符串

    Returns:
        (is_valid, error_message): 是否合法及错误信息
    """
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return (
            False,
            f"SyntaxError: {e.msg} at line {e.lineno}, col {e.offset}",
        )
    except Exception as e:
        return False, f"Parse error: {str(e)}"


def _pass_static_analysis(content: str) -> tuple[bool, Optional[str]]:
    """
    对Python代码进行静态分析，检查危险模式。

    Phase 1简化版：仅检查明显的危险导入和调用。

    Args:
        content: 要分析的Python代码字符串

    Returns:
        (is_safe, error_message): 是否安全及错误信息
    """
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # 语法错误已在validate_python_syntax中检查
        return True, None

    # 危险导入列表（Phase 1简化版）
    dangerous_imports = {
        "os.system",
        "os.popen",
        "os.spawn",
        "os.exec",
        "subprocess.call",
        "subprocess.run",
        "subprocess.Popen",
        "eval",
        "exec",
        "compile",
        "__import__",
        "socket",
        "urllib",
        "http",
        "ftplib",
    }

    for node in ast.walk(tree):
        # 检查导入语句
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ("os", "subprocess", "socket"):
                    # 允许导入模块，但会警告
                    pass

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                full_name = f"{module}.{alias.name}"
                if full_name in dangerous_imports:
                    return (
                        False,
                        f"Static analysis: dangerous import " f"'{full_name}' detected",
                    )

        # 检查函数调用
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec", "__import__"):
                    return (
                        False,
                        f"Static analysis: dangerous call "
                        f"'{node.func.id}' detected",
                    )
            elif isinstance(node.func, ast.Attribute):
                # 检查属性调用如 os.system
                if isinstance(node.func.value, ast.Name):
                    full_name = f"{node.func.value.id}.{node.func.attr}"
                    if full_name in dangerous_imports:
                        return (
                            False,
                            f"Static analysis: dangerous call "
                            f"'{full_name}' detected",
                        )

    return True, None


def _compute_content_hash(content: str) -> str:
    """计算内容的SHA256哈希值。"""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def append_audit_log(
    filepath: str,
    content: str,
    operation: str = "WRITE",
    success: bool = True,
    error_message: Optional[str] = None,
) -> None:
    """
    将操作记录追加到审计日志。

    审计日志是不可篡改的操作记录，用于追踪所有文件写入操作。

    Args:
        filepath: 被操作的文件路径
        content: 写入的内容（用于计算哈希）
        operation: 操作类型（WRITE, BACKUP, ROLLBACK等）
        success: 操作是否成功
        error_message: 错误信息（如果失败）
    """
    timestamp = _get_timestamp()
    content_hash = _compute_content_hash(content)

    # 构建日志条目
    log_entry = (
        f"[{timestamp}] "
        f"OP={operation} "
        f"FILE={filepath} "
        f"HASH={content_hash} "
        f"SUCCESS={success}"
    )

    if error_message:
        # 对错误信息进行转义，避免换行符破坏日志格式
        escaped_error = error_message.replace("\n", "\\n").replace("\r", "")
        log_entry += f" ERROR={escaped_error}"

    log_entry += "\n"

    # 追加到审计日志文件
    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        # 审计日志写入失败是严重问题，但不应阻止主流程
        # 在实际生产环境中应该触发警报
        print(f"[CRITICAL] Failed to write audit log: {e}")


def safe_write(filepath: str, content: str) -> dict:
    """
    四层防护的安全文件写入机制。

    这是核心内核层函数，永远不被系统自动修改。

    四层防护：
        1. 备份：写入前备份现有文件到 .bak.{timestamp}
        2. 验证：content通过语法检查和静态分析
        3. 原子写入：写入临时文件，验证后原子替换
        4. 审计：记录所有写入操作到不可篡改的audit.log

    Args:
        filepath: 目标文件路径
        content: 要写入的内容

    Returns:
        字典包含：
        - success: bool - 是否成功
        - backup_path: Optional[str] - 备份文件路径（如果有）
        - error: Optional[str] - 错误信息（如果失败）
        - timestamp: str - 操作时间戳
    """
    result = {
        "success": False,
        "backup_path": None,
        "error": None,
        "timestamp": _get_timestamp(),
    }

    filepath_obj = Path(filepath)

    # 确保目标目录存在
    try:
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        result["error"] = f"Failed to create directory: {e}"
        append_audit_log(
            filepath,
            content,
            "WRITE",
            success=False,
            error_message=str(result["error"]),
        )
        return result

    # Layer 1: 备份
    backup_path = None
    if filepath_obj.exists():
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
        backup_path = str(filepath_obj) + f".bak.{timestamp_str}"
        try:
            shutil.copy2(filepath, backup_path)
            result["backup_path"] = backup_path
            append_audit_log(backup_path, content, "BACKUP", success=True)
        except Exception as e:
            result["error"] = f"Backup failed: {e}"
            append_audit_log(
                filepath,
                content,
                "BACKUP",
                success=False,
                error_message=str(result["error"]),
            )
            return result

    # Layer 2: 验证
    # 2.1 语法验证
    is_valid, syntax_error = _validate_python_syntax(content)
    if not is_valid:
        result["error"] = f"Syntax validation failed: {syntax_error}"
        append_audit_log(
            filepath,
            content,
            "WRITE",
            success=False,
            error_message=str(result["error"]),
        )
        return result

    # 2.2 静态分析
    is_safe, analysis_error = _pass_static_analysis(content)
    if not is_safe:
        result["error"] = f"Static analysis failed: {analysis_error}"
        append_audit_log(
            filepath,
            content,
            "WRITE",
            success=False,
            error_message=str(result["error"]),
        )
        return result

    # Layer 3: 原子写入
    tmp_path = str(filepath_obj) + ".tmp"
    try:
        # 写入临时文件
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(content)

        # 验证临时文件可读取且内容正确
        with open(tmp_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        if written_content != content:
            result["error"] = "Content verification failed after write"
            append_audit_log(
                filepath,
                content,
                "WRITE",
                success=False,
                error_message=str(result["error"]),
            )
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return result

        # 原子替换
        os.replace(tmp_path, filepath)

    except Exception as e:
        result["error"] = f"Atomic write failed: {e}"
        append_audit_log(
            filepath,
            content,
            "WRITE",
            success=False,
            error_message=str(result["error"]),
        )
        # 清理临时文件
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return result

    # Layer 4: 审计
    append_audit_log(filepath, content, "WRITE", success=True)

    result["success"] = True
    return result


def read_audit_log(limit: int = 100) -> list[dict]:
    """
    读取审计日志内容。

    Args:
        limit: 最多返回的条目数（从最新开始）

    Returns:
        审计日志条目列表
    """
    if not AUDIT_LOG_PATH.exists():
        return []

    try:
        with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 取最后limit行
        lines = lines[-limit:] if len(lines) > limit else lines

        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 简单解析日志条目
            entry = {"raw": line}
            # 提取关键字段
            if line.startswith("["):
                end_idx = line.find("]")
                if end_idx > 0:
                    entry["timestamp"] = line[1:end_idx]
            entries.append(entry)

        return entries
    except Exception as e:
        return [{"error": str(e)}]


if __name__ == "__main__":
    # 简单测试
    test_file = "/tmp/test_kernel.py"
    test_code = """
def hello():
    return "Hello, SEMDS!"
"""
    result = safe_write(test_file, test_code)
    print(f"Write result: {result}")

    # 测试语法错误
    bad_code = "def broken("
    result2 = safe_write(test_file, bad_code)
    print(f"Bad code result: {result2}")

"""
自我验证器 - Phase 1 核心组件

自动检测代码生成错误，支持自动重试机制。
"""

import ast
import re
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List, Optional, Any

from evolution.test_runner import TestRunner


class SelfValidator:
    """
    自我验证器 - 自动检测代码生成错误

    Phase 1 实现：
    - 语法检查
    - 函数签名检查（函数名、参数）
    - 基础测试运行
    """

    def __init__(self, expected_function_name: str = "evaluate") -> None:
        self.expected_function_name = expected_function_name
        self.validation_history: List[Dict[str, Any]] = []

    def validate(
        self, code: str, test_runner: Optional[TestRunner] = None, test_code: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        验证代码并给出修正建议

        Returns:
            (是否通过, 修正提示, 详细信息)
        """
        # Level 1: 语法检查
        syntax_valid, syntax_error = self._check_syntax(code)
        if not syntax_valid:
            self.validation_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "syntax",
                    "passed": False,
                    "error": syntax_error,
                }
            )
            return (
                False,
                f"Syntax error: {syntax_error}. Please fix and regenerate.",
                {"level": "syntax"},
            )

        # Level 2: 函数签名检查
        function_valid, function_info = self._check_function_signature(code)
        if not function_valid:
            actual_name = function_info.get("actual_name", "unknown")
            self.validation_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "level": "function_name",
                    "passed": False,
                    "expected": self.expected_function_name,
                    "actual": actual_name,
                }
            )
            return (
                False,
                (
                    f"Function name error: Expected '{self.expected_function_name}', "
                    f"but got '{actual_name}'. "
                    f"Function signature must be: def {self.expected_function_name}(expression: str) -> float. "
                    f"Please regenerate with correct function name."
                ),
                {
                    "level": "function_name",
                    "expected": self.expected_function_name,
                    "actual": actual_name,
                },
            )

        # Level 3: 测试运行（如果提供了测试）
        if test_runner and test_code:
            test_result = self._run_test(code, test_runner, test_code)
            if test_result["pass_rate"] < 1.0:
                failed_count = len(test_result.get("failed", []))
                total_count = test_result.get("total_tests", 0)
                self.validation_history.append(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "level": "test",
                        "passed": False,
                        "pass_rate": test_result["pass_rate"],
                        "failed_count": failed_count,
                    }
                )
                return (
                    False,
                    (
                        f"Tests failed: {failed_count}/{total_count} failed. "
                        f"Pass rate: {test_result['pass_rate']:.1%}. "
                        f"Please analyze and fix the implementation."
                    ),
                    {"level": "test", "result": test_result},
                )

        # 全部通过
        self.validation_history.append(
            {"timestamp": datetime.now().isoformat(), "level": "all", "passed": True}
        )
        return True, "All validations passed.", {"level": "all"}

    def _check_syntax(self, code: str) -> Tuple[bool, str]:
        """检查Python语法"""
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)

    def _check_function_signature(self, code: str) -> Tuple[bool, Dict[str, Any]]:
        """检查函数签名是否正确"""
        info: Dict[str, Any] = {"found": False, "actual_name": None}

        # 尝试解析AST
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    info["found"] = True
                    info["actual_name"] = node.name

                    if node.name == self.expected_function_name:
                        return True, info
        except Exception:
            pass

        # AST解析失败，使用正则表达式备用
        pattern = r"def\s+(\w+)\s*\("
        matches = re.findall(pattern, code)
        if matches:
            info["found"] = True
            info["actual_name"] = matches[0]
            if matches[0] == self.expected_function_name:
                return True, info

        return False, info

    def _run_test(self, code: str, test_runner: TestRunner, test_code: str) -> Dict[str, Any]:
        """运行测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入代码
            solution_path = Path(tmpdir) / "solution.py"
            with open(solution_path, "w", encoding="utf-8") as f:
                f.write(code)

            # 写入测试
            test_path = Path(tmpdir) / "test_solution.py"
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            # 运行测试
            result = test_runner.run_tests(str(test_path), str(solution_path), tmpdir)

        return result

    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证历史摘要"""
        if not self.validation_history:
            return {"total": 0}

        total = len(self.validation_history)
        passed = sum(1 for v in self.validation_history if v.get("passed"))
        failed = total - passed

        by_level: Dict[str, Dict[str, Any]] = {}
        for v in self.validation_history:
            level = v.get("level", "unknown")
            if level not in by_level:
                by_level[level] = {"total": 0, "passed": 0}
            by_level[level]["total"] += 1
            if v.get("passed"):
                by_level[level]["passed"] += 1

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0,
            "by_level": by_level,
        }

"""
Code Optimizer - 代码优化器
强制执行极简、安全、健壮原则
"""

import ast
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Optimization:
    """优化建议"""

    line: int
    code: str
    message: str
    severity: str  # error, warning, suggestion
    auto_fixable: bool
    fix_code: Optional[str] = None


class MinimalismChecker:
    """极简主义检查器"""

    def check(self, code: str) -> List[Optimization]:
        """检查极简原则"""
        issues = []

        # 1. 代码行数检查
        lines = code.split("\n")
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        if len(code_lines) > 100:
            issues.append(
                Optimization(
                    line=1,
                    code="CODE_TOO_LONG",
                    message=f"Code has {len(code_lines)} lines, consider simplifying (max 100)",
                    severity="warning",
                    auto_fixable=False,
                )
            )

        # 2. 未使用导入检查
        issues.extend(self._check_unused_imports(code))

        # 3. 冗余变量检查
        issues.extend(self._check_redundant_variables(code))

        # 4. 重复代码检查
        issues.extend(self._check_duplication(code))

        return issues

    def _check_unused_imports(self, code: str) -> List[Optimization]:
        """检查未使用的导入"""
        issues = []
        try:
            tree = ast.parse(code)

            # 收集所有导入
            imports = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = node.lineno
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = node.lineno

            # 检查是否被使用（简化版：检查 Name 节点）
            used_names = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)

            for name, lineno in imports.items():
                base_name = name.split(".")[0]
                if base_name not in used_names and name != "Capability":
                    issues.append(
                        Optimization(
                            line=lineno,
                            code="UNUSED_IMPORT",
                            message=f"Import '{name}' appears to be unused",
                            severity="warning",
                            auto_fixable=True,
                            fix_code=f"# Remove: import {name}",
                        )
                    )
        except:
            pass

        return issues

    def _check_redundant_variables(self, code: str) -> List[Optimization]:
        """检查冗余变量"""
        issues = []
        # 简单检查：var = value; return var 模式
        pattern = r"(\w+)\s*=\s*(.+?)\s*$\s*^\s*return\s+\1"
        matches = re.finditer(pattern, code, re.MULTILINE)
        for m in matches:
            issues.append(
                Optimization(
                    line=code[: m.start()].count("\n") + 1,
                    code="REDUNDANT_VARIABLE",
                    message=f"Variable '{m.group(1)}' is redundant, return directly",
                    severity="suggestion",
                    auto_fixable=True,
                    fix_code=f"return {m.group(2)}",
                )
            )
        return issues

    def _check_duplication(self, code: str) -> List[Optimization]:
        """检查重复代码块"""
        issues = []
        lines = code.split("\n")

        # 查找重复的行组（3行以上）
        for i in range(len(lines) - 3):
            block = "\n".join(lines[i : i + 3])
            if len(block.strip()) < 20:  # 忽略短块
                continue

            # 在后面查找重复
            rest = "\n".join(lines[i + 3 :])
            if block in rest:
                issues.append(
                    Optimization(
                        line=i + 1,
                        code="CODE_DUPLICATION",
                        message="Detected potentially duplicated code block, consider refactoring",
                        severity="warning",
                        auto_fixable=False,
                    )
                )
                break  # 只报告一次

        return issues


class SecurityChecker:
    """安全检查器"""

    DANGEROUS_FUNCTIONS = [
        "eval",
        "exec",
        "compile",
        "__import__",
        "pickle.loads",
        "pickle.load",
        "yaml.load",  # unsafe
        "subprocess.call",
        "subprocess.Popen",
        "os.system",
        "os.popen",
    ]

    def check(self, code: str) -> List[Optimization]:
        """安全检查"""
        issues = []

        # 1. 危险函数检查
        issues.extend(self._check_dangerous_functions(code))

        # 2. 硬编码密钥检查
        issues.extend(self._check_hardcoded_secrets(code))

        # 3. 路径操作检查
        issues.extend(self._check_path_traversal(code))

        # 4. SQL 注入检查
        issues.extend(self._check_sql_injection(code))

        return issues

    def _check_dangerous_functions(self, code: str) -> List[Optimization]:
        """检查危险函数调用"""
        issues = []

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = self._get_func_name(node.func)
                    if func_name in self.DANGEROUS_FUNCTIONS:
                        issues.append(
                            Optimization(
                                line=node.lineno,
                                code="DANGEROUS_FUNCTION",
                                message=f"Dangerous function '{func_name}' detected",
                                severity="error",
                                auto_fixable=False,
                            )
                        )
        except:
            pass

        return issues

    def _get_func_name(self, node) -> str:
        """获取函数名"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}"
        return ""

    def _check_hardcoded_secrets(self, code: str) -> List[Optimization]:
        """检查硬编码密钥"""
        issues = []
        patterns = [
            (
                r'["\']\s*(?:api[_-]?key|password|secret|token)\s*["\']\s*=\s*["\'][^"\']+["\']',
                "HARDCODED_SECRET",
            ),
            (r"(?:sk-|pk-|ak-)[a-zA-Z0-9]{20,}", "API_KEY_PATTERN"),
        ]

        for pattern, code_type in patterns:
            for match in re.finditer(pattern, code, re.IGNORECASE):
                issues.append(
                    Optimization(
                        line=code[: match.start()].count("\n") + 1,
                        code=code_type,
                        message="Possible hardcoded secret detected",
                        severity="error",
                        auto_fixable=False,
                    )
                )

        return issues

    def _check_path_traversal(self, code: str) -> List[Optimization]:
        """检查路径遍历风险"""
        issues = []

        # 检查 open() 调用是否验证路径
        if "open(" in code and "os.path.abspath" not in code:
            issues.append(
                Optimization(
                    line=1,
                    code="PATH_VALIDATION",
                    message="File operations should validate paths with os.path.abspath() and check for path traversal",
                    severity="warning",
                    auto_fixable=False,
                )
            )

        return issues

    def _check_sql_injection(self, code: str) -> List[Optimization]:
        """检查 SQL 注入风险"""
        issues = []

        # 检查字符串拼接 SQL
        sql_patterns = [
            r'execute\s*\(\s*["\'].*?\+',
            r'execute\s*\(\s*f["\']',
        ]

        for pattern in sql_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(
                    Optimization(
                        line=1,
                        code="SQL_INJECTION_RISK",
                        message="Possible SQL injection risk: use parameterized queries instead of string concatenation",
                        severity="error",
                        auto_fixable=False,
                    )
                )
                break

        return issues


class RobustnessChecker:
    """健壮性检查器"""

    def check(self, code: str) -> List[Optimization]:
        """健壮性检查"""
        issues = []

        # 1. 裸 except 检查
        issues.extend(self._check_bare_except(code))

        # 2. 输入验证检查
        issues.extend(self._check_input_validation(code))

        # 3. 超时控制检查
        issues.extend(self._check_timeout(code))

        return issues

    def _check_bare_except(self, code: str) -> List[Optimization]:
        """检查裸 except"""
        issues = []

        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Try):
                    for handler in node.handlers:
                        if handler.type is None:
                            issues.append(
                                Optimization(
                                    line=handler.lineno,
                                    code="BARE_EXCEPT",
                                    message="Bare 'except:' clause - use specific exceptions like 'except ValueError:'",
                                    severity="error",
                                    auto_fixable=True,
                                    fix_code="# Change to: except SpecificException as e:",
                                )
                            )
        except:
            pass

        return issues

    def _check_input_validation(self, code: str) -> List[Optimization]:
        """检查输入验证"""
        issues = []

        # 检查 execute 方法是否验证输入
        if "def execute(" in code:
            # 检查是否有 isinstance 或空值检查
            has_validation = (
                "isinstance(" in code or "if not " in code or ".strip()" in code
            )

            if not has_validation:
                issues.append(
                    Optimization(
                        line=1,
                        code="MISSING_INPUT_VALIDATION",
                        message="Function should validate inputs (type check, null check, etc.)",
                        severity="warning",
                        auto_fixable=False,
                    )
                )

        return issues

    def _check_timeout(self, code: str) -> List[Optimization]:
        """检查超时控制"""
        issues = []

        # 检查网络/IO 操作是否有超时
        io_functions = ["requests.get", "requests.post", "urlopen", "socket."]
        has_timeout = "timeout=" in code

        for func in io_functions:
            if func in code and not has_timeout:
                issues.append(
                    Optimization(
                        line=1,
                        code="MISSING_TIMEOUT",
                        message=f"IO operations should have timeout parameter to prevent hanging",
                        severity="warning",
                        auto_fixable=False,
                    )
                )
                break

        return issues


class CodeOptimizer:
    """
    代码优化器主类
    整合所有检查并提供优化建议
    """

    def __init__(self):
        self.minimalism = MinimalismChecker()
        self.security = SecurityChecker()
        self.robustness = RobustnessChecker()

    def optimize(self, code: str, tool_name: str = "<generated>") -> Dict:
        """
        全面优化检查

        Returns:
            {
                'optimized_code': str,
                'original_score': int,
                'optimized_score': int,
                'issues': List[Optimization],
                'suggestions': List[str],
                'passed': bool
            }
        """
        issues = []

        # 运行所有检查
        issues.extend(self.minimalism.check(code))
        issues.extend(self.security.check(code))
        issues.extend(self.robustness.check(code))

        # 计算分数
        original_score = self._calculate_score(code, issues)

        # 尝试自动修复
        optimized_code = self._auto_fix(code, issues)

        # 重新检查
        new_issues = []
        new_issues.extend(self.minimalism.check(optimized_code))
        new_issues.extend(self.security.check(optimized_code))
        new_issues.extend(self.robustness.check(optimized_code))

        optimized_score = self._calculate_score(optimized_code, new_issues)

        # 生成建议
        suggestions = self._generate_suggestions(issues)

        # 判断通过（没有 error 级别问题，分数 > 70）
        errors = [i for i in new_issues if i.severity == "error"]
        passed = len(errors) == 0 and optimized_score >= 70

        return {
            "optimized_code": optimized_code,
            "original_score": original_score,
            "optimized_score": optimized_score,
            "issues": new_issues,
            "suggestions": suggestions,
            "passed": passed,
        }

    def _calculate_score(self, code: str, issues: List[Optimization]) -> int:
        """计算代码质量分数"""
        score = 100

        weights = {"error": 15, "warning": 5, "suggestion": 1}
        for issue in issues:
            score -= weights.get(issue.severity, 1)

        # 代码长度惩罚
        lines = len([l for l in code.split("\n") if l.strip()])
        if lines > 100:
            score -= (lines - 100) // 10

        return max(0, score)

    def _auto_fix(self, code: str, issues: List[Optimization]) -> str:
        """自动修复代码"""
        lines = code.split("\n")

        # 按行号倒序处理，避免行号变化
        fixable = [i for i in issues if i.auto_fixable and i.fix_code]
        fixable.sort(key=lambda x: x.line, reverse=True)

        for issue in fixable:
            if issue.code == "UNUSED_IMPORT":
                # 删除未使用的导入行
                if 0 < issue.line <= len(lines):
                    lines.pop(issue.line - 1)
            elif issue.code == "REDUNDANT_VARIABLE":
                # 简化冗余变量
                if issue.fix_code:
                    lines[issue.line - 1] = issue.fix_code

        return "\n".join(lines)

    def _generate_suggestions(self, issues: List[Optimization]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        error_types = set(i.code for i in issues)

        if "CODE_TOO_LONG" in error_types:
            suggestions.append(
                "Consider splitting the tool into smaller functions or separate tools"
            )

        if "UNUSED_IMPORT" in error_types:
            suggestions.append("Remove unused imports to reduce dependencies")

        if "DANGEROUS_FUNCTION" in error_types:
            suggestions.append("Replace dangerous functions with safe alternatives")

        if "BARE_EXCEPT" in error_types:
            suggestions.append("Use specific exception types for better error handling")

        if "MISSING_INPUT_VALIDATION" in error_types:
            suggestions.append("Add input validation at function entry points")

        if not suggestions:
            suggestions.append(
                "Code looks good! Consider adding more docstrings for clarity."
            )

        return suggestions

    def print_report(self, result: Dict):
        """打印优化报告"""
        print("\n" + "=" * 60)
        print("Code Optimization Report")
        print("=" * 60)
        print(f"Original Score: {result['original_score']}/100")
        print(f"Optimized Score: {result['optimized_score']}/100")
        status = "[PASS]" if result["passed"] else "[FAIL]"
        print(f"Status: {status}")

        if result["issues"]:
            print(f"\nIssues Found: {len(result['issues'])}")
            errors = [i for i in result["issues"] if i.severity == "error"]
            warnings = [i for i in result["issues"] if i.severity == "warning"]

            if errors:
                print(f"\n  Errors ({len(errors)}):")
                for e in errors[:5]:
                    print(f"    Line {e.line}: {e.code} - {e.message}")

            if warnings:
                print(f"\n  Warnings ({len(warnings)}):")
                for w in warnings[:3]:
                    print(f"    Line {w.line}: {w.code}")

        print("\nSuggestions:")
        for s in result["suggestions"]:
            print(f"  • {s}")

        print("=" * 60)


# 便捷函数
def optimize_code(code: str, tool_name: str = "<generated>") -> Dict:
    """快速优化代码"""
    optimizer = CodeOptimizer()
    return optimizer.optimize(code, tool_name)


if __name__ == "__main__":
    # 测试
    test_code = """
import os
import json
import sys

class TestTool:
    def execute(self, data):
        try:
            result = eval(data)
            temp = result
            return temp
        except:
            return None
"""

    result = optimize_code(test_code, "test.py")

    optimizer = CodeOptimizer()
    optimizer.print_report(result)

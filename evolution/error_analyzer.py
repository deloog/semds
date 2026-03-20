"""
错误分析器 - Phase 2 核心组件

解析测试失败详情，提取关键信息，格式化为 LLM 可理解的反馈。
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


class ErrorType(Enum):
    """错误类型枚举"""

    SYNTAX = "syntax"
    IMPORT = "import"
    RUNTIME = "runtime"
    ASSERTION = "assertion"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class TestFailure:
    """单个测试失败详情"""

    test_name: str
    error_type: ErrorType
    error_message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "test_name": self.test_name,
            "error_type": self.error_type.value,
            "error_message": self.error_message,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
        }


@dataclass
class AnalysisResult:
    """分析结果"""

    total_tests: int
    failed_tests: int
    passed_tests: int
    pass_rate: float
    failures: List[TestFailure] = field(default_factory=list)
    summary: str = ""
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "total_tests": self.total_tests,
            "failed_tests": self.failed_tests,
            "passed_tests": self.passed_tests,
            "pass_rate": self.pass_rate,
            "failures": [f.to_dict() for f in self.failures],
            "summary": self.summary,
            "suggestions": self.suggestions,
        }


class ErrorAnalyzer:
    """
    错误分析器

    解析 pytest 输出，提取结构化错误信息。
    """

    def __init__(self) -> None:
        self.patterns = {
            "test_result": re.compile(r"(\d+) passed|(\d+) failed|(\d+) error"),
            "failure_start": re.compile(r"FAILED\s+([\w/\._:]+::\w+)"),
            "assertion_error": re.compile(
                r"AssertionError:\s*(.+?)(?=\n\n|\Z)", re.DOTALL
            ),
            "syntax_error": re.compile(r"SyntaxError:\s*(.+?)(?=\n\n|\Z)", re.DOTALL),
            "runtime_error": re.compile(r"(\w+Error):\s*(.+?)(?=\n\n|\Z)", re.DOTALL),
            "file_line": re.compile(r'File\s+"([^"]+)"\s*,\s*line\s+(\d+)'),
            "code_context": re.compile(r">\s+(.+?)(?=\nE\s+\w+|$)", re.DOTALL),
        }

    def analyze(self, test_output: str, total_tests: int = 0) -> AnalysisResult:
        """
        分析测试输出

        Args:
            test_output: pytest 原始输出
            total_tests: 测试总数（如果从输出无法解析）

        Returns:
            AnalysisResult 结构化结果
        """
        # 解析基本统计
        passed, failed, errors = self._parse_summary(test_output)

        if total_tests > 0:
            total = total_tests
        else:
            total = passed + failed + errors

        pass_rate = passed / total if total > 0 else 0.0

        # 解析失败详情
        failures = self._parse_failures(test_output)

        # 生成摘要
        summary = self._generate_summary(passed, failed, errors, failures)

        # 生成建议
        suggestions = self._generate_suggestions(failures)

        return AnalysisResult(
            total_tests=total,
            failed_tests=failed + errors,
            passed_tests=passed,
            pass_rate=pass_rate,
            failures=failures,
            summary=summary,
            suggestions=suggestions,
        )

    def _parse_summary(self, output: str) -> Tuple[int, int, int]:
        """解析测试统计摘要"""
        passed = failed = errors = 0

        # 查找 passed/failed/error 数量
        passed_match = re.search(r"(\d+) passed", output)
        if passed_match:
            passed = int(passed_match.group(1))

        failed_match = re.search(r"(\d+) failed", output)
        if failed_match:
            failed = int(failed_match.group(1))

        error_match = re.search(r"(\d+) error", output)
        if error_match:
            errors = int(error_match.group(1))

        return passed, failed, errors

    def _parse_failures(self, output: str) -> List[TestFailure]:
        """解析失败详情"""
        failures = []

        # 分割各个失败块
        failure_blocks = self._split_failure_blocks(output)

        for block in failure_blocks:
            failure = self._parse_failure_block(block)
            if failure:
                failures.append(failure)

        return failures

    def _split_failure_blocks(self, output: str) -> List[str]:
        """将输出分割为独立的失败块"""
        # 匹配 "FAILED test_name" 开头的块
        pattern = r"(FAILED\s+[\w/\._:]+::\w+.*?)(?=FAILED\s+[\w/\._:]+::\w+|=+|$)"
        blocks = re.findall(pattern, output, re.DOTALL)

        if not blocks:
            # 备选：按错误类型分割
            pattern = r"([\w/\._:]+::\w+).*?(?=[\w/\._:]+::\w+|$)"
            blocks = re.findall(pattern, output, re.DOTALL)

        return blocks if blocks else [output]

    def _parse_failure_block(self, block: str) -> Optional[TestFailure]:
        """解析单个失败块"""
        # 提取测试名
        test_name_match = re.search(r"FAILED\s+([\w/\._:]+::\w+)", block)
        if test_name_match:
            test_name = test_name_match.group(1)
        else:
            # 备选：从 def test_xxx 提取
            test_name_match = re.search(r"def\s+(test_\w+)", block)
            test_name = test_name_match.group(1) if test_name_match else "unknown"

        # 确定错误类型
        error_type = self._determine_error_type(block)

        # 提取错误信息
        error_message = self._extract_error_message(block, error_type)

        # 提取文件和行号
        file_path, line_number = self._extract_location(block)

        # 提取代码片段
        code_snippet = self._extract_code_snippet(block)

        return TestFailure(
            test_name=test_name,
            error_type=error_type,
            error_message=error_message,
            file_path=file_path,
            line_number=line_number,
            code_snippet=code_snippet,
        )

    def _determine_error_type(self, block: str) -> ErrorType:
        """确定错误类型"""
        if "SyntaxError" in block:
            return ErrorType.SYNTAX
        elif "ImportError" in block or "ModuleNotFoundError" in block:
            return ErrorType.IMPORT
        elif "AssertionError" in block:
            return ErrorType.ASSERTION
        elif "timeout" in block.lower():
            return ErrorType.TIMEOUT
        elif re.search(r"\w+Error", block):
            return ErrorType.RUNTIME
        else:
            return ErrorType.UNKNOWN

    def _extract_error_message(self, block: str, error_type: ErrorType) -> str:
        """提取错误信息"""
        if error_type == ErrorType.ASSERTION:
            match = re.search(r"E\s+assert\s+(.+?)(?=\n\n|\Z)", block, re.DOTALL)
            if match:
                return f"Assertion failed: {match.group(1).strip()}"

        elif error_type == ErrorType.SYNTAX:
            match = re.search(r"SyntaxError:\s*(.+?)(?=\n|$)", block)
            if match:
                return f"Syntax error: {match.group(1).strip()}"

        elif error_type == ErrorType.RUNTIME:
            match = re.search(r"(\w+Error):\s*(.+?)(?=\n\n|\Z)", block, re.DOTALL)
            if match:
                return f"{match.group(1)}: {match.group(2).strip()[:200]}"

        # 备选：提取 E 行的错误
        match = re.search(r"E\s+(.+?)(?=\n\n|\Z)", block, re.DOTALL)
        if match:
            return match.group(1).strip()[:200]

        return "Unknown error"

    def _extract_location(self, block: str) -> Tuple[Optional[str], Optional[int]]:
        """提取错误位置"""
        match = re.search(r'File\s+"([^"]+)"\s*,\s*line\s+(\d+)', block)
        if match:
            return match.group(1), int(match.group(2))
        return None, None

    def _extract_code_snippet(self, block: str) -> Optional[str]:
        """提取相关代码片段"""
        # 匹配 > 开头的代码行
        match = re.search(r">\s+(.+?)(?=\nE\s+|$)", block, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _generate_summary(
        self, passed: int, failed: int, errors: int, failures: List[TestFailure]
    ) -> str:
        """生成分析摘要"""
        total = passed + failed + errors

        lines = [
            (
                f"Test Results: {passed}/{total} passed ({passed/total*100:.1f}%)"
                if total > 0
                else "No tests run"
            ),
        ]

        if failures:
            lines.append(f"\nFailed tests ({len(failures)}):")
            error_types: Dict[str, int] = {}
            for f in failures:
                et = f.error_type.value
                error_types[et] = error_types.get(et, 0) + 1

            for et, count in sorted(error_types.items(), key=lambda x: -x[1]):
                lines.append(f"  - {et}: {count}")

        return "\n".join(lines)

    def _generate_suggestions(self, failures: List[TestFailure]) -> List[str]:
        """生成修复建议"""
        suggestions = []

        error_types = set(f.error_type for f in failures)

        if ErrorType.SYNTAX in error_types:
            suggestions.append("Fix syntax errors before running tests")

        if ErrorType.IMPORT in error_types:
            suggestions.append("Check import statements and dependencies")

        if ErrorType.ASSERTION in error_types:
            suggestions.append("Review assertion logic and expected values")

        if ErrorType.RUNTIME in error_types:
            suggestions.append("Handle edge cases and input validation")

        return suggestions

    def format_for_llm(self, result: AnalysisResult, code: str = "") -> str:
        """
        格式化为 LLM 反馈

        Args:
            result: 分析结果
            code: 原始代码（可选，用于上下文）

        Returns:
            格式化后的反馈文本
        """
        lines = [
            "=" * 60,
            "TEST FAILURE ANALYSIS",
            "=" * 60,
            "",
            (
                f"Pass Rate: {result.pass_rate:.1%} "
                f"({result.passed_tests}/{result.total_tests})"
            ),
            "",
            "Failures:",
        ]

        for i, failure in enumerate(result.failures, 1):
            lines.extend(
                [
                    f"\n{i}. {failure.test_name}",
                    f"   Type: {failure.error_type.value}",
                    f"   Error: {failure.error_message[:150]}",
                ]
            )
            if failure.line_number:
                lines.append(f"   Line: {failure.line_number}")
            if failure.code_snippet:
                lines.append(f"   Code: {failure.code_snippet[:100]}")

        if result.suggestions:
            lines.extend(
                [
                    "",
                    "Suggestions:",
                ]
            )
            for s in result.suggestions:
                lines.append(f"  - {s}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

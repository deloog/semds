"""Test Runner 测试模块

测试 TestRunner 类的各项功能
包括测试执行、结果解析等
"""

from unittest.mock import MagicMock, patch

import pytest


class TestTestRunnerInit:
    """TestRunner 初始化测试"""

    def test_init_default_values(self):
        """测试使用默认值初始化"""
        from evolution.test_runner import TestRunner

        runner = TestRunner()

        assert runner.timeout_seconds == 30
        assert runner.verbose is False

    def test_init_custom_values(self):
        """测试使用自定义值初始化"""
        from evolution.test_runner import TestRunner

        runner = TestRunner(timeout_seconds=60, verbose=True)

        assert runner.timeout_seconds == 60
        assert runner.verbose is True


class TestCheckJsonReport:
    """测试 _check_json_report 方法"""

    @patch("importlib.util.find_spec")
    def test_json_report_available(self, mock_find_spec):
        """测试检测到 json-report 插件"""
        from evolution.test_runner import TestRunner

        mock_find_spec.return_value = MagicMock()  # 找到模块

        runner = TestRunner()
        result = runner._check_json_report()
        assert result is True

    @patch("importlib.util.find_spec")
    def test_json_report_not_available(self, mock_find_spec):
        """测试未检测到 json-report 插件"""
        from evolution.test_runner import TestRunner

        mock_find_spec.return_value = None  # 未找到模块

        runner = TestRunner()
        result = runner._check_json_report()
        assert result is False

    @patch("importlib.util.find_spec")
    def test_check_json_report_exception(self, mock_find_spec):
        """测试检测时发生异常"""
        from evolution.test_runner import TestRunner

        mock_find_spec.side_effect = Exception("Some error")

        runner = TestRunner()
        result = runner._check_json_report()
        assert result is False


class TestParseStandardOutput:
    """测试 _parse_standard_output 方法"""

    @pytest.fixture
    def runner(self):
        """创建测试用的 runner"""
        from evolution.test_runner import TestRunner

        return TestRunner()

    def test_parse_passed_tests(self, runner):
        """测试解析通过的测试"""
        output = """
test_file.py::test_one PASSED
test_file.py::test_two PASSED
========================= 2 passed in 0.01s =========================
"""
        result = runner._parse_standard_output(output)

        assert result["total_tests"] == 2
        assert len(result["passed"]) == 2
        assert len(result["failed"]) == 0
        assert result["pass_rate"] == 1.0

    def test_parse_failed_tests(self, runner):
        """测试解析失败的测试"""
        output = """
test_file.py::test_one PASSED
test_file.py::test_two FAILED
========================= 1 failed, 1 passed in 0.01s =========================
"""
        result = runner._parse_standard_output(output)

        assert result["total_tests"] == 2
        assert len(result["passed"]) == 1
        assert len(result["failed"]) == 1
        assert result["pass_rate"] == 0.5

    def test_parse_error_tests(self, runner):
        """测试解析错误的测试"""
        output = """
test_file.py::test_one ERROR
test_file.py::test_two PASSED
"""
        result = runner._parse_standard_output(output)

        assert result["total_tests"] == 2
        assert len(result["passed"]) == 1
        assert len(result["failed"]) == 1  # ERROR 被归类为 failed

    def test_parse_empty_output(self, runner):
        """测试解析空输出"""
        result = runner._parse_standard_output("")

        assert result["total_tests"] == 0
        assert result["pass_rate"] == 0.0

    def test_parse_no_test_lines(self, runner):
        """测试解析没有测试行的输出"""
        output = "Some random text without test results"
        result = runner._parse_standard_output(output)

        assert result["total_tests"] == 0
        assert result["pass_rate"] == 0.0


class TestFormatTestCode:
    """测试 _format_test_code 方法"""

    @pytest.fixture
    def runner(self):
        """创建测试用的 runner"""
        from evolution.test_runner import TestRunner

        return TestRunner()

    def test_format_simple_assert(self, runner):
        """测试格式化简单 assert"""
        code = """
assert add(1, 2) == 3
assert add(0, 0) == 0
"""
        result = runner._format_test_code(code)

        assert "def test_solution():" in result
        assert "from solution import *" in result
        assert "assert add(1, 2) == 3" in result

    def test_format_already_pytest_format(self, runner):
        """测试已经是 pytest 格式的代码"""
        code = """
from solution import add

def test_add():
    assert add(1, 2) == 3
"""
        result = runner._format_test_code(code)

        assert "def test_add():" in result
        # 应该保持原有格式

    def test_format_with_import(self, runner):
        """测试格式化时移除已有的 import"""
        code = """
from solution import add
assert add(1, 2) == 3
"""
        result = runner._format_test_code(code)

        # 应该只有一个 import
        assert result.count("from solution import") == 1


class TestRunTestsWithCode:
    """测试 run_tests_with_code 方法"""

    @patch("evolution.test_runner.TestRunner.run_tests")
    @patch("tempfile.mkdtemp")
    @patch("builtins.open")
    def test_creates_temp_files(self, mock_open, mock_mkdtemp, mock_run_tests):
        """测试创建临时文件"""
        from evolution.test_runner import TestRunner
        import os

        mock_mkdtemp.return_value = os.path.normpath("/tmp/test_dir")
        mock_run_tests.return_value = {
            "success": True,
            "pass_rate": 1.0,
            "passed": [],
            "failed": [],
        }

        runner = TestRunner()
        result = runner.run_tests_with_code(
            code="def add(a, b): return a + b",
            test_code="assert add(1, 2) == 3",
        )

        assert result is not None
        # 验证文件写入被调用
        assert mock_open.call_count >= 2  # solution.py 和 test_solution.py


class TestIndentCode:
    """测试 _indent_code 方法"""

    @pytest.fixture
    def runner(self):
        """创建测试用的 runner"""
        from evolution.test_runner import TestRunner

        return TestRunner()

    def test_indent_code_default(self, runner):
        """测试默认缩进"""
        code = "line1\nline2"
        result = runner._indent_code(code)

        assert result.startswith("    line1")
        assert "    line2" in result

    def test_indent_code_custom(self, runner):
        """测试自定义缩进"""
        code = "line1"
        result = runner._indent_code(code, indent=2)

        assert result == "  line1"

    def test_indent_preserves_empty_lines(self, runner):
        """测试保留空行"""
        code = "line1\n\nline2"
        result = runner._indent_code(code)

        lines = result.split("\n")
        assert lines[0] == "    line1"
        assert lines[1] == ""  # 空行应该保持为空

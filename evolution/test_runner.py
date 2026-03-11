"""
SEMDS Test Runner - Layer 1

测试运行器，负责在沙盒中执行测试并收集结果。

Phase 1: 使用subprocess直接执行pytest（无Docker隔离）
Phase 2: 将替换为Docker沙盒执行

本模块提供：
- TestRunner: 测试运行器类
"""

import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TestResult:
    """单个测试用例的结果。"""

    name: str
    passed: bool
    error_message: Optional[str] = None
    duration_ms: float = 0.0


class TestRunner:
    """
    测试运行器，执行pytest并解析结果。

    Phase 1实现使用subprocess直接执行，无Docker隔离。

    Attributes:
        timeout_seconds: 测试执行超时时间（秒）
        verbose: 是否输出详细日志
    """

    def __init__(self, timeout_seconds: int = 30, verbose: bool = False):
        """
        初始化测试运行器。

        Args:
            timeout_seconds: 测试执行超时时间（秒）
            verbose: 是否输出详细日志
        """
        self.timeout_seconds = timeout_seconds
        self.verbose = verbose

    def run_tests(
        self,
        test_file_path: str,
        solution_file_path: Optional[str] = None,
        working_dir: Optional[str] = None,
    ) -> dict:
        """
        运行测试文件并返回结果。

        Args:
            test_file_path: 测试文件的路径
            solution_file_path: 被测试的解决方案文件路径（用于import）
            working_dir: 工作目录（如果为None，使用测试文件所在目录）

        Returns:
            字典包含：
            - success: bool - 测试是否成功完成（注意：不是测试是否通过）
            - pass_rate: float - 测试通过率（0.0-1.0）
            - passed: list - 通过的测试名称列表
            - failed: list - 失败的测试名称列表
            - execution_time_ms: float - 执行时间（毫秒）
            - total_tests: int - 测试总数
            - raw_output: str - pytest原始输出
            - error: str - 错误信息（如果执行失败）
        """
        import time

        result = {
            "success": False,
            "pass_rate": 0.0,
            "passed": [],
            "failed": [],
            "execution_time_ms": 0.0,
            "total_tests": 0,
            "raw_output": "",
            "error": None,
        }

        # 确定工作目录
        if working_dir is None:
            working_dir = os.path.dirname(os.path.abspath(test_file_path))

        # 确保测试文件存在
        if not os.path.exists(test_file_path):
            result["error"] = f"Test file not found: {test_file_path}"
            return result

        # 构建pytest命令
        # 使用JSON报告格式便于解析
        cmd = [
            "python",
            "-m",
            "pytest",
            test_file_path,
            "-v",  # 详细输出
            "--tb=short",  # 短 traceback
            "--json-report",  # 生成JSON报告（需要pytest-json-report插件）
            "--json-report-file=-",  # 输出到stdout
        ]

        # 如果没有pytest-json-report，使用标准输出解析
        # 先尝试检测
        has_json_report = self._check_json_report()
        if not has_json_report:
            cmd = [
                "python",
                "-m",
                "pytest",
                test_file_path,
                "-v",
                "--tb=short",
            ]

        start_time = time.time()

        try:
            # 执行pytest
            process = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )

            execution_time = (time.time() - start_time) * 1000  # 转换为毫秒
            result["execution_time_ms"] = round(execution_time, 2)
            result["raw_output"] = process.stdout + "\n" + process.stderr

            if self.verbose:
                print(f"[TestRunner] pytest exit code: {process.returncode}")
                print(f"[TestRunner] stdout:\n{process.stdout}")
                print(f"[TestRunner] stderr:\n{process.stderr}")

            # 解析结果
            if has_json_report:
                parsed = self._parse_json_output(process.stdout)
            else:
                parsed = self._parse_standard_output(process.stdout)

            result.update(parsed)
            result["success"] = True

        except subprocess.TimeoutExpired:
            result["error"] = (
                f"Test execution timed out after {self.timeout_seconds} " f"seconds"
            )
            result["execution_time_ms"] = self.timeout_seconds * 1000

        except FileNotFoundError:
            result["error"] = (
                "pytest not found. Please install pytest: pip install pytest"
            )

        except Exception as e:
            result["error"] = f"Test execution failed: {str(e)}"

        return result

    def run_tests_with_code(
        self, code: str, test_code: str, working_dir: Optional[str] = None
    ) -> dict:
        """
        将代码写入临时文件并运行测试。

        这是一个便捷方法，用于Phase 1的快速测试。

        Args:
            code: 要测试的解决方案代码
            test_code: 测试代码
            working_dir: 工作目录（如果为None，创建临时目录）

        Returns:
            测试结果字典（同run_tests）
        """
        # 创建临时目录
        if working_dir is None:
            working_dir = tempfile.mkdtemp(prefix="semds_test_")
        else:
            os.makedirs(working_dir, exist_ok=True)

        # 写入解决方案文件
        solution_path = os.path.join(working_dir, "solution.py")
        with open(solution_path, "w", encoding="utf-8") as f:
            f.write(code)

        # 写入测试文件
        test_path = os.path.join(working_dir, "test_solution.py")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_code)

        # 运行测试
        return self.run_tests(test_path, solution_path, working_dir)

    def _check_json_report(self) -> bool:
        """检查是否安装了pytest-json-report插件。"""
        try:
            subprocess.run(
                ["python", "-m", "pytest", "--version"],
                capture_output=True,
                text=True,
            )
            # 简单检查：尝试运行带--json-report的pytest
            test_result = subprocess.run(
                ["python", "-m", "pytest", "--json-report", "--help"],
                capture_output=True,
                text=True,
            )
            return test_result.returncode == 0
        except Exception:
            return False

    def _parse_json_output(self, output: str) -> dict:
        """
        解析pytest-json-report的JSON输出。

        Args:
            output: pytest的stdout输出

        Returns:
            解析后的结果字典
        """
        result: dict[str, Any] = {
            "pass_rate": 0.0,
            "passed": [],
            "failed": [],
            "total_tests": 0,
        }

        try:
            # 查找JSON部分（通常在输出的最后）
            lines = output.strip().split("\n")
            json_str = None

            # 尝试找到JSON开始的位置
            for i, line in enumerate(lines):
                if line.strip().startswith("{"):
                    json_str = "\n".join(lines[i:])
                    break

            if json_str:
                data = json.loads(json_str)

                tests = data.get("tests", [])
                result["total_tests"] = len(tests)

                for test in tests:
                    test_name = test.get("nodeid", "unknown")
                    outcome = test.get("outcome", "unknown")

                    if outcome == "passed":
                        result["passed"].append(test_name)
                    else:
                        result["failed"].append(test_name)

                if result["total_tests"] > 0:
                    result["pass_rate"] = len(result["passed"]) / result["total_tests"]

        except json.JSONDecodeError:
            # JSON解析失败，回退到标准解析
            return self._parse_standard_output(output)
        except Exception as e:
            result["error"] = f"Failed to parse JSON output: {e}"

        return result

    def _parse_standard_output(self, output: str) -> dict:
        """
        解析pytest标准文本输出。

        Args:
            output: pytest的stdout输出

        Returns:
            解析后的结果字典
        """
        result: dict[str, Any] = {
            "pass_rate": 0.0,
            "passed": [],
            "failed": [],
            "total_tests": 0,
        }

        passed: list[str] = []
        failed: list[str] = []

        # 解析每一行
        for line in output.split("\n"):
            line = line.strip()

            # 匹配通过的测试: "test_file.py::TestClass::test_method PASSED"
            passed_match = re.match(r"(.*?)\s+PASSED", line)
            if passed_match:
                test_name = passed_match.group(1).strip()
                passed.append(test_name)
                continue

            # 匹配的失败测试: "test_file.py::TestClass::test_method FAILED"
            failed_match = re.match(r"(.*?)\s+FAILED", line)
            if failed_match:
                test_name = failed_match.group(1).strip()
                failed.append(test_name)
                continue

            # 匹配错误测试: "test_file.py::TestClass::test_method ERROR"
            error_match = re.match(r"(.*?)\s+ERROR", line)
            if error_match:
                test_name = error_match.group(1).strip()
                failed.append(test_name)

        result["passed"] = passed
        result["failed"] = failed
        result["total_tests"] = len(passed) + len(failed)

        if result["total_tests"] > 0:
            result["pass_rate"] = len(passed) / result["total_tests"]

        return result


if __name__ == "__main__":
    # 简单测试
    runner = TestRunner(verbose=True)

    # 测试代码
    solution_code = """
def add(a, b):
    return a + b
"""

    test_code = """
import pytest
from solution import add

def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -1) == -2

def test_add_mixed():
    assert add(-1, 1) == 0
"""

    result = runner.run_tests_with_code(solution_code, test_code)

    print("\n=== Test Result ===")
    print(f"Success: {result['success']}")
    print(f"Pass Rate: {result['pass_rate']:.2%}")
    print(f"Passed: {len(result['passed'])}")
    print(f"Failed: {len(result['failed'])}")
    print(f"Execution Time: {result['execution_time_ms']:.2f} ms")
    if result["error"]:
        print(f"Error: {result['error']}")

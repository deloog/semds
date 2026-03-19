"""
Phase 3 Mock LLM 压力测试

使用 Mock 代码生成器验证系统完整性和评估器一致性。
无需外部 API，可重复运行。
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.orchestrator import EvolutionOrchestrator
from evolution.test_runner import TestRunner
from evolution.dual_evaluator import DualEvaluator
from evolution.strategy_optimizer import StrategyOptimizer
from evolution.termination_checker import TerminationConfig


class MockCodeGenerator:
    """
    Mock 代码生成器，用于压力测试。

    可以配置返回不同质量的代码：
    - perfect: 完美代码（通过所有测试，高质量）
    - good: 良好代码（通过测试，中等质量）
    - buggy: 有缺陷代码（部分测试失败）
    - syntax_error: 语法错误代码
    """

    def __init__(self, mode="perfect", fixed_code=None):
        self.mode = mode
        self.fixed_code = fixed_code
        self.call_count = 0

    def generate(self, task_spec, **kwargs):
        """模拟代码生成"""
        self.call_count += 1

        if self.fixed_code:
            code = self.fixed_code
        elif self.mode == "perfect":
            code = self._generate_perfect_code(task_spec)
        elif self.mode == "good":
            code = self._generate_good_code(task_spec)
        elif self.mode == "buggy":
            code = self._generate_buggy_code(task_spec)
        elif self.mode == "syntax_error":
            code = "def solution():\n    return 1 + "  # 语法错误
        else:
            code = "def solution():\n    pass"

        return {
            "success": True,
            "code": code,
            "raw_response": f"```python\n{code}\n```",
            "error": None,
        }

    def _generate_perfect_code(self, task_spec):
        """生成完美代码"""
        desc = task_spec.get("description", "").lower()

        if "add" in desc or "加法" in desc:
            return '''def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b'''
        elif "sort" in desc or "排序" in desc:
            return '''def sort_list(arr: list) -> list:
    """Sort a list in ascending order."""
    return sorted(arr)'''
        elif "reverse" in desc or "反转" in desc:
            return '''def reverse_string(s: str) -> str:
    """Reverse a string."""
    return s[::-1]'''
        elif "fibonacci" in desc or "fib" in desc:
            return '''def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n < 0:
        raise ValueError("n must be non-negative")
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b'''
        else:
            return '''def solution():
    """Default solution."""
    return 42'''

    def _generate_good_code(self, task_spec):
        """生成良好但不够完美的代码（无类型注解）"""
        desc = task_spec.get("description", "").lower()

        if "add" in desc:
            return "def add(a, b):\n    return a + b"
        else:
            return "def solution():\n    return 42"

    def _generate_buggy_code(self, task_spec):
        """生成有缺陷的代码"""
        desc = task_spec.get("description", "").lower()

        if "add" in desc:
            return "def add(a, b):\n    return a - b"  # 错误的实现
        else:
            return "def solution():\n    return None"


def run_stress_test():
    """运行压力测试"""
    print("=" * 70)
    print("Phase 3 Mock LLM 压力测试")
    print("=" * 70)
    print(f"开始时间: {datetime.now().isoformat()}")
    print()

    # 测试场景
    # 注意：得分期望基于当前评估器配置（内生0.6权重 + 外生0.4权重）
    scenarios = [
        {
            "name": "Perfect Code - Addition",
            "mock_mode": "perfect",
            "requirements": ["Implement add(a, b) function"],
            "test_code": "assert add(1, 2) == 3\nassert add(-1, 1) == 0",
            "expected_score": 0.7,  # 内生~0.95, 外生~0.5, 加权~0.7
        },
        {
            "name": "Good Code - Addition (no type hints)",
            "mock_mode": "good",
            "requirements": ["Implement add(a, b) function"],
            "test_code": "assert add(1, 2) == 3\nassert add(-1, 1) == 0",
            "expected_score": 0.6,  # 内生~0.7, 外生~0.4, 加权~0.6
        },
        {
            "name": "Buggy Code - Subtraction instead of Addition",
            "mock_mode": "buggy",
            "requirements": ["Implement add(a, b) function"],
            "test_code": "assert add(1, 2) == 3\nassert add(-1, 1) == 0",
            "expected_score": 0.4,  # 内生~0.6, 外生~0.2, 加权~0.4 (测试失败但代码结构尚可)
        },
        {
            "name": "Perfect Code - Fibonacci",
            "mock_mode": "perfect",
            "requirements": ["Implement fibonacci(n) function"],
            "test_code": "assert fibonacci(0) == 0\nassert fibonacci(1) == 1\nassert fibonacci(10) == 55",
            "expected_score": 0.7,
        },
    ]

    results = []

    for scenario in scenarios:
        print(f"\n{'-' * 70}")
        print(f"场景: {scenario['name']}")
        print(f"{'-' * 70}")

        # 创建 Mock 生成器
        mock_generator = MockCodeGenerator(mode=scenario["mock_mode"])

        # 配置终止条件
        config = TerminationConfig(
            success_threshold=0.85,
            max_generations=5,
            stagnation_generations=3,
        )

        orchestrator = EvolutionOrchestrator(
            task_id=f"mock_test_{scenario['name']}",
            code_generator=mock_generator,
            termination_config=config,
        )

        start_time = time.time()

        try:
            result = orchestrator.evolve(
                requirements=scenario["requirements"],
                test_code=scenario["test_code"],
                max_generations=5,
            )

            elapsed = time.time() - start_time

            # 验证结果
            score_match = abs(result.best_score - scenario["expected_score"]) < 0.2

            print(f"  代数: {result.generations}")
            print(
                f"  得分: {result.best_score:.4f} (期望: ~{scenario['expected_score']})"
            )
            print(f"  成功: {result.success}")
            print(f"  终止: {result.termination_reason}")
            print(f"  时间: {elapsed:.2f}s")
            print(f"  得分验证: {'PASS' if score_match else 'FAIL'}")

            results.append(
                {
                    "scenario": scenario["name"],
                    "passed": score_match,
                    "generations": result.generations,
                    "score": result.best_score,
                    "time": elapsed,
                }
            )

        except Exception as e:
            print(f"  [ERROR] {e}")
            results.append(
                {
                    "scenario": scenario["name"],
                    "passed": False,
                    "error": str(e),
                }
            )

    # 汇总
    print(f"\n{'=' * 70}")
    print("测试结果汇总")
    print(f"{'=' * 70}")

    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)

    for r in results:
        status = "PASS" if r.get("passed") else "FAIL"
        print(f"  [{status}] {r['scenario']}")

    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.0f}%)")

    if passed == total:
        print("\n[SUCCESS] 所有测试场景通过！系统功能完整。")
        return 0
    else:
        print(f"\n[WARNING] {total - passed} 个场景失败，需要检查。")
        return 1


if __name__ == "__main__":
    exit_code = run_stress_test()
    sys.exit(exit_code)

"""
Extrinsic Evaluator 测试模块 - TDD Red Phase

测试 ExtrinsicEvaluator 类 - 外生评估（行为一致性验证）
通过生成边界用例验证代码行为一致性

测试目标：
1. P0: 危险代码模式检测
2. P0: 边界用例生成与执行
3. P1: 行为一致性评分
4. P1: 综合外生评估
"""

# Import will be added after implementation exists
# from evolution.extrinsic_evaluator import ExtrinsicEvaluator, EvaluationResult


# =============================================================================
# Test ExtrinsicEvaluator - Dangerous Pattern Detection
# =============================================================================


class TestExtrinsicEvaluatorDangerousPatterns:
    """危险代码模式检测测试（P0优先级）"""

    def test_detects_eval_usage(self):
        """测试检测eval使用"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = "result = eval('1 + 1')"
        score = evaluator._static_analysis(code)

        # 使用eval应该大幅降低得分
        assert score < 0.5, f"Expected low score for eval usage, got {score}"

    def test_detects_exec_usage(self):
        """测试检测exec使用"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = "exec('print(hello)')"
        score = evaluator._static_analysis(code)

        assert score < 0.5, f"Expected low score for exec usage, got {score}"

    def test_detects_compile_with_dangerous_mode(self):
        """测试检测compile危险模式"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = "compile('1+1', '<string>', 'exec')"
        score = evaluator._static_analysis(code)

        assert score < 1.0, f"Expected reduced score for compile, got {score}"

    def test_detects_hardcoded_secrets(self):
        """测试检测硬编码密钥"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = 'API_KEY = "sk-1234567890abcdef"'
        score = evaluator._static_analysis(code)

        assert score < 1.0, f"Expected reduced score for hardcoded secret, got {score}"

    def test_detects_dangerous_file_operations(self):
        """测试检测危险文件操作"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
import os
os.system('rm -rf /')
"""
        score = evaluator._static_analysis(code)

        assert (
            score < 0.3
        ), f"Expected very low score for dangerous os.system, got {score}"

    def test_detects_subprocess_shell_true(self):
        """测试检测subprocess with shell=True"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
import subprocess
subprocess.run('ls', shell=True)
"""
        score = evaluator._static_analysis(code)

        assert score < 0.5, f"Expected low score for shell=True, got {score}"


# =============================================================================
# Test ExtrinsicEvaluator - Good Practices
# =============================================================================


class TestExtrinsicEvaluatorGoodPractices:
    """良好实践奖励测试（P0优先级）"""

    def test_rewards_type_annotations(self):
        """测试奖励类型注解"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def calculate(a: int, b: int) -> int:
    return a + b
"""
        score = evaluator._static_analysis(code)

        assert score > 0.5, f"Expected good score for typed code, got {score}"

    def test_rewards_error_handling(self):
        """测试奖励错误处理"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        return float('inf')
"""
        score = evaluator._static_analysis(code)

        assert score > 0.5, f"Expected good score for error handling, got {score}"

    def test_rewards_docstrings(self):
        """测试奖励文档字符串"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = '''
def helper():
    """This is a helper function."""
    pass
'''
        score = evaluator._static_analysis(code)

        assert score > 0.5, f"Expected good score for documented code, got {score}"

    def test_perfect_code_gets_high_score(self):
        """测试完美代码获得高分"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
\"\"\"Well-structured module.\"\"\"

from typing import List, Optional


def process_data(items: List[int]) -> Optional[int]:
    \"\"\"Process a list of integers.

    Args:
        items: List of integers to process

    Returns:
        Sum of items or None if empty
    \"\"\"
    if not items:
        return None
    return sum(items)
"""
        score = evaluator._static_analysis(code)

        assert score >= 0.8, f"Expected high score for perfect code, got {score}"


# =============================================================================
# Test ExtrinsicEvaluator - Edge Case Generation
# =============================================================================


class TestExtrinsicEvaluatorEdgeCaseGeneration:
    """边界用例生成测试（P0优先级）"""

    def test_generates_edge_cases_for_add_function(self):
        """测试为加法函数生成边界用例"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        signature = "add(a: int, b: int) -> int"
        edge_cases = evaluator._generate_edge_cases(signature)

        # 应该生成多个边界用例
        assert (
            len(edge_cases) >= 3
        ), f"Expected at least 3 edge cases, got {len(edge_cases)}"

    def test_edge_cases_include_zero(self):
        """测试边界用例包含零值"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        signature = "multiply(a: int, b: int) -> int"
        edge_cases = evaluator._generate_edge_cases(signature)

        # 检查是否有零值
        has_zero = any(case.get("a") == 0 or case.get("b") == 0 for case in edge_cases)
        assert has_zero, "Expected edge cases to include zero values"

    def test_edge_cases_include_negative(self):
        """测试边界用例包含负值"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        signature = "abs_value(x: int) -> int"
        edge_cases = evaluator._generate_edge_cases(signature)

        # 检查是否有负值
        has_negative = any(case.get("x", 0) < 0 for case in edge_cases)
        assert has_negative, "Expected edge cases to include negative values"

    def test_edge_cases_include_large_values(self):
        """测试边界用例包含大数值"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        signature = "process(n: int) -> int"
        edge_cases = evaluator._generate_edge_cases(signature)

        # 检查是否有大数值
        has_large = any(abs(case.get("n", 0)) > 1000 for case in edge_cases)
        assert has_large, "Expected edge cases to include large values"

    def test_edge_case_has_expected_structure(self):
        """测试边界用例有正确的结构"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        signature = "func(x: int, y: str) -> bool"
        edge_cases = evaluator._generate_edge_cases(signature)

        for case in edge_cases:
            assert "inputs" in case or "x" in case, "Edge case should have inputs"
            assert "description" in case, "Edge case should have description"


# =============================================================================
# Test ExtrinsicEvaluator - Behavior Consistency
# =============================================================================


class TestExtrinsicEvaluatorBehaviorConsistency:
    """行为一致性测试（P1优先级）"""

    def test_evaluates_code_consistency(self):
        """测试评估代码一致性"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def add(a, b):
    return a + b
"""
        result = evaluator.evaluate(
            code=code,
            function_signature="add(a, b)",
            requirements=["Should return sum of two numbers"],
        )

        assert "consistency_score" in result
        assert 0.0 <= result["consistency_score"] <= 1.0

    def test_consistent_code_gets_high_score(self):
        """测试一致代码获得高分"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def add(a: int, b: int) -> int:
    \"\"\"Add two integers.\"\"\"
    return a + b
"""
        result = evaluator.evaluate(
            code=code,
            function_signature="add(a: int, b: int) -> int",
            requirements=["Returns sum of a and b"],
        )

        assert result["consistency_score"] > 0.7

    def test_inconsistent_code_gets_low_score(self):
        """测试不一致代码获得低分"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        # 这个函数声称是加法但实际做减法
        code = """
def add(a, b):
    return a - b  # Wrong operation!
"""
        result = evaluator.evaluate(
            code=code,
            function_signature="add(a, b)",
            requirements=["Should return a + b"],
        )

        assert result["consistency_score"] < 0.5


# =============================================================================
# Test ExtrinsicEvaluator - Full Evaluation
# =============================================================================


class TestExtrinsicEvaluatorFullEvaluation:
    """完整评估流程测试（P1优先级）"""

    def test_full_evaluation_returns_complete_result(self):
        """测试完整评估返回完整结果"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def multiply(a: int, b: int) -> int:
    \"\"\"Multiply two integers.\"\"\"
    return a * b
"""
        result = evaluator.evaluate(
            code=code,
            function_signature="multiply(a: int, b: int) -> int",
            requirements=["Returns product of a and b"],
        )

        # 检查结果包含所有必要字段
        assert "score" in result
        assert "consistency_score" in result
        assert "static_analysis_score" in result
        assert "edge_case_results" in result

    def test_evaluation_score_is_weighted(self):
        """测试评估得分是加权的"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def func(x):
    return x
"""
        result = evaluator.evaluate(
            code=code,
            function_signature="func(x: int) -> int",
            requirements=["Returns input"],
        )

        # 总得分应该在各分项之间
        scores = [result["consistency_score"], result["static_analysis_score"]]
        assert min(scores) <= result["score"] <= max(scores) or result["score"] == 0

    def test_edge_case_results_included(self):
        """测试结果包含边界用例执行结果"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def double(x):
    return x * 2
"""
        result = evaluator.evaluate(
            code=code,
            function_signature="double(x: int) -> int",
            requirements=["Returns x * 2"],
        )

        assert "edge_case_results" in result
        assert isinstance(result["edge_case_results"], list)

    def test_edge_case_result_has_required_fields(self):
        """测试边界用例结果有必需字段"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def identity(x):
    return x
"""
        result = evaluator.evaluate(
            code=code, function_signature="identity(x)", requirements=["Returns x"]
        )

        for edge_result in result["edge_case_results"]:
            assert "inputs" in edge_result
            assert "expected" in edge_result
            assert "actual" in edge_result
            assert "passed" in edge_result


# =============================================================================
# Test ExtrinsicEvaluator - Edge Cases
# =============================================================================


class TestExtrinsicEvaluatorEdgeCases:
    """边界情况测试"""

    def test_handles_empty_code(self):
        """测试处理空代码"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        result = evaluator.evaluate(
            code="", function_signature="func()", requirements=[]
        )

        assert result["score"] == 0.0

    def test_handles_syntax_error_code(self):
        """测试处理语法错误代码"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        result = evaluator.evaluate(
            code="def broken(", function_signature="broken()", requirements=[]
        )

        assert result["score"] == 0.0

    def test_handles_complex_function_signature(self):
        """测试处理复杂函数签名"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        signature = (
            "process(data: List[Dict[str, Any]], config: Optional[Config]) -> Result"
        )
        edge_cases = evaluator._generate_edge_cases(signature)

        # 应该能处理复杂签名
        assert isinstance(edge_cases, list)

    def test_handles_function_with_multiple_args(self):
        """测试处理多参数函数"""
        from evolution.extrinsic_evaluator import ExtrinsicEvaluator

        evaluator = ExtrinsicEvaluator()
        code = """
def combine(a, b, c, d):
    return a + b + c + d
"""
        result = evaluator.evaluate(
            code=code,
            function_signature="combine(a, b, c, d)",
            requirements=["Returns sum of all arguments"],
        )

        assert "score" in result

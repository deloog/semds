"""
Intrinsic Evaluator 测试模块 - TDD Red Phase

测试 IntrinsicEvaluator 类 - 静态代码质量评估
无需执行测试，仅分析代码本身

测试目标（按优先级排序）：
1. P0: 语法正确性检查
2. P0: 静态分析得分
3. P1: 代码结构评估
4. P1: 文档完整性
"""

# Import will be added after implementation exists
# from evolution.intrinsic_evaluator import IntrinsicEvaluator, EvaluationResult


# =============================================================================
# Test EvaluationResult Dataclass
# =============================================================================


class TestEvaluationResult:
    """EvaluationResult 数据类测试"""

    def test_result_has_syntax_valid_field(self):
        """测试结果包含语法有效性字段"""
        from evolution.intrinsic_evaluator import (
            EvaluationResult,
        )

        result = EvaluationResult(
            syntax_valid=True,
            static_score=0.85,
            structure_score=0.75,
            doc_score=0.60,
            total_score=0.73,
        )
        assert result.syntax_valid is True

    def test_result_has_static_score_field(self):
        """测试结果包含静态分析得分字段"""
        from evolution.intrinsic_evaluator import EvaluationResult

        result = EvaluationResult(
            syntax_valid=True,
            static_score=0.85,
            structure_score=0.75,
            doc_score=0.60,
            total_score=0.73,
        )
        assert result.static_score == 0.85

    def test_result_has_structure_score_field(self):
        """测试结果包含结构得分字段"""
        from evolution.intrinsic_evaluator import EvaluationResult

        result = EvaluationResult(
            syntax_valid=True,
            static_score=0.85,
            structure_score=0.75,
            doc_score=0.60,
            total_score=0.73,
        )
        assert result.structure_score == 0.75

    def test_result_has_doc_score_field(self):
        """测试结果包含文档得分字段"""
        from evolution.intrinsic_evaluator import EvaluationResult

        result = EvaluationResult(
            syntax_valid=True,
            static_score=0.85,
            structure_score=0.75,
            doc_score=0.60,
            total_score=0.73,
        )
        assert result.doc_score == 0.60

    def test_result_has_total_score_field(self):
        """测试结果包含总得分字段"""
        from evolution.intrinsic_evaluator import EvaluationResult

        result = EvaluationResult(
            syntax_valid=True,
            static_score=0.85,
            structure_score=0.75,
            doc_score=0.60,
            total_score=0.73,
        )
        assert result.total_score == 0.73

    def test_result_allows_optional_details(self):
        """测试结果允许可选详细信息"""
        from evolution.intrinsic_evaluator import EvaluationResult

        result = EvaluationResult(
            syntax_valid=True,
            static_score=0.85,
            structure_score=0.75,
            doc_score=0.60,
            total_score=0.73,
            syntax_errors=["Line 10: invalid syntax"],
            warnings=["Line 5: unused import"],
        )
        assert result.syntax_errors == ["Line 10: invalid syntax"]
        assert result.warnings == ["Line 5: unused import"]


# =============================================================================
# Test IntrinsicEvaluator - Core Functionality
# =============================================================================


class TestIntrinsicEvaluatorSyntax:
    """语法正确性评估测试（P0优先级）"""

    def test_evaluate_valid_syntax_code(self):
        """测试评估语法正确的代码"""
        from evolution.intrinsic_evaluator import (
            IntrinsicEvaluator,
        )

        evaluator = IntrinsicEvaluator()
        code = """
def add(a, b):
    return a + b
"""
        result = evaluator.evaluate(code)

        assert result.syntax_valid is True
        assert result.total_score > 0

    def test_evaluate_invalid_syntax_code(self):
        """测试评估语法错误的代码"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
def broken_function(
    # Missing closing parenthesis and colon
"""
        result = evaluator.evaluate(code)

        assert result.syntax_valid is False
        assert len(result.syntax_errors) > 0

    def test_evaluate_code_with_indentation_error(self):
        """测试评估缩进错误的代码"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
def bad_indent():
return "wrong indent"
"""
        result = evaluator.evaluate(code)

        assert result.syntax_valid is False

    def test_evaluate_empty_code(self):
        """测试评估空代码"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        result = evaluator.evaluate("")

        # 空代码应该被视为无效或极低分
        assert result.syntax_valid is False or result.total_score == 0

    def test_evaluate_code_with_incomplete_statement(self):
        """测试评估不完整语句的代码"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = "if True:"  # Missing body
        result = evaluator.evaluate(code)

        assert result.syntax_valid is False


class TestIntrinsicEvaluatorStaticAnalysis:
    """静态分析得分测试（P0优先级）"""

    def test_evaluate_detects_unused_import(self):
        """测试检测未使用的导入"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
import os  # Unused import
import sys  # Unused import

def hello():
    return "hello"
"""
        result = evaluator.evaluate(code)

        # 应该有警告关于未使用的导入
        warnings_str = " ".join(result.warnings) if result.warnings else ""
        assert "unused" in warnings_str.lower() or result.static_score < 1.0

    def test_evaluate_detects_undefined_variable(self):
        """测试检测未定义的变量"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
def function():
    return undefined_variable
"""
        result = evaluator.evaluate(code)

        # 语法可能有效，但静态分析应该发现未定义变量
        # 或者静态得分应该较低
        assert result.static_score < 1.0 or any(
            "undefined" in w.lower() for w in (result.warnings or [])
        )

    def test_evaluate_clean_code_gets_high_static_score(self):
        """测试干净代码获得高静态分析得分"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
\"\"\"A well-documented module.\"\"\"


def add(a: int, b: int) -> int:
    \"\"\"Add two numbers.\"\"\"
    return a + b


def multiply(x: float, y: float) -> float:
    \"\"\"Multiply two numbers.\"\"\"
    return x * y
"""
        result = evaluator.evaluate(code)

        assert result.static_score >= 0.8

    def test_static_score_zero_for_syntax_error(self):
        """测试语法错误时静态得分为0"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = "def broken("
        result = evaluator.evaluate(code)

        assert result.static_score == 0.0


class TestIntrinsicEvaluatorStructure:
    """代码结构评估测试（P1优先级）"""

    def test_evaluate_function_count(self):
        """测试评估函数数量"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
def func1(): pass
def func2(): pass
def func3(): pass
"""
        result = evaluator.evaluate(code)

        # 应该有合理的结构得分
        assert result.structure_score > 0

    def test_evaluate_class_structure(self):
        """测试评估类结构"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
class Calculator:
    def __init__(self):
        self.value = 0

    def add(self, x):
        self.value += x

    def reset(self):
        self.value = 0
"""
        result = evaluator.evaluate(code)

        # 有类的代码应该有更好的结构得分
        assert result.structure_score > 0.5

    def test_evaluate_nesting_depth(self):
        """测试评估嵌套深度"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
def deep():
    if True:
        if True:
            if True:
                if True:
                    pass
"""
        result = evaluator.evaluate(code)

        # 过深嵌套应该降低结构得分
        assert result.structure_score < 1.0

    def test_evaluate_function_length(self):
        """测试评估函数长度"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
def long_function():
    x = 1
    x = 2
    x = 3
    x = 4
    x = 5
    x = 6
    x = 7
    x = 8
    x = 9
    x = 10
    x = 11
    x = 12
    x = 13
    x = 14
    x = 15
    x = 16
    x = 17
    x = 18
    x = 19
    x = 20
    x = 21
    x = 22
    x = 23
    x = 24
    x = 25
    x = 26
    x = 27
    x = 28
    x = 29
    x = 30
    x = 31
    x = 32
    x = 33
    x = 34
    x = 35
    x = 36
    x = 37
    x = 38
    x = 39
    x = 40
    x = 41
    x = 42
    x = 43
    x = 44
    x = 45
    x = 46
    x = 47
    x = 48
    x = 49
    x = 50
    x = 51
    x = 52
    x = 53
    x = 54
    x = 55
    x = 56
    x = 57
    x = 58
    x = 59
    x = 60
    return x
"""
        result = evaluator.evaluate(code)

        # 过长的函数应该降低结构得分
        assert result.structure_score < 1.0


class TestIntrinsicEvaluatorDocumentation:
    """文档完整性评估测试（P1优先级）"""

    def test_evaluate_module_docstring(self):
        """测试评估模块文档字符串"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = '''
"""This is a well-documented module."""

def func():
    pass
'''
        result = evaluator.evaluate(code)

        # 有模块文档的代码应该有更好的文档得分
        assert result.doc_score > 0

    def test_evaluate_function_docstrings(self):
        """测试评估函数文档字符串"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = '''
def documented_func():
    """This function does something."""
    pass

def undocumented_func():
    pass
'''
        result = evaluator.evaluate(code)

        # 部分文档应该得到中等分数
        assert 0 < result.doc_score < 1.0

    def test_evaluate_all_documented_gets_high_score(self):
        """测试全部文档化获得高分"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = '''
"""Module docstring."""

def func1():
    """Func1 docstring."""
    pass

def func2():
    """Func2 docstring."""
    pass
'''
        result = evaluator.evaluate(code)

        # 全部文档化应该得到高分
        assert result.doc_score >= 0.8

    def test_evaluate_no_documentation_gets_low_score(self):
        """测试无文档化获得低分"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
def func1():
    pass

def func2():
    pass
"""
        result = evaluator.evaluate(code)

        # 无文档应该得到低分
        assert result.doc_score < 0.5


# =============================================================================
# Test IntrinsicEvaluator - Total Score Calculation
# =============================================================================


class TestIntrinsicEvaluatorTotalScore:
    """总得分计算测试"""

    def test_total_score_is_weighted_sum(self):
        """测试总得分是加权平均"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
\"\"\"Doc.\"\"\"
def func():
    \"\"\"Doc.\"\"\"
    return 1
"""
        result = evaluator.evaluate(code)

        # 总得分应该在各分项之间
        scores = [result.static_score, result.structure_score, result.doc_score]
        assert min(scores) <= result.total_score <= max(scores)

    def test_syntax_invalid_gives_low_total_score(self):
        """测试语法无效时总得分为低"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = "def broken("
        result = evaluator.evaluate(code)

        assert result.total_score < 0.3

    def test_perfect_code_gets_high_total_score(self):
        """测试完美代码获得高总得分"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = '''
"""Perfect module.

This module demonstrates perfect code quality.
"""

from typing import List


def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of a list of numbers.

    Args:
        numbers: A list of numbers to sum.

    Returns:
        The sum of all numbers.
    """
    return sum(numbers)


def calculate_average(numbers: List[float]) -> float:
    """Calculate the average of a list of numbers.

    Args:
        numbers: A list of numbers.

    Returns:
        The average value.

    Raises:
        ValueError: If the list is empty.
    """
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)
'''
        result = evaluator.evaluate(code)

        # 完美代码应该得到很高的总得分
        assert result.total_score >= 0.85


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestIntrinsicEvaluatorEdgeCases:
    """边界情况测试"""

    def test_evaluate_whitespace_only_code(self):
        """测试评估仅包含空白字符的代码"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        result = evaluator.evaluate("   \n\t\n  ")

        assert result.syntax_valid is False or result.total_score == 0

    def test_evaluate_comment_only_code(self):
        """测试评估仅包含注释的代码"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
# This is just a comment
# Another comment
"""
        result = evaluator.evaluate(code)

        # 注释本身可能被视为有效但得分为0
        assert result.total_score == 0 or result.structure_score == 0

    def test_evaluate_unicode_code(self):
        """测试评估包含Unicode的代码"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
# 这是一个注释
emoji = "😀"
"""
        result = evaluator.evaluate(code)

        # 应该能处理Unicode而不崩溃
        assert result.syntax_valid is True

    def test_evaluate_complex_nested_code(self):
        """测试评估复杂嵌套代码"""
        from evolution.intrinsic_evaluator import IntrinsicEvaluator

        evaluator = IntrinsicEvaluator()
        code = """
\"\"\"Complex module.\"\"\"

from typing import Dict, List, Optional


class DataProcessor:
    \"\"\"Process data with various strategies.\"\"\"

    def __init__(self):
        \"\"\"Initialize processor.\"\"\"
        self.data: Dict[str, List[float]] = {}

    def add_data(self, key: str, values: List[float]) -> None:
        \"\"\"Add data under a key.\"\"\"
        self.data[key] = values

    def process(self, key: str) -> Optional[float]:
        \"\"\"Process data for a key.\"\"\"
        if key not in self.data:
            return None
        values = self.data[key]
        if not values:
            return 0.0
        return sum(values) / len(values)


def main():
    \"\"\"Main function.\"\"\"
    processor = DataProcessor()
    processor.add_data("test", [1.0, 2.0, 3.0])
    result = processor.process("test")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()
"""
        result = evaluator.evaluate(code)

        # 复杂的但正确的代码应该得到较高的分数
        assert result.syntax_valid is True
        assert result.total_score >= 0.7

"""
String Calculator Test Suite - Advanced Multi-Generation Evolution Experiment

字符串表达式计算器测试套件 - 用于验证多代进化能力

相比简单计算器，此任务需要：
1. 解析字符串表达式
2. 处理运算符优先级
3. 支持括号嵌套
4. 处理空格和各种边界情况

预期进化路径：
- Gen 0-2: 基础解析，得分 0.3-0.5
- Gen 3-6: 优先级处理，得分 0.5-0.7
- Gen 7-12: 括号支持，得分 0.7-0.9
- Gen 13+: 边界情况处理，得分 0.9+
"""

import pytest
from solution import evaluate


class TestBasicOperations:
    """基本运算测试（最简单）"""

    def test_single_number(self):
        """测试单个数字"""
        assert evaluate("5") == 5
        assert evaluate("3.14") == 3.14

    def test_simple_addition(self):
        """测试简单加法"""
        assert evaluate("2 + 3") == 5
        assert evaluate("1 + 1") == 2

    def test_simple_subtraction(self):
        """测试简单减法"""
        assert evaluate("5 - 3") == 2
        assert evaluate("10 - 4") == 6

    def test_simple_multiplication(self):
        """测试简单乘法"""
        assert evaluate("4 * 3") == 12
        assert evaluate("2 * 5") == 10

    def test_simple_division(self):
        """测试简单除法"""
        assert evaluate("10 / 2") == 5.0
        assert evaluate("8 / 4") == 2.0


class TestOperatorPrecedence:
    """运算符优先级测试（中等难度）"""

    def test_multiplication_before_addition(self):
        """测试先乘除后加减"""
        assert evaluate("2 + 3 * 4") == 14  # 不是 20
        assert evaluate("10 - 2 * 3") == 4  # 不是 24

    def test_multiplication_before_subtraction(self):
        """测试乘法优先于减法"""
        assert evaluate("20 - 3 * 4") == 8

    def test_division_before_addition(self):
        """测试除法优先于加法"""
        assert evaluate("10 + 6 / 2") == 13  # 不是 8

    def test_left_to_right_same_precedence(self):
        """测试同优先级从左到右"""
        assert evaluate("10 - 3 - 2") == 5  # (10-3)-2 = 5, 不是 10-(3-2)=9
        assert evaluate("20 / 4 / 2") == 2.5  # (20/4)/2 = 2.5

    def test_complex_precedence(self):
        """测试复杂优先级组合"""
        assert evaluate("2 + 3 * 4 - 5") == 9  # 2+12-5=9
        assert evaluate("20 / 4 + 3 * 2") == 11  # 5+6=11


class TestParentheses:
    """括号支持测试（困难）"""

    def test_simple_parentheses(self):
        """测试简单括号"""
        assert evaluate("(2 + 3)") == 5
        assert evaluate("(10 - 4)") == 6

    def test_parentheses_override_precedence(self):
        """测试括号覆盖优先级"""
        assert evaluate("(2 + 3) * 4") == 20  # 不是 14
        assert evaluate("10 / (3 - 1)") == 5.0  # 不是 4

    def test_nested_parentheses(self):
        """测试嵌套括号"""
        assert evaluate("((2 + 3) * 4)") == 20
        assert evaluate("(10 - (3 + 2)) * 2") == 10

    def test_multiple_parentheses(self):
        """测试多个括号"""
        assert evaluate("(1 + 2) * (3 + 4)") == 21
        assert evaluate("(10 - 5) / (3 - 1)") == 2.5


class TestWhitespaceHandling:
    """空格处理测试（边界情况）"""

    def test_no_spaces(self):
        """测试无空格"""
        assert evaluate("2+3*4") == 14
        assert evaluate("10-5/2") == 7.5

    def test_extra_spaces(self):
        """测试多余空格"""
        assert evaluate("  2  +  3  *  4  ") == 14
        assert evaluate("  10  /  2  ") == 5.0

    def test_mixed_spaces(self):
        """测试混合空格"""
        assert evaluate("2+ 3*4") == 14
        assert evaluate("10 /2+ 3") == 8.0


class TestEdgeCases:
    """边界情况测试（最难）"""

    def test_negative_numbers(self):
        """测试负数"""
        assert evaluate("-5 + 3") == -2
        assert evaluate("10 * -2") == -20
        assert evaluate("-5 * -3") == 15

    def test_decimal_numbers(self):
        """测试小数"""
        assert evaluate("3.14 + 2.86") == 6.0
        assert abs(evaluate("0.1 + 0.2") - 0.3) < 1e-9

    def test_large_numbers(self):
        """测试大数"""
        assert evaluate("1000000 + 2000000") == 3000000
        assert evaluate("1e10 + 1e10") == 2e10

    def test_division_by_zero(self):
        """测试除零错误"""
        with pytest.raises(ValueError):
            evaluate("10 / 0")
        with pytest.raises(ValueError):
            evaluate("5 / (3 - 3)")

    def test_invalid_expression(self):
        """测试无效表达式"""
        with pytest.raises(ValueError):
            evaluate("2 + + 3")
        with pytest.raises(ValueError):
            evaluate("10 / * 2")


class TestComplexExpressions:
    """复杂表达式测试（综合）"""

    def test_complex_expression_1(self):
        """复杂表达式1"""
        assert evaluate("(1 + 2) * (3 + 4) - 5") == 16  # 3*7-5=16

    def test_complex_expression_2(self):
        """复杂表达式2"""
        assert evaluate("100 / (5 + 5) * 2 + 10") == 30  # 100/10*2+10=30

    def test_complex_expression_3(self):
        """复杂表达式3"""
        assert evaluate("((2 + 3) * 4 - 5) / 3") == 5.0  # (20-5)/3=5


# 测试统计：
# - TestBasicOperations: 5个（基础）
# - TestOperatorPrecedence: 5个（中等）
# - TestParentheses: 5个（困难）
# - TestWhitespaceHandling: 3个（边界）
# - TestEdgeCases: 5个（边界）
# - TestComplexExpressions: 3个（综合）
# 总计：26个测试用例

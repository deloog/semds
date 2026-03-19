"""
Calculator Test Suite - SEMDS Phase 1 Experiment

计算器进化实验的测试用例，对应规格文档第八章。

测试覆盖：
- 基本四则运算
- 边界情况（除零、无效操作符）
- 特殊数值（负数、浮点数、大数、零）
- 返回类型验证
"""

import pytest
from solution import calculate


class TestBasicOperations:
    """基本运算测试类。"""

    def test_addition(self):
        """测试加法运算。"""
        assert calculate(2, 3, "+") == 5

    def test_subtraction(self):
        """测试减法运算。"""
        assert calculate(5, 3, "-") == 2

    def test_multiplication(self):
        """测试乘法运算。"""
        assert calculate(4, 3, "*") == 12

    def test_division(self):
        """测试除法运算。"""
        assert calculate(10, 2, "/") == 5.0


class TestEdgeCases:
    """边界情况测试类。"""

    def test_division_by_zero(self):
        """测试除零时抛出ValueError。"""
        with pytest.raises(ValueError):
            calculate(1, 0, "/")

    def test_invalid_operator(self):
        """测试无效操作符时抛出ValueError。"""
        with pytest.raises(ValueError):
            calculate(1, 2, "%")

    def test_negative_numbers(self):
        """测试负数运算。"""
        assert calculate(-3, -2, "*") == 6

    def test_float_numbers(self):
        """测试浮点数运算（考虑精度）。"""
        assert abs(calculate(0.1, 0.2, "+") - 0.3) < 1e-9

    def test_large_numbers(self):
        """测试大数运算。"""
        assert calculate(1e10, 1e10, "+") == 2e10

    def test_zero_operand(self):
        """测试零作为操作数。"""
        assert calculate(0, 5, "+") == 5


class TestReturnType:
    """返回类型测试类。"""

    def test_returns_numeric(self):
        """测试返回值是数值类型。"""
        result = calculate(4, 2, "/")
        assert isinstance(result, (int, float))


# 测试用例总数：10个
# - TestBasicOperations: 4个
# - TestEdgeCases: 6个
# - TestReturnType: 1个

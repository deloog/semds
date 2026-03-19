#!/usr/bin/env python3
"""
分析字符串计算器测试失败原因

运行测试并详细记录每个测试用例的结果
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.env_loader import load_env

load_env()

from evolution.code_generator import CodeGenerator
from evolution.test_runner import TestRunner

# 这是实验中生成的最佳代码（从实验输出中提取）
BEST_CODE = """def solution(expression: str) -> float:
    def tokenize(expr):
        tokens = []
        i = 0
        while i < len(expr):
            if expr[i].isspace():
                i += 1
                continue
            if expr[i] in '()+-*/':
                tokens.append(expr[i])
                i += 1
            elif expr[i].isdigit() or expr[i] == '.':
                num = ''
                while i < len(expr) and (expr[i].isdigit() or expr[i] == '.'):
                    num += expr[i]
                    i += 1
                tokens.append(num)
            else:
                raise ValueError("Invalid character in expression")
        return tokens

    def parse_number(tokens, index):
        token = tokens[index]
        try:
            return float(token), index + 1
        except ValueError:
            raise ValueError("Invalid number format")

    def parse_factor(tokens, index):
        if index >= len(tokens):
            raise ValueError("Unexpected end of expression")
        
        token = tokens[index]
        if token == '(':
            value, next_index = parse_expression(tokens, index + 1)
            if next_index >= len(tokens) or tokens[next_index] != ')':
                raise ValueError("Missing closing parenthesis")
            return value, next_index + 1
        elif token == '+':
            value, next_index = parse_factor(tokens, index + 1)
            return value, next_index
        elif token == '-':
            value, next_index = parse_factor(tokens, index + 1)
            return -value, next_index
        else:
            return parse_number(tokens, index)

    def parse_term(tokens, index):
        value, index = parse_factor(tokens, index)
        
        while index < len(tokens) and tokens[index] in ('*', '/'):
            op = tokens[index]
            next_value, index = parse_factor(tokens, index + 1)
            
            if op == '*':
                value *= next_value
            elif op == '/':
                if next_value == 0:
                    raise ValueError("Division by zero")
                value /= next_value
        
        return value, index

    def parse_expression(tokens, index):
        value, index = parse_term(tokens, index)
        
        while index < len(tokens) and tokens[index] in ('+', '-'):
            op = tokens[index]
            next_value, index = parse_term(tokens, index + 1)
            
            if op == '+':
                value += next_value
            elif op == '-':
                value -= next_value
        
        return value, index

    tokens = tokenize(expression)
    if not tokens:
        raise ValueError("Empty expression")
    
    result, index = parse_expression(tokens, 0)
    if index != len(tokens):
        raise ValueError("Invalid expression format")
    
    return result
"""

# 读取测试文件
TEST_FILE_PATH = (
    Path(__file__).parent / "calculator" / "tests" / "test_string_calculator.py"
)

print("=" * 70)
print("字符串计算器测试失败分析")
print("=" * 70)
print()

# 创建临时目录运行测试
with tempfile.TemporaryDirectory() as tmpdir:
    # 写入代码
    solution_path = Path(tmpdir) / "solution.py"
    with open(solution_path, "w", encoding="utf-8") as f:
        f.write(BEST_CODE)

    # 写入测试
    test_path = Path(tmpdir) / "test_string_calculator.py"
    with open(test_path, "w", encoding="utf-8") as f:
        f.write(open(TEST_FILE_PATH, encoding="utf-8").read())

    # 运行测试
    runner = TestRunner(timeout_seconds=30, verbose=False)
    test_result = runner.run_tests(str(test_path), str(solution_path), tmpdir)

# 分析结果
print(f"总体得分: {test_result['pass_rate']:.2%}")
print(f"通过测试: {len(test_result['passed'])}")
print(f"失败测试: {len(test_result['failed'])}")
print(f"总测试数: {test_result['total_tests']}")
print()

# 按类别分析测试
passed_tests = test_result["passed"]
failed_tests = test_result["failed"]


# 提取测试名称
def extract_test_name(full_name):
    if "::" in full_name:
        return full_name.split("::")[-1]
    return full_name


passed_names = [extract_test_name(t) for t in passed_tests]
failed_names = [extract_test_name(t) for t in failed_tests]

print("-" * 70)
print("[通过的测试]")
print("-" * 70)
for name in passed_names:
    print(f"  [OK] {name}")
print()

print("-" * 70)
print("[失败的测试]")
print("-" * 70)
for name in failed_names:
    print(f"  [FAIL] {name}")
print()

# 按类别统计
categories = {
    "TestBasicOperations": "基本运算",
    "TestOperatorPrecedence": "运算符优先级",
    "TestParentheses": "括号支持",
    "TestWhitespaceHandling": "空格处理",
    "TestEdgeCases": "边界情况",
    "TestComplexExpressions": "复杂表达式",
}

print("-" * 70)
print("[按类别统计]")
print("-" * 70)
print(f"{'类别':<30} {'通过':<8} {'失败':<8} {'状态'}")
print("-" * 70)

for cat_class, cat_name in categories.items():
    cat_passed = [t for t in passed_tests if cat_class in t]
    cat_failed = [t for t in failed_tests if cat_class in t]
    total = len(cat_passed) + len(cat_failed)

    if total > 0:
        status = "OK" if len(cat_failed) == 0 else f"{len(cat_passed)}/{total}"
        print(f"{cat_name:<30} {len(cat_passed):<8} {len(cat_failed):<8} {status}")

print("-" * 70)
print()

# 详细分析失败原因
print("=" * 70)
print("[详细失败分析]")
print("=" * 70)
print()

# 从原始输出中提取失败详情
raw_output = test_result["raw_output"]

# 解析失败信息
if "FAILED" in raw_output:
    # 提取失败详情
    lines = raw_output.split("\n")
    current_test = None
    error_details = []

    for line in lines:
        if "::test_" in line and "FAILED" in line:
            current_test = line.strip()
            print(f"\n测试: {current_test}")
        elif current_test and line.strip().startswith("E   "):
            error_details.append(line.strip())
            print(f"  错误: {line.strip()}")
        elif current_test and "==" in line:
            print(f"  详情: {line.strip()}")

print()
print("=" * 70)
print("[失败原因总结]")
print("=" * 70)

# 根据测试类别推断失败原因
if any("TestEdgeCases" in t for t in failed_tests):
    print("\n1. 边界情况处理不完善")
    print("   - 可能原因: 负数、科学计数法(1e10)等未正确处理")

if any("TestWhitespaceHandling" in t for t in failed_tests):
    print("\n2. 空格处理有问题")
    print("   - 可能原因: 首尾空格、多个空格处理不当")

if any("TestComplexExpressions" in t for t in failed_tests):
    print("\n3. 复杂表达式解析问题")
    print("   - 可能原因: 多层括号或复杂运算符组合")

if any("TestParentheses" in t for t in failed_tests):
    print("\n4. 括号处理有缺陷")
    print("   - 可能原因: 嵌套括号或多个括号组合")

print("\n" + "=" * 70)
print("分析完成")
print("=" * 70)

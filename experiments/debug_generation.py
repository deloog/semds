#!/usr/bin/env python3
"""调试代码生成和测试"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.env_loader import load_env
load_env()

from evolution.code_generator import CodeGenerator
from evolution.test_runner import TestRunner

# 初始化
generator = CodeGenerator()
runner = TestRunner(verbose=True)

# 生成代码
task_spec = {
    "name": "calculator",
    "description": "实现一个四则运算计算器函数",
    "target_function_signature": "def calculate(a: float, b: float, op: str) -> float",
    "requirements": [
        "支持 +, -, *, / 运算符",
        "除零时抛出 ValueError",
        "无效操作符时抛出 ValueError"
    ]
}

print("Generating code...")
result = generator.generate(task_spec=task_spec)

if result["success"]:
    code = result["code"]
    print(f"\n=== Generated Code ({len(code)} chars) ===")
    print(code)
    print("="*60)
    
    # 测试代码
    test_code = '''
from solution import calculate

def test_addition():
    assert calculate(2, 3, '+') == 5

def test_subtraction():
    assert calculate(5, 3, '-') == 2

def test_multiplication():
    assert calculate(4, 3, '*') == 12
'''
    
    # 创建临时文件
    with tempfile.TemporaryDirectory() as tmpdir:
        solution_path = Path(tmpdir) / 'solution.py'
        test_path = Path(tmpdir) / 'test_calculator.py'
        
        with open(solution_path, 'w') as f:
            f.write(code)
        
        with open(test_path, 'w') as f:
            f.write(test_code)
        
        print(f"\nRunning tests from {test_path}")
        print(f"Solution at {solution_path}")
        print(f"Working dir {tmpdir}")
        
        # 运行测试
        test_result = runner.run_tests(str(test_path), str(solution_path), tmpdir)
        
        print("\n=== Test Result ===")
        print(f"Success: {test_result['success']}")
        print(f"Score: {test_result['pass_rate']:.2%}")
        print(f"Total tests: {test_result['total_tests']}")
        print(f"Passed: {len(test_result['passed'])}")
        print(f"Failed: {len(test_result['failed'])}")
        if test_result['failed']:
            print(f"Failed tests: {test_result['failed']}")
        print(f"\nRaw output:\n{test_result['raw_output']}")
else:
    print(f"Generation failed: {result.get('error')}")

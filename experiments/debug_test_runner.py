#!/usr/bin/env python3
"""调试 test_runner"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.test_runner import TestRunner

# 测试代码
test_code = '''
from solution import calculate

def test_addition():
    assert calculate(2, 3, '+') == 5
'''

# 解决方案代码
solution_code = '''
def calculate(a, b, op):
    if op == '+':
        return a + b
    return 0
'''

# 创建临时文件
with tempfile.TemporaryDirectory() as tmpdir:
    solution_path = Path(tmpdir) / 'solution.py'
    test_path = Path(tmpdir) / 'test_solution.py'
    
    with open(solution_path, 'w') as f:
        f.write(solution_code)
    
    with open(test_path, 'w') as f:
        f.write(test_code)
    
    print(f"Solution file: {solution_path}")
    print(f"Test file: {test_path}")
    print(f"Solution exists: {solution_path.exists()}")
    print(f"Test exists: {test_path.exists()}")
    
    # 运行测试
    runner = TestRunner(timeout_seconds=10, verbose=True)
    result = runner.run_tests(str(test_path), str(solution_path), tmpdir)
    
    print("\n=== Result ===")
    print(f"Success: {result['success']}")
    print(f"Score: {result['pass_rate']:.2%}")
    print(f"Passed: {result['passed']}")
    print(f"Failed: {result['failed']}")
    print(f"Total: {result['total_tests']}")
    print(f"Error: {result['error']}")
    print(f"\nRaw output:\n{result['raw_output'][:1000]}")

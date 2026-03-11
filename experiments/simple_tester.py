#!/usr/bin/env python3
"""
简单的代码测试器，不依赖 pytest
"""

import sys
import tempfile
from pathlib import Path
from typing import Dict, List


def run_basic_tests(code: str) -> Dict:
    """
    运行基础测试验证代码。
    
    Returns:
        {
            "success": bool,
            "pass_rate": float,
            "passed": List[str],
            "failed": List[str],
            "error": str or None
        }
    """
    results = {
        "success": True,
        "pass_rate": 0.0,
        "passed": [],
        "failed": [],
        "error": None
    }
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        # 动态导入模块
        import importlib.util
        spec = importlib.util.spec_from_file_location("solution", temp_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        calculate = module.calculate
        
        # 定义测试用例
        tests = [
            ("test_add", lambda: calculate(2, 3, "+") == 5),
            ("test_sub", lambda: calculate(5, 3, "-") == 2),
            ("test_mul", lambda: calculate(4, 3, "*") == 12),
            ("test_div", lambda: calculate(10, 2, "/") == 5.0),
            ("test_neg", lambda: calculate(-3, -2, "*") == 6),
            ("test_float", lambda: abs(calculate(0.1, 0.2, "+") - 0.3) < 1e-9),
            ("test_zero", lambda: calculate(0, 5, "+") == 5),
            ("test_large", lambda: calculate(1e10, 1e10, "+") == 2e10),
        ]
        
        # 异常测试
        def test_div_zero():
            try:
                calculate(1, 0, "/")
                return False
            except ValueError:
                return True
        
        def test_invalid_op():
            try:
                calculate(1, 2, "%")
                return False
            except ValueError:
                return True
        
        tests.extend([
            ("test_div_by_zero", test_div_zero),
            ("test_invalid_op", test_invalid_op),
        ])
        
        # 运行测试
        for name, test_fn in tests:
            try:
                if test_fn():
                    results["passed"].append(name)
                else:
                    results["failed"].append(name)
            except Exception as e:
                results["failed"].append(f"{name}({e})")
        
        total = len(tests)
        passed = len(results["passed"])
        results["pass_rate"] = passed / total if total > 0 else 0
        
    except Exception as e:
        results["success"] = False
        results["error"] = f"Code execution error: {e}"
    
    finally:
        # 清理临时文件
        Path(temp_path).unlink(missing_ok=True)
    
    return results


if __name__ == "__main__":
    # 测试示例代码
    test_code = '''
def calculate(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        if b == 0:
            raise ValueError("Division by zero")
        return a / b
    else:
        raise ValueError("Invalid operator")
'''
    
    print("测试示例代码...")
    result = run_basic_tests(test_code)
    print(f"通过率: {result['pass_rate']:.0%}")
    print(f"通过: {result['passed']}")
    print(f"失败: {result['failed']}")

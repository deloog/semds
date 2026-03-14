#!/usr/bin/env python3
"""
简化版进化实验 - 验证核心流程

不依赖复杂的数据库和模块导入，直接验证：
1. 代码生成器能工作
2. 测试运行器能评分
3. 多代进化能跑通
"""

import sys
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime

# 设置项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
from core.env_loader import load_env
load_env()

# 核心组件
from evolution.code_generator import CodeGenerator
from evolution.test_runner import TestRunner


# 计算器测试用例（规格文档8.2）
CALCULATOR_TEST = '''
from solution import calculate

def test_addition():
    assert calculate(2, 3, '+') == 5

def test_subtraction():
    assert calculate(5, 3, '-') == 2

def test_multiplication():
    assert calculate(4, 3, '*') == 12

def test_division():
    assert calculate(10, 2, '/') == 5.0

def test_division_by_zero():
    try:
        calculate(1, 0, '/')
        assert False
    except ValueError:
        pass

def test_invalid_operator():
    try:
        calculate(1, 2, '%')
        assert False
    except ValueError:
        pass

def test_negative_numbers():
    assert calculate(-3, -2, '*') == 6

def test_float_numbers():
    assert abs(calculate(0.1, 0.2, '+') - 0.3) < 1e-9

def test_large_numbers():
    assert calculate(1e10, 1e10, '+') == 2e10

def test_zero_operand():
    assert calculate(0, 5, '+') == 5
'''


def run_generation(generator: CodeGenerator, runner: TestRunner, 
                   gen_num: int, previous_code: str = None, 
                   previous_score: float = None, failed_tests: list = None) -> dict:
    """运行一代进化"""
    
    print(f"\n{'='*60}")
    print(f"Generation {gen_num}")
    print(f"{'='*60}")
    
    # 构建任务规格 - 特别强调函数签名
    task_spec = {
        "name": "calculator",
        "description": "实现一个四则运算计算器函数",
        "target_function_signature": "def calculate(a: float, b: float, op: str) -> float",
        "requirements": [
            "函数签名必须是: def calculate(a: float, b: float, op: str) -> float",
            "参数顺序: a(数字), b(数字), op(运算符字符串)",
            "支持 +, -, *, / 运算符",
            "除零时抛出 ValueError",
            "无效操作符时抛出 ValueError"
        ]
    }
    
    # 构建前代反馈
    previous_score_dict = None
    if previous_score is not None:
        previous_score_dict = {"intrinsic_score": previous_score}
    
    # 生成代码
    print("Generating code...")
    if failed_tests:
        print(f"  Feedback: Previous failed on: {failed_tests[:2]}")
    start_time = time.time()
    
    result = generator.generate(
        task_spec=task_spec,
        previous_code=previous_code,
        previous_score=previous_score_dict
    )
    
    gen_time = time.time() - start_time
    
    if not result["success"]:
        print(f"  [FAIL] Code generation failed: {result.get('error')}")
        return {"success": False, "score": 0.0, "code": None}
    
    code = result["code"]
    print(f"  [OK] Code generated in {gen_time:.2f}s ({len(code)} chars)")
    
    # 创建临时目录运行测试
    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入代码
        solution_path = Path(tmpdir) / "solution.py"
        with open(solution_path, 'w') as f:
            f.write(code)
        
        # 写入测试
        test_path = Path(tmpdir) / "test_calculator.py"
        with open(test_path, 'w') as f:
            f.write(CALCULATOR_TEST)
        
        # 运行测试
        print("Running tests...")
        test_result = runner.run_tests(str(test_path), str(solution_path), tmpdir)
    
    score = test_result.get("pass_rate", 0.0)
    passed = len(test_result.get("passed", []))
    total = test_result.get("total_tests", 10)
    
    print(f"  [RESULT] Score: {score:.2%} ({passed}/{total} tests)")
    
    # 提取失败测试的详细信息
    failed_details = []
    if test_result.get("failed"):
        for fail in test_result["failed"][:3]:
            # 提取测试名称中的函数名
            if "::" in fail:
                test_name = fail.split("::")[-1]
                failed_details.append(test_name)
        print(f"  [FAILED] {', '.join(failed_details)}")
    
    return {
        "success": True,
        "score": score,
        "code": code,
        "generation_time": gen_time,
        "passed": passed,
        "total": total,
        "failed_details": failed_details
    }


def run_evolution_experiment(max_generations: int = 5, target_score: float = 0.9):
    """运行完整进化实验"""
    
    print("="*60)
    print("SEMDS 简化进化实验")
    print("="*60)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Max generations: {max_generations}")
    print(f"Target score: {target_score:.0%}")
    print()
    
    # 初始化组件
    try:
        print("Initializing CodeGenerator...")
        generator = CodeGenerator()
        print("  [OK] CodeGenerator ready")
    except Exception as e:
        print(f"  [FAIL] {e}")
        print("\n[ABORT] Cannot initialize code generator. Check API key.")
        return
    
    runner = TestRunner(timeout_seconds=30, verbose=False)
    print("  [OK] TestRunner ready")
    print()
    
    # 进化历史
    history = []
    best_code = None
    best_score = 0.0
    
    # 运行多代
    start_time = time.time()
    failed_tests_info = []
    
    for gen in range(max_generations):
        # 获取前代信息
        previous_code = history[-1]["code"] if history else None
        previous_score = history[-1]["score"] if history else None
        
        # 运行一代
        result = run_generation(
            generator, runner, gen,
            previous_code=previous_code,
            previous_score=previous_score,
            failed_tests=failed_tests_info
        )
        
        if not result["success"]:
            print(f"  [SKIP] Generation {gen} failed, continuing...")
            continue
        
        history.append(result)
        
        # 提取失败测试信息供下一代使用
        if result.get("failed_details"):
            failed_tests_info = result["failed_details"]
        
        # 更新最佳
        if result["score"] > best_score:
            best_score = result["score"]
            best_code = result["code"]
            print(f"  [NEW BEST] Generation {gen}")
        
        # 检查是否达到目标
        if result["score"] >= target_score:
            print(f"\n[TARGET REACHED] Score {result['score']:.2%} >= {target_score:.0%}")
            break
        
        # 短暂延迟避免API限流
        if gen < max_generations - 1:
            time.sleep(2)
    
    elapsed = time.time() - start_time
    
    # 打印最终报告
    print("\n" + "="*60)
    print("EXPERIMENT REPORT")
    print("="*60)
    print(f"Total generations: {len(history)}")
    print(f"Best score: {best_score:.2%}")
    print(f"Total time: {elapsed:.2f}s")
    print()
    
    print("Evolution trajectory:")
    print("-"*60)
    print(f"{'Gen':<6} {'Score':<10} {'Passed':<10} {'Status'}")
    print("-"*60)
    
    for i, h in enumerate(history):
        status = "BEST" if h["code"] == best_code else ""
        print(f"{i:<6} {h['score']:<10.2%} {h['passed']}/{h['total']:<6} {status}")
    
    print("-"*60)
    
    if best_code:
        print("\nBest code:")
        print("="*60)
        print(best_code)
        print("="*60)
    
    # 分析与建议
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)
    
    if len(history) >= 2:
        first_score = history[0]["score"]
        last_score = history[-1]["score"]
        improvement = last_score - first_score
        
        print(f"First generation: {first_score:.2%}")
        print(f"Last generation:  {last_score:.2%}")
        print(f"Improvement:      {improvement:+.2%}")
        
        if improvement > 0:
            print("\n[OBSERVATION] Score improved over generations")
        elif improvement < 0:
            print("\n[OBSERVATION] Score decreased - LLM may not be learning from feedback")
        else:
            print("\n[OBSERVATION] No improvement - task may be too easy or feedback not effective")
    
    if best_score >= target_score:
        print(f"\n[CONCLUSION] Success! Target score reached.")
    else:
        print(f"\n[CONCLUSION] Target not reached. Best: {best_score:.2%}, Target: {target_score:.0%}")
    
    print("\n" + "="*60)
    print("Experiment complete")
    print("="*60)
    
    return {
        "history": history,
        "best_score": best_score,
        "best_code": best_code,
        "total_time": elapsed
    }


if __name__ == "__main__":
    # 运行实验
    result = run_evolution_experiment(max_generations=5, target_score=0.9)

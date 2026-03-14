#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock Evolution Experiment - No Docker required

This script uses a Mock code generator to simulate the multi-generation
evolution process without requiring Docker.
"""

import sys
import io
import time
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.orchestrator import EvolutionOrchestrator
from evolution.termination_checker import TerminationConfig


class MockEvolvingCodeGenerator:
    """
    模拟渐进式改进的代码生成器。
    
    模拟真实进化过程：从低质量代码开始，逐步改进。
    """
    
    def __init__(self):
        self.generation = 0
        self.implementations = [
            # Gen 0: 基础实现（有很多问题）
            '''def calculate(a, b, op):
    if op == '+':
        return a + b
    return 0''',
            
            # Gen 1: 添加减法
            '''def calculate(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    return 0''',
            
            # Gen 2: 添加乘除
            '''def calculate(a, b, op):
    if op == '+':
        return a + b
    elif op == '-':
        return a - b
    elif op == '*':
        return a * b
    elif op == '/':
        return a / b
    return 0''',
            
            # Gen 3: 添加除零检查
            '''def calculate(a, b, op):
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
    return 0''',
            
            # Gen 4+: 完整实现
            '''def calculate(a: float, b: float, op: str) -> float:
    """Calculate result of a op b."""
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
        raise ValueError("Invalid operator")'''
        ]
    
    def generate(self, **kwargs):
        """生成代码，模拟渐进式改进"""
        if self.generation < len(self.implementations):
            code = self.implementations[self.generation]
        else:
            code = self.implementations[-1]  # 最佳实现
        
        self.generation += 1
        
        return {
            "success": True,
            "code": code,
            "generation": self.generation
        }


def run_mock_evolution():
    """运行 Mock 进化实验，展示完整的多代改进过程"""
    
    print("=" * 70)
    print("SEMDS Mock 进化实验 - 验证多代进化流程")
    print("=" * 70)
    print(f"开始时间: {datetime.now().isoformat()}")
    print()
    
    # 配置
    config = TerminationConfig(
        success_threshold=0.90,
        max_generations=10,
        stagnation_generations=3
    )
    
    # 创建 Mock 生成器
    mock_generator = MockEvolvingCodeGenerator()
    
    orchestrator = EvolutionOrchestrator(
        task_id="mock_calculator_evolution",
        code_generator=mock_generator,
        termination_config=config,
    )
    
    requirements = [
        "实现四则运算计算器",
        "正确处理除零",
        "正确处理无效操作符"
    ]
    
    test_code = """
assert calculate(2, 3, '+') == 5
assert calculate(5, 3, '-') == 2
assert calculate(4, 3, '*') == 12
assert calculate(10, 2, '/') == 5.0
try:
    calculate(1, 0, '/')
    assert False
except ValueError:
    pass
try:
    calculate(1, 2, '%')
    assert False
except ValueError:
    pass
"""
    
    print("实验配置:")
    print(f"  - 任务: 计算器进化（Mock）")
    print(f"  - 成功阈值: {config.success_threshold}")
    print(f"  - 最大代数: {config.max_generations}")
    print(f"  - 使用 Docker: 否（本地执行）")
    print()
    
    # 运行进化
    start_time = time.time()
    
    print("开始进化...\n")
    
    result = orchestrator.evolve(
        requirements=requirements,
        test_code=test_code,
        max_generations=config.max_generations
    )
    
    elapsed_time = time.time() - start_time
    
    # 打印结果
    print("\n" + "=" * 70)
    print("[实验结果]")
    print("=" * 70)
    print(f"总代数: {result.generations}")
    print(f"最佳得分: {result.best_score:.4f}")
    print(f"是否成功: {result.success}")
    print(f"终止原因: {result.termination_reason}")
    print(f"运行时间: {elapsed_time:.2f} 秒")
    print()
    
    # 打印进化轨迹
    print("[进化轨迹]:")
    print("-" * 70)
    print(f"{'Gen':<5} {'Score':<10} {'Passed':<8} {'Code Quality'}")
    print("-" * 70)
    
    for gen_result in result.history:
        score = gen_result.score
        passed = 'YES' if gen_result.passed_tests else 'NO'
        
        # 评估代码质量
        if score < 0.3:
            quality = "Basic"
        elif score < 0.6:
            quality = "Improving"
        elif score < 0.9:
            quality = "Good"
        else:
            quality = "Excellent"
        
        print(f"{gen_result.generation:<5} {score:<10.4f} {passed:<8} {quality}")
    
    print("-" * 70)
    print()
    
    # 显示最佳代码
    if result.best_code:
        print("[最佳代码]:")
        print("=" * 70)
        print(result.best_code)
        print("=" * 70)
    
    # 验证进化路径
    print("\n" + "=" * 70)
    print("[进化路径分析]")
    print("=" * 70)
    
    scores = [h.score for h in result.history]
    if len(scores) >= 3:
        print(f"早期得分 (Gen 0):    {scores[0]:.4f}")
        if len(scores) > 3:
            mid_idx = len(scores) // 2
            print(f"中期得分 (Gen {mid_idx}):    {scores[mid_idx]:.4f}")
        print(f"最终得分 (Gen {len(scores)-1}):    {scores[-1]:.4f}")
        
        improvement = scores[-1] - scores[0]
        print(f"\n总改进幅度: +{improvement:.4f} ({improvement/scores[0]*100:.1f}%)")
        
        if improvement > 0:
            print("[OK] 观察到渐进式改进！")
        else:
            print("[WARN] 改进不明显")
    
    print("\n" + "=" * 70)
    print("✅ Mock 实验完成！系统各组件工作正常。")
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    run_mock_evolution()

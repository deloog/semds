"""
Phase 3 计算器实验 - 使用Mock验证进化系统流程

由于LLM API需要密钥，此版本使用模拟代码生成器验证系统流程。
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.orchestrator import EvolutionOrchestrator
from evolution.termination_checker import TerminationConfig


def create_mock_code_generator():
    """创建模拟代码生成器"""
    mock_generator = Mock()
    
    # 模拟生成的代码（逐步改进）
    generation_codes = [
        # Gen 1: 基本但错误
        "def add(a, b):\n    return a - b  # Wrong operation",
        
        # Gen 2: 部分正确
        "def add(a, b):\n    if a == 1 and b == 2:\n        return 3\n    return 0",
        
        # Gen 3: 改进中
        "def add(a, b):\n    '''Add function'''\n    return a + b * 0.5",
        
        # Gen 4: 接近正确
        "def add(a, b):\n    '''Add two numbers'''\n    return a + b",
        
        # Gen 5: 正确实现
        "def add(a: int, b: int) -> int:\n    '''Add two numbers and return the sum.'''\n    return a + b",
        
        # Gen 6+: 更完善
        "def add(a, b):\n    '''\n    Add two numbers.\n    \n    Args:\n        a: First number\n        b: Second number\n    Returns:\n        Sum of a and b\n    '''\n    return a + b",
    ]
    
    call_count = [0]
    
    def mock_generate(requirements, temperature=0.5):
        idx = min(call_count[0], len(generation_codes) - 1)
        code = generation_codes[idx]
        call_count[0] += 1
        print(f"  [Mock] Generating Gen {call_count[0]} code...")
        return code
    
    mock_generator.generate = mock_generate
    return mock_generator, call_count


def run_calculator_experiment_mock():
    """运行计算器实验（Mock版本）"""
    
    print("=" * 70)
    print("SEMDS Phase 3 - 计算器进化实验 (Mock版本)")
    print("=" * 70)
    print(f"开始时间: {datetime.now().isoformat()}")
    print()
    
    # 创建Mock代码生成器
    mock_generator, call_count = create_mock_code_generator()
    
    # 实验配置
    config = TerminationConfig(
        success_threshold=0.85,  # 降低阈值以适应Mock
        max_generations=10,
        stagnation_generations=5
    )
    
    orchestrator = EvolutionOrchestrator(
        task_id="calculator_add_mock",
        code_generator=mock_generator,
        termination_config=config,
    )
    
    requirements = [
        "Write a Python function 'add(a, b)' that returns the sum.",
        "Include type hints and docstring.",
    ]
    
    test_code = """
assert add(1, 2) == 3
assert add(0, 0) == 0
assert add(-1, 1) == 0
"""
    
    print("实验配置:")
    print(f"  - 任务: 实现加法函数 add(a, b)")
    print(f"  - 成功阈值: {config.success_threshold}")
    print(f"  - 最大代数: {config.max_generations}")
    print(f"  - 停滞检测: {config.stagnation_generations} 代")
    print(f"  - 代码生成器: Mock (模拟渐进改进)")
    print()
    
    start_time = time.time()
    
    try:
        result = orchestrator.evolve(
            requirements=requirements,
            test_code=test_code,
            max_generations=10
        )
        
        elapsed_time = time.time() - start_time
        
        # 生成报告
        print("=" * 70)
        print("实验结果")
        print("=" * 70)
        print(f"总代数: {result.generations}")
        print(f"最佳得分: {result.best_score:.4f}")
        print(f"是否成功: {result.success}")
        print(f"终止原因: {result.termination_reason}")
        print(f"Mock调用次数: {call_count[0]}")
        print(f"运行时间: {elapsed_time:.2f} 秒")
        print()
        
        print("最佳代码:")
        print("-" * 70)
        print(result.best_code if result.best_code else "(无代码)")
        print("-" * 70)
        print()
        
        print("进化历史:")
        print("-" * 70)
        for gen_result in result.history:
            print(f"  Gen {gen_result.generation:2d}: "
                  f"score={gen_result.score:.4f} | "
                  f"tests={'PASS' if gen_result.passed_tests else 'FAIL'} | "
                  f"strategy={gen_result.strategy.get('mutation_type', 'unknown')}")
        print("-" * 70)
        print()
        
        # 验证实验目标
        print("=" * 70)
        print("实验目标验证")
        print("=" * 70)
        
        # Phase 3目标验证
        target_generations = 10
        target_score = 0.85
        
        gen_check = result.generations >= target_generations
        score_check = result.best_score >= target_score
        
        print(f"[OK] 运行 >={target_generations} 代: {result.generations} 代 "
              f"{'PASS' if gen_check else 'FAIL'}")
        print(f"[OK] 最终得分 >={target_score}: {result.best_score:.4f} "
              f"{'PASS' if score_check else 'FAIL'}")
        print()
        
        if gen_check and score_check:
            print("[SUCCESS] 实验成功！Phase 3 目标达成！")
            status = "SUCCESS"
        elif gen_check:
            print("[PARTIAL] 实验部分成功：达到代数要求但得分未达标")
            status = "PARTIAL"
        else:
            print("[INCOMPLETE] 实验未完成：未达到代数或得分要求")
            status = "INCOMPLETE"
        
        print()
        print(f"结束时间: {datetime.now().isoformat()}")
        print("=" * 70)
        
        # 生成实验报告文件
        report_path = Path(__file__).parent / "phase3_experiment_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("SEMDS Phase 3 实验报告\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"实验状态: {status}\n")
            f.write(f"总代数: {result.generations}\n")
            f.write(f"最佳得分: {result.best_score:.4f}\n")
            f.write(f"成功: {result.success}\n")
            f.write(f"终止原因: {result.termination_reason}\n")
            f.write(f"运行时间: {elapsed_time:.2f} 秒\n\n")
            f.write("最佳代码:\n")
            f.write("-" * 70 + "\n")
            f.write(result.best_code if result.best_code else "(无代码)")
            f.write("\n" + "=" * 70 + "\n")
        
        print(f"\n实验报告已保存: {report_path}")
        
        return result, status
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[ERROR] 实验失败: {e}")
        print(f"运行时间: {elapsed_time:.2f} 秒")
        import traceback
        traceback.print_exc()
        return None, "FAILED"


if __name__ == "__main__":
    result, status = run_calculator_experiment_mock()
    sys.exit(0 if status == "SUCCESS" else 1)

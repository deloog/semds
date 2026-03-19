"""
Phase 3 计算器实验 - 验证进化系统

目标：验证进化系统能够运行 ≥10 代，最终得分 ≥0.90
"""

import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.orchestrator import EvolutionOrchestrator
from evolution.termination_checker import TerminationConfig


def run_calculator_experiment():
    """运行计算器加法实验"""

    print("=" * 70)
    print("SEMDS Phase 3 - 计算器进化实验")
    print("=" * 70)
    print(f"开始时间: {datetime.now().isoformat()}")
    print()

    # 实验配置
    config = TerminationConfig(
        success_threshold=0.90, max_generations=15, stagnation_generations=5  # 最多15代
    )

    orchestrator = EvolutionOrchestrator(
        task_id="calculator_add",
        termination_config=config,
    )

    # 实验要求
    requirements = [
        "Write a Python function 'add(a, b)' that returns the sum of two numbers.",
        "The function should handle integers and floats.",
        "Include proper type hints and docstring.",
    ]

    # 测试代码
    test_code = """
# Test cases for add function
assert add(1, 2) == 3, "Basic addition failed"
assert add(0, 0) == 0, "Zero addition failed"
assert add(-1, 1) == 0, "Negative number failed"
assert add(2.5, 2.5) == 5.0, "Float addition failed"
assert add(-5, -3) == -8, "Two negatives failed"
"""

    print("实验配置:")
    print(f"  - 任务: 实现加法函数 add(a, b)")
    print(f"  - 成功阈值: {config.success_threshold}")
    print(f"  - 最大代数: {config.max_generations}")
    print(f"  - 停滞检测: {config.stagnation_generations} 代")
    print()

    # 运行进化
    start_time = time.time()

    try:
        result = orchestrator.evolve(
            requirements=requirements, test_code=test_code, max_generations=15
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
        print(f"运行时间: {elapsed_time:.2f} 秒")
        print()

        print("最佳代码:")
        print("-" * 70)
        print(result.best_code if result.best_code else "(无代码)")
        print("-" * 70)
        print()

        # 历史记录
        print("进化历史:")
        print("-" * 70)
        for gen_result in result.history:
            print(
                f"  Gen {gen_result.generation}: "
                f"score={gen_result.score:.4f}, "
                f"tests={'PASS' if gen_result.passed_tests else 'FAIL'}"
            )
        print("-" * 70)
        print()

        # 验证实验目标
        print("=" * 70)
        print("实验目标验证")
        print("=" * 70)

        target_generations = 10
        target_score = 0.90

        gen_check = result.generations >= target_generations
        score_check = result.best_score >= target_score

        print(
            f"[OK] 运行 ≥{target_generations} 代: {result.generations} 代 "
            f"{'PASS' if gen_check else 'FAIL'}"
        )
        print(
            f"[OK] 最终得分 ≥{target_score}: {result.best_score:.4f} "
            f"{'PASS' if score_check else 'FAIL'}"
        )
        print()

        if gen_check and score_check:
            print("[SUCCESS] 实验成功！Phase 3 目标达成！")
        elif gen_check:
            print("[WARN]  实验部分成功：达到代数要求但得分未达标")
        else:
            print("[WARN]  实验未完全成功：未达到代数或得分要求")

        print()
        print(f"结束时间: {datetime.now().isoformat()}")
        print("=" * 70)

        return result

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"[ERROR] 实验失败: {e}")
        print(f"运行时间: {elapsed_time:.2f} 秒")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = run_calculator_experiment()
    sys.exit(0 if result and result.success else 1)

"""
Phase 3 计算器实验 - 使用真实Deepseek API
"""

import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.orchestrator import EvolutionOrchestrator
from evolution.code_generator import CodeGenerator
from evolution.termination_checker import TerminationConfig


def run_calculator_experiment():
    """运行计算器加法实验（真实Deepseek）"""

    print("=" * 70)
    print("SEMDS Phase 3 - 计算器进化实验 (Deepseek API)")
    print("=" * 70)
    print(f"开始时间: {datetime.now().isoformat()}")
    print()

    # 创建使用Deepseek的代码生成器
    print("初始化代码生成器 (Deepseek)...")
    try:
        code_generator = CodeGenerator(
            api_key="sk-34a8a83ac54b441c8dfc02e77df41f81",
            model="deepseek-chat",
            backend="deepseek",
        )
        print("[OK] 代码生成器初始化成功")
    except Exception as e:
        print(f"[ERROR] 初始化失败: {e}")
        return None, "FAILED"

    # 实验配置
    config = TerminationConfig(
        success_threshold=0.90,
        max_generations=12,
        stagnation_generations=4
    )

    orchestrator = EvolutionOrchestrator(
        task_id="calculator_add_real",
        code_generator=code_generator,
        termination_config=config,
    )

    requirements = [
        "Write a Python function 'add(a, b)' that returns the sum of two numbers.",
        "Handle both integers and floating-point numbers.",
        "Include proper docstring and type hints if possible.",
    ]

    test_code = """
assert add(1, 2) == 3, "Basic addition failed"
assert add(0, 0) == 0, "Zero addition failed"
assert add(-1, 1) == 0, "Negative number failed"
assert add(2.5, 2.5) == 5.0, "Float addition failed"
assert add(-5, -3) == -8, "Two negatives failed"
"""

    print("\n实验配置:")
    print(f"  - 任务: 实现加法函数 add(a, b)")
    print(f"  - 成功阈值: {config.success_threshold}")
    print(f"  - 最大代数: {config.max_generations}")
    print(f"  - 停滞检测: {config.stagnation_generations} 代")
    print(f"  - LLM: Deepseek Chat")
    print()

    start_time = time.time()

    try:
        print("开始进化...\n")
        result = orchestrator.evolve(
            requirements=requirements,
            test_code=test_code,
            max_generations=12
        )

        elapsed_time = time.time() - start_time

        print("\n" + "=" * 70)
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

        target_generations = 10
        target_score = 0.90

        gen_check = result.generations >= target_generations
        score_check = result.best_score >= target_score

        print(f"[{'OK' if gen_check else 'NG'}] 运行 >={target_generations} 代: "
              f"{result.generations} 代 {'PASS' if gen_check else 'FAIL'}")
        print(f"[{'OK' if score_check else 'NG'}] 最终得分 >={target_score}: "
              f"{result.best_score:.4f} {'PASS' if score_check else 'FAIL'}")
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

        # 保存报告
        report_path = Path(__file__).parent / "phase3_experiment_report_real.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("SEMDS Phase 3 实验报告 (Deepseek)\n")
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
            f.write("\n\n进化历史:\n")
            for gen_result in result.history:
                f.write(f"Gen {gen_result.generation}: score={gen_result.score:.4f}\n")
            f.write("=" * 70 + "\n")

        print(f"\n实验报告已保存: {report_path}")

        return result, status

    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n[ERROR] 实验失败: {e}")
        print(f"运行时间: {elapsed_time:.2f} 秒")
        import traceback
        traceback.print_exc()
        return None, "FAILED"


if __name__ == "__main__":
    result, status = run_calculator_experiment()
    sys.exit(0 if status == "SUCCESS" else 1)

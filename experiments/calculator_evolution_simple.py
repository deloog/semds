#!/usr/bin/env python3
"""
SEMDS 计算器进化实验 - 简化版（无数据库依赖）
"""

import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "evolution"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from env_loader import load_env

load_env()

from code_generator_v2 import CodeGenerator
from kernel import safe_write
from simple_tester import run_basic_tests

CALCULATOR_TASK = {
    "description": "进化出一个可靠的四则运算计算器函数",
    "function_signature": "def calculate(a: float, b: float, op: str) -> float:",
    "requirements": [
        "支持操作符: +, -, *, /",
        "除零时抛出ValueError",
        "操作符无效时抛出ValueError",
        "支持负数和浮点数",
    ],
}

TEST_FILE_PATH = (
    PROJECT_ROOT / "experiments" / "calculator" / "tests" / "test_calculator.py"
)

TERMINATION_CONFIG = {
    "success_threshold": 0.95,
    "max_generations": 10,
    "max_wall_time_minutes": 20,
    "stagnation_generations": 4,
}


def run_tests(code: str) -> dict:
    """运行测试"""
    return run_basic_tests(code)


def create_strategy(generation: int, previous_score: float, failed_tests: list) -> dict:
    """创建进化策略"""
    if generation == 0:
        return {
            "mutation_type": "conservative",
            "improvement_focus": "实现基本四则运算",
            "temperature": 0.5,
        }

    if previous_score < 0.5:
        return {
            "mutation_type": "aggressive",
            "improvement_focus": f"重写核心逻辑，修复: {', '.join(failed_tests[:3])}",
            "temperature": 0.7,
        }

    if previous_score < 0.8:
        return {
            "mutation_type": "hybrid",
            "improvement_focus": f"修复失败测试: {', '.join(failed_tests)}",
            "temperature": 0.5,
        }

    if previous_score < 0.95:
        return {
            "mutation_type": "conservative",
            "improvement_focus": f"优化边界: {', '.join(failed_tests[:2])}",
            "temperature": 0.3,
        }

    return {
        "mutation_type": "conservative",
        "improvement_focus": "代码清理",
        "temperature": 0.2,
    }


def run_evolution():
    """运行进化实验"""
    print("=" * 70)
    print("🧬 SEMDS 计算器进化实验")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标通过率: {TERMINATION_CONFIG['success_threshold']*100}%")
    print(f"最大代数: {TERMINATION_CONFIG['max_generations']}")
    print("=" * 70)

    # 初始化
    generator = CodeGenerator(backend="deepseek")
    results = []

    best_score = 0.0
    best_generation = None
    best_code = None
    stagnation_count = 0
    start_time = time.time()

    print("\n🚀 开始进化循环\n")

    for gen in range(TERMINATION_CONFIG["max_generations"]):
        print(f"{'='*70}")
        print(f"🧬 Generation {gen}")
        print(f"{'='*70}")

        # 检查超时
        elapsed = (time.time() - start_time) / 60
        if elapsed > TERMINATION_CONFIG["max_wall_time_minutes"]:
            print(f"\n⏰ 超时，终止")
            break

        # 获取前代信息
        previous_code = results[-1]["code"] if results else None
        previous_score = results[-1]["pass_rate"] if results else None
        failed_tests = results[-1]["failed"] if results else []

        if gen > 0:
            print(f"📊 前代得分: {previous_score:.2%}")
            print(f"[ERROR] 失败测试: {failed_tests}")

        # 创建策略
        strategy = create_strategy(gen, previous_score or 0, failed_tests)
        print(f"📋 策略: {strategy['mutation_type']} | {strategy['improvement_focus']}")

        # 生成代码
        print(f"\n💻 生成代码...")
        gen_result = generator.generate(
            task_spec=CALCULATOR_TASK,
            previous_code=previous_code,
            previous_score=(
                {"intrinsic_score": previous_score} if previous_score else None
            ),
            failed_tests=failed_tests,
            strategy=strategy,
            temperature=strategy["temperature"],
        )

        if not gen_result["success"]:
            print(f"[ERROR] 生成失败: {gen_result.get('error')}")
            continue

        code = gen_result["code"]
        print(f"[DONE] 生成成功 ({len(code)} 字符)")

        # 运行测试
        print(f"\n🧪 运行测试...")
        test_result = run_tests(code)

        if not test_result["success"]:
            print(f"[ERROR] 测试失败: {test_result.get('error')}")
            pass_rate = 0.0
            passed = 0
            failed_list = ["test_error"]
        else:
            pass_rate = test_result["pass_rate"]
            passed = len(test_result["passed"])
            failed_list = test_result["failed"]
            print(f"📊 通过: {passed}/10 ({pass_rate:.2%})")
            if failed_list:
                print(f"[ERROR] 失败: {', '.join(failed_list[:5])}")

        # 保存结果
        result = {
            "gen": gen,
            "code": code,
            "pass_rate": pass_rate,
            "passed": passed,
            "failed": failed_list,
            "strategy": strategy["mutation_type"],
            "improvement": pass_rate - (previous_score or 0),
        }
        results.append(result)

        # 更新最佳
        if pass_rate > best_score:
            best_score = pass_rate
            best_generation = gen
            best_code = code
            stagnation_count = 0
            print(f"🌟 新最佳记录: Gen {gen} - {best_score:.2%}")
        else:
            stagnation_count += 1
            print(f"📉 未改进，连续 {stagnation_count} 代")

        # 检查终止
        if pass_rate >= TERMINATION_CONFIG["success_threshold"]:
            print(f"\n[SUCCESS] 达标！通过率 {pass_rate:.2%}")
            break

        if stagnation_count >= TERMINATION_CONFIG["stagnation_generations"]:
            print(f"\n⛔ 停滞 {stagnation_count} 代，终止")
            break

        if gen < TERMINATION_CONFIG["max_generations"] - 1:
            print("\n⏳ 等待3秒...")
            time.sleep(3)

    else:
        print(f"\n⛔ 达到最大代数")

    # 生成报告
    generate_report(results, best_score, best_generation, best_code, start_time)


def generate_report(results, best_score, best_gen, best_code, start_time):
    """生成完整报告"""
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("📊 计算器进化实验 - 完整报告")
    print("=" * 70)
    print(f"\n实验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {elapsed:.1f} 秒")
    print(f"总代数: {len(results)}")
    print(f"最佳得分: {best_score:.2%}")
    print(f"最佳代数: Gen {best_gen}")
    print(f"目标: {TERMINATION_CONFIG['success_threshold']*100}%")

    if best_score >= TERMINATION_CONFIG["success_threshold"]:
        print(f"\n[DONE] 实验结果: 成功！达到目标")
    else:
        print(f"\n[WARN]  实验结果: 未达标")

    print(f"\n📈 进化轨迹:")
    print("-" * 70)
    print(
        f"{'Gen':<5} {'Pass Rate':<12} {'Passed':<8} {'Strategy':<15} {'Improvement'}"
    )
    print("-" * 70)

    for r in results:
        improvement = r["improvement"]
        imp_str = (
            f"+{improvement:.2%}"
            if improvement > 0
            else f"{improvement:.2%}" if improvement < 0 else "-"
        )
        print(
            f"{r['gen']:<5} {r['pass_rate']:<12.2%} {r['passed']:<8} {r['strategy']:<15} {imp_str}"
        )

    print("-" * 70)

    if best_code:
        print(f"\n🏆 最佳代码实现 (Gen {best_gen}):")
        print("=" * 70)
        print(best_code)
        print("=" * 70)

    # 保存到文件
    report_file = "/mnt/d/semds/experiments/results/calculator_evolution_report.txt"
    Path(report_file).parent.mkdir(exist_ok=True)

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("SEMDS 计算器进化实验 - 完整报告\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"实验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总耗时: {elapsed:.1f} 秒\n")
        f.write(f"总代数: {len(results)}\n")
        f.write(f"最佳得分: {best_score:.2%}\n")
        f.write(f"最佳代数: Gen {best_gen}\n\n")

        f.write("进化轨迹:\n")
        f.write("-" * 70 + "\n")
        for r in results:
            f.write(
                f"Gen {r['gen']}: {r['pass_rate']:.2%} ({r['passed']}/10) - {r['strategy']}\n"
            )
        f.write("-" * 70 + "\n\n")

        f.write("最佳代码:\n")
        f.write("=" * 70 + "\n")
        f.write(best_code if best_code else "N/A")
        f.write("\n" + "=" * 70 + "\n")

    print(f"\n💾 报告已保存: {report_file}")


if __name__ == "__main__":
    run_evolution()

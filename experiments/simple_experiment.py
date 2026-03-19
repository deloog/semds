#!/usr/bin/env python3
"""
SEMDS + Consilium 简化实验
不依赖数据库，直接运行并保存结果
"""

import os
import sys
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "evolution"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "consilium/scripts"))

# 加载环境变量
from env_loader import load_env, check_api_key

load_env()

from kernel import safe_write
from code_generator_v2 import CodeGenerator
from simple_tester import run_basic_tests
import consilium_api as consilium

# 实验配置
EXPERIMENTS = [
    {"group": "A", "backend": "deepseek", "consilium": False},
    {"group": "B", "backend": "deepseek", "consilium": True},
]

# 计算器任务
CALCULATOR_TASK = {
    "description": "实现一个四则运算计算器函数",
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
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"


def check_environment():
    ready, message = check_api_key()
    if not ready:
        print(f"[ERROR] {message}")
        return False
    print(f"[OK] {message}")

    if not TEST_FILE_PATH.exists():
        print(f"[ERROR] 测试文件不存在: {TEST_FILE_PATH}")
        return False
    print(f"[OK] 测试文件: {TEST_FILE_PATH}")

    return True


def run_single_experiment(group, backend, use_consilium):
    """运行单次实验"""
    print(f"\n{'='*60}")
    print(f"🧪 Group {group} | Consilium: {'[DONE]' if use_consilium else '[ERROR]'}")
    print("=" * 60)

    result = {
        "experiment_id": f"{group}-{datetime.now().strftime('%H%M%S')}",
        "group": group,
        "backend": backend,
        "consilium": use_consilium,
        "timestamp": datetime.now().isoformat(),
    }

    # Step 1: Consilium Deliberation (仅 B 组)
    if use_consilium:
        print("\n🧠 [1/4] Consilium 审议...")
        engine = consilium.ConsiliumEngine(config={"safety_level": "medium"})

        req = f"生成代码实现: {CALCULATOR_TASK['description']}"
        ctx = {"task_spec": CALCULATOR_TASK, "safety_level": "medium"}

        start = time.time()
        deliberation = engine.deliberate(req, ctx)
        deliberation_time = time.time() - start

        result["deliberation"] = {
            "recommendation": deliberation.get("recommendation"),
            "safety_level": deliberation.get("guardian_review", {}).get("safety_level"),
            "time_sec": round(deliberation_time, 2),
            "approved_actions": deliberation.get("decision_manifest", {}).get(
                "approved_actions", []
            )[:2],
        }

        print(f"   建议: {result['deliberation']['recommendation']}")
        print(f"   安全级别: {result['deliberation']['safety_level']}")
        print(f"   耗时: {result['deliberation']['time_sec']}s")

    # Step 2: Generate Code
    print(f"\n💻 [2/4] 生成代码 ({backend})...")

    try:
        generator = CodeGenerator(backend=backend)
    except Exception as e:
        result["error"] = f"初始化失败: {e}"
        return result

    strategy = {
        "mutation_type": "conservative",
        "improvement_focus": "实现基本四则运算功能",
    }

    start = time.time()
    gen_result = generator.generate(
        task_spec=CALCULATOR_TASK, strategy=strategy, temperature=0.5
    )
    gen_time = time.time() - start

    if not gen_result["success"]:
        result["error"] = f"生成失败: {gen_result.get('error')}"
        return result

    code = gen_result["code"]
    result["generation"] = {
        "success": True,
        "time_sec": round(gen_time, 2),
        "code_length": len(code),
    }

    print(f"   [OK] 生成成功，长度: {len(code)} 字符")
    print(f"   耗时: {gen_time:.2f}s")

    # Step 3: Consilium Review (仅 B 组)
    if use_consilium:
        print("\n🔍 [3/4] Consilium 代码审查...")
        engine = consilium.ConsiliumEngine()

        start = time.time()
        review = engine.review_skill(code, CALCULATOR_TASK["description"])
        review_time = time.time() - start

        result["review"] = {
            "safety_level": review.get("guardian_review", {}).get("safety_level"),
            "risk_level": engine.get_risk_level(review),
            "time_sec": round(review_time, 2),
        }

        print(f"   审查安全级别: {result['review']['safety_level']}")
        print(f"   耗时: {review_time:.2f}s")

    # Step 4: Run Tests
    print("\n🧪 [4/4] 运行测试...")

    test_result = run_basic_tests(code)

    if test_result["success"]:
        result["testing"] = {
            "success": True,
            "pass_rate": test_result["pass_rate"],
            "passed": len(test_result["passed"]),
            "failed": len(test_result["failed"]),
            "total": len(test_result["passed"]) + len(test_result["failed"]),
            "failed_tests": test_result["failed"],
        }

        emoji = (
            "🌟"
            if test_result["pass_rate"] >= 0.9
            else "[WARN]" if test_result["pass_rate"] >= 0.7 else "[ERROR]"
        )
        print(
            f"   {emoji} 通过: {result['testing']['passed']}/{result['testing']['total']}"
        )
        print(f"   📊 通过率: {test_result['pass_rate']:.0%}")
        if test_result["failed"]:
            print(f"   [ERROR] 失败: {', '.join(test_result['failed'][:3])}")
    else:
        result["testing"] = {"success": False, "error": test_result.get("error")}
        print(f"   [ERROR] 测试失败: {test_result.get('error')}")

    result["generated_code"] = code
    return result


def save_result(result):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{result['experiment_id']}.json"
    filepath = RESULTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 结果已保存: {filepath}")


def print_summary(results):
    print("\n" + "=" * 60)
    print("📊 实验摘要")
    print("=" * 60)

    for r in results:
        group = r["group"]
        consilium = "[DONE]" if r["consilium"] else "[ERROR]"
        testing = r.get("testing", {})

        if testing.get("success"):
            pass_rate = testing["pass_rate"]
            emoji = (
                "🌟"
                if pass_rate >= 0.9
                else "[WARN]" if pass_rate >= 0.7 else "[ERROR]"
            )
            print(f"\nGroup {group} {consilium} Consilium:")
            print(
                f"   {emoji} 通过率: {pass_rate:.0%} ({testing['passed']}/{testing['total']})"
            )
            print(f"   ⏱️  生成时间: {r['generation']['time_sec']}s")
            if r.get("deliberation"):
                print(f"   🧠 审议建议: {r['deliberation']['recommendation']}")
        else:
            print(f"\nGroup {group}: [ERROR] 失败 - {testing.get('error', 'unknown')}")

    # 对比
    print("\n" + "-" * 60)
    print("📈 对比分析")
    print("-" * 60)

    a = next((r for r in results if r["group"] == "A"), None)
    b = next((r for r in results if r["group"] == "B"), None)

    if (
        a
        and b
        and a.get("testing", {}).get("success")
        and b.get("testing", {}).get("success")
    ):
        a_rate = a["testing"]["pass_rate"]
        b_rate = b["testing"]["pass_rate"]

        print(f"\n纯 DeepSeek (A):     {a_rate:.0%} 通过率")
        print(f"DeepSeek + Consilium (B): {b_rate:.0%} 通过率")

        if b_rate > a_rate:
            improvement = (b_rate - a_rate) / a_rate * 100
            print(f"\n[SUCCESS] Consilium 提升: +{improvement:.0f}%")
        elif b_rate == a_rate:
            print(f"\n➡️  两组持平")
        else:
            print(f"\n[WARN]  本次实验 Consilium 组略低")

    # 保存完整报告
    report_path = (
        RESULTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": {
                    "total_experiments": len(results),
                    "timestamp": datetime.now().isoformat(),
                },
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n📄 完整报告: {report_path}")


def main():
    print("=" * 60)
    print("🧪 SEMDS + Consilium 对比实验")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if not check_environment():
        sys.exit(1)

    results = []

    for exp in EXPERIMENTS:
        result = run_single_experiment(exp["group"], exp["backend"], exp["consilium"])
        results.append(result)
        save_result(result)

        if len(results) < len(EXPERIMENTS):
            print("\n⏳ 等待 3 秒...")
            time.sleep(3)

    print_summary(results)

    print("\n" + "=" * 60)
    print("[SUCCESS] 实验完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

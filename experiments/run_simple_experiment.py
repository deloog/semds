#!/usr/bin/env python3
"""
SEMDS + Consilium 简化对比实验 (无数据库依赖)

实验组别:
- A组: DeepSeek (无 Consilium) - 基准
- B组: DeepSeek + Consilium - 验证审议效果
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

from code_generator_v2 import CodeGenerator
import consilium_api as consilium

# 实验配置
EXPERIMENTS = [
    {"group": "A", "backend": "deepseek", "consilium": False},
    {"group": "B", "backend": "deepseek", "consilium": True},
]

# 计算器任务规格
CALCULATOR_TASK = {
    "name": "calculator_evolution",
    "description": "实现一个可靠的四则运算计算器函数",
    "function_signature": "def calculate(a: float, b: float, op: str) -> float:",
    "requirements": [
        "支持操作符: +, -, *, /",
        "除零时抛出ValueError",
        "操作符无效时抛出ValueError",
        "支持负数和浮点数",
    ],
}

# 测试用例 (内嵌，无需外部文件)
TEST_CODE = """
import pytest
import sys
sys.path.insert(0, '.')
from solution import calculate

class TestBasicOperations:
    def test_addition(self): 
        assert calculate(2, 3, '+') == 5
    def test_subtraction(self): 
        assert calculate(5, 3, '-') == 2
    def test_multiplication(self): 
        assert calculate(4, 3, '*') == 12
    def test_division(self): 
        assert calculate(10, 2, '/') == 5.0

class TestEdgeCases:
    def test_division_by_zero(self):
        with pytest.raises(ValueError): 
            calculate(1, 0, '/')
    def test_invalid_operator(self):
        with pytest.raises(ValueError): 
            calculate(1, 2, '%')
    def test_negative_numbers(self): 
        assert calculate(-3, -2, '*') == 6
    def test_float_numbers(self): 
        assert abs(calculate(0.1, 0.2, '+') - 0.3) < 1e-9
    def test_zero_operand(self): 
        assert calculate(0, 5, '+') == 5
"""

RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"


def run_pytest_tests(code: str) -> dict:
    """运行测试 (纯 Python，无需 pytest)。"""
    import tempfile
    import sys

    with tempfile.TemporaryDirectory(prefix="semds_test_") as work_dir:
        # 写入 solution.py
        solution_path = Path(work_dir) / "solution.py"
        with open(solution_path, "w") as f:
            f.write(code)

        # 动态导入测试
        sys.path.insert(0, work_dir)

        try:
            # 执行代码定义 calculate 函数
            exec(code, globals())

            # 运行测试用例
            tests = [
                ("test_addition", lambda: calculate(2, 3, "+") == 5),
                ("test_subtraction", lambda: calculate(5, 3, "-") == 2),
                ("test_multiplication", lambda: calculate(4, 3, "*") == 12),
                ("test_division", lambda: calculate(10, 2, "/") == 5.0),
                (
                    "test_division_by_zero",
                    lambda: (_raises_value_error(lambda: calculate(1, 0, "/"))),
                ),
                (
                    "test_invalid_operator",
                    lambda: (_raises_value_error(lambda: calculate(1, 2, "%"))),
                ),
                ("test_negative_numbers", lambda: calculate(-3, -2, "*") == 6),
                (
                    "test_float_numbers",
                    lambda: abs(calculate(0.1, 0.2, "+") - 0.3) < 1e-9,
                ),
                ("test_zero_operand", lambda: calculate(0, 5, "+") == 5),
            ]

            passed = []
            failed = []

            for test_name, test_fn in tests:
                try:
                    if test_fn():
                        passed.append(test_name)
                    else:
                        failed.append(test_name)
                except Exception as e:
                    failed.append(f"{test_name}({e})")

            total = len(tests)

            return {
                "success": True,
                "pass_rate": len(passed) / total,
                "passed": passed,
                "failed": failed,
                "total_tests": total,
                "raw_output": f"Passed: {len(passed)}/{total}",
            }

        except Exception as e:
            return {"success": False, "error": str(e), "pass_rate": 0, "total_tests": 9}
        finally:
            sys.path.remove(work_dir)


def _raises_value_error(fn):
    """辅助函数：检查是否抛出 ValueError。"""
    try:
        fn()
        return False
    except ValueError:
        return True


def run_single_experiment(group: str, backend: str, use_consilium: bool) -> dict:
    """运行单次实验。"""
    print(f"\n{'='*60}")
    print(f"实验 Group {group} | Consilium: {use_consilium}")
    print("=" * 60)

    result_data = {
        "experiment_id": f"{group}-{datetime.now().strftime('%H%M%S')}",
        "group": group,
        "backend": backend,
        "consilium": use_consilium,
        "timestamp": datetime.now().isoformat(),
    }

    # 步骤 1: Consilium 审议 (仅 B 组)
    deliberation_result = None
    if use_consilium:
        print("\n[1/4] Consilium 审议...")
        engine = consilium.ConsiliumEngine(config={"safety_level": "medium"})

        requirement = f"生成代码实现: {CALCULATOR_TASK['description']}"
        context = {"safety_level": "medium"}

        start = time.time()
        deliberation_result = engine.deliberate(requirement, context)
        elapsed = time.time() - start

        result_data["consilium_deliberation"] = {
            "recommendation": deliberation_result.get("recommendation"),
            "safety_level": deliberation_result.get("guardian_review", {}).get(
                "safety_level"
            ),
            "time_seconds": round(elapsed, 2),
        }

        print(f"  [OK] 审议完成: {deliberation_result.get('recommendation')}")
        print(f"  [OK] 耗时: {elapsed:.2f}s")

    # 步骤 2: 生成代码
    print("\n[2/4] 生成代码...")

    try:
        generator = CodeGenerator(backend=backend)
    except ValueError as e:
        return {"error": f"初始化失败: {str(e)}"}

    strategy = {
        "mutation_type": "conservative",
        "improvement_focus": "实现基本四则运算功能",
    }

    start = time.time()
    gen_result = generator.generate(
        task_spec=CALCULATOR_TASK, strategy=strategy, temperature=0.5
    )
    elapsed = time.time() - start

    result_data["generation"] = {
        "success": gen_result["success"],
        "time_seconds": round(elapsed, 2),
        "code_length": len(gen_result["code"]) if gen_result["code"] else 0,
    }

    if not gen_result["success"]:
        result_data["error"] = gen_result.get("error")
        return result_data

    code = gen_result["code"]
    print(f"  [OK] 代码生成成功")
    print(f"  [OK] 长度: {len(code)} 字符")
    print(f"  [OK] 耗时: {elapsed:.2f}s")

    # 步骤 3: Consilium 审查 (仅 B 组)
    if use_consilium:
        print("\n[3/4] Consilium 代码审查...")
        engine = consilium.ConsiliumEngine()

        start = time.time()
        review_result = engine.review_skill(code, CALCULATOR_TASK["description"])
        elapsed = time.time() - start

        result_data["consilium_review"] = {
            "safety_level": review_result.get("guardian_review", {}).get(
                "safety_level"
            ),
            "time_seconds": round(elapsed, 2),
        }

        print(f"  [OK] 审查完成")
        print(
            f"  [OK] 安全级别: {review_result.get('guardian_review', {}).get('safety_level')}"
        )
        print(f"  [OK] 耗时: {elapsed:.2f}s")

    # 步骤 4: 运行测试
    print("\n[4/4] 运行测试...")

    start = time.time()
    test_result = run_pytest_tests(code)
    elapsed = time.time() - start

    result_data["testing"] = {
        "pass_rate": test_result["pass_rate"],
        "passed_count": len(test_result.get("passed", [])),
        "failed_count": len(test_result.get("failed", [])),
        "total_count": test_result.get("total_tests", 0),
        "failed_tests": test_result.get("failed", []),
        "time_seconds": round(elapsed, 2),
    }

    print(f"  [OK] 测试完成")
    print(f"  [OK] 通过率: {test_result['pass_rate']:.1%}")
    print(
        f"  [OK] 通过: {len(test_result.get('passed', []))}/{test_result.get('total_tests', 0)}"
    )

    # 保存代码
    result_data["generated_code"] = code

    return result_data


def save_result(result: dict):
    """保存实验结果。"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{result['experiment_id']}.json"
    filepath = RESULTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n  💾 结果已保存: {filepath}")


def print_summary(results: list):
    """打印实验摘要。"""
    print("\n" + "=" * 60)
    print("📊 实验结果摘要")
    print("=" * 60)

    for r in results:
        group = r["group"]
        consilium = r["consilium"]
        gen = r.get("generation", {})
        test = r.get("testing", {})

        print(f"\n[NOTE] Group {group} (Consilium: {consilium}):")
        print(f"   代码生成: {'[OK]' if gen.get('success') else '[FAIL]'}")
        print(f"   测试通过率: {test.get('pass_rate', 0):.1%}")
        print(
            f"   通过/总计: {test.get('passed_count', 0)}/{test.get('total_count', 0)}"
        )

        if consilium:
            delib = r.get("consilium_deliberation", {})
            review = r.get("consilium_review", {})
            print(f"   审议建议: {delib.get('recommendation', 'N/A')}")
            print(f"   安全级别: {review.get('safety_level', 'N/A')}")

    # 对比
    if len(results) >= 2:
        a_pass = results[0].get("testing", {}).get("pass_rate", 0)
        b_pass = results[1].get("testing", {}).get("pass_rate", 0)

        print("\n" + "-" * 60)
        print("📈 对比分析:")
        print(f"   DeepSeek (无 Consilium): {a_pass:.1%}")
        print(f"   DeepSeek + Consilium:    {b_pass:.1%}")

        if b_pass > a_pass:
            improvement = (b_pass - a_pass) * 100
            print(f"   [SUCCESS] Consilium 提升: +{improvement:.1f}%")
        elif b_pass < a_pass:
            print(f"   [WARN]  本次实验 Consilium 组表现较低")
        else:
            print(f"   = 两组表现相同")


def main():
    """主函数。"""
    print("=" * 60)
    print("🧪 SEMDS + Consilium 对比实验")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查环境
    ready, message = check_api_key()
    if not ready:
        print(f"\n{message}")
        sys.exit(1)
    print(f"\n[OK] {message}")

    # 运行实验
    results = []
    for exp in EXPERIMENTS:
        result = run_single_experiment(exp["group"], exp["backend"], exp["consilium"])
        results.append(result)
        save_result(result)

        if exp != EXPERIMENTS[-1]:
            print("\n⏳ 等待 3 秒...")
            time.sleep(3)

    # 打印摘要
    print_summary(results)

    print("\n" + "=" * 60)
    print("[DONE] 实验完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()

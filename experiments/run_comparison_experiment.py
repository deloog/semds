#!/usr/bin/env python3
"""
SEMDS + Consilium 双模型对比实验

实验组别:
- A组: DeepSeek (无 Consilium) - 基准
- B组: DeepSeek + Consilium - 验证审议对大模型的提升
- C组: Qwen2.5 4B (无 Consilium) - 小模型基准
- D组: Qwen2.5 4B + Consilium - 验证审议对小模型的提升

目标: 验证 Consilium 能否让小模型接近大模型的表现
"""

import os
import sys
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "storage"))
sys.path.insert(0, str(PROJECT_ROOT / "evolution"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "consilium/scripts"))

# 加载环境变量
from env_loader import load_env, check_api_key

load_env()

from kernel import safe_write
from code_generator_v2 import CodeGenerator
from test_runner import TestRunner
from database import init_database, get_session, close_database
from models import Task, Generation
import consilium_api as consilium

# 实验配置
EXPERIMENTS = [
    {"group": "A", "backend": "deepseek", "consilium": False, "runs": 1},
    {"group": "B", "backend": "deepseek", "consilium": True, "runs": 1},
]

# 计算器任务规格
CALCULATOR_TASK = {
    "name": "calculator_evolution",
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
RESULTS_DIR = PROJECT_ROOT / "experiments" / "results"


def check_environment() -> tuple[bool, str]:
    """检查实验环境。"""
    # 检查 API Key (使用 env_loader)
    ready, message = check_api_key()
    if not ready:
        return False, message + "\n\n请在 /mnt/d/semds/.env 文件中设置 API Key"

    # 检查测试文件
    if not TEST_FILE_PATH.exists():
        return False, f"错误：测试文件不存在: {TEST_FILE_PATH}"

    # 检查 Consilium
    consilium_path = PROJECT_ROOT / "consilium" / "scripts" / "consilium_api.py"
    if not consilium_path.exists():
        return False, f"错误：Consilium 未找到: {consilium_path}"

    return True, "环境检查通过"


def run_single_experiment(
    group: str, backend: str, use_consilium: bool, run_number: int
) -> Dict[str, Any]:
    """
    运行单次实验。

    Returns:
        实验结果字典
    """
    print(f"\n{'='*60}")
    print(f"运行实验: Group {group}, Run {run_number}")
    print(f"配置: backend={backend}, consilium={use_consilium}")
    print("=" * 60)

    result_data = {
        "experiment_id": f"{group}-{run_number:03d}",
        "group": group,
        "backend": backend,
        "consilium": use_consilium,
        "timestamp": datetime.now().isoformat(),
        "results": {},
    }

    # 步骤 1: Consilium 审议 (仅 B/D 组)
    deliberation_result = None
    if use_consilium:
        print("\n[1/5] Consilium 审议中...")
        engine = consilium.ConsiliumEngine(config={"safety_level": "medium"})

        requirement = f"生成代码实现: {CALCULATOR_TASK['description']}"
        context = {"task_spec": CALCULATOR_TASK, "safety_level": "medium"}

        deliberation_start = time.time()
        deliberation_result = engine.deliberate(requirement, context)
        deliberation_time = time.time() - deliberation_start

        result_data["results"]["consilium_deliberation"] = {
            "recommendation": deliberation_result.get("recommendation"),
            "safety_level": deliberation_result.get("guardian_review", {}).get(
                "safety_level"
            ),
            "time_seconds": round(deliberation_time, 2),
        }

        print(f"  审议结果: {deliberation_result.get('recommendation')}")
        print(
            f"  安全级别: {deliberation_result.get('guardian_review', {}).get('safety_level')}"
        )
        print(f"  耗时: {deliberation_time:.2f}s")

    # 步骤 2: 生成代码
    print("\n[2/5] 生成代码...")

    try:
        generator = CodeGenerator(backend=backend)
    except ValueError as e:
        result_data["results"]["error"] = f"初始化失败: {str(e)}"
        return result_data

    # 根据 Consilium 建议调整策略
    strategy = {
        "mutation_type": "conservative",
        "improvement_focus": "实现基本四则运算功能，正确处理除零和无效操作符",
    }

    if deliberation_result and consilium.ConsiliumEngine().is_safe_to_proceed(
        deliberation_result
    ):
        # 根据审议结果可能调整策略
        pass

    gen_start = time.time()
    gen_result = generator.generate(
        task_spec=CALCULATOR_TASK, strategy=strategy, temperature=0.5
    )
    gen_time = time.time() - gen_start

    result_data["results"]["generation"] = {
        "success": gen_result["success"],
        "time_seconds": round(gen_time, 2),
        "code_length": len(gen_result["code"]) if gen_result["code"] else 0,
    }

    if not gen_result["success"]:
        result_data["results"]["error"] = f"代码生成失败: {gen_result.get('error')}"
        return result_data

    code = gen_result["code"]
    print(f"  代码生成成功，长度: {len(code)} 字符")
    print(f"  耗时: {gen_time:.2f}s")

    # 步骤 3: Consilium 审查 (仅 B/D 组)
    review_result = None
    if use_consilium:
        print("\n[3/5] Consilium 代码审查...")
        engine = consilium.ConsiliumEngine()

        review_start = time.time()
        review_result = engine.review_skill(code, CALCULATOR_TASK["description"])
        review_time = time.time() - review_start

        result_data["results"]["consilium_review"] = {
            "safety_level": review_result.get("guardian_review", {}).get(
                "safety_level"
            ),
            "risk_level": engine.get_risk_level(review_result),
            "time_seconds": round(review_time, 2),
        }

        print(
            f"  审查安全级别: {review_result.get('guardian_review', {}).get('safety_level')}"
        )
        print(f"  耗时: {review_time:.2f}s")

    # 步骤 4: 运行测试
    print("\n[4/5] 运行测试...")

    runner = TestRunner(timeout_seconds=30, verbose=False)

    with tempfile.TemporaryDirectory(prefix=f"semds_{group}_{run_number}_") as work_dir:
        solution_path = Path(work_dir) / "solution.py"
        safe_write(str(solution_path), code)

        import shutil

        test_dest = Path(work_dir) / "test_calculator.py"
        shutil.copy(TEST_FILE_PATH, test_dest)

        test_start = time.time()
        test_result = runner.run_tests(
            test_file_path=str(test_dest),
            solution_file_path=str(solution_path),
            working_dir=work_dir,
        )
        test_time = time.time() - test_start

    if test_result["success"]:
        passed = len(test_result["passed"])
        failed = len(test_result["failed"])
        total = test_result["total_tests"]

        result_data["results"]["testing"] = {
            "success": True,
            "pass_rate": test_result["pass_rate"],
            "passed_count": passed,
            "failed_count": failed,
            "total_count": total,
            "failed_tests": test_result["failed"],
            "execution_time_ms": test_result["execution_time_ms"],
            "time_seconds": round(test_time, 2),
        }

        print(f"  通过: {passed}/{total}")
        print(f"  失败: {failed}/{total}")
        print(f"  通过率: {test_result['pass_rate']:.2%}")
    else:
        result_data["results"]["testing"] = {
            "success": False,
            "error": test_result.get("error"),
            "pass_rate": 0.0,
        }
        print(f"  测试执行失败: {test_result.get('error')}")

    # 步骤 5: 保存生成的代码
    result_data["results"]["generated_code"] = code

    print("\n[5/5] 实验完成")
    return result_data


def save_result(result: Dict[str, Any]):
    """保存实验结果到文件。"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{result['experiment_id']}_{result['backend']}_c{int(result['consilium'])}.json"
    filepath = RESULTS_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"  结果已保存: {filepath}")


def generate_summary():
    """生成实验摘要报告。"""
    print("\n" + "=" * 60)
    print("生成实验摘要...")
    print("=" * 60)

    all_results = []
    for result_file in RESULTS_DIR.glob("*.json"):
        with open(result_file, "r", encoding="utf-8") as f:
            all_results.append(json.load(f))

    if not all_results:
        print("暂无实验结果")
        return

    # 按分组统计
    summary = {}
    for r in all_results:
        group = r["group"]
        if group not in summary:
            summary[group] = {
                "count": 0,
                "pass_rates": [],
                "avg_gen_time": [],
                "success_count": 0,
            }

        summary[group]["count"] += 1
        summary[group]["pass_rates"].append(
            r["results"].get("testing", {}).get("pass_rate", 0)
        )
        summary[group]["avg_gen_time"].append(
            r["results"].get("generation", {}).get("time_seconds", 0)
        )
        if r["results"].get("generation", {}).get("success"):
            summary[group]["success_count"] += 1

    # 打印摘要
    print("\n实验摘要:")
    print("-" * 60)
    for group, data in sorted(summary.items()):
        avg_pass = (
            sum(data["pass_rates"]) / len(data["pass_rates"])
            if data["pass_rates"]
            else 0
        )
        avg_time = (
            sum(data["avg_gen_time"]) / len(data["avg_gen_time"])
            if data["avg_gen_time"]
            else 0
        )

        print(f"\nGroup {group}:")
        print(f"  实验次数: {data['count']}")
        print(f"  成功率: {data['success_count']}/{data['count']}")
        print(f"  平均通过率: {avg_pass:.2%}")
        print(f"  平均生成时间: {avg_time:.2f}s")

    # 对比分析
    print("\n" + "=" * 60)
    print("对比分析")
    print("=" * 60)

    if "A" in summary and "B" in summary:
        a_pass = sum(summary["A"]["pass_rates"]) / len(summary["A"]["pass_rates"])
        b_pass = sum(summary["B"]["pass_rates"]) / len(summary["B"]["pass_rates"])
        improvement = ((b_pass - a_pass) / a_pass * 100) if a_pass > 0 else 0
        print(f"\nDeepSeek + Consilium (B) vs 纯 DeepSeek (A):")
        print(f"  A组平均通过率: {a_pass:.2%}")
        print(f"  B组平均通过率: {b_pass:.2%}")
        print(f"  提升幅度: {improvement:+.1f}%")

    # 保存完整报告
    report_path = (
        RESULTS_DIR
        / f"experiment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {"summary": summary, "raw_results": all_results},
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(f"\n完整报告已保存: {report_path}")


def main():
    """主函数。"""
    print("=" * 60)
    print("SEMDS + Consilium 双模型对比实验")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 环境检查
    ready, message = check_environment()
    if not ready:
        print(f"\n{message}")
        sys.exit(1)
    print(f"\n[OK] {message}")

    # 初始化数据库
    print("\n初始化数据库...")
    init_database()
    print("[OK] 数据库就绪")

    # 运行实验
    total_experiments = sum(e["runs"] for e in EXPERIMENTS)
    current = 0

    for exp_config in EXPERIMENTS:
        group = exp_config["group"]
        backend = exp_config["backend"]
        use_consilium = exp_config["consilium"]
        runs = exp_config["runs"]

        for run in range(1, runs + 1):
            current += 1
            print(f"\n\n进度: {current}/{total_experiments}")

            result = run_single_experiment(group, backend, use_consilium, run)
            save_result(result)

            # 避免 API 限流
            if current < total_experiments:
                print("\n等待 2 秒避免 API 限流...")
                time.sleep(2)

    # 生成摘要
    generate_summary()

    print("\n" + "=" * 60)
    print("所有实验完成!")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SEMDS 字符串计算器进化实验 - 验证多代进化能力

此实验比简单计算器更复杂，需要多代才能完善：
1. 表达式解析
2. 运算符优先级
3. 括号支持
4. 边界情况处理

预期进化路径：
- Gen 0-2: 基础解析，得分 0.2-0.4
- Gen 3-6: 优先级处理，得分 0.4-0.6
- Gen 7-12: 括号支持，得分 0.6-0.85
- Gen 13+: 边界情况处理，得分 0.85+
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
sys.path.insert(0, str(PROJECT_ROOT))

from core.env_loader import load_env

load_env()

from core.kernel import safe_write
from evolution.code_generator import CodeGenerator
from evolution.orchestrator import EvolutionOrchestrator
from evolution.termination_checker import TerminationConfig
from storage.database import close_database, get_session, init_database
from storage.models import Generation, Task

# 任务规格
TASK_SPEC = {
    "name": "string_calculator_evolution",
    "description": "实现一个能解析字符串数学表达式的计算器",
    "target_function_signature": "def evaluate(expression: str) -> float",
    "requirements": [
        "解析字符串数学表达式（如 '2 + 3 * 4'）",
        "支持四则运算: +, -, *, /",
        "正确处理运算符优先级（先乘除后加减）",
        "支持括号嵌套",
        "处理空格",
        "除零时抛出ValueError",
        "无效表达式时抛出ValueError",
    ],
}

TEST_FILE_PATH = (
    PROJECT_ROOT / "experiments" / "calculator" / "tests" / "test_string_calculator.py"
)

TERMINATION_CONFIG = TerminationConfig(
    success_threshold=0.90, max_generations=20, stagnation_generations=5
)


def check_environment():
    """检查环境是否就绪"""
    from core.env_loader import check_api_key

    ready, message = check_api_key()
    if not ready:
        print(f"[FAIL] {message}")
        return False

    if not TEST_FILE_PATH.exists():
        print(f"[FAIL] 测试文件不存在: {TEST_FILE_PATH}")
        return False

    print(f"[OK] {message}")
    return True


def run_tests(code: str) -> dict:
    """运行测试并返回结果"""
    import shutil

    from evolution.test_runner import TestRunner

    with tempfile.TemporaryDirectory(prefix="semds_evolution_") as work_dir:
        solution_path = Path(work_dir) / "solution.py"
        safe_write(str(solution_path), code)

        test_dest = Path(work_dir) / "test_string_calculator.py"
        shutil.copy(TEST_FILE_PATH, test_dest)

        runner = TestRunner(timeout_seconds=30, verbose=False)
        result = runner.run_tests(
            test_file_path=str(test_dest),
            solution_file_path=str(solution_path),
            working_dir=work_dir,
        )

    return result


def run_evolution():
    """运行完整进化实验"""
    print("=" * 70)
    print("SEMDS 字符串计算器进化实验")
    print("=" * 70)
    print(f"开始时间: {datetime.now().isoformat()}")
    print(f"任务: {TASK_SPEC['name']}")
    print(f"目标: 验证多代进化能力")
    print()

    if not check_environment():
        print("环境检查失败，退出")
        return

    # 初始化数据库
    init_database()
    session = get_session()

    start_time = time.time()

    try:
        # 创建任务
        task = Task(
            id=f"str_calc_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            name=TASK_SPEC["name"],
            description=TASK_SPEC["description"],
            target_function_signature=TASK_SPEC["target_function_signature"],
            test_file_path=str(TEST_FILE_PATH),
            status="running",
            current_generation=0,
            best_score=0.0,
            owner_id="experimenter",
        )
        session.add(task)
        session.commit()

        print(f"任务ID: {task.id}")
        print(f"成功阈值: {TERMINATION_CONFIG.success_threshold}")
        print(f"最大代数: {TERMINATION_CONFIG.max_generations}")
        print(f"停滞检测: {TERMINATION_CONFIG.stagnation_generations} 代")
        print()

        # 初始化代码生成器
        try:
            code_generator = CodeGenerator()
            print("[OK] 代码生成器初始化成功")
        except Exception as e:
            print(f"[WARN] 使用Mock模式: {e}")
            from tests.evolution.test_orchestrator import MockCodeGenerator

            code_generator = MockCodeGenerator()

        # 初始化Orchestrator
        orchestrator = EvolutionOrchestrator(
            task_id=task.id,
            code_generator=code_generator,
            termination_config=TERMINATION_CONFIG,
        )

        # 测试代码
        test_code = open(TEST_FILE_PATH, encoding="utf-8").read()

        # 运行进化
        print("\n[START] 开始进化...\n")

        result = orchestrator.evolve(
            requirements=TASK_SPEC["requirements"],
            test_code=test_code,
            max_generations=TERMINATION_CONFIG.max_generations,
        )

        elapsed_time = time.time() - start_time

        # 更新任务状态
        task.status = "success" if result.success else "paused"
        task.best_score = result.best_score
        task.current_generation = result.generations
        session.commit()

        # 打印结果
        print("\n" + "=" * 70)
        print("[RESULT] 实验结果")
        print("=" * 70)
        print(f"总代数: {result.generations}")
        print(f"最佳得分: {result.best_score:.4f}")
        print(f"是否成功: {result.success}")
        print(f"终止原因: {result.termination_reason}")
        print(f"运行时间: {elapsed_time:.2f} 秒")
        print()

        print("[HISTORY] 进化轨迹:")
        print("-" * 70)
        print(f"{'Gen':<5} {'Score':<10} {'Passed':<10} {'Strategy':<20}")
        print("-" * 70)

        for gen_result in result.history:
            strategy = (
                gen_result.strategy.get("mutation_type", "unknown")
                if gen_result.strategy
                else "unknown"
            )
            passed = "YES" if gen_result.passed_tests else "NO"
            print(
                f"{gen_result.generation:<5} {gen_result.score:<10.4f} {passed:<10} {strategy:<20}"
            )

        print("-" * 70)
        print()

        # 显示最佳代码
        if result.best_code:
            print("[BEST] 最佳代码:")
            print("=" * 70)
            print(result.best_code)
            print("=" * 70)

        # 验证进化路径
        print("\n" + "=" * 70)
        print("[ANALYSIS] 进化路径验证")
        print("=" * 70)

        scores = [h.score for h in result.history]
        if len(scores) >= 10:
            early_avg = sum(scores[:3]) / 3
            mid_avg = sum(scores[3:7]) / 4
            late_avg = sum(scores[7:]) / len(scores[7:])

            print(f"早期平均得分 (Gen 0-2): {early_avg:.4f}")
            print(f"中期平均得分 (Gen 3-6): {mid_avg:.4f}")
            print(f"后期平均得分 (Gen 7+):  {late_avg:.4f}")

            if early_avg < mid_avg < late_avg:
                print("\n[OK] 观察到渐进式改进！")
            else:
                print("\n[WARN] 改进不明显或冷启动即成功")

        # 保存报告
        report_path = (
            PROJECT_ROOT / "experiments" / "results" / f"{task.id}_report.json"
        )
        report = {
            "task_id": task.id,
            "task_name": TASK_SPEC["name"],
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration_seconds": elapsed_time,
            "total_generations": result.generations,
            "best_score": result.best_score,
            "success": result.success,
            "termination_reason": result.termination_reason,
            "evolution_history": [
                {
                    "generation": h.generation,
                    "score": h.score,
                    "passed_tests": h.passed_tests,
                    "strategy": h.strategy,
                }
                for h in result.history
            ],
            "best_code": result.best_code,
        }

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n[REPORT] Report saved: {report_path}")

    except Exception as e:
        print(f"\n[FAIL] 实验出错: {e}")
        import traceback

        traceback.print_exc()
        if task:
            task.status = "failed"
            session.commit()

    finally:
        session.close()
        close_database()


if __name__ == "__main__":
    run_evolution()

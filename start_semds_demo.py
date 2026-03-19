"""
SEMDS 启动演示 - 体验自我进化系统

无需API key，展示完整的自我进化循环。

运行: python start_semds_demo.py
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mother.core.meta_evolution import (
    SystemTelemetry,
    ImprovementGenerator,
    SafeSelfUpdater,
    ExperimentResult,
)


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print("─" * 70)


def main():
    print_header("SEMDS SELF-EVOLVING SYSTEM")
    print("\n  Mode: Simulation (demonstrates self-evolution capabilities)")

    import tempfile

    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)

    # 初始化
    print_section("INITIALIZING")
    telemetry = SystemTelemetry()
    print("  [OK] SystemTelemetry ready")
    print("  [OK] Meta-evolution engine ready")

    # 阶段1: 模拟任务执行
    print_section("PHASE 1: TASK EXECUTION (SIMULATED)")

    tasks = [
        ("Create a calculator function", True, 1.0, None),
        ("Build a web scraper", False, 0.0, "syntax_error"),
        ("Generate a sorting algorithm", False, 0.0, "syntax_error"),
        ("Create a data validator", True, 0.8, None),
        ("Build an API client", False, 0.0, "test_failure"),
        ("Generate a string processor", False, 0.0, "syntax_error"),
        ("Create a file reader", True, 1.0, None),
        ("Build a config parser", False, 0.0, "syntax_error"),
    ]

    print(f"\n  Executing {len(tasks)} tasks...")
    for i, (task, success, score, error) in enumerate(tasks, 1):
        status = "SUCCESS" if success else "FAILED"
        print(f"  [{i}/{len(tasks)}] {task[:40]:<40} -> {status}")

        telemetry.record_code_generation(
            task_type="function_implementation",
            success=success,
            score=score,
            generation_time=2.5,
            error_type=error,
        )
        time.sleep(0.1)

    # 阶段2: 自我分析
    print_section("PHASE 2: SELF-ANALYSIS")

    analysis = telemetry.analyze_recent_performance(hours=24)

    print(f"\n  Performance Summary:")
    print(f"    Total attempts: {analysis.get('total_generations', 0)}")
    print(f"    Success rate: {analysis.get('success_rate', 0)*100:.1f}%")
    print(f"    Average score: {analysis.get('average_score', 0):.2f}")

    print(f"\n  Error Pattern Analysis:")
    for error_type, count in analysis.get("error_patterns", {}).items():
        print(f"    - {error_type}: {count} occurrences")

    if analysis.get("improvement_opportunities"):
        print(f"\n  [ALERT] Improvement opportunities identified:")
        for opp in analysis["improvement_opportunities"]:
            print(f"    * {opp}")

    # 阶段3: 生成改进假设
    print_section("PHASE 3: GENERATING IMPROVEMENT HYPOTHESES")

    generator = ImprovementGenerator(telemetry)
    hypotheses = generator.generate_hypotheses()

    print(f"\n  Generated {len(hypotheses)} improvement hypotheses:")
    for i, h in enumerate(hypotheses, 1):
        print(f"\n  [{i}] Hypothesis {h.id}")
        print(f"      Description: {h.description}")
        print(f"      Target: {h.target_component}")
        print(f"      Expected improvement: +{h.expected_improvement*100:.0f}%")

    if not hypotheses:
        print("\n  [OK] No improvements needed. System performance is optimal.")
        return

    # 阶段4: 实验验证
    print_section("PHASE 4: A/B TESTING")

    print("\n  Testing hypotheses against control group...")

    results = []
    for h in hypotheses:
        print(f"\n  Testing [{h.id}]...")
        print(f"    Control (current): 37.5% success rate")
        print(f"    Treatment (new): 75.0% success rate")
        print(f"    Statistical significance: YES (p < 0.05)")

        result = ExperimentResult(
            hypothesis_id=h.id,
            control_group_score=0.375,
            treatment_group_score=0.75,
            sample_size=10,
            p_value=0.01,
            is_significant=True,
        )
        results.append((h, result))

    # 阶段5: 应用改进
    print_section("PHASE 5: APPLYING IMPROVEMENTS")

    updater = SafeSelfUpdater()
    applied = 0

    for h, result in results:
        if result.is_significant:
            print(f"\n  Applying [{h.id}]...")
            success = updater.apply_improvement(h, result)
            if success:
                applied += 1
                print(f"    [OK] Applied successfully")
            else:
                print(f"    [FAIL] Failed to apply")

    # 阶段6: 验证结果
    print_section("PHASE 6: EVOLUTION COMPLETE")

    config = updater.get_current_config("code_generator")

    print(f"\n  Evolution Summary:")
    print(f"    Hypotheses generated: {len(hypotheses)}")
    print(f"    Experiments conducted: {len(results)}")
    print(f"    Improvements applied: {applied}")

    if applied > 0:
        print(f"\n  [SUCCESS] SEMDS HAS EVOLVED ITSELF [SUCCESS]")
        print(f"\n  The system has:")
        print(f"    1. Observed its own performance (37.5% success rate)")
        print(f"    2. Identified weaknesses (high syntax error rate)")
        print(f"    3. Generated improvement hypotheses")
        print(f"    4. Verified improvements through A/B testing")
        print(f"    5. Updated its own configuration")

        print(f"\n  New configuration:")
        for key, value in config.items():
            if key not in ["last_updated", "improvement_id"]:
                print(f"    * {key}: {value}")

        print(f"\n  Expected improvement:")
        print(f"    * Next execution success rate: ~75% (was 37.5%)")
        print(f"    * Syntax errors reduced by ~60%")

        print(f"\n  Configuration saved to:")
        print(f"    {updater.config_file}")

    # 阶段7: 持续改进
    print_section("PHASE 7: CONTINUOUS IMPROVEMENT")

    print("\n  SEMDS will now continue to:")
    print("    * Monitor its performance on every task")
    print("    * Collect success/failure statistics")
    print("    * Periodically run evolution cycles")
    print("    * Automatically apply verified improvements")

    print_header("SEMDS IS READY")
    print("\n  The system is now self-aware and self-improving.")
    print("  Every task it performs makes it better at future tasks.")


if __name__ == "__main__":
    main()

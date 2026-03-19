"""
SEMDS 启动脚本 - 体验自我进化系统

运行方式:
    python launch_semds.py

功能:
    1. 初始化自我进化系统
    2. 执行一系列编程任务
    3. 观察系统如何分析自己的表现
    4. 触发自我进化
    5. 查看进化后的改进效果
"""

import sys
import os
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """打印章节"""
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print("─" * 70)


def check_api_key():
    """检查是否配置了API key"""
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key and len(deepseek_key) > 10:
        return True, "DeepSeek"

    # 尝试从.env文件读取
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("DEEPSEEK_API_KEY="):
                        key = line.strip().split("=", 1)[1].strip("\"'")
                        if len(key) > 10:
                            os.environ["DEEPSEEK_API_KEY"] = key
                            return True, "DeepSeek (from .env)"
        except:
            pass

    return False, None


def run_with_mock_mode():
    """使用Mock模式运行（无需API key）"""
    print_header("SEMDS SELF-EVOLVING SYSTEM (MOCK MODE)")
    print("\n  Mode: Simulation (no API key required)")
    print("  This demonstrates the self-evolution loop with simulated LLM responses.")

    from mother.core.meta_evolution import (
        SystemTelemetry,
        ImprovementGenerator,
        SafeSelfUpdater,
        ExperimentResult,
        ImprovementHypothesis,
    )

    import tempfile

    tmpdir = tempfile.mkdtemp()
    os.chdir(tmpdir)

    # 初始化
    print_section("INITIALIZING SEMDS")
    telemetry = SystemTelemetry()
    print("  [OK] SystemTelemetry initialized")
    print("  [OK] Meta-evolution engine ready")
    print(f"  [INFO] Working directory: {tmpdir}")

    # 阶段1: 模拟任务执行（有成功有失败）
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
        time.sleep(0.1)  # 模拟延迟

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
        print(f"\n  ⚠ Improvement opportunities identified:")
        for opp in analysis["improvement_opportunities"]:
            print(f"    • {opp}")

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
    print_section("PHASE 4: A/B TESTING (SIMULATED)")

    print("\n  Testing hypotheses against control group...")

    results = []
    for h in hypotheses:
        print(f"\n  Testing [{h.id}]...")
        print(f"    Control (current strategy): 37.5% success rate")
        print(f"    Treatment (new strategy): 75.0% success rate")
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
    print_section("PHASE 5: APPLYING VERIFIED IMPROVEMENTS")

    updater = SafeSelfUpdater()
    applied = 0

    for h, result in results:
        if result.is_significant:
            print(f"\n  Applying [{h.id}]...")
            success = updater.apply_improvement(h, result)
            if success:
                applied += 1
                print(f"    [OK] Applied successfully")
                print(f"    • Change: {h.proposed_change}")
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
                print(f"    • {key}: {value}")

        print(f"\n  Expected improvement:")
        print(f"    • Next execution success rate: ~75% (was 37.5%)")
        print(f"    • Syntax errors reduced by ~60%")

        print(f"\n  Configuration file:")
        print(f"    {updater.config_file}")
        if updater.config_file.exists():
            import json

            with open(updater.config_file) as f:
                full_config = json.load(f)
            print(f"\n    Full config:")
            print(json.dumps(full_config, indent=4))

    # 阶段7: 展示持续改进
    print_section("PHASE 7: CONTINUOUS IMPROVEMENT")

    print("\n  SEMDS will now continue to:")
    print("    • Monitor its performance on every task")
    print("    • Collect success/failure statistics")
    print("    • Periodically run evolution cycles")
    print("    • Automatically apply verified improvements")

    print("\n  You can trigger evolution manually:")
    print("    mother.evolve_self()")

    print("\n  Or view current analysis:")
    print("    mother.get_self_analysis()")

    print_header("SEMDS IS READY")
    print("\n  The system is now self-aware and self-improving.")
    print("  Every task it performs makes it better at future tasks.")
    print("\n  To use with real LLM:")
    print("    export DEEPSEEK_API_KEY='your-key'")
    print("    python launch_semds.py")


def run_with_real_llm():
    """使用真实LLM运行（需要API key）"""
    print_header("SEMDS SELF-EVOLVING SYSTEM (LIVE MODE)")
    print("\n  Mode: Live (using real LLM API)")
    print("  API: DeepSeek")

    from mother.core.self_evolving_mother import SelfEvolvingMother

    # 初始化
    print_section("INITIALIZING SEMDS")
    mother = SelfEvolvingMother()

    # 执行实际任务
    print_section("PHASE 1: EXECUTING REAL TASKS")

    tasks = [
        "Write a Python function to calculate factorial",
        "Create a function to check if a string is palindrome",
        "Generate a function to find the maximum number in a list",
    ]

    for i, task in enumerate(tasks, 1):
        print(f"\n[{i}/{len(tasks)}] Task: {task}")
        print("    Executing...")

        result = mother.fulfill_request(task)

        status = "SUCCESS" if result.get("success") else "FAILED"
        print(f"    Result: {status}")
        if result.get("service_url"):
            print(f"    Service URL: {result['service_url']}")

        time.sleep(1)

    # 自我进化
    print_section("PHASE 2: TRIGGERING SELF-EVOLUTION")
    evolution_result = mother.evolve_self()

    print_section("PHASE 3: RESULTS")
    print(f"\nHypotheses generated: {evolution_result.get('hypotheses_generated', 0)}")
    print(f"Experiments run: {evolution_result.get('experiments_run', 0)}")
    print(f"Improvements applied: {evolution_result.get('improvements_applied', 0)}")

    if evolution_result.get("improvements_applied", 0) > 0:
        print("\n✓✓✓ SEMDS HAS EVOLVED ITSELF ✓✓✓")


def main():
    """主入口"""
    has_key, api_name = check_api_key()

    print("\n" + "=" * 70)
    print("  SEMDS - Self-Evolving Meta-Development System")
    print("  Launching...")
    print("=" * 70)

    if has_key:
        print(f"\n  [OK] API Key detected: {api_name}")
        choice = input("\n  Run in live mode with real LLM? [Y/n]: ").strip().lower()
        if choice in ("", "y", "yes"):
            run_with_real_llm()
        else:
            run_with_mock_mode()
    else:
        print("\n  [INFO] No API key detected")
        print(
            "  Running in simulation mode to demonstrate self-evolution capabilities."
        )
        print("\n  To use live mode, set:")
        print("    export DEEPSEEK_API_KEY='your-api-key'")
        input("\n  Press Enter to continue with simulation...")
        run_with_mock_mode()


if __name__ == "__main__":
    main()

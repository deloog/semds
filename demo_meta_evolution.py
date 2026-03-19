"""
SEMDS 核心自我进化演示

这个演示展示SEMDS最重要的能力：自我改进。
不需要API key，展示核心逻辑。
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mother.core.meta_evolution import (
    SystemTelemetry,
    ImprovementGenerator,
    SafeSelfUpdater,
    ImprovementHypothesis,
)


def main():
    print("="*70)
    print("SEMDS Core: Meta-Evolution Demonstration")
    print("="*70)
    print()
    print("This demonstrates SEMDS's self-improvement capability:")
    print("1. Observe its own performance")
    print("2. Identify improvement opportunities")
    print("3. Generate hypotheses")
    print("4. Apply verified improvements")
    print("5. Update its own configuration")
    print()
    print("-"*70)
    
    # 使用临时目录存储数据
    import tempfile
    tmpdir = tempfile.mkdtemp()
    print(f"\n[Setup] Using temp directory: {tmpdir}")
    os.chdir(tmpdir)
    
    # 初始化遥测系统
    telemetry = SystemTelemetry()
    print("[OK] SystemTelemetry initialized")
    
    # 场景1：系统发现自己代码生成成功率低
    print("\n[Scenario] SEMDS observes its code generation performance")
    print("           Over the last 24 hours:")
    
    # 模拟失败数据（语法错误频繁）
    print("  - 5 syntax errors (62%)")
    print("  - 2 test failures (25%)")
    print("  - 1 success (13%)")
    print("  Overall success rate: 13% (BELOW TARGET)")
    
    # 记录这些数据
    for i in range(5):
        telemetry.record_code_generation(
            task_type="function_implementation",
            success=False,
            score=0.0,
            generation_time=2.5,
            error_type="syntax_error"
        )
    
    for i in range(2):
        telemetry.record_code_generation(
            task_type="function_implementation",
            success=False,
            score=0.3,
            generation_time=3.0,
            error_type="test_failure"
        )
    
    telemetry.record_code_generation(
        task_type="function_implementation",
        success=True,
        score=1.0,
        generation_time=2.8
    )
    
    print("\n[OK] Performance data recorded")
    print("-"*70)
    
    # 分析性能
    print("\n[Step 1/5] Analyzing system performance...")
    analysis = telemetry.analyze_recent_performance(hours=24)
    
    print(f"  Success rate: {analysis.get('success_rate', 0):.1%}")
    print(f"  Total generations: {analysis.get('total_generations', 0)}")
    print(f"  Error patterns: {analysis.get('error_patterns', {})}")
    print(f"  Opportunities: {analysis.get('improvement_opportunities', [])}")
    
    if analysis.get('improvement_opportunities'):
        print(f"\n  [ALERT] Improvement opportunities identified!")
        for opp in analysis['improvement_opportunities']:
            print(f"    - {opp}")
    
    print("-"*70)
    
    # 生成改进假设
    print("\n[Step 2/5] Generating improvement hypotheses...")
    generator = ImprovementGenerator(telemetry)
    hypotheses = generator.generate_hypotheses()
    
    print(f"  Generated {len(hypotheses)} hypotheses")
    
    for i, h in enumerate(hypotheses, 1):
        print(f"\n  [{i}] {h.id}: {h.description}")
        print(f"      Target: {h.target_component}")
        print(f"      Expected improvement: +{h.expected_improvement:.0%}")
        print(f"      Proposed change: {h.proposed_change}")
    
    if not hypotheses:
        print("  No hypotheses generated (system performance acceptable)")
        return
    
    print("-"*70)
    
    # 模拟实验验证（简化版，不实际调用LLM）
    print("\n[Step 3/5] Running A/B experiments (simulated)...")
    
    from mother.core.meta_evolution import ExperimentResult
    
    results = []
    for h in hypotheses:
        print(f"\n  Testing [{h.id}]...")
        print(f"    Control (current): 0.30 success rate")
        print(f"    Treatment (new): 0.75 success rate")
        print(f"    Improvement: +150%")
        print(f"    Significant: YES (p < 0.05)")
        
        # 创建模拟实验结果
        result = ExperimentResult(
            hypothesis_id=h.id,
            control_group_score=0.30,
            treatment_group_score=0.75,
            sample_size=10,
            p_value=0.01,
            is_significant=True
        )
        results.append((h, result))
    
    print("-"*70)
    
    # 应用改进
    print("\n[Step 4/5] Applying verified improvements...")
    updater = SafeSelfUpdater()
    
    applied = 0
    for h, result in results:
        if result.is_significant:
            success = updater.apply_improvement(h, result)
            if success:
                applied += 1
                print(f"  [OK] Applied {h.id}: {h.description}")
            else:
                print(f"  [FAIL] Could not apply {h.id}")
    
    print("-"*70)
    
    # 验证配置更新
    print("\n[Step 5/5] Verifying configuration update...")
    config = updater.get_current_config("code_generator")
    
    if config:
        print("  Configuration successfully updated:")
        for key, value in config.items():
            if key not in ['last_updated', 'improvement_id']:
                print(f"    - {key}: {value}")
        print(f"    - Updated at: {config.get('last_updated')}")
        print(f"    - Improvement ID: {config.get('improvement_id')}")
    else:
        print("  No configuration changes")
    
    # 总结
    print("\n" + "="*70)
    print("EVOLUTION RESULTS")
    print("="*70)
    print(f"\nHypotheses generated: {len(hypotheses)}")
    print(f"Experiments conducted: {len(results)}")
    print(f"Improvements applied: {applied}")
    
    if applied > 0:
        print(f"\nSUCCESS: SEMDS has evolved itself!")
        print(f"  The system identified weaknesses in its code generation")
        print(f"  strategy, tested improvements, and updated its configuration.")
        print(f"\n  Next time SEMDS generates code, it will use the improved")
        print(f"  strategy with higher expected success rate.")
        
        print(f"\n  Configuration saved to: {updater.config_file}")
        if updater.config_file.exists():
            import json
            with open(updater.config_file) as f:
                full_config = json.load(f)
            print(f"  Full config: {json.dumps(full_config, indent=2)}")
    else:
        print(f"\nNo improvements applied this cycle.")
    
    print("\n" + "="*70)
    print("This is the core of SEMDS: Continuous self-improvement")
    print("="*70)


if __name__ == "__main__":
    main()

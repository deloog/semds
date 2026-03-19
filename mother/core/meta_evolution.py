"""
SEMDS Meta-Evolution Engine - 自我进化引擎

这是SEMDS的核心：系统能够观察自己的行为，发现问题，
提出改进假设，进行实验验证，并安全地更新自身代码。

核心循环（每24小时或触发条件满足时运行）：
1. 观察：收集系统运行数据（成功率、错误模式、性能指标）
2. 分析：识别低效环节和改进机会
3. 假设：生成具体的改进假设（如"添加X约束可提升Y%成功率"）
4. 实验：A/B测试对比新旧策略
5. 验证：统计显著性检验
6. 更新：如果验证通过，安全地更新系统代码
7. 监控：观察更新后的效果，必要时回滚
"""

import json
import os
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evolution.code_generator import CodeGenerator
from evolution.dual_evaluator import DualEvaluator
from evolution.test_runner import TestRunner


@dataclass
class SystemObservation:
    """系统运行观察数据"""
    timestamp: datetime
    metric_name: str
    metric_value: float
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ImprovementHypothesis:
    """改进假设"""
    id: str
    description: str
    target_component: str  # 如 "code_generator", "task_analyzer"
    proposed_change: Dict[str, Any]  # 具体的配置/代码变更
    expected_improvement: float  # 预期提升百分比
    test_scenarios: List[str]  # 用于验证的测试场景
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExperimentResult:
    """实验结果"""
    hypothesis_id: str
    control_group_score: float  # 对照组（当前系统）
    treatment_group_score: float  # 实验组（改进后）
    sample_size: int
    p_value: float  # 统计显著性
    is_significant: bool  # p < 0.05?
    raw_data: List[Dict] = field(default_factory=list)


class SystemTelemetry:
    """
    系统遥测：收集和分析系统运行数据
    
    记录每一次代码生成、任务执行的结果，
    用于发现模式和改进机会。
    """
    
    def __init__(self, storage_dir: str = "storage/meta_evolution"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.observations_file = self.storage_dir / "observations.jsonl"
        self.daily_stats_file = self.storage_dir / "daily_stats.json"
    
    def record(self, metric_name: str, metric_value: float, context: Dict = None):
        """记录一个观察数据点"""
        observation = SystemObservation(
            timestamp=datetime.now(),
            metric_name=metric_name,
            metric_value=metric_value,
            context=context or {}
        )
        
        # 追加写入JSONL
        with open(self.observations_file, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "timestamp": observation.timestamp.isoformat(),
                "metric_name": observation.metric_name,
                "metric_value": observation.metric_value,
                "context": observation.context
            }) + "\n")
    
    def record_code_generation(
        self,
        task_type: str,
        success: bool,
        score: float,
        generation_time: float,
        error_type: Optional[str] = None
    ):
        """记录代码生成事件"""
        self.record(
            metric_name="code_generation",
            metric_value=1.0 if success else 0.0,
            context={
                "task_type": task_type,
                "score": score,
                "generation_time": generation_time,
                "error_type": error_type,
                "success": success
            }
        )
    
    def analyze_recent_performance(self, hours: int = 24) -> Dict:
        """分析最近N小时的性能数据"""
        if not self.observations_file.exists():
            return {"error": "No data available"}
        
        cutoff_time = time.time() - (hours * 3600)
        
        # 读取最近的观察数据
        observations = []
        with open(self.observations_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obs = json.loads(line.strip())
                    obs_time = datetime.fromisoformat(obs["timestamp"]).timestamp()
                    if obs_time >= cutoff_time:
                        observations.append(obs)
                except:
                    continue
        
        if not observations:
            return {"error": f"No data in last {hours} hours"}
        
        # 计算关键指标
        code_gen_obs = [o for o in observations if o["metric_name"] == "code_generation"]
        
        if not code_gen_obs:
            return {"error": "No code generation data"}
        
        success_rate = sum(o["metric_value"] for o in code_gen_obs) / len(code_gen_obs)
        avg_score = sum(o["context"].get("score", 0) for o in code_gen_obs) / len(code_gen_obs)
        
        # 错误模式分析
        error_counts = {}
        for o in code_gen_obs:
            if not o["context"].get("success"):
                error_type = o["context"].get("error_type", "unknown")
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "period_hours": hours,
            "total_generations": len(code_gen_obs),
            "success_rate": success_rate,
            "average_score": avg_score,
            "error_patterns": error_counts,
            "improvement_opportunities": self._identify_improvements(error_counts, success_rate)
        }
    
    def _identify_improvements(self, error_counts: Dict, success_rate: float) -> List[str]:
        """基于错误模式识别改进机会"""
        opportunities = []
        
        if success_rate < 0.8:
            opportunities.append("success_rate_below_target")
        
        if error_counts.get("syntax_error", 0) > 2:
            opportunities.append("high_syntax_error_rate")
        
        if error_counts.get("test_failure", 0) > 3:
            opportunities.append("frequent_test_failures")
        
        return opportunities


class ImprovementGenerator:
    """
    改进假设生成器
    
    基于系统遥测数据，生成具体的改进假设。
    每个假设都必须可测试、可验证。
    """
    
    def __init__(self, telemetry: SystemTelemetry):
        self.telemetry = telemetry
    
    def generate_hypotheses(self) -> List[ImprovementHypothesis]:
        """基于当前性能数据生成改进假设"""
        analysis = self.telemetry.analyze_recent_performance(hours=24)
        
        if "error" in analysis:
            return []
        
        hypotheses = []
        
        # 假设1: 如果语法错误多，增加语法约束提示
        if "high_syntax_error_rate" in analysis.get("improvement_opportunities", []):
            h = ImprovementHypothesis(
                id=str(uuid.uuid4())[:8],
                description="Add explicit syntax validation constraint to code generation prompt",
                target_component="code_generator",
                proposed_change={
                    "constraint_type": "syntax_validation",
                    "prompt_addition": "Before returning code, validate that it passes Python syntax check (ast.parse). If not, fix it."
                },
                expected_improvement=0.15,  # 预期提升15%
                test_scenarios=["calculator", "fibonacci", "string_processor"]
            )
            hypotheses.append(h)
        
        # 假设2: 如果测试失败多，增加测试驱动提示
        if "frequent_test_failures" in analysis.get("improvement_opportunities", []):
            h = ImprovementHypothesis(
                id=str(uuid.uuid4())[:8],
                description="Add test-case-first generation strategy",
                target_component="code_generator",
                proposed_change={
                    "strategy": "test_first",
                    "prompt_addition": "Generate code by first understanding what each test expects, then implement to satisfy all tests."
                },
                expected_improvement=0.20,
                test_scenarios=["edge_case_handler", "type_converter"]
            )
            hypotheses.append(h)
        
        # 假设3: 如果整体成功率低，降低温度参数
        if analysis.get("success_rate", 1.0) < 0.7:
            h = ImprovementHypothesis(
                id=str(uuid.uuid4())[:8],
                description="Reduce temperature for more deterministic generation",
                target_component="code_generator",
                proposed_change={
                    "temperature": 0.1,  # 从默认0.7降低
                    "reasoning": "Lower temperature reduces creativity errors"
                },
                expected_improvement=0.10,
                test_scenarios=["all_standard_tasks"]
            )
            hypotheses.append(h)
        
        return hypotheses


class SelfExperiment:
    """
    自我实验框架
    
    对改进假设进行受控实验，使用统计方法验证效果。
    """
    
    def __init__(self, telemetry: SystemTelemetry):
        self.telemetry = telemetry
        self.test_runner = TestRunner()
        self.code_generator = CodeGenerator()
    
    def run_ab_test(
        self,
        hypothesis: ImprovementHypothesis,
        n_samples: int = 10
    ) -> ExperimentResult:
        """
        运行A/B测试验证假设
        
        Args:
            hypothesis: 要验证的改进假设
            n_samples: 每个组的样本数
            
        Returns:
            实验结果，包含统计显著性
        """
        print(f"[SelfExperiment] Testing hypothesis: {hypothesis.description}")
        print(f"[SelfExperiment] Running {n_samples} samples per group...")
        
        control_scores = []
        treatment_scores = []
        
        # 测试场景
        test_cases = [
            ("def add(a, b):", "assert add(1, 2) == 3"),
            ("def factorial(n):", "assert factorial(5) == 120"),
            ("def is_palindrome(s):", "assert is_palindrome('racecar')"),
        ]
        
        for i in range(n_samples):
            # 随机选择测试用例
            test_case = test_cases[i % len(test_cases)]
            
            # 对照组（当前系统）
            control_code = self._generate_with_config(test_case[0], {})
            control_result = self._evaluate_code(control_code, test_case[1])
            control_scores.append(control_result["score"])
            
            # 实验组（改进后）
            treatment_code = self._generate_with_config(
                test_case[0],
                hypothesis.proposed_change
            )
            treatment_result = self._evaluate_code(treatment_code, test_case[1])
            treatment_scores.append(treatment_result["score"])
        
        # 计算统计显著性（简化版t-test）
        import statistics
        
        control_mean = statistics.mean(control_scores)
        treatment_mean = statistics.mean(treatment_scores)
        
        # 简化p值计算（实际应使用scipy）
        # 这里用简单的均值差异判断
        improvement = treatment_mean - control_mean
        is_significant = improvement > 0.1  # 提升超过10%认为显著
        
        return ExperimentResult(
            hypothesis_id=hypothesis.id,
            control_group_score=control_mean,
            treatment_group_score=treatment_mean,
            sample_size=n_samples,
            p_value=0.01 if is_significant else 0.5,  # 简化
            is_significant=is_significant,
            raw_data=[
                {"group": "control", "scores": control_scores},
                {"group": "treatment", "scores": treatment_scores}
            ]
        )
    
    def _generate_with_config(self, signature: str, config: Dict) -> str:
        """使用特定配置生成代码"""
        # 这里简化实现，实际应调用CodeGenerator并传入config
        prompt = f"Write a Python function: {signature}\n"
        if config.get("prompt_addition"):
            prompt += f"\nAdditional constraint: {config['prompt_addition']}"
        
        # 使用当前generator生成
        return self.code_generator.generate(prompt, config)
    
    def _evaluate_code(self, code: str, test_code: str) -> Dict:
        """评估代码质量"""
        # 运行测试
        result = self.test_runner.run(code, test_code)
        
        return {
            "score": result.pass_rate if result.success else 0.0,
            "success": result.success,
            "execution_time": result.execution_time
        }


class SafeSelfUpdater:
    """
    安全的自我更新器
    
    使用Layer 0的安全机制，确保系统自我更新不会破坏自身。
    """
    
    def __init__(self, backup_dir: str = "storage/meta_evolution/backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = Path("storage/meta_evolution/system_config.json")
    
    def apply_improvement(
        self,
        hypothesis: ImprovementHypothesis,
        experiment_result: ExperimentResult
    ) -> bool:
        """
        安全地应用验证通过的改进
        
        Returns:
            是否成功应用
        """
        if not experiment_result.is_significant:
            print(f"[SafeSelfUpdater] Rejecting {hypothesis.id}: not significant")
            return False
        
        print(f"[SafeSelfUpdater] Applying improvement: {hypothesis.description}")
        
        # 1. 备份当前配置
        self._backup_current_config()
        
        # 2. 应用变更
        try:
            self._apply_config_change(hypothesis)
            print(f"[SafeSelfUpdater] Applied successfully")
            return True
        except Exception as e:
            print(f"[SafeSelfUpdater] Failed to apply: {e}")
            self._rollback()
            return False
    
    def _backup_current_config(self):
        """备份当前配置"""
        if self.config_file.exists():
            backup_path = self.backup_dir / f"config_{int(time.time())}.json"
            import shutil
            shutil.copy(self.config_file, backup_path)
            print(f"[SafeSelfUpdater] Backed up to {backup_path}")
    
    def _apply_config_change(self, hypothesis: ImprovementHypothesis):
        """应用配置变更"""
        # 读取当前配置
        config = {}
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        
        # 应用变更
        target = hypothesis.target_component
        if target not in config:
            config[target] = {}
        
        config[target].update(hypothesis.proposed_change)
        config[target]["last_updated"] = datetime.now().isoformat()
        config[target]["improvement_id"] = hypothesis.id
        
        # 写入新配置
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    
    def _rollback(self):
        """回滚到上一个配置"""
        backups = sorted(self.backup_dir.glob("config_*.json"))
        if backups:
            latest_backup = backups[-1]
            import shutil
            shutil.copy(latest_backup, self.config_file)
            print(f"[SafeSelfUpdater] Rolled back to {latest_backup}")
    
    def get_current_config(self, component: str) -> Dict:
        """获取组件当前配置"""
        if not self.config_file.exists():
            return {}
        
        with open(self.config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        return config.get(component, {})


class MetaEvolutionEngine:
    """
    元进化引擎 - SEMDS自我进化的核心
    
    这是系统的"免疫系统"，持续监控、诊断、改进自身。
    """
    
    def __init__(self):
        self.telemetry = SystemTelemetry()
        self.improvement_generator = ImprovementGenerator(self.telemetry)
        self.experiment = SelfExperiment(self.telemetry)
        self.updater = SafeSelfUpdater()
        
        print("[MetaEvolution] Engine initialized")
        print("[MetaEvolution] Ready to evolve myself")
    
    def run_evolution_cycle(self) -> Dict:
        """
        运行一次完整的自我进化循环
        
        这是核心方法，实现了完整的自我进化闭环。
        """
        print("\n" + "="*60)
        print("[MetaEvolution] Starting self-evolution cycle")
        print("="*60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "observations": None,
            "hypotheses_generated": 0,
            "experiments_run": 0,
            "improvements_applied": 0,
            "details": []
        }
        
        # Step 1: 观察
        print("\n[Step 1/5] Observing system performance...")
        analysis = self.telemetry.analyze_recent_performance(hours=24)
        results["observations"] = analysis
        
        if "error" in analysis:
            print(f"[MetaEvolution] Cannot proceed: {analysis['error']}")
            return results
        
        print(f"  Success rate: {analysis.get('success_rate', 0):.2%}")
        print(f"  Opportunities: {analysis.get('improvement_opportunities', [])}")
        
        # Step 2: 生成假设
        print("\n[Step 2/5] Generating improvement hypotheses...")
        hypotheses = self.improvement_generator.generate_hypotheses()
        results["hypotheses_generated"] = len(hypotheses)
        
        if not hypotheses:
            print("[MetaEvolution] No improvement opportunities identified")
            return results
        
        for h in hypotheses:
            print(f"  - [{h.id}] {h.description}")
            print(f"    Expected improvement: +{h.expected_improvement:.0%}")
        
        # Step 3: 实验验证
        print("\n[Step 3/5] Running experiments...")
        for hypothesis in hypotheses:
            print(f"\n  Testing [{hypothesis.id}]...")
            
            experiment_result = self.experiment.run_ab_test(hypothesis, n_samples=5)
            results["experiments_run"] += 1
            
            print(f"    Control: {experiment_result.control_group_score:.2f}")
            print(f"    Treatment: {experiment_result.treatment_group_score:.2f}")
            print(f"    Significant: {'YES' if experiment_result.is_significant else 'NO'}")
            
            results["details"].append({
                "hypothesis": hypothesis,
                "experiment": experiment_result
            })
            
            # Step 4: 应用改进（如果显著）
            if experiment_result.is_significant:
                print("\n[Step 4/5] Applying verified improvement...")
                success = self.updater.apply_improvement(hypothesis, experiment_result)
                
                if success:
                    results["improvements_applied"] += 1
                    print(f"  [OK] Applied {hypothesis.id}")
                else:
                    print(f"  [FAIL] Could not apply {hypothesis.id}")
        
        # Step 5: 总结
        print("\n[Step 5/5] Cycle complete")
        print(f"  Hypotheses: {results['hypotheses_generated']}")
        print(f"  Experiments: {results['experiments_run']}")
        print(f"  Applied: {results['improvements_applied']}")
        
        return results
    
    def record_generation_result(
        self,
        task_type: str,
        success: bool,
        score: float,
        generation_time: float,
        error_type: Optional[str] = None
    ):
        """供其他模块调用，记录代码生成结果"""
        self.telemetry.record_code_generation(
            task_type=task_type,
            success=success,
            score=score,
            generation_time=generation_time,
            error_type=error_type
        )


def demo_meta_evolution():
    """
    演示SEMDS自我进化能力
    """
    print("="*70)
    print("SEMDS Meta-Evolution Demo")
    print("Demonstrating: Self-observation → Self-improvement")
    print("="*70)
    
    # 创建引擎
    engine = MetaEvolutionEngine()
    
    # 模拟一些历史数据（模拟系统运行了一段时间）
    print("\n[Setup] Simulating historical performance data...")
    
    # 模拟失败记录（让系统发现改进机会）
    for i in range(5):
        engine.record_generation_result(
            task_type="calculator",
            success=False,
            score=0.0,
            generation_time=2.0,
            error_type="syntax_error"
        )
    
    for i in range(3):
        engine.record_generation_result(
            task_type="calculator",
            success=True,
            score=0.8,
            generation_time=3.0
        )
    
    print("  Recorded 5 failures, 3 successes")
    print(f"  Current success rate: ~37% (needs improvement)")
    
    # 运行自我进化循环
    result = engine.run_evolution_cycle()
    
    # 显示结果
    print("\n" + "="*70)
    print("Evolution Cycle Results")
    print("="*70)
    print(f"Timestamp: {result['timestamp']}")
    print(f"Hypotheses generated: {result['hypotheses_generated']}")
    print(f"Experiments run: {result['experiments_run']}")
    print(f"Improvements applied: {result['improvements_applied']}")
    
    if result['improvements_applied'] > 0:
        print("\n✅ SEMDS has successfully evolved itself!")
        print("   New configuration saved.")
        print("   Next code generation will use improved strategy.")
    else:
        print("\nℹ️ No improvements applied this cycle.")
        print("   Either no opportunities found or experiments not significant.")
    
    return result


if __name__ == "__main__":
    demo_meta_evolution()

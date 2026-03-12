# SEMDS Phase 3 TDD 原子化实施路线图

**版本**: v1.0-TDD  
**日期**: 2026-03-11  
**目标**: 实现完整进化循环（遵循TDD严格模式）  
**验收标准**: 跑通计算器实验 ≥10 代进化

---

## 📋 TDD 开发原则

```
每个任务必须遵循：
┌─────────────────────────────────────────────────────────┐
│ 1. 写测试文件（Red）→ 2. 实现代码（Green）→ 3. 重构（Refactor）│
└─────────────────────────────────────────────────────────┘

禁止：
❌ 先写实现后补测试
❌ 测试覆盖率 < 100%（新代码）
❌ 提交前不运行完整检查
❌ 测试不通过时禁止修改测试文件，确须修改，应请示并给出诚实且充分理由。
```

---

## 🎯 任务总览（原子化分解）

### 任务清单

| ID | 任务名称 | 类型 | 估算 | 依赖 | 状态 |
|----|----------|------|------|------|------|
| **P3-TEST-01** | Thompson Sampling 策略臂测试 | 测试 | 2h | - | ✅ |
| **P3-IMPL-01** | StrategyArm 实现 | 实现 | 2h | P3-TEST-01 | ✅ |
| **P3-TEST-02** | 策略优化器测试 | 测试 | 2h | P3-IMPL-01 | ✅ |
| **P3-IMPL-02** | StrategyOptimizer 实现 | 实现 | 3h | P3-TEST-02 | ✅ |
| **P3-TEST-03** | 内生评估测试 | 测试 | 2h | - | ✅ |
| **P3-IMPL-03** | IntrinsicEvaluator 实现 | 实现 | 2h | P3-TEST-03 | ✅ |
| **P3-TEST-04** | 外生评估测试 | 测试 | 3h | - | ✅ |
| **P3-IMPL-04** | ExtrinsicEvaluator 实现 | 实现 | 3h | P3-TEST-04 | ✅ |
| **P3-TEST-05** | Goodhart检测测试 | 测试 | 2h | - | ✅ |
| **P3-IMPL-05** | GoodhartDetector 实现 | 实现 | 2h | P3-TEST-05 | ✅ |
| **P3-TEST-06** | 双轨评估器集成测试 | 测试 | 2h | P3-IMPL-03~05 | ✅ |
| **P3-IMPL-06** | DualEvaluator 集成实现 | 实现 | 2h | P3-TEST-06 | ✅ |
| **P3-TEST-07** | 终止条件测试 | 测试 | 2h | - | ✅ |
| **P3-IMPL-07** | TerminationChecker 实现 | 实现 | 2h | P3-TEST-07 | ✅ |
| **P3-TEST-08** | Git管理测试 | 测试 | 2h | - | ✅ |
| **P3-IMPL-08** | GitManager 实现 | 实现 | 2h | P3-TEST-08 | ✅ |
| **P3-TEST-09** | 技能库测试 | 测试 | 2h | - | ✅ |
| **P3-IMPL-09** | Skills Library 实现 | 实现 | 2h | P3-TEST-09 | ✅ |
| **P3-TEST-10** | Orchestrator集成测试 | 测试 | 3h | P3-IMPL-01~09 | ⬜ |
| **P3-IMPL-10** | EvolutionOrchestrator 实现 | 实现 | 4h | P3-TEST-10 | ⬜ |
| **P3-TEST-11** | 端到端进化测试 | 测试 | 2h | P3-IMPL-10 | ⬜ |
| **P3-DEMO** | 计算器实验运行 | 演示 | 2h | P3-TEST-11 | ⬜ |

**总估算**: 46 小时（约 6 个工作日）

---

## 📝 详细任务规格

### P3-TEST-01: StrategyArm 测试

**文件**: `tests/evolution/test_strategy_optimizer.py`

**测试用例**:
```python
class TestStrategyArm:
    """StrategyArm单元测试 - TDD Red阶段"""
    
    def test_initial_alpha_beta(self):
        """测试初始alpha=1.0, beta=1.0"""
        arm = StrategyArm(key="test")
        assert arm.alpha == 1.0
        assert arm.beta == 1.0
    
    def test_sample_returns_float_between_0_and_1(self):
        """测试采样返回0-1之间的浮点数"""
        arm = StrategyArm(key="test")
        sample = arm.sample()
        assert isinstance(sample, float)
        assert 0.0 <= sample <= 1.0
    
    def test_update_increases_alpha_on_success(self):
        """测试成功时alpha增加"""
        arm = StrategyArm(key="test")
        arm.update(success=True)
        assert arm.alpha == 2.0
        assert arm.beta == 1.0
    
    def test_update_increases_beta_on_failure(self):
        """测试失败时beta增加"""
        arm = StrategyArm(key="test")
        arm.update(success=False)
        assert arm.alpha == 1.0
        assert arm.beta == 2.0
    
    def test_expected_value_calculation(self):
        """测试期望值计算"""
        arm = StrategyArm(key="test", alpha=3.0, beta=1.0)
        assert arm.expected_value() == 0.75  # 3/(3+1)
```

**验收标准**:
- [ ] 所有测试先写并失败（Red）
- [ ] 实现后所有测试通过（Green）
- [ ] 覆盖率 100%

---

### P3-IMPL-01: StrategyArm 实现

**文件**: `evolution/strategy_optimizer.py`

**类规格**:
```python
@dataclass
class StrategyArm:
    """
    Thompson Sampling策略臂
    
    使用Beta分布进行采样
    """
    key: str
    alpha: float = 1.0
    beta: float = 1.0
    total_uses: int = 0
    
    def sample(self) -> float:
        """从Beta分布采样"""
        pass  # TODO: 实现
    
    def update(self, success: bool) -> None:
        """更新策略性能"""
        pass  # TODO: 实现
    
    def expected_value(self) -> float:
        """期望性能 = alpha/(alpha+beta)"""
        pass  # TODO: 实现
```

---

### P3-TEST-02: StrategyOptimizer 测试

**文件**: `tests/evolution/test_strategy_optimizer.py`

**测试用例**:
```python
class TestStrategyOptimizer:
    """策略优化器测试"""
    
    def test_initializes_all_strategy_combinations(self):
        """测试初始化所有策略组合"""
        optimizer = StrategyOptimizer(task_id="test")
        # 3(mutation) * 2(validation) * 3(temperature) = 18种组合
        assert len(optimizer.arms) == 18
    
    def test_select_strategy_returns_valid_strategy(self):
        """测试选择策略返回有效配置"""
        optimizer = StrategyOptimizer(task_id="test")
        strategy = optimizer.select_strategy()
        assert "mutation_type" in strategy
        assert "validation_mode" in strategy
        assert "generation_temperature" in strategy
    
    def test_report_result_updates_arm(self):
        """测试报告结果更新策略臂"""
        optimizer = StrategyOptimizer(task_id="test")
        strategy = optimizer.select_strategy()
        optimizer.report_result(strategy, success=True, score=0.8)
        
        key = optimizer._strategy_to_key(strategy)
        arm = optimizer.arms[key]
        assert arm.total_uses == 1
```

---

### P3-IMPL-02: StrategyOptimizer 实现

**文件**: `evolution/strategy_optimizer.py`

**类规格**:
```python
class StrategyOptimizer:
    """
    Thompson Sampling策略优化器
    
    职责:
    - 管理策略臂集合
    - 选择下一策略（采样）
    - 更新策略性能
    - 任务间策略隔离
    """
    
    STRATEGY_DIMENSIONS = {
        "mutation_type": ["conservative", "aggressive", "hybrid"],
        "validation_mode": ["lightweight", "comprehensive"],
        "generation_temperature": [0.2, 0.5, 0.8]
    }
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.arms: Dict[str, StrategyArm] = {}
        self._initialize_arms()
    
    def _initialize_arms(self) -> None:
        """初始化所有策略组合"""
        pass  # TODO: 实现
    
    def select_strategy(self) -> dict:
        """使用Thompson Sampling选择策略"""
        pass  # TODO: 实现
    
    def report_result(self, strategy: dict, success: bool, score: float) -> None:
        """报告策略执行结果"""
        pass  # TODO: 实现
    
    def _strategy_to_key(self, strategy: dict) -> str:
        """策略字典转字符串键"""
        pass  # TODO: 实现
```

---

### P3-TEST-03: IntrinsicEvaluator 测试

**文件**: `tests/evolution/test_dual_evaluator.py`

**测试用例**:
```python
class TestIntrinsicEvaluator:
    """内生评估测试"""
    
    def test_evaluate_returns_correct_pass_rate(self):
        """测试评估返回正确通过率"""
        evaluator = IntrinsicEvaluator()
        test_report = TestRunReport(
            pass_rate=0.8,
            results=[TestResult("test1", True), TestResult("test2", False)]
        )
        result = evaluator.evaluate(test_report)
        assert result["pass_rate"] == 0.8
    
    def test_empty_results_returns_zero(self):
        """测试空结果返回0"""
        evaluator = IntrinsicEvaluator()
        test_report = TestRunReport(pass_rate=0.0, results=[])
        result = evaluator.evaluate(test_report)
        assert result["pass_rate"] == 0.0
```

---

### P3-IMPL-03: IntrinsicEvaluator 实现

**文件**: `evolution/dual_evaluator.py`

```python
class IntrinsicEvaluator:
    """内生评估器 - 基于测试通过率"""
    
    def evaluate(self, test_report: TestRunReport) -> dict:
        """
        评估测试通过率
        
        Returns:
            {
                "score": float,  # 同pass_rate
                "pass_rate": float,
                "test_results": Dict[str, bool],
                "execution_time_ms": float
            }
        """
        pass  # TODO: 实现
```

---

### P3-TEST-04: ExtrinsicEvaluator 测试

**文件**: `tests/evolution/test_dual_evaluator.py`

**测试用例**:
```python
class TestExtrinsicEvaluator:
    """外生评估测试"""
    
    def test_static_analysis_detects_dangerous_patterns(self):
        """测试静态分析检测危险模式"""
        evaluator = ExtrinsicEvaluator()
        code = "eval('1+1')"
        score = evaluator._static_analysis(code)
        assert score < 1.0  # 应该扣分
    
    def test_static_analysis_rewards_good_practices(self):
        """测试静态分析奖励良好实践"""
        evaluator = ExtrinsicEvaluator()
        code = '''
        def calculate(a, b):
            """Add two numbers."""
            try:
                return a + b
            except Exception:
                raise
        '''
        score = evaluator._static_analysis(code)
        assert score > 0.5
```

---

### P3-IMPL-04: ExtrinsicEvaluator 实现

**文件**: `evolution/dual_evaluator.py`

```python
class ExtrinsicEvaluator:
    """外生评估器 - 行为一致性验证"""
    
    def evaluate(
        self,
        code: str,
        function_signature: str,
        requirements: List[str]
    ) -> dict:
        """
        外生评估
        
        Returns:
            {
                "score": float,
                "consistency_score": float,
                "static_analysis_score": float,
                "edge_case_results": List[dict]
            }
        """
        pass  # TODO: 实现
    
    def _static_analysis(self, code: str) -> float:
        """静态代码分析"""
        pass  # TODO: 实现
    
    def _generate_edge_cases(self, signature: str) -> List[dict]:
        """生成边界用例"""
        pass  # TODO: 实现
```

---

### P3-TEST-05: GoodhartDetector 测试

**文件**: `tests/evolution/test_dual_evaluator.py`

**测试用例**:
```python
class TestGoodhartDetector:
    """Goodhart检测测试"""
    
    def test_detects_goodhart_when_high_pass_low_consistency(self):
        """测试高通过率+低一致性触发Goodhart"""
        detector = GoodhartDetector()
        flag, reason = detector.detect(
            pass_rate=0.95,
            consistency_score=0.3
        )
        assert flag is True
        assert "Goodhart" in reason
    
    def test_no_goodhart_when_both_high(self):
        """测试双高不触发Goodhart"""
        detector = GoodhartDetector()
        flag, reason = detector.detect(
            pass_rate=0.95,
            consistency_score=0.85
        )
        assert flag is False
```

---

### P3-IMPL-05: GoodhartDetector 实现

**文件**: `evolution/dual_evaluator.py`

```python
class GoodhartDetector:
    """Goodhart现象检测器"""
    
    # 阈值
    PASS_THRESHOLD = 0.9
    CONSISTENCY_THRESHOLD = 0.5
    
    def detect(self, pass_rate: float, consistency_score: float) -> tuple:
        """
        检测Goodhart现象
        
        Returns:
            (flag: bool, reason: Optional[str])
        """
        pass  # TODO: 实现
```

---

### P3-TEST-06: DualEvaluator 集成测试

**测试用例**:
```python
class TestDualEvaluatorIntegration:
    """双轨评估集成测试"""
    
    def test_full_evaluation_pipeline(self):
        """测试完整评估流程"""
        evaluator = DualEvaluator()
        # 集成测试代码...
```

---

### P3-IMPL-06: DualEvaluator 集成实现

**文件**: `evolution/dual_evaluator.py`

```python
@dataclass
class EvaluationReport:
    """评估报告"""
    intrinsic_score: float
    pass_rate: float
    extrinsic_score: float
    consistency_score: float
    final_score: float
    goodhart_flag: bool
    goodhart_reason: Optional[str]

class DualEvaluator:
    """双轨评估器"""
    
    WEIGHT_PASS = 0.6
    WEIGHT_CONSISTENCY = 0.2
    WEIGHT_LATENCY = 0.1
    WEIGHT_COMPLEXITY = 0.1
    
    def __init__(self):
        self.intrinsic = IntrinsicEvaluator()
        self.extrinsic = ExtrinsicEvaluator()
        self.goodhart = GoodhartDetector()
    
    def evaluate(self, code: str, test_report: TestRunReport) -> EvaluationReport:
        """完整双轨评估"""
        pass  # TODO: 实现
```

---

### P3-TEST-07: TerminationChecker 测试

**文件**: `tests/evolution/test_termination_checker.py`

**测试用例**:
```python
class TestTerminationChecker:
    """终止条件检查器测试"""
    
    def test_terminates_on_success_threshold(self):
        """测试达到成功阈值终止"""
        checker = TerminationChecker()
        decision = checker.check(current_gen=5, current_score=0.96)
        assert decision.should_terminate is True
        assert decision.is_success is True
    
    def test_terminates_on_max_generations(self):
        """测试达到最大代数终止"""
        checker = TerminationChecker(config=TerminationConfig(max_generations=10))
        decision = checker.check(current_gen=10, current_score=0.5)
        assert decision.should_terminate is True
        assert decision.is_success is False
    
    def test_detects_stagnation(self):
        """测试停滞检测"""
        checker = TerminationChecker(config=TerminationConfig(stagnation_generations=3))
        # 模拟3代无改进
        for _ in range(3):
            checker.check(current_gen=1, current_score=0.5)
        decision = checker.check(current_gen=4, current_score=0.5)
        assert decision.should_terminate is True
```

---

### P3-IMPL-07: TerminationChecker 实现

**文件**: `evolution/termination_checker.py`

```python
@dataclass
class TerminationConfig:
    success_threshold: float = 0.95
    max_generations: int = 50
    stagnation_generations: int = 10

@dataclass  
class TerminationDecision:
    should_terminate: bool
    reason: str
    is_success: bool

class TerminationChecker:
    """终止条件检查器"""
    
    def __init__(self, config: TerminationConfig = None):
        self.config = config or TerminationConfig()
        self.score_history = []
    
    def check(self, current_gen: int, current_score: float) -> TerminationDecision:
        """检查是否终止"""
        pass  # TODO: 实现
```

---

### P3-TEST-08: GitManager 测试

**文件**: `tests/core/test_version_control.py`

**测试用例**:
```python
class TestGitManager:
    """Git管理器测试"""
    
    def test_commit_generation_creates_commit(self, tmp_path):
        """测试提交一代创建commit"""
        # 初始化git仓库
        os.system(f"cd {tmp_path} && git init")
        
        manager = GitManager(str(tmp_path))
        hash = manager.commit_generation(
            task_id="test",
            gen_number=1,
            file_path="solution.py",
            score=0.85
        )
        assert len(hash) == 40  # SHA-1 hash
    
    def test_rollback_restores_file(self, tmp_path):
        """测试回滚恢复文件"""
        # 实现测试...
```

---

### P3-IMPL-08: GitManager 实现

**文件**: `core/version_control.py`

```python
class GitManager:
    """Git版本控制管理器"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
    
    def commit_generation(
        self,
        task_id: str,
        gen_number: int,
        file_path: str,
        score: float
    ) -> str:
        """提交一代代码"""
        pass  # TODO: 实现
    
    def rollback_to_generation(self, file_path: str, commit_hash: str) -> None:
        """回滚到指定代"""
        pass  # TODO: 实现
```

---

### P3-TEST-09: Skills Library 测试

**文件**: `tests/skills/test_template_manager.py`

**测试用例**:
```python
class TestTemplateManager:
    """模板管理器测试"""
    
    def test_render_prompt_with_context(self, tmp_path):
        """测试使用上下文渲染Prompt"""
        # 创建测试模板
        template_dir = tmp_path / "templates"
        template_dir.mkdir()
        (template_dir / "test.j2").write_text("Hello {{ name }}!")
        
        manager = TemplateManager(str(template_dir))
        result = manager.render_prompt("test", {"name": "World"})
        assert result == "Hello World!"
```

---

### P3-IMPL-09: Skills Library 实现

**文件**: `skills/template_manager.py`, `skills/strategy_registry.py`

```python
class TemplateManager:
    """模板管理器"""
    
    def __init__(self, templates_dir: str = "skills/templates"):
        pass  # TODO: 实现
    
    def render_prompt(self, template_name: str, context: dict) -> str:
        """渲染Prompt模板"""
        pass  # TODO: 实现

class StrategyRegistry:
    """策略注册表"""
    
    def add_verified_strategy(self, strategy: dict, task_type: str) -> None:
        """添加已验证策略"""
        pass  # TODO: 实现
```

---

### P3-TEST-10: Orchestrator 集成测试

**文件**: `tests/evolution/test_orchestrator.py`

**测试用例**:
```python
class TestEvolutionOrchestrator:
    """进化编排器集成测试"""
    
    def test_orchestrator_runs_single_generation(self):
        """测试编排器运行单代"""
        # 使用mock组件测试编排逻辑
        pass  # TODO: 实现
    
    def test_orchestrator_tracks_best_score(self):
        """测试编排器跟踪最佳得分"""
        pass  # TODO: 实现
```

---

### P3-IMPL-10: EvolutionOrchestrator 实现

**文件**: `evolution/orchestrator.py`

```python
class EvolutionOrchestrator:
    """
    进化编排器
    
    协调所有组件完成进化循环
    """
    
    def __init__(
        self,
        task: Task,
        code_generator: CodeGenerator,
        test_runner: TestRunner,
        dual_evaluator: DualEvaluator,
        strategy_optimizer: StrategyOptimizer,
        termination_checker: TerminationChecker,
        git_manager: GitManager
    ):
        pass  # TODO: 实现
    
    def run(self) -> EvolutionResult:
        """运行完整进化循环"""
        pass  # TODO: 实现
```

---

### P3-TEST-11: 端到端测试

**文件**: `tests/integration/test_evolution_end_to_end.py`

**测试用例**:
```python
class TestEndToEndEvolution:
    """端到端进化测试"""
    
    def test_calculator_evolution_converges(self):
        """测试计算器进化收敛"""
        # 使用mock LLM API
        # 验证多代后得分提升
        pass  # TODO: 实现
```

---

### P3-DEMO: 计算器实验

**文件**: `demo_phase3.py`

**目标**: 跑通计算器实验 ≥10 代进化

**验收标准**:
- [ ] 成功运行 ≥10 代
- [ ] 最终得分 ≥0.90
- [ ] 生成完整的进化报告
- [ ] 所有数据正确存入数据库

---

## ✅ 检查清单（实施前必读）

### 每个任务开始前
- [ ] 理解需求（阅读规格文档）
- [ ] 识别涉及的架构层
- [ ] 评估理解度 ≥70%

### 每个任务完成后
- [ ] 单元测试 100% 通过
- [ ] 新代码覆盖率 100%
- [ ] 类型检查通过（mypy）
- [ ] 代码格式检查通过（black, flake8）
- [ ] 静态检查通过（pylint ≥9.0）
- [ ] 文档字符串完整

### 提交前
```bash
make check-strict  # 运行完整检查
```

---

## 📊 进度追踪

| 日期 | 完成任务 | 进度 | 备注 |
|------|----------|------|------|
| 2026-03-11 | P3-TEST-01~P3-IMPL-03 | 27% | StrategyArm, StrategyOptimizer, IntrinsicEvaluator 完成 |
| 2026-03-11 | P3-TEST-04~P3-IMPL-05 | 45% | ExtrinsicEvaluator, GoodhartDetector 完成 |

**最后更新**: 2026-03-11

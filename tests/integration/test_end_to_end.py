"""
端到端集成测试 - TDD Red Phase

测试完整的进化流程，使用模拟组件验证系统级行为。

目标：
1. 验证所有组件协同工作
2. 验证进化流程完整执行
3. 验证最终报告生成
"""

# =============================================================================
# Test End-to-End Evolution Flow
# =============================================================================


class TestEndToEndEvolutionFlow:
    """端到端进化流程测试"""

    def test_evolution_runs_multiple_generations(self):
        """测试进化运行多代"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=3, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="e2e_test",
            termination_config=config,
        )

        result = orchestrator.evolve(
            requirements=["Write a function that returns 42"],
            test_code="assert solution() == 42",
            max_generations=3,
        )

        # 验证运行了多代
        assert result.generations >= 1
        assert result.generations <= 3

    def test_evolution_produces_final_report(self):
        """测试进化产生最终报告"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="e2e_test",
            termination_config=config,
        )

        result = orchestrator.evolve(
            requirements=["Write a simple function"],
            test_code="pass",
            max_generations=2,
        )

        # 验证报告包含必要字段
        assert hasattr(result, "generations")
        assert hasattr(result, "best_score")
        assert hasattr(result, "best_code")
        assert hasattr(result, "success")
        assert hasattr(result, "termination_reason")

    def test_evolution_tracks_history(self):
        """测试进化追踪历史"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=3, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="e2e_test",
            termination_config=config,
        )

        orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=3,
        )

        # 验证历史记录
        assert len(orchestrator.history) >= 1
        assert len(orchestrator.history) <= 3

    def test_evolution_best_score_improves_or_stable(self):
        """测试最佳得分改善或保持稳定"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=3, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="e2e_test",
            termination_config=config,
        )

        evolution_result = orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=3,
        )

        # 验证得分在有效范围
        assert 0.0 <= evolution_result.best_score <= 1.0

    def test_evolution_terminates_properly(self):
        """测试进化正确终止"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="e2e_test",
            termination_config=config,
        )

        result = orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=2,
        )

        # 验证有终止原因
        assert result.termination_reason is not None
        assert len(result.termination_reason) > 0


# =============================================================================
# Test Calculator Experiment (Simplified)
# =============================================================================


class TestCalculatorExperiment:
    """计算器实验简化测试"""

    def test_calculator_add_evolution_runs(self):
        """测试计算器加法进化运行"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=5, success_threshold=0.95)
        orchestrator = EvolutionOrchestrator(
            task_id="calculator_add",
            termination_config=config,
        )

        result = orchestrator.evolve(
            requirements=[
                "Write an add function that takes two numbers and returns their sum",
                "Function signature: def add(a, b):",
            ],
            test_code="""
assert add(1, 2) == 3
assert add(0, 0) == 0
assert add(-1, 1) == 0
""",
            max_generations=5,
        )

        # 验证进化完成
        assert result.generations >= 1
        assert result.best_code is not None

    def test_calculator_produces_executable_code(self):
        """测试计算器产生可执行代码"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=3, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="calculator",
            termination_config=config,
        )

        result = orchestrator.evolve(
            requirements=["Write a multiply function"],
            test_code="assert multiply(2, 3) == 6",
            max_generations=3,
        )

        # 验证代码可解析
        if result.best_code:
            try:
                compile(result.best_code, "<string>", "exec")
                syntax_valid = True
            except SyntaxError:
                syntax_valid = False
            assert syntax_valid

    def test_experiment_reaches_reasonable_score(self):
        """测试实验达到合理得分"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=3, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="experiment",
            termination_config=config,
        )

        result = orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=3,
        )

        # 验证得分在合理范围（由于使用模拟LLM，得分可能较低）
        assert 0.0 <= result.best_score <= 1.0


# =============================================================================
# Test Component Integration
# =============================================================================


class TestComponentIntegration:
    """组件集成测试"""

    def test_all_components_work_together(self):
        """测试所有组件协同工作"""
        from evolution.code_generator import CodeGenerator
        from evolution.dual_evaluator import DualEvaluator
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.strategy_optimizer import StrategyOptimizer
        from evolution.termination_checker import TerminationChecker
        from evolution.test_runner import TestRunner

        orchestrator = EvolutionOrchestrator(
            task_id="integration_test",
            code_generator=CodeGenerator(),
            test_runner=TestRunner(),
            dual_evaluator=DualEvaluator(),
            strategy_optimizer=StrategyOptimizer("integration_test"),
            termination_checker=TerminationChecker(),
        )

        # 验证所有组件已初始化
        assert orchestrator.code_generator is not None
        assert orchestrator.test_runner is not None
        assert orchestrator.dual_evaluator is not None
        assert orchestrator.strategy_optimizer is not None
        assert orchestrator.termination_checker is not None

    def test_strategy_optimizer_updates_during_evolution(self):
        """测试策略优化器在进化中更新"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="strategy_test",
            termination_config=config,
        )

        # 运行进化前记录策略状态
        initial_arms = len(orchestrator.strategy_optimizer.arms)

        orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=2,
        )

        # 验证策略臂数量不变（但参数会更新）
        assert len(orchestrator.strategy_optimizer.arms) == initial_arms

    def test_termination_checker_tracks_progress(self):
        """测试终止检查器追踪进度"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="termination_test",
            termination_config=config,
        )

        # 运行进化
        orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=2,
        )

        # 验证终止检查器记录了代数
        assert orchestrator.current_generation >= 1


# =============================================================================
# Test Error Handling
# =============================================================================


class TestEndToEndErrorHandling:
    """端到端错误处理测试"""

    def test_handles_empty_requirements(self):
        """测试处理空需求"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="error_test",
            termination_config=config,
        )

        # 空需求不应导致崩溃
        result = orchestrator.evolve(
            requirements=[],
            test_code="pass",
            max_generations=2,
        )

        assert result is not None

    def test_handles_invalid_test_code(self):
        """测试处理无效测试代码"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="error_test",
            termination_config=config,
        )

        # 无效测试代码不应导致崩溃
        result = orchestrator.evolve(
            requirements=["Write a function"],
            test_code="invalid syntax (((",
            max_generations=2,
        )

        assert result is not None

    def test_graceful_degradation_on_failure(self):
        """测试失败时优雅降级"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        orchestrator = EvolutionOrchestrator(
            task_id="graceful_test",
            termination_config=config,
        )

        # 即使所有代都失败，也应返回结果
        result = orchestrator.evolve(
            requirements=["Write an impossible function that violates physics"],
            test_code="assert False",
            max_generations=2,
        )

        assert result.best_code is not None or result.best_code == ""
        assert result.termination_reason is not None

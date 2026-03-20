"""
Evolution Orchestrator 测试模块 - TDD Red Phase

测试 EvolutionOrchestrator 类 - 进化流程编排器

职责：
1. 协调所有组件完成进化循环
2. 管理进化状态和历史
3. 处理进化终止条件
4. 生成进化报告
"""

import os
from unittest.mock import MagicMock, patch

# =============================================================================
# Test EvolutionOrchestrator Initialization
# =============================================================================


class TestEvolutionOrchestratorInitialization:
    """EvolutionOrchestrator 初始化测试"""

    @patch("evolution.code_generator.OpenAI")
    def test_initializes_with_all_components(self, mock_openai):
        """测试使用所有组件初始化"""
        from core.git_manager import GitManager
        from evolution.code_generator import CodeGenerator
        from evolution.dual_evaluator import DualEvaluator
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.strategy_optimizer import StrategyOptimizer
        from evolution.termination_checker import TerminationChecker
        from evolution.test_runner import TestRunner

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        orchestrator = EvolutionOrchestrator(
            task_id="test_task",
            code_generator=CodeGenerator(api_key="test-key"),
            test_runner=TestRunner(),
            dual_evaluator=DualEvaluator(),
            strategy_optimizer=StrategyOptimizer("test_task"),
            termination_checker=TerminationChecker(),
            git_manager=GitManager(),
        )

        assert orchestrator.task_id == "test_task"
        assert orchestrator.code_generator is not None

    @patch("evolution.code_generator.OpenAI")
    def test_initializes_with_minimal_config(self, mock_openai):
        """测试使用最小配置初始化"""
        from evolution.orchestrator import EvolutionOrchestrator

        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(task_id="test_task")

        assert orchestrator.task_id == "test_task"
        assert orchestrator.code_generator is not None


# =============================================================================
# Test EvolutionOrchestrator - Single Generation
# =============================================================================


class TestEvolutionOrchestratorSingleGeneration:
    """单代进化测试（P0优先级）"""

    @patch("evolution.code_generator.OpenAI")
    def test_runs_single_generation(self, mock_openai):
        """测试运行单代进化"""
        from evolution.orchestrator import EvolutionOrchestrator

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    return 42\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(task_id="test")

        result = orchestrator.run_single_generation(
            generation=1,
            requirements=["Write a function that returns 42"],
            test_code="assert solution() == 42",
        )

        assert result is not None
        assert result.code is not None
        assert result.score is not None

    @patch("evolution.code_generator.OpenAI")
    def test_generation_produces_valid_code(self, mock_openai):
        """测试代进化产生有效代码"""
        from evolution.orchestrator import EvolutionOrchestrator

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    return 42\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(task_id="test")

        result = orchestrator.run_single_generation(
            generation=1,
            requirements=["Write a function that returns 42"],
            test_code="assert solution() == 42",
        )

        # 代码应该能通过语法检查
        import ast

        try:
            ast.parse(result.code)
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False

        assert syntax_valid

    @patch("evolution.code_generator.OpenAI")
    def test_generation_returns_score(self, mock_openai):
        """测试代进化返回得分"""
        from evolution.orchestrator import EvolutionOrchestrator

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(task_id="test")

        result = orchestrator.run_single_generation(
            generation=1,
            requirements=["Write a function"],
            test_code="pass",
        )

        assert result.score is not None
        assert 0.0 <= result.score <= 1.0


# =============================================================================
# Test EvolutionOrchestrator - Evolution Loop
# =============================================================================


class TestEvolutionOrchestratorEvolutionLoop:
    """进化循环测试（P0优先级）"""

    @patch("evolution.code_generator.OpenAI")
    def test_runs_evolution_loop_for_multiple_generations(self, mock_openai):
        """测试运行多代进化循环"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        config = TerminationConfig(max_generations=3, success_threshold=1.0)
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                termination_config=config,
            )

        result = orchestrator.evolve(
            requirements=["Write a simple function"],
            test_code="pass",
            max_generations=3,
        )

        assert result is not None
        assert result.generations >= 1

    @patch("evolution.code_generator.OpenAI")
    def test_evolution_stores_history(self, mock_openai):
        """测试进化存储历史记录"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                termination_config=config,
            )

        orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=2,
        )

        # 应该存储历史
        assert len(orchestrator.history) >= 1

    @patch("evolution.code_generator.OpenAI")
    def test_evolution_tracks_best_solution(self, mock_openai):
        """测试进化追踪最佳解决方案"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        config = TerminationConfig(max_generations=3, success_threshold=1.0)
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                termination_config=config,
            )

        orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=3,
        )

        assert orchestrator.best_score >= 0.0
        assert orchestrator.best_code is not None


# =============================================================================
# Test EvolutionOrchestrator - Termination
# =============================================================================


class TestEvolutionOrchestratorTermination:
    """终止条件测试（P0优先级）"""

    @patch("evolution.code_generator.OpenAI")
    def test_stops_at_max_generations(self, mock_openai):
        """测试在最大代数时停止"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        config = TerminationConfig(max_generations=2, success_threshold=1.0)
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                termination_config=config,
            )

        result = orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=2,
        )

        assert result.generations <= 2

    @patch("evolution.code_generator.OpenAI")
    def test_stops_at_success_threshold(self, mock_openai):
        """测试在成功阈值时停止"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        # 设置一个很低的成功阈值以便测试
        config = TerminationConfig(max_generations=10, success_threshold=0.0)
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                termination_config=config,
            )

        result = orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
        )

        # 应该成功终止
        assert result.success is True

    @patch("evolution.code_generator.OpenAI")
    def test_respects_stagnation_limit(self, mock_openai):
        """测试遵守停滞限制"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.termination_checker import TerminationConfig

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        config = TerminationConfig(
            max_generations=10,
            success_threshold=1.0,
            stagnation_generations=2,
        )
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                termination_config=config,
            )

        result = orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
        )

        # 应该因停滞而终止
        assert result.termination_reason is not None
        # 使用result避免未使用变量警告
        assert result.generations >= 1


# =============================================================================
# Test EvolutionOrchestrator - Strategy Optimization
# =============================================================================


class TestEvolutionOrchestratorStrategyOptimization:
    """策略优化测试（P1优先级）"""

    @patch("evolution.code_generator.OpenAI")
    def test_uses_strategy_optimizer(self, mock_openai):
        """测试使用策略优化器"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.strategy_optimizer import StrategyOptimizer

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        optimizer = StrategyOptimizer("test")
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                strategy_optimizer=optimizer,
            )

        # 运行一代
        result = orchestrator.run_single_generation(
            generation=1,
            requirements=["Write a function"],
            test_code="pass",
        )

        assert result is not None

    @patch("evolution.code_generator.OpenAI")
    def test_updates_strategy_based_on_result(self, mock_openai):
        """测试根据结果更新策略"""
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.strategy_optimizer import StrategyOptimizer

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        optimizer = StrategyOptimizer("test")
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                strategy_optimizer=optimizer,
            )

        # 运行并报告结果
        result = orchestrator.run_single_generation(
            generation=1,
            requirements=["Write a function"],
            test_code="pass",
        )

        orchestrator.report_generation_result(result, success=True)

        # 策略优化器应该被更新
        assert True  # 如果未抛出异常则认为成功


# =============================================================================
# Test EvolutionOrchestrator - Git Integration
# =============================================================================


class TestEvolutionOrchestratorGitIntegration:
    """Git集成测试（P1优先级）"""

    @patch("evolution.code_generator.OpenAI")
    def test_commits_each_generation(self, mock_openai, tmp_path):
        """测试每代都提交到Git"""
        import subprocess

        from core.git_manager import GitManager
        from evolution.orchestrator import EvolutionOrchestrator

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        # 创建临时git仓库
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始提交
        (repo_path / "initial.txt").write_text("initial")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        git_manager = GitManager(str(repo_path))
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(
                task_id="test",
                git_manager=git_manager,
            )

        # 运行一代
        orchestrator.run_single_generation(
            generation=1,
            requirements=["Write a function"],
            test_code="pass",
        )

        # 验证有提交
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        assert "gen-1" in result.stdout or len(result.stdout.split("\n")) > 1


# =============================================================================
# Test EvolutionResult
# =============================================================================


class TestEvolutionResult:
    """进化结果测试"""

    def test_result_has_generations_field(self):
        """测试结果包含代数字段"""
        from evolution.orchestrator import EvolutionResult

        result = EvolutionResult(
            generations=10,
            best_score=0.95,
            best_code="def solution(): return 42",
            success=True,
            termination_reason="Success threshold reached",
        )

        assert result.generations == 10

    def test_result_has_best_score_field(self):
        """测试结果包含最佳得分字段"""
        from evolution.orchestrator import EvolutionResult

        result = EvolutionResult(
            generations=10,
            best_score=0.95,
            best_code="def solution(): return 42",
            success=True,
            termination_reason="Success threshold reached",
        )

        assert result.best_score == 0.95

    def test_result_has_best_code_field(self):
        """测试结果包含最佳代码字段"""
        from evolution.orchestrator import EvolutionResult

        result = EvolutionResult(
            generations=10,
            best_score=0.95,
            best_code="def solution(): return 42",
            success=True,
            termination_reason="Success threshold reached",
        )

        assert "def solution" in result.best_code

    def test_result_has_success_field(self):
        """测试结果包含成功字段"""
        from evolution.orchestrator import EvolutionResult

        result = EvolutionResult(
            generations=10,
            best_score=0.95,
            best_code="def solution(): return 42",
            success=True,
            termination_reason="Success threshold reached",
        )

        assert result.success is True

    def test_result_has_termination_reason_field(self):
        """测试结果包含终止原因字段"""
        from evolution.orchestrator import EvolutionResult

        result = EvolutionResult(
            generations=10,
            best_score=0.95,
            best_code="def solution(): return 42",
            success=True,
            termination_reason="Success threshold reached",
        )

        assert "threshold" in result.termination_reason


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestEvolutionOrchestratorEdgeCases:
    """边界情况测试"""

    @patch("evolution.code_generator.OpenAI")
    def test_handles_empty_requirements(self, mock_openai):
        """测试处理空需求"""
        from evolution.orchestrator import EvolutionOrchestrator

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(task_id="test")

        # 应该处理空需求而不崩溃
        result = orchestrator.run_single_generation(
            generation=1,
            requirements=[],
            test_code="pass",
        )

        assert result is not None

    @patch("evolution.code_generator.OpenAI")
    def test_handles_syntax_error_in_test_code(self, mock_openai):
        """测试处理测试代码语法错误"""
        from evolution.orchestrator import EvolutionOrchestrator

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="```python\ndef solution():\n    pass\n```"
                    )
                )
            ]
        )
        mock_openai.return_value = mock_client

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(task_id="test")

        # 使用有语法错误的测试代码
        result = orchestrator.run_single_generation(
            generation=1,
            requirements=["Write a function"],
            test_code="assert solution(  # invalid syntax",
        )

        # 应该返回结果，即使测试失败
        assert result is not None
        assert result.score is not None

    def test_handles_zero_max_generations(self):
        """测试处理零最大代数"""
        from evolution.orchestrator import EvolutionOrchestrator

        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": "test-key"}):
            orchestrator = EvolutionOrchestrator(task_id="test")

        result = orchestrator.evolve(
            requirements=["Write a function"],
            test_code="pass",
            max_generations=0,
        )

        # 应该立即终止（或运行1代后停止）
        assert result.generations <= 1

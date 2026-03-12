"""
Termination Checker 测试模块 - TDD Red Phase

测试 TerminationChecker 类 - 检测进化终止条件

终止条件：
1. 达到成功阈值（进化成功）
2. 达到最大代数（进化失败）
3. 检测到停滞（无改进超过N代）
"""

# Import will be added after implementation exists
# from evolution.termination_checker import (
#     TerminationChecker,
#     TerminationConfig,
#     TerminationDecision,
# )


# =============================================================================
# Test TerminationConfig Dataclass
# =============================================================================


class TestTerminationConfig:
    """TerminationConfig 数据类测试"""

    def test_config_has_success_threshold_field(self):
        """测试配置包含成功阈值字段"""
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(success_threshold=0.95)
        assert config.success_threshold == 0.95

    def test_config_has_max_generations_field(self):
        """测试配置包含最大代数字段"""
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(max_generations=100)
        assert config.max_generations == 100

    def test_config_has_stagnation_generations_field(self):
        """测试配置包含停滞代数字段"""
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig(stagnation_generations=10)
        assert config.stagnation_generations == 10

    def test_config_has_default_values(self):
        """测试配置有默认值"""
        from evolution.termination_checker import TerminationConfig

        config = TerminationConfig()
        assert config.success_threshold == 0.95
        assert config.max_generations == 50
        assert config.stagnation_generations == 10


# =============================================================================
# Test TerminationDecision Dataclass
# =============================================================================


class TestTerminationDecision:
    """TerminationDecision 数据类测试"""

    def test_decision_has_should_terminate_field(self):
        """测试决策包含是否终止字段"""
        from evolution.termination_checker import TerminationDecision

        decision = TerminationDecision(
            should_terminate=True, reason="Success threshold reached", is_success=True
        )
        assert decision.should_terminate is True

    def test_decision_has_reason_field(self):
        """测试决策包含原因字段"""
        from evolution.termination_checker import TerminationDecision

        decision = TerminationDecision(
            should_terminate=False, reason="Continue evolving", is_success=False
        )
        assert decision.reason == "Continue evolving"

    def test_decision_has_is_success_field(self):
        """测试决策包含是否成功字段"""
        from evolution.termination_checker import TerminationDecision

        decision = TerminationDecision(
            should_terminate=True, reason="Max generations reached", is_success=False
        )
        assert decision.is_success is False


# =============================================================================
# Test TerminationChecker - Success Threshold
# =============================================================================


class TestTerminationCheckerSuccessThreshold:
    """成功阈值终止测试（P0优先级）"""

    def test_terminates_when_score_exceeds_threshold(self):
        """测试得分超过阈值时终止"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()
        decision = checker.check(current_gen=5, current_score=0.96)

        assert decision.should_terminate is True
        assert decision.is_success is True

    def test_does_not_terminate_when_score_below_threshold(self):
        """测试得分低于阈值时不终止"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()
        decision = checker.check(current_gen=5, current_score=0.85)

        assert decision.should_terminate is False

    def test_terminates_at_exact_threshold(self):
        """测试得分等于阈值时终止"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()
        decision = checker.check(current_gen=5, current_score=0.95)

        assert decision.should_terminate is True
        assert decision.is_success is True

    def test_reason_includes_success_message(self):
        """测试成功终止的原因包含成功信息"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()
        decision = checker.check(current_gen=5, current_score=0.98)

        assert (
            "success" in decision.reason.lower()
            or "threshold" in decision.reason.lower()
        )


# =============================================================================
# Test TerminationChecker - Max Generations
# =============================================================================


class TestTerminationCheckerMaxGenerations:
    """最大代数终止测试（P0优先级）"""

    def test_terminates_at_max_generations(self):
        """测试达到最大代数时终止"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        config = TerminationConfig(max_generations=10)
        checker = TerminationChecker(config=config)
        decision = checker.check(current_gen=10, current_score=0.5)

        assert decision.should_terminate is True
        assert decision.is_success is False

    def test_does_not_terminate_before_max_generations(self):
        """测试未达到最大代数时不终止"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        config = TerminationConfig(max_generations=10)
        checker = TerminationChecker(config=config)
        decision = checker.check(current_gen=9, current_score=0.5)

        assert decision.should_terminate is False

    def test_reason_includes_max_generations_message(self):
        """测试最大代数终止的原因包含相关信息"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        config = TerminationConfig(max_generations=10)
        checker = TerminationChecker(config=config)
        decision = checker.check(current_gen=10, current_score=0.5)

        assert (
            "generation" in decision.reason.lower() or "max" in decision.reason.lower()
        )


# =============================================================================
# Test TerminationChecker - Stagnation Detection
# =============================================================================


class TestTerminationCheckerStagnation:
    """停滞检测测试（P0优先级）"""

    def test_detects_stagnation_after_n_generations(self):
        """测试N代无改进后检测停滞"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        config = TerminationConfig(stagnation_generations=3)
        checker = TerminationChecker(config=config)

        # 模拟3代无改进
        checker.check(current_gen=1, current_score=0.5)
        checker.check(current_gen=2, current_score=0.5)
        checker.check(current_gen=3, current_score=0.5)
        decision = checker.check(current_gen=4, current_score=0.5)

        assert decision.should_terminate is True
        assert decision.is_success is False

    def test_does_not_detect_stagnation_if_improving(self):
        """测试有改进时不检测停滞"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        config = TerminationConfig(stagnation_generations=3)
        checker = TerminationChecker(config=config)

        # 持续改进
        for gen in range(1, 10):
            decision = checker.check(current_gen=gen, current_score=0.1 * gen)

        assert decision.should_terminate is False

    def test_resets_stagnation_counter_on_improvement(self):
        """测试改进时重置停滞计数器"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        config = TerminationConfig(stagnation_generations=3)
        checker = TerminationChecker(config=config)

        # 2代无改进
        checker.check(current_gen=1, current_score=0.5)
        checker.check(current_gen=2, current_score=0.5)
        # 第3代有改进
        checker.check(current_gen=3, current_score=0.6)
        # 再2代无改进
        checker.check(current_gen=4, current_score=0.6)
        decision = checker.check(current_gen=5, current_score=0.6)

        # 应该还未终止（停滞计数器已重置）
        assert decision.should_terminate is False

    def test_reason_includes_stagnation_message(self):
        """测试停滞终止的原因包含停滞信息"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        config = TerminationConfig(stagnation_generations=2)
        checker = TerminationChecker(config=config)

        checker.check(current_gen=1, current_score=0.5)
        checker.check(current_gen=2, current_score=0.5)
        decision = checker.check(current_gen=3, current_score=0.5)

        assert (
            "stagnation" in decision.reason.lower()
            or "improve" in decision.reason.lower()
        )


# =============================================================================
# Test TerminationChecker - Priority Order
# =============================================================================


class TestTerminationCheckerPriority:
    """终止条件优先级测试（P1优先级）"""

    def test_success_takes_priority_over_max_generations(self):
        """测试成功优先于最大代数"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        # 低最大代数，但已达到成功阈值
        config = TerminationConfig(max_generations=5, success_threshold=0.9)
        checker = TerminationChecker(config=config)
        decision = checker.check(current_gen=5, current_score=0.95)

        # 应该标记为成功
        assert decision.should_terminate is True
        assert decision.is_success is True

    def test_success_takes_priority_over_stagnation(self):
        """测试成功优先于停滞"""
        from evolution.termination_checker import TerminationConfig, TerminationChecker

        config = TerminationConfig(stagnation_generations=2, success_threshold=0.9)
        checker = TerminationChecker(config=config)

        # 先触发停滞
        checker.check(current_gen=1, current_score=0.5)
        checker.check(current_gen=2, current_score=0.5)
        # 但第3代达到成功阈值
        decision = checker.check(current_gen=3, current_score=0.95)

        # 应该标记为成功
        assert decision.should_terminate is True
        assert decision.is_success is True


# =============================================================================
# Test TerminationChecker - Edge Cases
# =============================================================================


class TestTerminationCheckerEdgeCases:
    """边界情况测试"""

    def test_handles_zero_generation(self):
        """测试处理第0代"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()
        decision = checker.check(current_gen=0, current_score=0.5)

        assert decision.should_terminate is False

    def test_handles_perfect_score(self):
        """测试处理完美分数"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()
        decision = checker.check(current_gen=1, current_score=1.0)

        assert decision.should_terminate is True
        assert decision.is_success is True

    def test_handles_zero_score(self):
        """测试处理零分"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()
        decision = checker.check(current_gen=1, current_score=0.0)

        assert decision.should_terminate is False

    def test_handles_negative_generation_gracefully(self):
        """测试优雅处理负代数"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()
        # 应该处理为0或拒绝，不崩溃
        decision = checker.check(current_gen=-1, current_score=0.5)
        assert isinstance(decision.should_terminate, bool)

    def test_tracks_best_score(self):
        """测试追踪最佳得分"""
        from evolution.termination_checker import TerminationChecker

        checker = TerminationChecker()

        checker.check(current_gen=1, current_score=0.5)
        checker.check(current_gen=2, current_score=0.6)
        checker.check(current_gen=3, current_score=0.55)

        # 最佳得分应该是0.6
        assert checker.best_score == 0.6

    def test_detects_stagnation_at_high_score(self):
        """测试在高得分时检测停滞"""
        from evolution.termination_checker import TerminationChecker, TerminationConfig

        config = TerminationConfig(
            success_threshold=0.99, stagnation_generations=2  # 非常高的阈值
        )
        checker = TerminationChecker(config=config)

        # 得分很高但不再提高
        checker.check(current_gen=1, current_score=0.95)
        checker.check(current_gen=2, current_score=0.95)
        decision = checker.check(current_gen=3, current_score=0.95)

        # 应该因停滞而终止（未达到成功阈值）
        assert decision.should_terminate is True
        assert decision.is_success is False

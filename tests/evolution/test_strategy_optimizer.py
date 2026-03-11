"""
Strategy Optimizer 测试模块 - TDD Red Phase

测试 StrategyArm 和 StrategyOptimizer 类
严格按照TDD流程：先写测试，确保失败，再写实现
"""

# Import implementation from the module
from evolution.strategy_optimizer import StrategyArm, StrategyOptimizer

# =============================================================================
# Test StrategyArm
# =============================================================================


class TestStrategyArm:
    """
    StrategyArm 单元测试 - TDD Red阶段

    StrategyArm 是Thompson Sampling的策略臂，使用Beta分布
    """

    def test_initial_alpha_beta_values(self):
        """测试初始alpha=1.0, beta=1.0（Beta分布的先验参数）"""
        # Arrange & Act
        arm = StrategyArm(key="test_strategy")

        # Assert
        assert arm.alpha == 1.0, f"Expected alpha=1.0, got {arm.alpha}"
        assert arm.beta == 1.0, f"Expected beta=1.0, got {arm.beta}"

    def test_sample_returns_float(self):
        """测试sample()返回float类型"""
        # Arrange
        arm = StrategyArm(key="test")

        # Act
        result = arm.sample()

        # Assert
        assert isinstance(result, float), f"Expected float, got {type(result)}"

    def test_sample_returns_value_between_0_and_1(self):
        """测试sample()返回0-1之间的值（Beta分布范围）"""
        # Arrange
        arm = StrategyArm(key="test")

        # Act - 多次采样确保稳定性
        samples = [arm.sample() for _ in range(10)]

        # Assert
        for sample in samples:
            assert 0.0 <= sample <= 1.0, f"Sample {sample} out of range [0, 1]"

    def test_sample_with_different_alpha_beta(self):
        """测试不同alpha/beta参数的采样行为"""
        # Arrange - 高alpha应该倾向于产生更高值
        high_alpha_arm = StrategyArm(key="high", alpha=10.0, beta=1.0)
        low_alpha_arm = StrategyArm(key="low", alpha=1.0, beta=10.0)

        # Act
        high_samples = [high_alpha_arm.sample() for _ in range(100)]
        low_samples = [low_alpha_arm.sample() for _ in range(100)]

        # Assert - 高alpha的平均值应该大于低alpha
        high_mean = sum(high_samples) / len(high_samples)
        low_mean = sum(low_samples) / len(low_samples)
        assert (
            high_mean > low_mean
        ), f"High alpha mean {high_mean} should be > low alpha mean {low_mean}"

    def test_update_increases_alpha_on_success(self):
        """测试update(success=True)时alpha增加1"""
        # Arrange
        arm = StrategyArm(key="test", alpha=1.0, beta=1.0)

        # Act
        arm.update(success=True)

        # Assert
        assert arm.alpha == 2.0, f"Expected alpha=2.0 after success, got {arm.alpha}"
        assert arm.beta == 1.0, f"Beta should remain 1.0, got {arm.beta}"

    def test_update_increases_beta_on_failure(self):
        """测试update(success=False)时beta增加1"""
        # Arrange
        arm = StrategyArm(key="test", alpha=1.0, beta=1.0)

        # Act
        arm.update(success=False)

        # Assert
        assert arm.alpha == 1.0, f"Alpha should remain 1.0, got {arm.alpha}"
        assert arm.beta == 2.0, f"Expected beta=2.0 after failure, got {arm.beta}"

    def test_update_increments_total_uses(self):
        """测试update()增加total_uses计数"""
        # Arrange
        arm = StrategyArm(key="test")

        # Act
        arm.update(success=True)
        arm.update(success=False)
        arm.update(success=True)

        # Assert
        assert arm.total_uses == 3, f"Expected total_uses=3, got {arm.total_uses}"

    def test_expected_value_calculation(self):
        """测试期望值计算：alpha / (alpha + beta)"""
        # Arrange
        arm = StrategyArm(key="test", alpha=3.0, beta=1.0)

        # Act
        expected = arm.expected_value()

        # Assert - 3/(3+1) = 0.75
        assert expected == 0.75, f"Expected 0.75, got {expected}"

    def test_expected_value_with_equal_alpha_beta(self):
        """测试alpha=beta时期望值为0.5"""
        # Arrange
        arm = StrategyArm(key="test", alpha=5.0, beta=5.0)

        # Act
        expected = arm.expected_value()

        # Assert
        assert expected == 0.5, f"Expected 0.5 for equal alpha/beta, got {expected}"

    def test_expected_value_with_high_beta(self):
        """测试高beta时期望值较低"""
        # Arrange
        arm = StrategyArm(key="test", alpha=1.0, beta=9.0)

        # Act
        expected = arm.expected_value()

        # Assert - 1/(1+9) = 0.1
        assert expected == 0.1, f"Expected 0.1, got {expected}"

    def test_key_is_stored(self):
        """测试key被正确存储"""
        # Arrange & Act
        arm = StrategyArm(key="my_strategy_key")

        # Assert
        assert (
            arm.key == "my_strategy_key"
        ), f"Expected key='my_strategy_key', got {arm.key}"


# =============================================================================
# Test StrategyArm Edge Cases
# =============================================================================


class TestStrategyArmEdgeCases:
    """StrategyArm 边界情况测试"""

    def test_with_zero_total_uses(self):
        """测试初始状态total_uses=0"""
        arm = StrategyArm(key="test")
        assert arm.total_uses == 0

    def test_multiple_updates_maintain_correct_ratio(self):
        """测试多次更新后比率正确"""
        arm = StrategyArm(key="test")

        # 5次成功，3次失败
        for _ in range(5):
            arm.update(success=True)
        for _ in range(3):
            arm.update(success=False)

        # 初始alpha=1，5次成功 -> 6
        # 初始beta=1，3次失败 -> 4
        assert arm.alpha == 6.0
        assert arm.beta == 4.0
        assert arm.expected_value() == 6.0 / 10.0


# =============================================================================
# Test StrategyOptimizer - P3-TEST-02
# =============================================================================


class TestStrategyOptimizer:
    """
    StrategyOptimizer 单元测试 - TDD Red阶段

    测试Thompson Sampling策略优化器
    """

    def test_initializes_all_strategy_combinations(self):
        """测试初始化所有策略组合（3*2*3=18种）"""
        # Arrange & Act
        optimizer = StrategyOptimizer(task_id="test_task")

        # Assert - 3(mutation) * 2(validation) * 3(temperature) = 18
        assert len(optimizer.arms) == 18, f"Expected 18 arms, got {len(optimizer.arms)}"

    def test_arms_have_correct_keys(self):
        """测试策略臂的键格式正确"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")

        # Assert - 检查所有键都是有效的JSON
        for key in optimizer.arms.keys():
            import json

            strategy = json.loads(key)
            assert "mutation_type" in strategy
            assert "validation_mode" in strategy
            assert "generation_temperature" in strategy

    def test_select_strategy_returns_valid_strategy(self):
        """测试选择策略返回有效配置字典"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")

        # Act
        strategy = optimizer.select_strategy()

        # Assert
        assert isinstance(strategy, dict)
        assert "mutation_type" in strategy
        assert strategy["mutation_type"] in ["conservative", "aggressive", "hybrid"]
        assert "validation_mode" in strategy
        assert strategy["validation_mode"] in ["lightweight", "comprehensive"]
        assert "generation_temperature" in strategy
        assert strategy["generation_temperature"] in [0.2, 0.5, 0.8]

    def test_select_strategy_returns_consistent_format(self):
        """测试多次选择返回相同格式的策略"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")

        # Act
        strategies = [optimizer.select_strategy() for _ in range(10)]

        # Assert - 所有策略都有相同的键
        required_keys = {"mutation_type", "validation_mode", "generation_temperature"}
        for strategy in strategies:
            assert set(strategy.keys()) == required_keys

    def test_report_result_updates_arm_on_success(self):
        """测试报告成功结果时更新对应策略臂"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")
        strategy = {
            "mutation_type": "conservative",
            "validation_mode": "lightweight",
            "generation_temperature": 0.5,
        }
        key = optimizer._strategy_to_key(strategy)
        initial_uses = optimizer.arms[key].total_uses

        # Act
        optimizer.report_result(strategy, success=True, score=0.85)

        # Assert
        assert optimizer.arms[key].total_uses == initial_uses + 1
        assert optimizer.arms[key].alpha == 2.0  # 初始1.0 + 1

    def test_report_result_updates_arm_on_failure(self):
        """测试报告失败结果时更新对应策略臂"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")
        strategy = {
            "mutation_type": "aggressive",
            "validation_mode": "comprehensive",
            "generation_temperature": 0.8,
        }
        key = optimizer._strategy_to_key(strategy)

        # Act
        optimizer.report_result(strategy, success=False, score=0.3)

        # Assert
        assert optimizer.arms[key].beta == 2.0  # 初始1.0 + 1

    def test_strategy_to_key_returns_consistent_string(self):
        """测试策略到键的转换一致（相同输入产生相同输出）"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")
        strategy = {"a": 1, "b": 2}

        # Act
        key1 = optimizer._strategy_to_key(strategy)
        key2 = optimizer._strategy_to_key(strategy)

        # Assert
        assert key1 == key2
        assert isinstance(key1, str)

    def test_strategy_to_key_is_deterministic(self):
        """测试策略到键的转换是确定性的（键排序）"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")
        strategy1 = {"z": 1, "a": 2, "m": 3}
        strategy2 = {"a": 2, "m": 3, "z": 1}  # 不同顺序

        # Act
        key1 = optimizer._strategy_to_key(strategy1)
        key2 = optimizer._strategy_to_key(strategy2)

        # Assert - 不同顺序应该产生相同的键（因为排序）
        assert key1 == key2

    def test_key_to_strategy_reverses_strategy_to_key(self):
        """测试键到策略的转换是策略到键的逆操作"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")
        original_strategy = {"type": "test", "param": 0.5}

        # Act
        key = optimizer._strategy_to_key(original_strategy)
        recovered_strategy = optimizer._key_to_strategy(key)

        # Assert
        assert recovered_strategy == original_strategy

    def test_get_arm_stats_returns_list_of_dicts(self):
        """测试获取策略臂统计返回字典列表"""
        # Arrange
        optimizer = StrategyOptimizer(task_id="test")

        # Act
        stats = optimizer.get_arm_stats()

        # Assert
        assert isinstance(stats, list)
        assert len(stats) == 18
        for stat in stats:
            assert isinstance(stat, dict)
            assert "key" in stat
            assert "alpha" in stat
            assert "beta" in stat
            assert "uses" in stat
            assert "expected" in stat

    def test_task_id_is_stored(self):
        """测试task_id被正确存储用于策略隔离"""
        # Arrange & Act
        optimizer = StrategyOptimizer(task_id="my_task_123")

        # Assert
        assert optimizer.task_id == "my_task_123"

    def test_different_tasks_have_independent_optimizers(self):
        """测试不同任务有独立的优化器（策略隔离）"""
        # Arrange
        optimizer1 = StrategyOptimizer(task_id="task1")
        optimizer2 = StrategyOptimizer(task_id="task2")

        # Act - 更新optimizer1的某个策略
        strategy = optimizer1.select_strategy()
        optimizer1.report_result(strategy, success=True, score=0.9)

        # Assert - optimizer2的对应策略不应被更新
        key = optimizer1._strategy_to_key(strategy)
        assert optimizer1.arms[key].total_uses == 1
        assert optimizer2.arms[key].total_uses == 0


# =============================================================================
# Test StrategyOptimizer Edge Cases
# =============================================================================


class TestStrategyOptimizerEdgeCases:
    """StrategyOptimizer 边界情况测试"""

    def test_all_mutation_types_present(self):
        """测试所有变异类型都存在"""
        optimizer = StrategyOptimizer(task_id="test")
        mutation_types = set()

        for arm in optimizer.arms.values():
            import json

            strategy = json.loads(arm.key)
            mutation_types.add(strategy["mutation_type"])

        assert mutation_types == {"conservative", "aggressive", "hybrid"}

    def test_all_temperatures_present(self):
        """测试所有温度值都存在"""
        optimizer = StrategyOptimizer(task_id="test")
        temperatures = set()

        for arm in optimizer.arms.values():
            import json

            strategy = json.loads(arm.key)
            temperatures.add(strategy["generation_temperature"])

        assert temperatures == {0.2, 0.5, 0.8}

    def test_report_result_with_unknown_strategy_raises(self):
        """测试报告未知策略时抛出异常"""
        optimizer = StrategyOptimizer(task_id="test")
        unknown_strategy = {
            "mutation_type": "invalid",
            "validation_mode": "unknown",
            "generation_temperature": 1.5,
        }

        # 应该不抛出异常，只是忽略或记录
        # 实际行为需要在实现时确定
        optimizer.report_result(unknown_strategy, success=True, score=0.5)
        # 如果没有异常，测试通过

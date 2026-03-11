"""
Strategy Optimizer 测试模块 - TDD Red Phase

测试 StrategyArm 和 StrategyOptimizer 类
严格按照TDD流程：先写测试，确保失败，再写实现
"""

import pytest
import numpy as np
from dataclasses import dataclass


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
        assert high_mean > low_mean, f"High alpha mean {high_mean} should be > low alpha mean {low_mean}"
    
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
        assert arm.key == "my_strategy_key", f"Expected key='my_strategy_key', got {arm.key}"


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
# Import implementation (P3-IMPL-01 completed)
# =============================================================================

from evolution.strategy_optimizer import StrategyArm, StrategyOptimizer

"""
SEMDS Strategy Optimizer - Phase 3

Thompson Sampling策略优化器
使用多臂老虎机算法选择最优生成策略
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import itertools


@dataclass
class StrategyArm:
    """
    Thompson Sampling策略臂
    
    使用Beta分布进行采样，平衡探索与利用
    
    Attributes:
        key: 策略组合的唯一标识
        alpha: Beta分布的alpha参数（成功次数+先验）
        beta: Beta分布的beta参数（失败次数+先验）
        total_uses: 总使用次数
    """
    
    key: str
    alpha: float = 1.0
    beta: float = 1.0
    total_uses: int = 0
    
    def sample(self) -> float:
        """
        从Beta分布采样
        
        使用numpy的beta分布生成0-1之间的随机数。
        alpha越高，倾向于产生更大的值（更可能选择）
        
        Returns:
            float: 0.0-1.0之间的采样值
        """
        return float(np.random.beta(self.alpha, self.beta))
    
    def update(self, success: bool) -> None:
        """
        更新策略性能
        
        Args:
            success: 是否成功（得分超过阈值）
            
        更新规则:
        - 成功: alpha += 1
        - 失败: beta += 1
        - total_uses += 1
        """
        if success:
            self.alpha += 1.0
        else:
            self.beta += 1.0
        self.total_uses += 1
    
    def expected_value(self) -> float:
        """
        计算期望性能
        
        Beta分布的期望值: E[X] = alpha / (alpha + beta)
        
        Returns:
            float: 0.0-1.0之间的期望值
        """
        return self.alpha / (self.alpha + self.beta)


# =============================================================================
# Placeholder for StrategyOptimizer (will be implemented in P3-IMPL-02)
# =============================================================================

class StrategyOptimizer:
    """
    Thompson Sampling策略优化器 - 待实现
    
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
        """
        初始化策略优化器
        
        Args:
            task_id: 任务ID，用于策略隔离
        """
        self.task_id = task_id
        self.arms: Dict[str, StrategyArm] = {}
        self._initialize_arms()
    
    def _initialize_arms(self) -> None:
        """
        初始化所有策略组合
        
        生成所有可能的策略组合，为每个组合创建一个StrategyArm
        """
        keys = list(self.STRATEGY_DIMENSIONS.keys())
        values = list(self.STRATEGY_DIMENSIONS.values())
        
        for combo in itertools.product(*values):
            strategy = dict(zip(keys, combo))
            key = self._strategy_to_key(strategy)
            self.arms[key] = StrategyArm(key=key)
    
    def select_strategy(self) -> dict:
        """
        选择下一个策略
        
        使用Thompson Sampling:
        1. 从每个臂的Beta分布采样
        2. 选择采样值最高的臂
        3. 返回对应的策略配置
        
        Returns:
            dict: 策略配置字典
        """
        if not self.arms:
            raise ValueError("No strategy arms initialized")
        
        # 从每个臂采样，选择最大值
        best_key = max(self.arms.keys(), key=lambda k: self.arms[k].sample())
        return self._key_to_strategy(best_key)
    
    def report_result(self, strategy: dict, success: bool, score: float) -> None:
        """
        报告策略执行结果
        
        Args:
            strategy: 使用的策略配置
            success: 是否成功（得分超过阈值）
            score: 具体得分（用于日志/调试）
        """
        key = self._strategy_to_key(strategy)
        if key in self.arms:
            self.arms[key].update(success)
    
    def _strategy_to_key(self, strategy: dict) -> str:
        """
        策略字典转字符串键
        
        使用JSON格式，按键排序确保一致性
        """
        return json.dumps(strategy, sort_keys=True)
    
    def _key_to_strategy(self, key: str) -> dict:
        """
        字符串键转策略字典
        """
        return json.loads(key)
    
    def get_arm_stats(self) -> List[dict]:
        """
        获取所有策略臂统计
        
        Returns:
            List[dict]: 每个臂的统计信息
        """
        return [
            {
                "key": arm.key,
                "alpha": arm.alpha,
                "beta": arm.beta,
                "uses": arm.total_uses,
                "expected": arm.expected_value()
            }
            for arm in self.arms.values()
        ]

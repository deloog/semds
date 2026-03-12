"""
Termination Checker 模块 - 进化终止条件检测

检测三种终止条件：
1. 成功阈值：得分达到预设阈值，进化成功
2. 最大代数：达到最大代数限制，进化失败
3. 停滞检测：多代无改进，进化失败

优先级：成功 > 停滞 > 最大代数
（成功可以覆盖其他终止条件）
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TerminationConfig:
    """终止条件配置

    Attributes:
        success_threshold: 成功阈值 (0-1)，默认0.95
        max_generations: 最大代数，默认50
        stagnation_generations: 停滞检测代数，默认10
    """

    success_threshold: float = 0.95
    max_generations: int = 50
    stagnation_generations: int = 10


@dataclass
class TerminationDecision:
    """终止决策

    Attributes:
        should_terminate: 是否应该终止
        reason: 终止原因
        is_success: 是否成功终止
    """

    should_terminate: bool
    reason: str
    is_success: bool


class TerminationChecker:
    """终止条件检查器

    追踪进化过程，检测是否应该终止。

    Example:
        >>> checker = TerminationChecker()
        >>> for gen in range(1, 51):
        ...     score = evaluate_generation(gen)
        ...     decision = checker.check(gen, score)
        ...     if decision.should_terminate:
        ...         print(f"Stopped: {decision.reason}")
        ...         break
    """

    def __init__(self, config: Optional[TerminationConfig] = None):
        """初始化检查器

        Args:
            config: 终止条件配置，默认使用标准配置
        """
        self.config = config or TerminationConfig()
        self.best_score: float = 0.0
        self.generations_without_improvement: int = 0
        self._last_score: Optional[float] = None

    def check(self, current_gen: int, current_score: float) -> TerminationDecision:
        """检查是否终止

        Args:
            current_gen: 当前代数（从1开始）
            current_score: 当前得分

        Returns:
            TerminationDecision: 终止决策
        """
        # 规范化输入
        current_gen = max(0, current_gen)
        current_score = max(0.0, min(1.0, current_score))

        # 更新最佳得分和停滞计数
        self._update_progress(current_score)

        # 检查终止条件（按优先级）

        # 1. 成功阈值（最高优先级）
        if current_score >= self.config.success_threshold:
            return TerminationDecision(
                should_terminate=True,
                reason=(
                    f"Success: {current_score:.0%} >= "
                    f"{self.config.success_threshold:.0%}"
                ),
                is_success=True,
            )

        # 2. 停滞检测
        if self.generations_without_improvement >= self.config.stagnation_generations:
            return TerminationDecision(
                should_terminate=True,
                reason=(
                    f"Stagnation: {self.generations_without_improvement} "
                    f"gens without improvement"
                ),
                is_success=False,
            )

        # 3. 最大代数
        if current_gen >= self.config.max_generations:
            return TerminationDecision(
                should_terminate=True,
                reason=f"Maximum generations reached: {current_gen}",
                is_success=False,
            )

        # 不终止，继续进化
        return TerminationDecision(
            should_terminate=False,
            reason="Continue evolving",
            is_success=False,
        )

    def _update_progress(self, current_score: float) -> None:
        """更新进度追踪

        Args:
            current_score: 当前得分
        """
        # 更新最佳得分
        if current_score > self.best_score:
            self.best_score = current_score
            self.generations_without_improvement = 0
        else:
            self.generations_without_improvement += 1

        self._last_score = current_score

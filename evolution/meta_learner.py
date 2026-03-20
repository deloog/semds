"""
元学习器 - Phase 3 核心组件

记忆失败模式，自动调整策略，实现跨任务经验迁移。
"""

import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path


@dataclass
class FailurePattern:
    """失败模式记录"""

    pattern_id: str
    task_type: str
    error_type: str
    error_signature: str  # 错误特征摘要
    original_code: str
    fixed_code: str
    fix_description: str
    success_rate: float
    usage_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: Optional[str] = None


@dataclass
class StrategyEffectiveness:
    """策略效果记录"""

    strategy_name: str
    task_type: str
    attempts: int = 0
    successes: int = 0
    avg_improvement: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.successes / self.attempts if self.attempts > 0 else 0.0


class MetaLearner:
    """
    元学习器

    记录失败模式和修复策略，支持经验复用。
    """

    def __init__(self, storage_path: Optional[str] = None) -> None:
        """
        Args:
            storage_path: 模式库存储路径，None 则使用内存存储
        """
        self.storage_path = storage_path
        self.patterns: Dict[str, FailurePattern] = {}
        self.strategies: Dict[str, StrategyEffectiveness] = {}

        if storage_path:
            self._load_storage()

    def record_failure_and_fix(
        self,
        task_type: str,
        error_type: str,
        original_code: str,
        fixed_code: str,
        error_message: str,
        fix_description: str = "",
    ) -> str:
        """
        记录失败和修复模式

        Returns:
            pattern_id
        """
        # 生成错误签名（用于相似性匹配）
        error_signature = self._generate_signature(error_message, error_type)
        pattern_id = hashlib.md5(
            f"{task_type}:{error_signature}".encode(), usedforsecurity=False
        ).hexdigest()[:12]

        # 检查是否已有相似模式
        existing = self._find_similar_pattern(task_type, error_signature)
        if existing:
            # 更新现有模式
            existing.usage_count += 1
            existing.success_rate = (existing.success_rate + 1.0) / 2  # 简单平均
            existing.last_used = datetime.now().isoformat()
            return existing.pattern_id

        # 创建新模式
        pattern = FailurePattern(
            pattern_id=pattern_id,
            task_type=task_type,
            error_type=error_type,
            error_signature=error_signature,
            original_code=original_code[:500],  # 限制长度
            fixed_code=fixed_code[:500],
            fix_description=fix_description,
            success_rate=1.0,
            usage_count=1,
            last_used=datetime.now().isoformat(),
        )

        self.patterns[pattern_id] = pattern
        self._save_storage()

        return pattern_id

    def find_applicable_patterns(
        self, task_type: str, error_type: str, error_message: str, top_k: int = 3
    ) -> List[FailurePattern]:
        """
        查找适用的修复模式

        Args:
            task_type: 任务类型
            error_type: 错误类型
            error_message: 错误信息
            top_k: 返回前 k 个最匹配的模式

        Returns:
            匹配的模式列表
        """
        candidates = []

        for pattern in self.patterns.values():
            score = 0.0

            # 任务类型匹配
            if pattern.task_type == task_type:
                score += 3.0

            # 错误类型匹配
            if pattern.error_type == error_type:
                score += 2.0

            # 错误签名相似度
            current_sig = self._generate_signature(error_message, error_type)
            sig_similarity = self._signature_similarity(
                pattern.error_signature, current_sig
            )
            score += sig_similarity * 2.0

            # 成功率加权
            score *= pattern.success_rate

            if score > 0:
                candidates.append((score, pattern))

        # 排序并返回 top_k
        candidates.sort(key=lambda x: -x[0])
        return [p for _, p in candidates[:top_k]]

    def record_strategy_result(
        self,
        strategy_name: str,
        task_type: str,
        success: bool,
        improvement: float = 0.0,
    ) -> None:
        """记录策略效果"""
        key = f"{strategy_name}:{task_type}"

        if key not in self.strategies:
            self.strategies[key] = StrategyEffectiveness(
                strategy_name=strategy_name, task_type=task_type
            )

        strategy = self.strategies[key]
        strategy.attempts += 1
        if success:
            strategy.successes += 1

        # 更新平均提升
        strategy.avg_improvement = (
            strategy.avg_improvement * (strategy.attempts - 1) + improvement
        ) / strategy.attempts

        self._save_storage()

    def recommend_strategy(
        self, task_type: str, available_strategies: List[str]
    ) -> Tuple[str, float]:
        """
        推荐最佳策略

        Returns:
            (推荐策略名, 预期成功率)
        """
        best_strategy = None
        best_rate = 0.0

        for strategy_name in available_strategies:
            key = f"{strategy_name}:{task_type}"
            if key in self.strategies:
                rate = self.strategies[key].success_rate
                if rate > best_rate:
                    best_rate = rate
                    best_strategy = strategy_name

        # 如果没有历史数据，默认使用第一个
        if best_strategy is None:
            return available_strategies[0], 0.5

        return best_strategy, best_rate

    def generate_enhanced_prompt(
        self,
        task_type: str,
        base_prompt: str,
        error_history: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """
        基于历史经验生成增强提示词

        Args:
            task_type: 任务类型
            base_prompt: 基础提示词
            error_history: 历史错误记录

        Returns:
            增强后的提示词
        """
        enhancements = []

        # 添加相关模式的经验
        if error_history:
            for error in error_history:
                patterns = self.find_applicable_patterns(
                    task_type,
                    error.get("error_type", ""),
                    error.get("error_message", ""),
                    top_k=1,
                )

                for pattern in patterns:
                    if pattern.fix_description:
                        enhancements.append(
                            f"【经验】类似问题曾通过以下方式解决: {pattern.fix_description}"
                        )

        # 推荐策略
        recommended, rate = self.recommend_strategy(
            task_type, ["minimal_constraints", "strong_constraints", "with_examples"]
        )

        if rate > 0.7:
            enhancements.append(
                f"【建议】对此类任务使用 '{recommended}' 策略（历史成功率 {rate:.0%}）"
            )

        # 组合增强提示词
        if enhancements:
            enhanced = base_prompt + "\n\n" + "\n".join(enhancements)
            return enhanced

        return base_prompt

    def get_learning_summary(self) -> Dict[str, Any]:
        """获取学习摘要"""
        return {
            "total_patterns": len(self.patterns),
            "total_strategies": len(self.strategies),
            "pattern_types": self._count_by_field("task_type"),
            "error_types": self._count_by_field("error_type"),
            "top_patterns": sorted(
                [
                    (p.pattern_id, p.success_rate, p.usage_count)
                    for p in self.patterns.values()
                ],
                key=lambda x: -x[1],
            )[:5],
            "strategy_effectiveness": [
                {
                    "strategy": s.strategy_name,
                    "task": s.task_type,
                    "success_rate": s.success_rate,
                    "attempts": s.attempts,
                }
                for s in sorted(
                    self.strategies.values(), key=lambda x: -x.success_rate
                )[:5]
            ],
        }

    def _generate_signature(self, error_message: str, error_type: str) -> str:
        """生成错误签名"""
        # 简化错误信息，提取关键特征
        simplified = error_message.lower()
        # 移除具体数值
        simplified = " ".join(
            word for word in simplified.split() if not word.replace(".", "").isdigit()
        )
        # 取前100字符
        simplified = simplified[:100]
        return f"{error_type}:{simplified}"

    def _signature_similarity(self, sig1: str, sig2: str) -> float:
        """计算签名相似度（简单版本）"""
        words1 = set(sig1.split())
        words2 = set(sig2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _find_similar_pattern(
        self, task_type: str, error_signature: str
    ) -> Optional[FailurePattern]:
        """查找相似模式"""
        for pattern in self.patterns.values():
            if (
                pattern.task_type == task_type
                and self._signature_similarity(pattern.error_signature, error_signature)
                > 0.7
            ):
                return pattern
        return None

    def _count_by_field(self, field_name: str) -> Dict[str, int]:
        """按字段统计"""
        counts: Dict[str, int] = {}
        for pattern in self.patterns.values():
            value = getattr(pattern, field_name, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts

    def _load_storage(self) -> None:
        """从文件加载"""
        if not self.storage_path:
            return

        path = Path(self.storage_path)
        if not path.exists():
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for p_data in data.get("patterns", []):
                pattern = FailurePattern(**p_data)
                self.patterns[pattern.pattern_id] = pattern

            for s_data in data.get("strategies", []):
                strategy = StrategyEffectiveness(**s_data)
                key = f"{strategy.strategy_name}:{strategy.task_type}"
                self.strategies[key] = strategy

        except Exception as e:
            print(f"Warning: Failed to load meta-learning storage: {e}")

    def _save_storage(self) -> None:
        """保存到文件"""
        if not self.storage_path:
            return

        try:
            data = {
                "patterns": [asdict(p) for p in self.patterns.values()],
                "strategies": [asdict(s) for s in self.strategies.values()],
                "updated_at": datetime.now().isoformat(),
            }

            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Warning: Failed to save meta-learning storage: {e}")

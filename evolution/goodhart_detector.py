"""
Goodhart Detector 模块 - 检测代码进化中的作弊模式

Goodhart定律："当一个指标成为目标时，它就不再是一个好的指标"

在SEMDS代码进化中，这表现为：
- 高测试通过率（通过硬编码/作弊手段）
- 低行为一致性（无法正确处理边界情况）

本模块检测这种"高通过率+低一致性"的Goodhart现象。
"""

from dataclasses import dataclass


@dataclass
class GoodhartDetectionResult:
    """Goodhart检测结果

    Attributes:
        is_goodhart: 是否检测到Goodhart现象
        confidence: 置信度 (0-1)
        reason: 检测原因说明
    """

    is_goodhart: bool
    confidence: float
    reason: str = ""


class GoodhartDetector:
    """Goodhart现象检测器

    检测高通过率+低一致性的作弊模式。

    默认阈值：
    - pass_rate_threshold: 0.9 (通过率阈值)
    - consistency_threshold: 0.5 (一致性阈值)

    检测逻辑：
    - Goodhart = pass_rate >= threshold AND consistency < threshold

    Example:
        >>> detector = GoodhartDetector()
        >>> result = detector.detect(pass_rate=0.95, consistency_score=0.3)
        >>> if result.is_goodhart:
        ...     print(f"Warning: {result.reason}")
    """

    # 默认阈值
    DEFAULT_PASS_RATE_THRESHOLD = 0.9
    DEFAULT_CONSISTENCY_THRESHOLD = 0.5

    def __init__(
        self, pass_rate_threshold: float = None, consistency_threshold: float = None
    ):
        """初始化检测器

        Args:
            pass_rate_threshold: 通过率阈值，默认0.9
            consistency_threshold: 一致性阈值，默认0.5
        """
        self.pass_rate_threshold = (
            pass_rate_threshold
            if pass_rate_threshold is not None
            else self.DEFAULT_PASS_RATE_THRESHOLD
        )
        self.consistency_threshold = (
            consistency_threshold
            if consistency_threshold is not None
            else self.DEFAULT_CONSISTENCY_THRESHOLD
        )

    def detect(
        self, pass_rate: float, consistency_score: float
    ) -> GoodhartDetectionResult:
        """检测Goodhart现象

        Args:
            pass_rate: 测试通过率 (0-1)
            consistency_score: 行为一致性得分 (0-1)

        Returns:
            GoodhartDetectionResult: 检测结果
        """
        # 规范化输入（处理越界值）
        pass_rate = max(0.0, min(1.0, pass_rate))
        consistency_score = max(0.0, min(1.0, consistency_score))

        # 检测Goodhart：高通过率 + 低一致性
        is_goodhart = (
            pass_rate >= self.pass_rate_threshold
            and consistency_score < self.consistency_threshold
        )

        # 计算置信度
        confidence = self._calculate_confidence(
            pass_rate, consistency_score, is_goodhart
        )

        # 生成原因说明
        reason = self._generate_reason(
            pass_rate, consistency_score, is_goodhart, confidence
        )

        return GoodhartDetectionResult(
            is_goodhart=is_goodhart, confidence=confidence, reason=reason
        )

    def _calculate_confidence(
        self, pass_rate: float, consistency_score: float, is_goodhart: bool
    ) -> float:
        """计算检测置信度

        置信度基于：
        1. 通过率超出阈值的程度
        2. 一致性低于阈值的程度
        3. 两者之间的差距

        Args:
            pass_rate: 通过率
            consistency_score: 一致性得分
            is_goodhart: 是否检测到Goodhart

        Returns:
            置信度 (0-1)
        """
        if not is_goodhart:
            return 0.0

        # 通过率超出阈值的程度 (0-1)
        pass_excess = (pass_rate - self.pass_rate_threshold) / (
            1.0 - self.pass_rate_threshold
        )
        pass_excess = max(0.0, min(1.0, pass_excess))

        # 一致性低于阈值的程度 (0-1)
        consistency_deficit = (
            self.consistency_threshold - consistency_score
        ) / self.consistency_threshold
        consistency_deficit = max(0.0, min(1.0, consistency_deficit))

        # 综合差距 (pass_rate - consistency_score) / 最大可能差距
        gap = pass_rate - consistency_score
        max_possible_gap = 1.0 - 0.0  # 最大可能差距
        normalized_gap = gap / max_possible_gap

        # 加权综合：差距最重要，其次是通过率超出和一致性不足
        confidence = (
            0.5 * normalized_gap + 0.25 * pass_excess + 0.25 * consistency_deficit
        )

        return round(min(1.0, max(0.0, confidence)), 2)

    def _generate_reason(
        self,
        pass_rate: float,
        consistency_score: float,
        is_goodhart: bool,
        confidence: float,
    ) -> str:
        """生成检测原因说明

        Args:
            pass_rate: 通过率
            consistency_score: 一致性得分
            is_goodhart: 是否检测到Goodhart
            confidence: 置信度

        Returns:
            原因说明字符串
        """
        if not is_goodhart:
            return ""

        # 格式化百分比
        pass_pct = f"{pass_rate*100:.0f}%"
        consistency_pct = f"{consistency_score*100:.0f}%"

        # 构建原因
        if pass_rate == 1.0 and consistency_score == 0.0:
            return (
                f"Critical Goodhart detected: "
                f"Pass rate {pass_pct} (perfect) with "
                f"consistency {consistency_pct} (zero). "
                f"Likely hardcoded solutions."
            )

        # 判断严重程度
        if confidence >= 0.9:
            severity = "Critical"
        elif confidence >= 0.7:
            severity = "High"
        elif confidence >= 0.5:
            severity = "Moderate"
        else:
            severity = "Low"

        return (
            f"{severity} Goodhart detected: "
            f"Pass rate {pass_pct} (threshold {self.pass_rate_threshold*100:.0f}%) "
            f"but consistency {consistency_pct} "
            f"(threshold {self.consistency_threshold*100:.0f}%). "
            f"Confidence {confidence*100:.0f}%."
        )

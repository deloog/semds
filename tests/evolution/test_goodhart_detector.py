"""
Goodhart Detector 测试模块 - TDD Red Phase

测试 GoodhartDetector 类 - 检测高通过率+低一致性的作弊模式

Goodhart定律："当一个指标成为目标时，它就不再是一个好的指标"
在代码进化中，表现为高测试通过率但低行为一致性
"""

# Import will be added after implementation exists
# from evolution.goodhart_detector import GoodhartDetector, GoodhartDetectionResult


# =============================================================================
# Test GoodhartDetectionResult Dataclass
# =============================================================================


class TestGoodhartDetectionResult:
    """GoodhartDetectionResult 数据类测试"""

    def test_result_has_flag_field(self):
        """测试结果包含检测标志字段"""
        from evolution.goodhart_detector import GoodhartDetectionResult

        result = GoodhartDetectionResult(
            is_goodhart=True,
            confidence=0.85,
            reason="High pass rate but low consistency",
        )
        assert result.is_goodhart is True

    def test_result_has_confidence_field(self):
        """测试结果包含置信度字段"""
        from evolution.goodhart_detector import GoodhartDetectionResult

        result = GoodhartDetectionResult(
            is_goodhart=False, confidence=0.92, reason="No Goodhart detected"
        )
        assert result.confidence == 0.92

    def test_result_has_reason_field(self):
        """测试结果包含原因字段"""
        from evolution.goodhart_detector import GoodhartDetectionResult

        result = GoodhartDetectionResult(
            is_goodhart=True,
            confidence=0.75,
            reason="Pass rate 0.95 with consistency 0.2",
        )
        assert "Pass rate" in result.reason

    def test_result_allows_empty_reason_when_no_goodhart(self):
        """测试无Goodhart时原因可为空"""
        from evolution.goodhart_detector import GoodhartDetectionResult

        result = GoodhartDetectionResult(is_goodhart=False, confidence=1.0, reason="")
        assert result.reason == ""


# =============================================================================
# Test GoodhartDetector - Basic Detection
# =============================================================================


class TestGoodhartDetectorBasicDetection:
    """基本检测逻辑测试（P0优先级）"""

    def test_detects_goodhart_when_high_pass_low_consistency(self):
        """测试高通过率+低一致性触发Goodhart检测"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.95, consistency_score=0.3)

        assert result.is_goodhart is True
        assert result.confidence > 0.5

    def test_no_goodhart_when_both_high(self):
        """测试双高不触发Goodhart"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.95, consistency_score=0.85)

        assert result.is_goodhart is False

    def test_no_goodhart_when_both_low(self):
        """测试双低不触发Goodhart"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.3, consistency_score=0.2)

        assert result.is_goodhart is False

    def test_no_goodhart_when_low_pass_high_consistency(self):
        """测试低通过+高一致不触发Goodhart"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.4, consistency_score=0.9)

        assert result.is_goodhart is False

    def test_extreme_goodhart_case(self):
        """测试极端Goodhart情况（完美通过+零一致）"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=1.0, consistency_score=0.0)

        assert result.is_goodhart is True
        assert result.confidence >= 0.9


# =============================================================================
# Test GoodhartDetector - Thresholds
# =============================================================================


class TestGoodhartDetectorThresholds:
    """阈值测试（P0优先级）"""

    def test_pass_rate_threshold_boundary(self):
        """测试通过率阈值边界"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()

        # 刚好在阈值上（默认0.9）
        result = detector.detect(pass_rate=0.9, consistency_score=0.3)
        # 边界情况应该触发（>=阈值）
        assert result.is_goodhart is True

    def test_consistency_threshold_boundary(self):
        """测试一致性阈值边界"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()

        # 刚好在阈值上（默认0.5）
        result = detector.detect(pass_rate=0.95, consistency_score=0.5)
        # 边界情况应该不触发（>=阈值表示足够好）
        assert result.is_goodhart is False

    def test_below_pass_threshold_no_goodhart(self):
        """测试低于通过阈值不触发Goodhart"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.89, consistency_score=0.2)

        assert result.is_goodhart is False

    def test_above_consistency_threshold_no_goodhart(self):
        """测试高于一致阈值不触发Goodhart"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.95, consistency_score=0.51)

        assert result.is_goodhart is False


# =============================================================================
# Test GoodhartDetector - Confidence Calculation
# =============================================================================


class TestGoodhartDetectorConfidence:
    """置信度计算测试（P1优先级）"""

    def test_confidence_increases_with_gap(self):
        """测试差距越大置信度越高"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()

        result_small_gap = detector.detect(pass_rate=0.9, consistency_score=0.4)
        result_large_gap = detector.detect(pass_rate=0.99, consistency_score=0.1)

        assert result_large_gap.confidence > result_small_gap.confidence

    def test_confidence_is_zero_when_no_goodhart(self):
        """测试无Goodhart时置信度为0"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.5, consistency_score=0.5)

        assert result.confidence == 0.0

    def test_confidence_bounded_between_0_and_1(self):
        """测试置信度在0-1之间"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()

        test_cases = [
            (0.95, 0.3),
            (0.99, 0.1),
            (0.91, 0.49),
        ]

        for pass_rate, consistency in test_cases:
            result = detector.detect(pass_rate, consistency)
            assert 0.0 <= result.confidence <= 1.0

    def test_maximum_confidence_at_extreme_gap(self):
        """测试极端差距时置信度最大"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=1.0, consistency_score=0.0)

        assert result.confidence == 1.0


# =============================================================================
# Test GoodhartDetector - Reason Generation
# =============================================================================


class TestGoodhartDetectorReason:
    """原因生成测试（P1优先级）"""

    def test_reason_includes_pass_rate(self):
        """测试原因包含通过率信息"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.95, consistency_score=0.3)

        assert "pass" in result.reason.lower() or "0.95" in result.reason

    def test_reason_includes_consistency(self):
        """测试原因包含一致性信息"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.95, consistency_score=0.3)

        assert "consistency" in result.reason.lower() or "0.3" in result.reason

    def test_reason_explains_goodhart(self):
        """测试原因解释Goodhart现象"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.95, consistency_score=0.3)

        assert result.is_goodhart is True
        assert len(result.reason) > 10  # 应该有足够详细的解释

    def test_no_reason_when_no_goodhart(self):
        """测试无Goodhart时原因可为简短说明"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.5, consistency_score=0.5)

        assert result.is_goodhart is False
        # 可以为空或简短说明
        assert isinstance(result.reason, str)


# =============================================================================
# Test GoodhartDetector - Custom Configuration
# =============================================================================


class TestGoodhartDetectorCustomConfig:
    """自定义配置测试（P1优先级）"""

    def test_custom_pass_rate_threshold(self):
        """测试自定义通过率阈值"""
        from evolution.goodhart_detector import GoodhartDetector

        # 设置更高的阈值
        detector = GoodhartDetector(pass_rate_threshold=0.95)

        result = detector.detect(pass_rate=0.94, consistency_score=0.3)
        assert result.is_goodhart is False  # 低于新阈值

        result = detector.detect(pass_rate=0.96, consistency_score=0.3)
        assert result.is_goodhart is True  # 高于新阈值

    def test_custom_consistency_threshold(self):
        """测试自定义一致性阈值"""
        from evolution.goodhart_detector import GoodhartDetector

        # 设置更高的一致性阈值
        detector = GoodhartDetector(consistency_threshold=0.7)

        result = detector.detect(pass_rate=0.95, consistency_score=0.6)
        assert result.is_goodhart is True  # 低于新阈值

        result = detector.detect(pass_rate=0.95, consistency_score=0.8)
        assert result.is_goodhart is False  # 高于新阈值

    def test_default_thresholds(self):
        """测试默认阈值"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()

        # 默认通过率阈值 0.9，一致性阈值 0.5
        assert detector.pass_rate_threshold == 0.9
        assert detector.consistency_threshold == 0.5


# =============================================================================
# Test GoodhartDetector - Edge Cases
# =============================================================================


class TestGoodhartDetectorEdgeCases:
    """边界情况测试"""

    def test_handles_zero_pass_rate(self):
        """测试处理零通过率"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.0, consistency_score=0.0)

        assert result.is_goodhart is False

    def test_handles_zero_consistency(self):
        """测试处理零一致性"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.95, consistency_score=0.0)

        assert result.is_goodhart is True

    def test_handles_perfect_scores(self):
        """测试处理完美分数"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=1.0, consistency_score=1.0)

        assert result.is_goodhart is False  # 双高不是Goodhart

    def test_handles_negative_scores_gracefully(self):
        """测试优雅处理负分数"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=-0.1, consistency_score=-0.5)

        # 应该处理为0或拒绝，不崩溃
        assert result.is_goodhart is False

    def test_handles_scores_above_one_gracefully(self):
        """测试优雅处理超1分数"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=1.5, consistency_score=0.3)

        # 应该处理为1或拒绝，不崩溃
        assert isinstance(result.is_goodhart, bool)

    def test_handles_very_small_gap(self):
        """测试处理极小差距"""
        from evolution.goodhart_detector import GoodhartDetector

        detector = GoodhartDetector()
        result = detector.detect(pass_rate=0.91, consistency_score=0.49)

        # 差距很小，置信度应该很低
        if result.is_goodhart:
            assert result.confidence < 0.5

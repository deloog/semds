"""测试HumanGateMonitor"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock


class TestReview:
    """审查记录模型测试"""
    
    def test_review_creation(self):
        """应能创建审查记录"""
        from factory.human_gate import Review
        
        review = Review(
            approved=True,
            duration_seconds=10.5,
            reviewed_at=datetime.now(timezone.utc),
            reviewer_id="user-123"
        )
        
        assert review.approved is True
        assert review.duration_seconds == 10.5
        assert review.reviewer_id == "user-123"
    
    def test_review_defaults(self):
        """审查记录应有正确的默认值"""
        from factory.human_gate import Review
        
        review = Review(approved=False, duration_seconds=5.0)
        
        assert review.reviewed_at is None
        assert review.reviewer_id is None


class TestApprovalRequest:
    """审批请求模型测试"""
    
    def test_approval_request_creation(self):
        """应能创建审批请求"""
        from factory.human_gate import ApprovalRequest
        
        request = ApprovalRequest(
            id="approval-123",
            task_id="task-123",
            generation_id="gen-456",
            code="def test(): pass",
            reason="需要审批",
            status="pending",
            created_at=datetime.now(timezone.utc)
        )
        
        assert request.id == "approval-123"
        assert request.status == "pending"
        assert request.reviewed_at is None


class TestHumanGateMonitorInit:
    """HumanGateMonitor初始化测试"""
    
    def test_monitor_initialization(self):
        """监控器应正确初始化"""
        from factory.human_gate import HumanGateMonitor
        
        monitor = HumanGateMonitor()
        
        assert monitor.reviews == []
        assert monitor.approval_rate_threshold == 0.98
        assert monitor.min_review_time_seconds == 5.0


class TestApprovalRateCalculation:
    """批准率计算测试"""
    
    def test_calculate_approval_rate_with_mixed_reviews(self):
        """应正确计算混合审查的批准率"""
        from factory.human_gate import HumanGateMonitor, Review
        
        monitor = HumanGateMonitor()
        reviews = [
            Review(approved=True, duration_seconds=10),
            Review(approved=True, duration_seconds=10),
            Review(approved=False, duration_seconds=10),
        ]
        
        approval_rate = monitor._calculate_approval_rate(reviews)
        
        assert approval_rate == 2 / 3
    
    def test_calculate_approval_rate_empty_list(self):
        """空列表应返回0.0"""
        from factory.human_gate import HumanGateMonitor
        
        monitor = HumanGateMonitor()
        approval_rate = monitor._calculate_approval_rate([])
        
        assert approval_rate == 0.0
    
    def test_calculate_approval_rate_all_approved(self):
        """全部批准应返回1.0"""
        from factory.human_gate import HumanGateMonitor, Review
        
        monitor = HumanGateMonitor()
        reviews = [Review(approved=True, duration_seconds=5) for _ in range(5)]
        
        approval_rate = monitor._calculate_approval_rate(reviews)
        
        assert approval_rate == 1.0
    
    def test_calculate_approval_rate_all_rejected(self):
        """全部拒绝应返回0.0"""
        from factory.human_gate import HumanGateMonitor, Review
        
        monitor = HumanGateMonitor()
        reviews = [Review(approved=False, duration_seconds=5) for _ in range(5)]
        
        approval_rate = monitor._calculate_approval_rate(reviews)
        
        assert approval_rate == 0.0


class TestAverageReviewTimeCalculation:
    """平均审查时间计算测试"""
    
    def test_calculate_avg_review_time(self):
        """应正确计算平均审查时间"""
        from factory.human_gate import HumanGateMonitor, Review
        
        monitor = HumanGateMonitor()
        reviews = [
            Review(approved=True, duration_seconds=10),
            Review(approved=True, duration_seconds=20),
            Review(approved=False, duration_seconds=30),
        ]
        
        avg_time = monitor._calculate_avg_review_time(reviews)
        
        assert avg_time == 20.0
    
    def test_calculate_avg_review_time_empty_list(self):
        """空列表应返回0.0"""
        from factory.human_gate import HumanGateMonitor
        
        monitor = HumanGateMonitor()
        avg_time = monitor._calculate_avg_review_time([])
        
        assert avg_time == 0.0


class TestCheckApprovalQuality:
    """审批质量检查测试"""
    
    def test_high_approval_rate_low_review_time_triggers_warning(self):
        """高批准率且低审查时间应触发警告"""
        from factory.human_gate import HumanGateMonitor, Review
        
        monitor = HumanGateMonitor()
        # 99%批准率，平均3秒审查时间
        reviews = [
            Review(approved=True, duration_seconds=3)
            for _ in range(99)
        ] + [Review(approved=False, duration_seconds=3)]
        
        result = monitor.check_approval_quality(reviews)
        
        assert result is False  # 质量检查未通过
    
    def test_normal_approval_rate_passes_check(self):
        """正常批准率应通过检查"""
        from factory.human_gate import HumanGateMonitor, Review
        
        monitor = HumanGateMonitor()
        reviews = [
            Review(approved=True, duration_seconds=10),
            Review(approved=False, duration_seconds=10),
        ]
        
        result = monitor.check_approval_quality(reviews)
        
        assert result is True  # 质量检查通过
    
    def test_insufficient_reviews_passes_check(self):
        """审查数量不足时应直接通过（不触发警告）"""
        from factory.human_gate import HumanGateMonitor, Review
        
        monitor = HumanGateMonitor()
        reviews = [Review(approved=True, duration_seconds=3) for _ in range(5)]
        
        result = monitor.check_approval_quality(reviews)
        
        assert result is True  # 数量不足，不触发警告
    
    def test_low_approval_rate_passes_check(self):
        """低批准率（即使审查快）也应通过检查"""
        from factory.human_gate import HumanGateMonitor, Review
        
        monitor = HumanGateMonitor()
        # 50%批准率，平均3秒审查时间
        reviews = [
            Review(approved=True, duration_seconds=3)
            for _ in range(25)
        ] + [
            Review(approved=False, duration_seconds=3)
            for _ in range(25)
        ]
        
        result = monitor.check_approval_quality(reviews)
        
        assert result is True  # 批准率不高，不触发警告


class TestRecordReview:
    """记录审查测试"""
    
    def test_record_review_adds_to_list(self):
        """记录审查应添加到列表"""
        from factory.human_gate import HumanGateMonitor
        
        monitor = HumanGateMonitor()
        
        monitor.record_review(approved=True, duration_seconds=10.5, reviewer_id="user-1")
        
        assert len(monitor.reviews) == 1
        assert monitor.reviews[0].approved is True
        assert monitor.reviews[0].duration_seconds == 10.5
        assert monitor.reviews[0].reviewer_id == "user-1"
    
    def test_record_multiple_reviews(self):
        """应能记录多个审查"""
        from factory.human_gate import HumanGateMonitor
        
        monitor = HumanGateMonitor()
        
        monitor.record_review(approved=True, duration_seconds=10)
        monitor.record_review(approved=False, duration_seconds=15)
        monitor.record_review(approved=True, duration_seconds=8)
        
        assert len(monitor.reviews) == 3


class TestHumanGatePersistence:
    """HumanGate数据持久化测试"""
    
    def test_monitor_has_max_reviews_limit(self):
        """应配置最大审查记录数限制"""
        from factory.human_gate import HumanGateMonitor
        
        monitor = HumanGateMonitor()
        
        # 验证有最大记录数限制属性
        assert hasattr(monitor, 'max_reviews')
        assert isinstance(monitor.max_reviews, int)
        assert monitor.max_reviews > 0
        assert monitor.max_reviews <= 10000  # 合理上限
    
    def test_record_review_limits_storage_size(self):
        """审查记录超过限制时应清理旧记录"""
        from factory.human_gate import HumanGateMonitor
        
        monitor = HumanGateMonitor(max_reviews=5)
        
        # 添加超过限制的记录
        for i in range(7):
            monitor.record_review(approved=True, duration_seconds=1.0, reviewer_id=f"reviewer-{i}")
        
        # 验证只保留最新的记录
        assert len(monitor.reviews) <= monitor.max_reviews


class TestAlertGeneration:
    """警告生成测试"""
    
    def test_generate_alert_message(self):
        """应生成警告消息"""
        from factory.human_gate import HumanGateMonitor
        
        monitor = HumanGateMonitor()
        
        alert = monitor.generate_alert(
            approval_rate=0.99,
            avg_review_time=3.0
        )
        
        assert "警告" in alert or "alert" in alert.lower()
        assert "0.99" in alert or "99" in alert
        assert "3.0" in alert or "3" in alert

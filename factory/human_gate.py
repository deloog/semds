"""Human Gate Module

Provides approval quality monitoring and review record management.
Corresponds to SEMDS_v1.1_SPEC.md Section 4.7 Human Gate.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

__all__ = ["Review", "ApprovalRequest", "HumanGateMonitor"]


@dataclass
class Review:
    """Review record"""
    approved: bool
    duration_seconds: float
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None


@dataclass
class ApprovalRequest:
    """Approval request"""
    id: str
    task_id: str
    generation_id: str
    code: str
    reason: str
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_comment: Optional[str] = None


class HumanGateMonitor:
    """Human gate monitor for approval quality
    
    Monitors review quality and manages review records with automatic
    cleanup to prevent memory overflow.
    """
    
    DEFAULT_MAX_REVIEWS = 1000  # 默认最大审查记录数
    
    def __init__(self, max_reviews: int = DEFAULT_MAX_REVIEWS):
        """Initialize the monitor
        
        Args:
            max_reviews: Maximum number of review records to keep in memory.
                        Older records are automatically removed when limit is reached.
        """
        self.reviews: List[Review] = []
        self.approval_rate_threshold = 0.98
        self.min_review_time_seconds = 5.0
        self.min_reviews_for_check = 10
        self.max_reviews = max_reviews
    
    def _calculate_approval_rate(self, reviews: List[Review]) -> float:
        """Calculate approval rate"""
        if not reviews:
            return 0.0
        approved_count = sum(1 for r in reviews if r.approved)
        return approved_count / len(reviews)
    
    def _calculate_avg_review_time(self, reviews: List[Review]) -> float:
        """Calculate average review time"""
        if not reviews:
            return 0.0
        return sum(r.duration_seconds for r in reviews) / len(reviews)
    
    def check_approval_quality(self, reviews: List[Review]) -> bool:
        """
        Check approval quality
        
        Returns:
            True: Quality is good
            False: Quality degraded (trigger warning)
        """
        if len(reviews) < self.min_reviews_for_check:
            return True
        
        approval_rate = self._calculate_approval_rate(reviews)
        avg_review_time = self._calculate_avg_review_time(reviews)
        
        # High approval rate + low review time = quality degradation
        if approval_rate > self.approval_rate_threshold and avg_review_time < self.min_review_time_seconds:
            return False
        
        return True
    
    def record_review(self, approved: bool, duration_seconds: float, reviewer_id: Optional[str] = None) -> None:
        """Record a review
        
        Automatically removes oldest records when max_reviews limit is reached
        to prevent memory overflow.
        """
        review = Review(
            approved=approved,
            duration_seconds=duration_seconds,
            reviewed_at=datetime.now(timezone.utc),
            reviewer_id=reviewer_id
        )
        self.reviews.append(review)
        
        # 限制记录数量，防止内存溢出
        if len(self.reviews) > self.max_reviews:
            # 移除最旧的记录（假设列表按时间顺序，移除前部）
            excess = len(self.reviews) - self.max_reviews
            self.reviews = self.reviews[excess:]
    
    def generate_alert(self, approval_rate: float, avg_review_time: float) -> str:
        """Generate alert message"""
        return f"Alert: Review quality degradation detected. Approval rate: {approval_rate:.1%}, Average review time: {avg_review_time:.1f}s. Please review carefully."

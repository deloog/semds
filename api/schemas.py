"""Pydantic数据模型定义

定义所有API请求和响应的数据模型，用于数据验证和序列化。
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

__all__ = [
    "TaskStatus",
    "TaskCreate",
    "TaskResponse",
    "EvolutionStart",
    "EvolutionControl",
    "GenerationResponse",
    "EvolutionProgress",
    "SystemStats",
    "ApprovalResponse",
    "ApprovalCreate",
    "ApprovalReview",
]


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"


class TaskCreate(BaseModel):
    """创建任务请求模型"""

    name: str = Field(..., min_length=1, max_length=100, description="任务名称")
    description: str = Field(..., description="任务描述")
    target_function_signature: str = Field(..., description="目标函数签名")
    test_code: str = Field(
        ...,
        min_length=1,
        max_length=50000,  # 限制最大50KB，防止DoS
        description="测试代码内容",
    )
    success_criteria: Optional[Dict] = Field(
        default_factory=dict, description="成功标准"
    )
    max_generations: int = Field(default=50, ge=1, le=1000, description="最大进化代数")


class TaskResponse(BaseModel):
    """任务响应模型"""

    id: str = Field(..., description="任务ID")
    name: str = Field(..., description="任务名称")
    description: str = Field(..., description="任务描述")
    status: TaskStatus = Field(..., description="任务状态")
    current_generation: int = Field(..., description="当前代数")
    best_score: float = Field(..., description="最佳得分")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = {"from_attributes": True}


class EvolutionStart(BaseModel):
    """启动进化请求模型"""

    task_id: str = Field(..., description="任务ID")


class EvolutionControl(BaseModel):
    """进化控制请求模型"""

    task_id: str = Field(..., description="任务ID")


class GenerationResponse(BaseModel):
    """进化代响应模型"""

    id: str = Field(..., description="进化代ID")
    gen_number: int = Field(..., description="代数编号")
    intrinsic_score: float = Field(..., description="内生评分（测试通过率）")
    extrinsic_score: float = Field(..., description="外生评分（一致性验证）")
    final_score: float = Field(..., description="综合评分")
    goodhart_flag: bool = Field(..., description="是否触发Goodhart检测")
    created_at: datetime = Field(..., description="创建时间")

    model_config = {"from_attributes": True}


class EvolutionProgress(BaseModel):
    """进化进度模型"""

    task_id: str = Field(..., description="任务ID")
    current_gen: int = Field(..., description="当前代数")
    max_gen: int = Field(..., description="最大代数")
    current_score: float = Field(..., description="当前得分")
    best_score: float = Field(..., description="最佳得分")
    best_gen: int = Field(..., description="最佳代数")
    status: TaskStatus = Field(..., description="任务状态")
    recent_generations: List[GenerationResponse] = Field(
        default_factory=list, description="最近进化代"
    )


class SystemStats(BaseModel):
    """系统统计模型"""

    total_tasks: int = Field(..., description="总任务数")
    active_tasks: int = Field(..., description="活跃任务数")
    completed_tasks: int = Field(..., description="已完成任务数")
    total_generations: int = Field(..., description="总进化代数")


class ApprovalResponse(BaseModel):
    """审批响应模型"""

    id: str = Field(..., description="审批ID")
    task_id: str = Field(..., description="任务ID")
    generation_id: str = Field(..., description="进化代ID")
    status: str = Field(..., description="审批状态: pending/approved/rejected")
    created_at: datetime = Field(..., description="创建时间")
    reviewed_at: Optional[datetime] = Field(None, description="审核时间")
    reviewer_comment: Optional[str] = Field(None, description="审核意见")

    model_config = {"from_attributes": True}


class ApprovalCreate(BaseModel):
    """创建审批请求模型"""

    task_id: str = Field(..., description="任务ID")
    generation_id: str = Field(..., description="进化代ID")
    code: str = Field(..., description="代码内容")
    reason: str = Field(..., description="审批原因")


class ApprovalReview(BaseModel):
    """审批审核请求模型"""

    approved: bool = Field(..., description="是否批准")
    comment: Optional[str] = Field(None, description="审核意见")

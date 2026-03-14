"""审批API路由

处理人工审批相关的请求，包括：
- 获取待审批列表
- 提交审批请求
- 批准/拒绝请求

Phase 5更新: 添加了用户权限验证
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from api.auth.dependencies import get_current_user
from api.auth.models import User
from api.auth.permissions import ApprovalPermission
from api.auth.decorators import check_permission
from api.schemas import ApprovalCreate, ApprovalResponse, ApprovalReview

router = APIRouter(prefix="/approvals", tags=["approvals"])


def verify_approval_permission(user: User) -> bool:
    """验证用户是否有审批权限

    使用T5/T6标准权限模块进行检查。
    保留此函数以保持向后兼容。

    Args:
        user: 当前用户

    Returns:
        True如果有权限
    """
    try:
        check_permission(user, ApprovalPermission.READ)
        return True
    except HTTPException:
        return False


def require_approval_read(user: User = Depends(get_current_user)) -> User:
    """要求审批读取权限

    FastAPI依赖函数，用于保护审批查询端点。
    使用T5/T6标准权限模块进行权限检查。
    可被测试覆盖。

    Args:
        user: 当前用户

    Returns:
        用户对象如果有权限

    Raises:
        HTTPException: 403如果没有权限
    """
    check_permission(user, ApprovalPermission.READ)
    return user


def require_approval_approve(user: User = Depends(get_current_user)) -> User:
    """要求审批批准权限

    FastAPI依赖函数，用于保护审批批准端点。
    使用T5/T6标准权限模块进行权限检查。
    可被测试覆盖。

    Args:
        user: 当前用户

    Returns:
        用户对象如果有权限

    Raises:
        HTTPException: 403如果没有权限
    """
    check_permission(user, ApprovalPermission.APPROVE)
    return user


def require_approval_reject(user: User = Depends(get_current_user)) -> User:
    """要求审批拒绝权限

    FastAPI依赖函数，用于保护审批拒绝端点。
    使用T5/T6标准权限模块进行权限检查。
    可被测试覆盖。

    Args:
        user: 当前用户

    Returns:
        用户对象如果有权限

    Raises:
        HTTPException: 403如果没有权限
    """
    check_permission(user, ApprovalPermission.REJECT)
    return user


# 向后兼容别名
require_approval_permission = require_approval_read


# 审批状态机定义
# key: 当前状态, value: 允许流转到的状态集合
VALID_STATUS_TRANSITIONS = {
    "pending": {"approved", "rejected"},
    "approved": set(),  # 终态，不可再流转
    "rejected": set(),  # 终态，不可再流转
}


def validate_status_transition(current_status: str, new_status: str) -> bool:
    """验证状态流转是否合法

    Args:
        current_status: 当前状态
        new_status: 目标状态

    Returns:
        True如果流转合法，False否则
    """
    allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, set())
    return new_status in allowed_transitions


@router.get("/pending", response_model=List[ApprovalResponse])
async def list_pending_approvals(
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_approval_read),
) -> List[ApprovalResponse]:
    """获取待审批列表

    返回所有状态为pending的审批请求。

    Args:
        db: 数据库会话
        current_user: 当前用户（自动注入，需审批权限）
    """
    from storage.models import ApprovalRequest

    approvals = (
        db.query(ApprovalRequest)
        .filter(ApprovalRequest.status == "pending")
        .order_by(ApprovalRequest.created_at.desc())
        .all()
    )

    return [
        ApprovalResponse(
            id=approval.id,
            task_id=approval.task_id,
            generation_id=approval.generation_id,
            status=approval.status,
            created_at=approval.created_at,
            reviewed_at=approval.reviewed_at,
            reviewer_comment=approval.reviewer_comment,
        )
        for approval in approvals
    ]


@router.post("/", response_model=ApprovalResponse, status_code=status.HTTP_201_CREATED)
async def create_approval_request(
    request: ApprovalCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ApprovalResponse:
    """创建审批请求

    当代码触发Goodhart检测或其他需要人工确认的场景时，
    创建审批请求等待人工审核。

    Args:
        request: 审批请求数据
        db: 数据库会话
        current_user: 当前用户（自动注入）
    """
    from storage.models import ApprovalRequest

    approval = ApprovalRequest(
        task_id=request.task_id,
        generation_id=request.generation_id,
        code=request.code,
        reason=request.reason,
        status="pending",
    )

    db.add(approval)
    db.commit()
    db.refresh(approval)

    return ApprovalResponse(
        id=approval.id,
        task_id=approval.task_id,
        generation_id=approval.generation_id,
        status=approval.status,
        created_at=approval.created_at,
        reviewed_at=approval.reviewed_at,
        reviewer_comment=approval.reviewer_comment,
    )


@router.post("/{approval_id}/approve", response_model=dict)
async def approve_request(
    approval_id: str,
    review: ApprovalReview,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_approval_approve),
) -> dict:
    """批准请求

    审核通过，更新审批状态为approved。

    Args:
        approval_id: 审批请求ID
        review: 审批意见
        db: 数据库会话
        current_user: 当前用户（自动注入，需审批权限）

    Raises:
        HTTPException: 404如果审批请求不存在，400如果状态流转不合法，403如果无权限
    """
    from storage.models import ApprovalRequest

    approval = (
        db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    )

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found"
        )

    # 验证状态流转
    if not validate_status_transition(approval.status, "approved"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve from '{approval.status}' status. "
            f"Allowed transitions from '{approval.status}': "
            f"{VALID_STATUS_TRANSITIONS.get(approval.status, set())}",
        )

    approval.status = "approved"
    approval.reviewed_at = datetime.now(timezone.utc)
    approval.reviewer_comment = review.comment

    db.commit()

    return {
        "message": "Approval request approved",
        "id": approval_id,
        "comment": review.comment,
    }


@router.post("/{approval_id}/reject", response_model=dict)
async def reject_request(
    approval_id: str,
    review: ApprovalReview,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(require_approval_reject),
) -> dict:
    """拒绝请求

    审核不通过，更新审批状态为rejected。

    Args:
        approval_id: 审批请求ID
        review: 审批意见（建议填写拒绝原因）
        db: 数据库会话
        current_user: 当前用户（自动注入，需审批权限）

    Raises:
        HTTPException: 404如果审批请求不存在，400如果状态流转不合法，403如果无权限
    """
    from storage.models import ApprovalRequest

    approval = (
        db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    )

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found"
        )

    # 验证状态流转
    if not validate_status_transition(approval.status, "rejected"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reject from '{approval.status}' status. "
            f"Allowed transitions from '{approval.status}': "
            f"{VALID_STATUS_TRANSITIONS.get(approval.status, set())}",
        )

    approval.status = "rejected"
    approval.reviewed_at = datetime.now(timezone.utc)
    approval.reviewer_comment = review.comment

    db.commit()

    return {
        "message": "Approval request rejected",
        "id": approval_id,
        "comment": review.comment,
    }


@router.get("/{approval_id}", response_model=ApprovalResponse)
async def get_approval(
    approval_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ApprovalResponse:
    """获取单个审批请求详情

    Args:
        approval_id: 审批请求ID
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        审批请求详情

    Raises:
        HTTPException: 404如果不存在
    """
    from storage.models import ApprovalRequest

    approval = (
        db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    )

    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found"
        )

    return ApprovalResponse(
        id=approval.id,
        task_id=approval.task_id,
        generation_id=approval.generation_id,
        status=approval.status,
        created_at=approval.created_at,
        reviewed_at=approval.reviewed_at,
        reviewer_comment=approval.reviewer_comment,
    )

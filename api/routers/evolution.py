"""进化控制路由

提供进化控制操作：启动、暂停、恢复、中止。

Phase 5: 已添加用户认证和权限控制
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from api.auth.dependencies import get_current_user
from api.auth.models import User
from api.schemas import TaskStatus
from api.state import active_evolutions
from api.routers.tasks import require_task_access
from storage.models import Task

router = APIRouter()


def _get_task_or_404(db: Session, task_id: str) -> Task:
    """获取任务，不存在时抛出404"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)
    return task

# 错误消息常量
ERROR_TASK_NOT_FOUND = "任务不存在"
ERROR_EVOLUTION_ALREADY_RUNNING = "进化已在运行"
ERROR_EVOLUTION_NOT_RUNNING = "进化未运行"
ERROR_INVALID_STATE_TRANSITION = "无效的状态转换"
ERROR_CANNOT_RESUME = "无法从 {current_status} 状态恢复进化"
MESSAGE_EVOLUTION_STARTED = "进化已启动"
MESSAGE_EVOLUTION_PAUSED = "进化已暂停"
MESSAGE_EVOLUTION_RESUMED = "进化已恢复"
MESSAGE_EVOLUTION_ABORTED = "进化已中止"

# 允许恢复进化的状态
ALLOWED_RESUME_STATES = {TaskStatus.PAUSED, TaskStatus.FAILED}


@router.post("/{task_id}/start")
async def start_evolution(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """启动进化
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户（自动注入）
    
    Returns:
        启动成功消息
    
    Raises:
        HTTPException: 任务不存在、无权限或已在运行时
    """
    task = _get_task_or_404(db, task_id)
    
    # 验证任务访问权限
    require_task_access(task, current_user)
    
    if task.status == TaskStatus.RUNNING or task_id in active_evolutions:
        raise HTTPException(status_code=400, detail=ERROR_EVOLUTION_ALREADY_RUNNING)
    
    # 标记为活跃进化（使用Dict存储以便存储更多信息）
    active_evolutions[task_id] = {
        "status": "running",
        "started_at": None,  # TODO: 添加时间戳
    }
    
    # 更新任务状态
    task.status = TaskStatus.RUNNING
    db.commit()
    
    return {
        "message": MESSAGE_EVOLUTION_STARTED,
        "task_id": task_id
    }


@router.post("/{task_id}/pause")
async def pause_evolution(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """暂停进化
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户（自动注入）
    
    Returns:
        暂停成功消息
    
    Raises:
        HTTPException: 任务不存在、无权限或未在运行时
    """
    task = _get_task_or_404(db, task_id)
    
    # 验证任务访问权限
    require_task_access(task, current_user)
    
    if task.status != TaskStatus.RUNNING:
        raise HTTPException(status_code=400, detail=ERROR_EVOLUTION_NOT_RUNNING)
    
    # 更新任务状态
    task.status = TaskStatus.PAUSED
    db.commit()
    
    return {"message": MESSAGE_EVOLUTION_PAUSED}


@router.post("/{task_id}/resume")
async def resume_evolution(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """恢复进化
    
    只能从 PAUSED 或 FAILED 状态恢复。
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户（自动注入）
    
    Returns:
        恢复成功消息
    
    Raises:
        HTTPException: 任务不存在、无权限或状态不允许恢复时
    """
    task = _get_task_or_404(db, task_id)
    
    # 验证任务访问权限
    require_task_access(task, current_user)
    
    # 验证当前状态允许恢复
    if task.status not in ALLOWED_RESUME_STATES:
        raise HTTPException(
            status_code=400,
            detail=ERROR_CANNOT_RESUME.format(current_status=task.status)
        )
    
    # 更新任务状态
    task.status = TaskStatus.RUNNING
    db.commit()
    
    return {"message": MESSAGE_EVOLUTION_RESUMED}


@router.post("/{task_id}/abort")
async def abort_evolution(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """中止进化
    
    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户（自动注入）
    
    Returns:
        中止成功消息
    
    Raises:
        HTTPException: 任务不存在或无权限时
    """
    task = _get_task_or_404(db, task_id)
    
    # 验证任务访问权限
    require_task_access(task, current_user)
    
    # 从活跃集合移除
    if task_id in active_evolutions:
        del active_evolutions[task_id]
    
    # 更新任务状态
    task.status = TaskStatus.ABORTED
    db.commit()
    
    return {"message": MESSAGE_EVOLUTION_ABORTED}

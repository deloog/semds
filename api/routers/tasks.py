"""任务管理路由

提供任务CRUD操作：创建、查询、删除任务，以及进化历史查询。

Phase 5更新: 添加了用户认证和任务所有权验证
"""

import re
import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.auth.decorators import check_permission
from api.auth.dependencies import get_current_user
from api.auth.models import User, UserRole
from api.auth.permissions import TaskPermission
from api.dependencies import get_db_session
from api.schemas import GenerationResponse, TaskCreate, TaskResponse, TaskStatus
from storage.models import Generation, Task

router = APIRouter()


def verify_task_ownership(task: Task, current_user: User) -> bool:
    """验证任务所有权

    Args:
        task: 任务对象
        current_user: 当前用户

    Returns:
        True如果是任务所有者或管理员，False否则
    """
    # 管理员可以访问所有任务
    if current_user.role == UserRole.ADMIN:
        return True

    # 检查任务是否属于当前用户
    # TODO(P5+): 实际应从数据库查询任务的user_id字段
    # 当前简化处理：假设任务有owner_id属性
    task_owner_id = getattr(task, "owner_id", None)
    if task_owner_id is None:
        # 如果没有设置owner，允许访问（向后兼容）
        return True

    return task_owner_id == current_user.id


def require_task_access(
    task: Task, current_user: User, permission: TaskPermission = TaskPermission.READ
):
    """要求任务访问权限

    两层权限验证：
    1. 权限检查：用户是否有该操作的权限（基于T5/T6）
    2. 所有权检查：用户是否拥有该任务（基于ownership）

    Args:
        task: 任务对象
        current_user: 当前用户
        permission: 要求的权限，默认为READ

    Raises:
        HTTPException: 403如果没有权限
    """
    # 第一层：权限检查（使用T5/T6标准模块）
    check_permission(current_user, permission)

    # 第二层：所有权检查（保留原有逻辑）
    if not verify_task_ownership(task, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="没有权限访问此任务"
        )


def sanitize_filename(name: str) -> str:
    """
    清理文件名，防止路径遍历攻击。

    移除路径分隔符和特殊字符，防止 ../../../etc/passwd 类型的攻击。

    Args:
        name: 原始文件名/任务名

    Returns:
        清理后的安全文件名
    """
    # 移除Windows和Unix的路径分隔符及特殊字符
    name = re.sub(r'[\\/<>:"|?*]', "_", name)
    # 防止 .. 遍历
    name = name.replace("..", "_")
    # 限制长度，防止路径过长
    return name.strip()[:100]


# 错误消息常量
ERROR_TASK_NOT_FOUND = "任务不存在"
ERROR_GENERATION_NOT_FOUND = "进化代不存在"
MESSAGE_TASK_DELETED = "任务已删除"
MESSAGE_ROLLBACK_SUCCESS = "已回滚到第 {gen_number} 代"


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """创建新任务

    Args:
        task: 任务创建数据
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        创建的任务对象
    """
    # 清理任务名，防止路径遍历
    safe_name = sanitize_filename(task.name)

    db_task = Task(
        id=str(uuid.uuid4()),
        name=task.name,
        description=task.description,
        target_function_signature=task.target_function_signature,
        test_file_path=f"experiments/{safe_name}/tests/test_solution.py",
        status=TaskStatus.PENDING,
        current_generation=0,
        best_score=0.0,
        owner_id=current_user.id,  # 设置任务所有者
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: TaskStatus = None,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """列出用户的任务

    普通用户只能看到自己的任务，管理员可以看到所有任务。

    Args:
        status: 可选的状态过滤条件
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        任务列表
    """
    query = db.query(Task)

    # 非管理员只能看到自己的任务
    if current_user.role != UserRole.ADMIN:
        query = query.filter(Task.owner_id == current_user.id)

    if status:
        query = query.filter(Task.status == status)
    return query.all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """获取任务详情

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        任务详情

    Raises:
        HTTPException: 任务不存在或无权限时返回404/403
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    # 验证任务访问权限
    require_task_access(task, current_user)

    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """删除任务

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        删除成功消息

    Raises:
        HTTPException: 任务不存在或无权限时返回404/403
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)

    # 验证任务访问权限（需要DELETE权限）
    require_task_access(task, current_user, TaskPermission.DELETE)

    db.delete(task)
    db.commit()
    return {"message": MESSAGE_TASK_DELETED}


# 分页限制常量
MAX_LIMIT = 1000


@router.get("/{task_id}/generations", response_model=List[GenerationResponse])
async def get_task_generations(
    task_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """获取进化历史

    Args:
        task_id: 任务ID
        skip: 跳过的记录数
        limit: 返回的最大记录数（最大1000）
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        进化代列表

    Raises:
        HTTPException: 任务不存在或无权限时返回404/403
    """
    # 验证任务存在和权限
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)
    require_task_access(task, current_user)

    # 限制最大返回数量，防止DoS
    effective_limit = min(limit, MAX_LIMIT)

    generations = (
        db.query(Generation)
        .filter(Generation.task_id == task_id)
        .order_by(Generation.gen_number)
        .offset(skip)
        .limit(effective_limit)
        .all()
    )

    return generations


@router.get("/{task_id}/generations/{gen_id}", response_model=GenerationResponse)
async def get_generation_detail(
    task_id: str,
    gen_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """获取单代详情

    Args:
        task_id: 任务ID
        gen_id: 进化代ID
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        进化代详情

    Raises:
        HTTPException: 进化代不存在或无权限时返回404/403
    """
    # 验证任务存在和权限
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)
    require_task_access(task, current_user)

    gen = (
        db.query(Generation)
        .filter(Generation.task_id == task_id, Generation.id == gen_id)
        .first()
    )

    if not gen:
        raise HTTPException(status_code=404, detail=ERROR_GENERATION_NOT_FOUND)

    return gen


@router.get("/{task_id}/best")
async def get_best_solution(
    task_id: str,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """获取最佳实现

    Args:
        task_id: 任务ID
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        最佳实现代码和得分

    Raises:
        HTTPException: 无最佳实现或无权限时返回404/403
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.best_generation_id:
        raise HTTPException(status_code=404, detail="无最佳实现")

    # 验证任务访问权限
    require_task_access(task, current_user)

    gen = db.query(Generation).filter(Generation.id == task.best_generation_id).first()

    return {"generation": gen.gen_number, "score": gen.final_score, "code": gen.code}


@router.post("/{task_id}/rollback/{gen_number}")
async def rollback_to_generation(
    task_id: str,
    gen_number: int,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """回滚到指定代

    Args:
        task_id: 任务ID
        gen_number: 进化代编号
        db: 数据库会话
        current_user: 当前用户（自动注入）

    Returns:
        回滚成功消息

    Raises:
        HTTPException: 进化代不存在或无权限时返回404/403
    """
    # 验证任务存在和权限
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail=ERROR_TASK_NOT_FOUND)
    require_task_access(task, current_user)

    gen = (
        db.query(Generation)
        .filter(Generation.task_id == task_id, Generation.gen_number == gen_number)
        .first()
    )

    if not gen:
        raise HTTPException(status_code=404, detail=ERROR_GENERATION_NOT_FOUND)

    # TODO: 实现Git回滚

    return {"message": MESSAGE_ROLLBACK_SUCCESS.format(gen_number=gen_number)}


# ============== 批量操作 API ==============

import logging
from typing import Callable, Dict, List, Set, Tuple

from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)


class BatchTaskCreate(BaseModel):
    """批量创建任务请求"""

    tasks: List[TaskCreate]


class BatchTaskIds(BaseModel):
    """批量任务ID请求"""

    task_ids: List[str]


class BatchOperationResult(TypedDict):
    """批量操作结果类型"""

    successful: List[str]
    failed: List[Dict[str, str]]


class BatchPauseResult(TypedDict):
    """批量暂停结果类型"""

    paused: List[str]
    failed: List[Dict[str, str]]


class BatchResumeResult(TypedDict):
    """批量恢复结果类型"""

    resumed: List[str]
    failed: List[Dict[str, str]]


class BatchAbortResult(TypedDict):
    """批量中止结果类型"""

    aborted: List[str]
    failed: List[Dict[str, str]]


class BatchDeleteResult(TypedDict):
    """批量删除结果类型"""

    deleted: List[str]
    failed: List[Dict[str, str]]


MAX_BATCH_SIZE = 100  # 批量操作最大数量限制


def _validate_batch_ids(task_ids: List[str], max_size: int = MAX_BATCH_SIZE) -> None:
    """验证批量任务ID列表

    Args:
        task_ids: 任务ID列表
        max_size: 最大允许数量

    Raises:
        HTTPException: 列表为空或超过限制
    """
    if not task_ids:
        raise HTTPException(status_code=400, detail="Task ID list cannot be empty")

    if len(task_ids) > max_size:
        raise HTTPException(
            status_code=400, detail=f"Batch size exceeds maximum limit of {max_size}"
        )

    # 检查空字符串ID
    for task_id in task_ids:
        if not task_id or not task_id.strip():
            raise HTTPException(status_code=400, detail="Task ID cannot be empty")


def _fetch_tasks_by_ids(db: Session, task_ids: List[str]) -> Dict[str, Task]:
    """批量获取任务，使用IN查询避免N+1问题

    Args:
        db: 数据库会话
        task_ids: 任务ID列表

    Returns:
        任务ID到任务对象的映射
    """
    unique_ids = list(set(task_ids))  # 去重
    tasks = db.query(Task).filter(Task.id.in_(unique_ids)).all()
    return {task.id: task for task in tasks}


def _process_batch_operation(
    db: Session,
    current_user: User,
    task_ids: List[str],
    operation: Callable[[Task], None],
    valid_statuses: Set[TaskStatus],
    success_key: str,
) -> Dict[str, List]:
    """执行批量操作的通用函数（支持部分成功）

    注意：此函数设计为允许部分成功。每个任务独立处理，失败不影响其他任务。
    如果需要原子操作（全成功或全失败），应在调用方实现预检查。

    Args:
        db: 数据库会话
        current_user: 当前用户
        task_ids: 任务ID列表
        operation: 要对每个任务执行的操作函数
        valid_statuses: 允许操作的任务状态集合
        success_key: 成功列表的键名

    Returns:
        包含成功和失败列表的字典
    """
    result: Dict[str, List] = {success_key: [], "failed": []}

    # 批量查询减少N+1
    task_map = _fetch_tasks_by_ids(db, task_ids)

    for task_id in task_ids:
        try:
            task = task_map.get(task_id)
            if not task:
                result["failed"].append(
                    {"task_id": task_id, "reason": "Task not found"}
                )
                continue

            if not verify_task_ownership(task, current_user):
                result["failed"].append(
                    {"task_id": task_id, "reason": "Permission denied"}
                )
                continue

            if task.status not in valid_statuses:
                valid_names = ", ".join(s.value for s in valid_statuses)
                result["failed"].append(
                    {
                        "task_id": task_id,
                        "reason": f"Task status must be one of: {valid_names}",
                    }
                )
                continue

            operation(task)
            result[success_key].append(task_id)

        except SQLAlchemyError as e:
            logger.error(f"Database error for task {task_id}: {e}")
            result["failed"].append({"task_id": task_id, "reason": "Database error"})
        except Exception as e:
            logger.exception(f"Unexpected error for task {task_id}: {e}")
            result["failed"].append({"task_id": task_id, "reason": "Operation failed"})

    db.commit()
    return result


@router.post("/batch", response_model=List[TaskResponse], status_code=201)
async def create_batch_tasks(
    batch: BatchTaskCreate,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """批量创建任务

    一次创建多个任务，返回创建成功的任务列表。

    Args:
        batch: 批量任务创建请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        创建的任务列表

    Raises:
        HTTPException: 400如果任务列表为空或超过限制
    """
    if not batch.tasks:
        raise HTTPException(status_code=400, detail="Task list cannot be empty")

    if len(batch.tasks) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum limit of {MAX_BATCH_SIZE}",
        )

    created_tasks: List[Task] = []

    try:
        for task_data in batch.tasks:
            # 清理任务名
            safe_name = sanitize_filename(task_data.name)

            db_task = Task(
                id=str(uuid.uuid4()),
                name=task_data.name,
                description=task_data.description,
                target_function_signature=task_data.target_function_signature,
                test_file_path=f"experiments/{safe_name}/tests/test_solution.py",
                status=TaskStatus.PENDING,
                current_generation=0,
                best_score=0.0,
                owner_id=current_user.id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            db.add(db_task)
            db.flush()  # 立即获取ID但不提交
            created_tasks.append(db_task)

        db.commit()

        # 刷新所有任务
        for task in created_tasks:
            db.refresh(task)

        return created_tasks

    except SQLAlchemyError as e:
        logger.error(f"Database error during batch create: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Database error during task creation"
        )
    except Exception as e:
        logger.exception(f"Unexpected error during batch create: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create tasks")


@router.post("/batch/pause", response_model=BatchPauseResult)
async def batch_pause_tasks(
    batch: BatchTaskIds,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """批量暂停任务（支持部分成功）

    暂停所有指定ID的运行中任务。允许部分成功，失败的任务会记录在failed列表中。

    Args:
        batch: 批量任务ID请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        BatchPauseResult: 操作结果，包含成功暂停的任务列表和失败列表

    Raises:
        HTTPException: 400如果任务ID列表为空或超过限制
    """
    _validate_batch_ids(batch.task_ids)

    def pause_operation(task: Task) -> None:
        # TODO: 实际暂停进化任务
        task.status = TaskStatus.PAUSED

    return _process_batch_operation(
        db,
        current_user,
        batch.task_ids,
        pause_operation,
        {TaskStatus.RUNNING},
        "paused",
    )


@router.post("/batch/resume", response_model=BatchResumeResult)
async def batch_resume_tasks(
    batch: BatchTaskIds,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """批量恢复任务（支持部分成功）

    恢复所有指定ID的暂停任务。允许部分成功，失败的任务会记录在failed列表中。

    Args:
        batch: 批量任务ID请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        BatchResumeResult: 操作结果，包含成功恢复的任务列表和失败列表

    Raises:
        HTTPException: 400如果任务ID列表为空或超过限制
    """
    _validate_batch_ids(batch.task_ids)

    def resume_operation(task: Task) -> None:
        # TODO: 实际恢复进化任务
        task.status = TaskStatus.RUNNING

    return _process_batch_operation(
        db,
        current_user,
        batch.task_ids,
        resume_operation,
        {TaskStatus.PAUSED},
        "resumed",
    )


@router.post("/batch/abort", response_model=BatchAbortResult)
async def batch_abort_tasks(
    batch: BatchTaskIds,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """批量中止任务（支持部分成功）

    中止所有指定ID的运行中或暂停任务。允许部分成功，失败的任务会记录在failed列表中。

    Args:
        batch: 批量任务ID请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        BatchAbortResult: 操作结果，包含成功中止的任务列表和失败列表

    Raises:
        HTTPException: 400如果任务ID列表为空或超过限制
    """
    _validate_batch_ids(batch.task_ids)

    def abort_operation(task: Task) -> None:
        # TODO: 实际中止进化任务
        task.status = TaskStatus.ABORTED

    return _process_batch_operation(
        db,
        current_user,
        batch.task_ids,
        abort_operation,
        {TaskStatus.RUNNING, TaskStatus.PAUSED},
        "aborted",
    )


@router.post("/batch/delete", response_model=BatchDeleteResult)
async def batch_delete_tasks(
    batch: BatchTaskIds,
    db: Session = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
):
    """批量删除任务（支持部分成功）

    删除所有指定ID的任务。允许部分成功，失败的任务会记录在failed列表中。

    Args:
        batch: 批量任务ID请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        BatchDeleteResult: 操作结果，包含成功删除的任务列表和失败列表

    Raises:
        HTTPException: 400如果任务ID列表为空或超过限制
    """
    _validate_batch_ids(batch.task_ids)

    def delete_operation(task: Task) -> None:
        db.delete(task)

    return _process_batch_operation(
        db,
        current_user,
        batch.task_ids,
        delete_operation,
        {
            TaskStatus.PENDING,
            TaskStatus.RUNNING,
            TaskStatus.PAUSED,
            TaskStatus.SUCCESS,
            TaskStatus.ABORTED,
            TaskStatus.FAILED,
        },
        "deleted",
    )

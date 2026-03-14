"""监控路由

提供WebSocket实时推送和系统统计功能。
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from api.schemas import TaskStatus
from api.state import active_evolutions, connections
from storage.models import Task, Generation

# 导入JWT验证
from api.auth.jwt import verify_token
from api.auth.models import User, UserRole

router = APIRouter()
logger = logging.getLogger(__name__)

# 配置常量
PROGRESS_UPDATE_INTERVAL = 1.0  # 进度更新间隔（秒）
MAX_WEBSOCKET_CONNECTIONS = int(
    os.getenv("MAX_WS_CONNECTIONS", "100")
)  # 最大WebSocket连接数限制（防DoS）


def extract_token_from_query(query_string: str) -> Optional[str]:
    """从查询字符串中提取token

    Args:
        query_string: URL查询字符串（如 "token=abc123&foo=bar"）

    Returns:
        token字符串，如果没有找到则返回None

    Example:
        >>> extract_token_from_query("token=abc123")
        'abc123'
        >>> extract_token_from_query("foo=bar&token=xyz789")
        'xyz789'
        >>> extract_token_from_query("foo=bar")
        None
    """
    if not query_string:
        return None

    parsed = parse_qs(query_string)
    tokens = parsed.get("token", [])
    return tokens[0] if tokens else None


def verify_websocket_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """验证WebSocket Token

    使用JWT验证token的有效性。

    Args:
        token: JWT token字符串

    Returns:
        Token payload字典如果有效，None如果无效或过期

    Example:
        >>> payload = verify_websocket_token("eyJhbGciOiJIUzI1Ni...")
        >>> payload["sub"]
        'user-123'
    """
    if not token:
        return None

    return verify_token(token)


def check_task_permission(user: User, task) -> bool:
    """检查用户是否有权限访问任务

    权限规则：
    - Admin 可以访问任何任务
    - 任务所有者可以访问自己的任务
    - 无所有者的任务允许任何人访问（向后兼容）

    Args:
        user: 用户对象
        task: 任务对象（需有owner_id属性）

    Returns:
        True 如果有权限，False 如果无权限

    Example:
        >>> user = User(id="user-123", ...)
        >>> task = Task(owner_id="user-123")
        >>> check_task_permission(user, task)
        True
    """
    # Admin 有所有权限
    if user.role == UserRole.ADMIN:
        return True

    # 获取任务所有者ID
    task_owner_id = getattr(task, "owner_id", None)

    # 无所有者的任务允许访问（向后兼容）
    if task_owner_id is None:
        return True

    # 检查是否为任务所有者
    return task_owner_id == user.id


def get_task_by_id(db: Session, task_id: str):
    """通过ID获取任务

    Args:
        db: 数据库会话
        task_id: 任务ID

    Returns:
        任务对象，如果不存在则返回None
    """
    return db.query(Task).filter(Task.id == task_id).first()


@router.websocket("/ws/tasks/{task_id}")
async def evolution_websocket(websocket: WebSocket, task_id: str):
    """
    进化实时推送WebSocket

    连接成功后，客户端可以发送 {"action": "subscribe"} 开始接收进度推送。

    Args:
        websocket: WebSocket连接对象
        task_id: 任务ID

    Security:
        - Token认证：通过query参数传递token（如 ?token=xxx）
        - 限制最大连接数防止DoS攻击
        - 超过限制时返回1008状态码
        - 无效token时返回1008状态码
    """
    # 检查连接数限制（防DoS）
    if len(connections) >= MAX_WEBSOCKET_CONNECTIONS:
        await websocket.close(code=1008, reason="Server capacity reached")
        logger.warning(
            f"WebSocket rejected: max connections reached ({MAX_WEBSOCKET_CONNECTIONS})"
        )
        return

    # Token认证
    token = websocket.query_params.get("token")
    payload = verify_websocket_token(token)

    if not payload:
        await websocket.close(code=1008, reason="Authentication required")
        logger.warning(
            f"WebSocket rejected: invalid or missing token, task_id={task_id}"
        )
        return

    # 权限验证：检查用户是否有权限访问此任务（T10实现）
    user_id = payload.get("sub")
    role_str = payload.get("role", "user")
    # 验证role有效性，无效则拒绝连接
    if role_str not in [r.value for r in UserRole]:
        await websocket.close(code=1008, reason="Invalid role")
        logger.warning(
            f"WebSocket rejected: invalid role '{role_str}', task_id={task_id}"
        )
        return

    role = UserRole(role_str)

    user = User(
        id=user_id,
        username=user_id,  # 使用ID作为用户名
        email=f"{user_id}@example.com",
        hashed_password="",  # WebSocket连接不需要密码
        role=role,
    )

    # 获取任务并验证权限
    from api.dependencies import get_db_session
    from sqlalchemy.orm import Session

    db: Session = next(get_db_session())
    try:
        task = get_task_by_id(db, task_id)
        if task and not check_task_permission(user, task):
            await websocket.close(code=1008, reason="Permission denied")
            logger.warning(
                f"WebSocket rejected: permission denied, user={user_id}, task_id={task_id}"
            )
            return
    finally:
        db.close()

    await websocket.accept()
    connections[task_id] = websocket
    logger.info(f"WebSocket connected: task_id={task_id}, total={len(connections)}")

    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                if message.get("action") == "subscribe":
                    # 开始推送进度
                    await send_progress_updates(task_id, websocket)
                else:
                    # 未知动作，返回错误
                    await websocket.send_json(
                        {
                            "error": "unknown_action",
                            "message": f"Unknown action: {message.get('action')}",
                        }
                    )
            except json.JSONDecodeError:
                # 无效的JSON
                await websocket.send_json(
                    {"error": "invalid_json", "message": "Invalid JSON format"}
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: task_id={task_id}")
    except Exception as e:
        logger.error(f"WebSocket error: task_id={task_id}, error={e}")
    finally:
        # 清理连接
        if task_id in connections:
            del connections[task_id]


async def send_progress_updates(task_id: str, websocket: WebSocket):
    """
    发送进度更新（修复版：推送真实进化数据）

    如果任务在活跃进化中，定期推送进度信息。

    Args:
        task_id: 任务ID
        websocket: WebSocket连接对象
    """
    from sqlalchemy.orm import Session
    from api.dependencies import get_db_session
    
    db: Session = next(get_db_session())
    
    try:
        while task_id in connections:
            try:
                # 从活跃进化状态获取真实数据（由 EvolutionRunner 更新）
                if task_id in active_evolutions:
                    evo_state = active_evolutions[task_id]
                    progress = {
                        "type": "progress",
                        "task_id": task_id,
                        "status": evo_state.get("status", "unknown"),
                        "current_gen": evo_state.get("current_gen", 0),
                        "best_score": round(evo_state.get("best_score", 0.0), 4),
                        "progress": evo_state.get("progress", 0),
                        "timestamp": evo_state.get("updated_at"),
                    }
                    await websocket.send_json(progress)
                else:
                    # 任务不在活跃状态，查询数据库获取最新状态
                    task = db.query(Task).filter(Task.id == task_id).first()
                    if task:
                        progress = {
                            "type": "status",
                            "task_id": task_id,
                            "status": task.status,
                            "current_gen": task.current_generation,
                            "best_score": round(task.best_score, 4) if task.best_score else None,
                            "message": f"Task status: {task.status}",
                        }
                        await websocket.send_json(progress)
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Task not found",
                        })
                        break

                # 按配置间隔更新
                await asyncio.sleep(PROGRESS_UPDATE_INTERVAL)

            except Exception as e:
                logger.error(f"Error sending progress: {e}")
                break
    finally:
        db.close()


@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db_session)):
    """
    获取系统统计信息

    Returns:
        系统统计数据，包括任务数、进化代数等
    """
    total = db.query(Task).count()
    active = db.query(Task).filter(Task.status == TaskStatus.RUNNING).count()
    completed = db.query(Task).filter(Task.status.in_(["success", "failed"])).count()
    total_gens = db.query(Generation).count()

    return {
        "total_tasks": total,
        "active_tasks": active,
        "completed_tasks": completed,
        "total_generations": total_gens,
    }


@router.get("/active-tasks")
async def get_active_tasks():
    """
    获取当前活跃的任务列表

    Returns:
        活跃任务ID列表
    """
    return {
        "active_tasks": list(active_evolutions.keys()),
        "count": len(active_evolutions),
    }

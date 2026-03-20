"""测试WebSocket权限验证"""

# flake8: noqa: E402

import os

# 设置JWT密钥（必须在导入模块之前）
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestWebSocketTaskPermission:
    """WebSocket任务权限验证测试"""

    @pytest.fixture
    def mock_websocket(self):
        """提供模拟WebSocket对象"""
        mock_ws = AsyncMock()
        mock_ws.query_params = MagicMock()
        mock_ws.close = AsyncMock()
        mock_ws.accept = AsyncMock()
        return mock_ws

    def test_admin_can_connect_to_any_task(self, mock_websocket):
        """管理员应能连接任何任务的WebSocket"""
        import asyncio

        from api.auth.jwt import create_access_token
        from api.routers.monitor import connections, evolution_websocket

        # 创建管理员token
        token = create_access_token(data={"sub": "admin-1", "role": "admin"})
        mock_websocket.query_params.get.return_value = token

        # 清理connections
        connections.clear()

        # 模拟任务（任何任务管理员都有权限）
        mock_task = MagicMock()
        mock_task.owner_id = "user-999"  # 其他用户的任务

        # 运行WebSocket处理器
        async def run_test():
            try:
                await evolution_websocket(mock_websocket, "task-123")
            except Exception:
                pass

        # 模拟get_task_by_id返回任务
        import api.routers.monitor as monitor

        original_get_task = getattr(monitor, "get_task_by_id", None)
        monitor.get_task_by_id = lambda db, task_id: mock_task

        try:
            asyncio.run(run_test())
        finally:
            if original_get_task:
                monitor.get_task_by_id = original_get_task
            else:
                delattr(monitor, "get_task_by_id")

        # 验证accept被调用（管理员有权限）
        mock_websocket.accept.assert_called_once()

    def test_user_can_connect_to_own_task(self, mock_websocket):
        """用户应能连接自己任务的WebSocket"""
        import asyncio

        from api.auth.jwt import create_access_token
        from api.routers.monitor import connections, evolution_websocket

        # 创建普通用户token
        token = create_access_token(data={"sub": "user-123", "role": "user"})
        mock_websocket.query_params.get.return_value = token

        # 清理connections
        connections.clear()

        # 模拟任务所有权（通过mock数据库查询）
        with MagicMock() as mock_task:
            mock_task.owner_id = "user-123"

            # 运行WebSocket处理器
            async def run_test():
                try:
                    await evolution_websocket(mock_websocket, "task-123")
                except Exception:
                    pass

            # 模拟get_task_by_id返回用户自己的任务
            with pytest.MonkeyPatch.context() as mp:
                mp.setattr(
                    "api.routers.monitor.get_task_by_id",
                    lambda db, task_id: mock_task,
                )
                asyncio.run(run_test())

        # 验证accept被调用（用户有权限访问自己的任务）
        mock_websocket.accept.assert_called_once()

    def test_user_cannot_connect_to_others_task(self, mock_websocket):
        """用户不应能连接他人任务的WebSocket"""
        import asyncio

        from api.auth.jwt import create_access_token
        from api.routers.monitor import connections, evolution_websocket

        # 创建普通用户token（用户ID为user-123）
        token = create_access_token(data={"sub": "user-123", "role": "user"})
        mock_websocket.query_params.get.return_value = token

        # 清理connections
        connections.clear()

        # 模拟任务所有权（任务属于其他用户）
        mock_task = MagicMock()
        mock_task.owner_id = "user-999"  # 其他用户

        # 运行WebSocket处理器
        async def run_test():
            await evolution_websocket(mock_websocket, "task-999")

        # 模拟get_task_by_id返回他人的任务
        import api.routers.monitor as monitor

        original_get_task = getattr(monitor, "get_task_by_id", None)
        monitor.get_task_by_id = lambda db, task_id: mock_task

        try:
            asyncio.run(run_test())
        finally:
            if original_get_task:
                monitor.get_task_by_id = original_get_task
            else:
                delattr(monitor, "get_task_by_id")

        # 验证close被调用且code为1008（权限不足）
        mock_websocket.close.assert_called_once()
        call_args = mock_websocket.close.call_args
        code = call_args.kwargs.get("code") or call_args.args[0]
        assert code == 1008


class TestWebSocketPermissionUtils:
    """WebSocket权限工具函数测试"""

    def test_check_task_permission_returns_true_for_owner(self):
        """任务所有者应有权限"""
        from api.auth.models import User, UserRole
        from api.routers.monitor import check_task_permission

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        mock_task = MagicMock()
        mock_task.owner_id = "user-123"

        result = check_task_permission(user, mock_task)
        assert result is True

    def test_check_task_permission_returns_true_for_admin(self):
        """管理员应有任何任务权限"""
        from api.auth.models import User, UserRole
        from api.routers.monitor import check_task_permission

        admin = User(
            id="admin-1",
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        mock_task = MagicMock()
        mock_task.owner_id = "user-999"  # 其他用户的任务

        result = check_task_permission(admin, mock_task)
        assert result is True

    def test_check_task_permission_returns_false_for_other_user(self):
        """其他用户不应有权限"""
        from api.auth.models import User, UserRole
        from api.routers.monitor import check_task_permission

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        mock_task = MagicMock()
        mock_task.owner_id = "user-999"  # 其他用户的任务

        result = check_task_permission(user, mock_task)
        assert result is False

    def test_check_task_permission_returns_true_for_no_owner(self):
        """无所有者的任务应允许访问（向后兼容）"""
        from api.auth.models import User, UserRole
        from api.routers.monitor import check_task_permission

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        mock_task = MagicMock()
        mock_task.owner_id = None  # 无所有者

        result = check_task_permission(user, mock_task)
        assert result is True

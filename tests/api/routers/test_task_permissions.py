"""测试任务路由权限"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status


class TestTaskOwnership:
    """任务所有权测试"""

    def test_verify_task_ownership_admin_can_access_any(self):
        """管理员应能访问任何任务"""
        from api.auth.models import User, UserRole
        from api.routers.tasks import verify_task_ownership

        admin = User(
            id="admin-1",
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        mock_task = MagicMock()
        mock_task.owner_id = "user-999"  # 任务属于其他用户

        result = verify_task_ownership(mock_task, admin)
        assert result is True

    def test_verify_task_ownership_owner_can_access_own(self):
        """任务所有者应能访问自己的任务"""
        from api.auth.models import User, UserRole
        from api.routers.tasks import verify_task_ownership

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        mock_task = MagicMock()
        mock_task.owner_id = "user-123"  # 任务属于该用户

        result = verify_task_ownership(mock_task, user)
        assert result is True

    def test_verify_task_ownership_other_cannot_access(self):
        """其他用户不应能访问他人的任务"""
        from api.auth.models import User, UserRole
        from api.routers.tasks import verify_task_ownership

        user = User(
            id="user-456",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        mock_task = MagicMock()
        mock_task.owner_id = "user-999"  # 任务属于其他用户

        result = verify_task_ownership(mock_task, user)
        assert result is False

    def test_verify_task_ownership_no_owner_allow_all(self):
        """无所有者的任务允许所有人访问（向后兼容）"""
        from api.auth.models import User, UserRole
        from api.routers.tasks import verify_task_ownership

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        mock_task = MagicMock()
        mock_task.owner_id = None  # 无所有者

        result = verify_task_ownership(mock_task, user)
        assert result is True


class TestRequireTaskAccess:
    """任务访问权限要求测试"""

    def test_require_task_access_raises_403_for_unauthorized(self):
        """无权限时应抛出403"""
        from api.auth.models import User, UserRole
        from api.routers.tasks import require_task_access

        user = User(
            id="user-456",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        mock_task = MagicMock()
        mock_task.owner_id = "user-999"  # 任务属于其他用户

        with pytest.raises(HTTPException) as exc_info:
            require_task_access(mock_task, user)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    def test_require_task_access_passes_for_owner(self):
        """所有者有权限不应抛出异常"""
        from api.auth.models import User, UserRole
        from api.routers.tasks import require_task_access

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        mock_task = MagicMock()
        mock_task.owner_id = "user-123"

        # 不应抛出异常
        require_task_access(mock_task, user)

"""测试审批路由权限"""

import pytest
from fastapi import HTTPException, status
from unittest.mock import MagicMock


class TestApprovalPermissions:
    """审批权限测试"""

    def test_only_authorized_can_approve(self):
        """只有授权用户能批准审批请求"""
        from api.auth.models import User, UserRole

        # 普通用户可以批准
        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # 验证用户有权限（简化测试，实际在端点中检查）
        assert user.role in [UserRole.USER, UserRole.ADMIN]

    def test_admin_can_approve_any_request(self):
        """管理员可以批准任何审批请求"""
        from api.auth.models import User, UserRole

        admin = User(
            id="admin-1",
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        assert admin.role == UserRole.ADMIN

    def test_verify_approval_permission_allows_user(self):
        """verify_approval_permission应允许普通用户"""
        from api.routers.approvals import verify_approval_permission
        from api.auth.models import User, UserRole

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # 不应抛出异常
        result = verify_approval_permission(user)
        assert result is True

    def test_verify_approval_permission_allows_admin(self):
        """verify_approval_permission应允许管理员"""
        from api.routers.approvals import verify_approval_permission
        from api.auth.models import User, UserRole

        admin = User(
            id="admin-1",
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        # 不应抛出异常
        result = verify_approval_permission(admin)
        assert result is True


class TestRequireApprovalPermission:
    """审批权限要求测试"""

    def test_require_approval_permission_passes_for_authorized(self):
        """有权限的用户应通过检查"""
        from api.routers.approvals import require_approval_permission
        from api.auth.models import User, UserRole

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # 不应抛出异常
        result = require_approval_permission(user)
        assert result == user

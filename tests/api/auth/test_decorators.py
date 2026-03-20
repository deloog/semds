"""测试权限装饰器"""

import pytest
from fastapi import HTTPException


class TestCheckPermission:
    """check_permission 函数测试"""

    def test_check_permission_allows_authorized(self):
        """有权限的用户应通过检查"""
        from api.auth.decorators import check_permission
        from api.auth.models import User, UserRole
        from api.auth.permissions import TaskPermission

        user = User(
            id="1",
            username="user",
            email="a@b.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # 不应抛出异常
        check_permission(user, TaskPermission.READ)

    def test_check_permission_allows_admin_any_permission(self):
        """管理员应有所有权限"""
        from api.auth.decorators import check_permission
        from api.auth.models import User, UserRole
        from api.auth.permissions import ApprovalPermission, TaskPermission

        admin = User(
            id="1",
            username="admin",
            email="admin@b.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        # Admin 可以执行任何操作，不应抛出异常
        check_permission(admin, TaskPermission.DELETE)
        check_permission(admin, ApprovalPermission.CREATE)

    def test_check_permission_denies_unauthorized(self):
        """无权限的用户应被拒绝"""
        from api.auth.decorators import check_permission
        from api.auth.models import User, UserRole
        from api.auth.permissions import TaskPermission

        user = User(
            id="1",
            username="user",
            email="a@b.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # USER 没有 DELETE 权限
        with pytest.raises(HTTPException) as exc_info:
            check_permission(user, TaskPermission.DELETE)

        assert exc_info.value.status_code == 403
        assert "Permission denied" in exc_info.value.detail
        assert TaskPermission.DELETE.value in exc_info.value.detail

    def test_check_permission_denies_create_approval_for_user(self):
        """普通用户应被拒绝创建审批请求"""
        from api.auth.decorators import check_permission
        from api.auth.models import User, UserRole
        from api.auth.permissions import ApprovalPermission

        user = User(
            id="1",
            username="user",
            email="a@b.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # USER 没有 CREATE approval 权限
        with pytest.raises(HTTPException) as exc_info:
            check_permission(user, ApprovalPermission.CREATE)

        assert exc_info.value.status_code == 403


class TestRequirePermission:
    """require_permission 装饰器工厂测试"""

    def test_require_permission_returns_callable(self):
        """require_permission 应返回可调用的依赖函数"""
        from api.auth.decorators import require_permission
        from api.auth.permissions import TaskPermission

        dependency = require_permission(TaskPermission.READ)

        assert callable(dependency)

    def test_require_permission_dependency_allows_authorized(self):
        """依赖函数应允许有权限的用户"""
        from api.auth.decorators import require_permission
        from api.auth.models import User, UserRole
        from api.auth.permissions import TaskPermission

        user = User(
            id="1",
            username="user",
            email="a@b.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        dependency = require_permission(TaskPermission.READ)

        # 不应抛出异常，且返回用户
        result = dependency(user)
        assert result == user

    def test_require_permission_dependency_denies_unauthorized(self):
        """依赖函数应拒绝无权限的用户"""
        from api.auth.decorators import require_permission
        from api.auth.models import User, UserRole
        from api.auth.permissions import TaskPermission

        user = User(
            id="1",
            username="user",
            email="a@b.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        dependency = require_permission(TaskPermission.DELETE)

        with pytest.raises(HTTPException) as exc_info:
            dependency(user)

        assert exc_info.value.status_code == 403


class TestPermissionIntegration:
    """权限检查集成测试"""

    def test_user_can_read_but_not_delete(self):
        """用户应能读取但不能删除任务"""
        from api.auth.decorators import check_permission
        from api.auth.models import User, UserRole
        from api.auth.permissions import TaskPermission

        user = User(
            id="1",
            username="user",
            email="a@b.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # 可以读取
        check_permission(user, TaskPermission.READ)

        # 不能删除
        with pytest.raises(HTTPException):
            check_permission(user, TaskPermission.DELETE)

    def test_admin_can_do_everything(self):
        """管理员应能执行所有操作"""
        from api.auth.decorators import check_permission
        from api.auth.models import User, UserRole
        from api.auth.permissions import ApprovalPermission, TaskPermission

        admin = User(
            id="1",
            username="admin",
            email="admin@b.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        # Admin 可以执行所有操作
        for perm in TaskPermission:
            check_permission(admin, perm)

        for perm in ApprovalPermission:
            check_permission(admin, perm)

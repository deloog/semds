"""测试认证依赖"""

import pytest
from fastapi import HTTPException


class TestCurrentUserDependency:
    """当前用户依赖测试"""

    def test_get_current_user_with_valid_token(self):
        """有效Token应返回用户"""
        from api.auth.dependencies import get_current_user
        from api.auth.jwt import create_access_token

        token = create_access_token(data={"sub": "user-123", "role": "user"})

        user = get_current_user(token)

        assert user is not None
        assert user.id == "user-123"
        assert user.role.value == "user"

    def test_get_current_user_with_invalid_token(self):
        """无效Token应抛出401"""
        from api.auth.dependencies import get_current_user

        with pytest.raises(HTTPException) as exc_info:
            get_current_user("invalid-token")

        assert exc_info.value.status_code == 401

    def test_get_current_user_with_expired_token(self):
        """过期Token应抛出401"""
        from datetime import timedelta

        from api.auth.dependencies import get_current_user
        from api.auth.jwt import create_access_token

        # 创建已过期的Token
        expired_token = create_access_token(
            data={"sub": "user-123"}, expires_delta=timedelta(minutes=-1)
        )

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(expired_token)

        assert exc_info.value.status_code == 401

    def test_get_current_user_missing_sub(self):
        """缺少sub字段应抛出401"""
        from api.auth.dependencies import get_current_user
        from api.auth.jwt import create_access_token

        # 创建没有sub的Token
        token = create_access_token(data={"role": "user"})

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token)

        assert exc_info.value.status_code == 401


class TestPermissionRequirements:
    """权限要求测试"""

    def test_require_admin_allows_admin(self):
        """管理员应通过admin检查"""
        from api.auth.dependencies import require_admin
        from api.auth.models import User, UserRole

        admin_user = User(
            id="admin-1",
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        # 不应抛出异常
        result = require_admin(admin_user)
        assert result == admin_user

    def test_require_admin_rejects_user(self):
        """普通用户应被拒绝admin权限"""
        from api.auth.dependencies import require_admin
        from api.auth.models import User, UserRole

        normal_user = User(
            id="user-1",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        with pytest.raises(HTTPException) as exc_info:
            require_admin(normal_user)

        assert exc_info.value.status_code == 403

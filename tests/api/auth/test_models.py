"""测试认证模型"""

import pytest
from datetime import datetime, timezone


class TestUserModel:
    """用户模型测试"""

    def test_user_creation_with_required_fields(self):
        """用户应包含必要字段"""
        from api.auth.models import User, UserRole

        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_secret",
            role=UserRole.USER,
        )

        assert user.id == "user-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_secret"
        assert user.role == UserRole.USER
        assert user.is_active is True

    def test_user_auto_generates_created_at(self):
        """用户应自动生成创建时间"""
        from api.auth.models import User, UserRole

        before = datetime.now(timezone.utc)
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )
        after = datetime.now(timezone.utc)

        assert user.created_at is not None
        assert before <= user.created_at <= after

    def test_user_role_validation(self):
        """用户角色应在允许范围内"""
        from api.auth.models import User, UserRole

        # 有效角色 - USER
        user1 = User(
            id="1",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )
        assert user1.role == UserRole.USER

        # 有效角色 - ADMIN
        user2 = User(
            id="2",
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        assert user2.role == UserRole.ADMIN

    def test_user_defaults(self):
        """用户应有合理的默认值"""
        from api.auth.models import User, UserRole

        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
        )

        assert user.role == UserRole.USER  # 默认角色
        assert user.is_active is True  # 默认激活


class TestTokenModel:
    """Token模型测试"""

    def test_token_creation(self):
        """Token应包含必要字段"""
        from api.auth.models import Token

        token = Token(
            access_token="eyJhbGciOiJIUzI1NiIs...", token_type="bearer", expires_in=3600
        )

        assert token.access_token == "eyJhbGciOiJIUzI1NiIs..."
        assert token.token_type == "bearer"
        assert token.expires_in == 3600

    def test_token_defaults(self):
        """Token应有合理的默认值"""
        from api.auth.models import Token

        token = Token(access_token="test-token")

        assert token.token_type == "bearer"
        assert token.expires_in == 3600

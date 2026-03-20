"""测试登录API"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestLoginAPI:
    """登录API测试"""

    def test_login_with_valid_credentials(self):
        """有效凭据应返回Token"""
        from api.main import app

        # Mock用户验证
        with patch("api.routers.auth.authenticate_user") as mock_auth:
            mock_user = MagicMock()
            mock_user.id = "user-123"
            mock_user.username = "testuser"
            mock_user.role = "user"
            mock_auth.return_value = mock_user

            client = TestClient(app)
            response = client.post(
                "/api/auth/login", data={"username": "testuser", "password": "secret"}
            )

            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"

    def test_login_with_invalid_credentials(self):
        """无效凭据应返回401"""
        from unittest.mock import patch

        from api.main import app

        with patch("api.routers.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = None

            client = TestClient(app)
            response = client.post(
                "/api/auth/login", data={"username": "testuser", "password": "wrong"}
            )

            assert response.status_code == 401

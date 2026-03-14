"""测试WebSocket认证"""

# flake8: noqa: E402

import os

# 设置JWT密钥（必须在导入模块之前）
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")  # noqa: E402

import pytest  # noqa: E402
from unittest.mock import AsyncMock, MagicMock


class TestWebSocketTokenAuth:
    """WebSocket Token认证测试"""

    def test_websocket_accepts_valid_token(self):
        """WebSocket应接受有效Token"""
        from api.auth.jwt import create_access_token
        from api.routers.monitor import verify_websocket_token

        # 创建有效token
        token = create_access_token(data={"sub": "user-123", "role": "user"})

        # 验证token应成功
        payload = verify_websocket_token(token)

        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "user"

    def test_websocket_rejects_invalid_token(self):
        """WebSocket应拒绝无效Token"""
        from api.routers.monitor import verify_websocket_token

        # 验证无效token应返回None
        payload = verify_websocket_token("invalid.token.here")

        assert payload is None

    def test_websocket_rejects_missing_token(self):
        """WebSocket应拒绝缺少Token"""
        from api.routers.monitor import verify_websocket_token

        # 验证None token应返回None
        payload = verify_websocket_token(None)

        assert payload is None

    def test_websocket_rejects_expired_token(self):
        """WebSocket应拒绝过期Token"""
        from datetime import timedelta
        from api.auth.jwt import create_access_token
        from api.routers.monitor import verify_websocket_token

        # 创建已过期token
        expired_token = create_access_token(
            data={"sub": "user-123", "role": "user"},
            expires_delta=timedelta(minutes=-1),
        )

        # 验证过期token应返回None
        payload = verify_websocket_token(expired_token)

        assert payload is None


class TestWebSocketAuthIntegration:
    """WebSocket认证集成测试（使用模拟WebSocket）"""

    @pytest.fixture
    def mock_websocket(self):
        """提供模拟WebSocket对象"""
        mock_ws = AsyncMock()
        mock_ws.query_params = MagicMock()
        mock_ws.close = AsyncMock()
        mock_ws.accept = AsyncMock()
        return mock_ws

    def test_websocket_endpoint_accepts_connection_with_valid_token(
        self, mock_websocket
    ):
        """带有效Token的WebSocket连接应被接受"""
        import asyncio
        from api.auth.jwt import create_access_token
        from api.routers.monitor import evolution_websocket, connections

        # 创建有效token（用户自己的任务）
        token = create_access_token(data={"sub": "user-123", "role": "user"})

        # 设置mock query_params
        mock_websocket.query_params.get.return_value = token

        # 清理connections
        connections.clear()

        # 模拟用户自己的任务
        mock_task = MagicMock()
        mock_task.owner_id = "user-123"

        # 运行WebSocket处理器（但捕获异常避免无限循环）
        async def run_test():
            try:
                await evolution_websocket(mock_websocket, "task-123")
            except Exception:
                pass  # 忽略后续异常，只关注accept是否被调用

        # 模拟get_task_by_id返回用户自己的任务
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

        # 验证accept被调用（认证通过）
        mock_websocket.accept.assert_called_once()

    def test_websocket_endpoint_rejects_connection_without_token(self, mock_websocket):
        """不带Token的WebSocket连接应被拒绝"""
        import asyncio
        from api.routers.monitor import evolution_websocket

        # 设置mock query_params返回None
        mock_websocket.query_params.get.return_value = None

        # 运行WebSocket处理器
        async def run_test():
            await evolution_websocket(mock_websocket, "task-123")

        asyncio.run(run_test())

        # 验证close被调用且code为1008（认证失败）
        mock_websocket.close.assert_called_once()
        call_args = mock_websocket.close.call_args
        assert call_args.kwargs.get("code") == 1008 or call_args.args[0] == 1008

    def test_websocket_endpoint_rejects_connection_with_invalid_token(
        self, mock_websocket
    ):
        """带无效Token的WebSocket连接应被拒绝"""
        import asyncio
        from api.routers.monitor import evolution_websocket

        # 设置mock query_params返回无效token
        mock_websocket.query_params.get.return_value = "invalid.token"

        # 运行WebSocket处理器
        async def run_test():
            await evolution_websocket(mock_websocket, "task-123")

        asyncio.run(run_test())

        # 验证close被调用且code为1008（认证失败）
        mock_websocket.close.assert_called_once()
        call_args = mock_websocket.close.call_args
        assert call_args.kwargs.get("code") == 1008 or call_args.args[0] == 1008


class TestWebSocketAuthUtils:
    """WebSocket认证工具函数测试"""

    def test_extract_token_from_query_string(self):
        """应从查询字符串中提取token"""
        from api.routers.monitor import extract_token_from_query

        # 测试带token的URL
        token = extract_token_from_query("token=abc123")
        assert token == "abc123"

        # 测试带多个参数的URL
        token = extract_token_from_query("foo=bar&token=xyz789&baz=qux")
        assert token == "xyz789"

        # 测试不带token的URL
        token = extract_token_from_query("foo=bar")
        assert token is None

        # 测试空字符串
        token = extract_token_from_query("")
        assert token is None

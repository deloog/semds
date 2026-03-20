"""测试Redis状态存储"""

from unittest.mock import MagicMock, patch

import pytest  # noqa: F401


class TestRedisStateManagerInitialization:
    """Redis状态管理器初始化测试"""

    def test_redis_state_manager_initialization(self):
        """Redis状态管理器应正确初始化"""
        from api.state_redis import RedisStateManager

        manager = RedisStateManager(redis_url="redis://localhost:6379/0")

        assert manager.redis_url == "redis://localhost:6379/0"
        assert manager._redis is None

    def test_redis_state_manager_default_url(self):
        """Redis状态管理器应使用默认URL"""
        from api.state_redis import RedisStateManager

        manager = RedisStateManager()

        assert "localhost:6379" in manager.redis_url


class TestRedisConnection:
    """Redis连接测试"""

    def test_get_redis_client_lazy_connection(self):
        """应延迟连接Redis"""
        from api.state_redis import RedisStateManager

        manager = RedisStateManager()
        assert manager._redis is None

    def test_get_redis_client_creates_connection(self):
        """获取客户端时应创建连接"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            client = manager.get_client()

            assert client is not None
            mock_from_url.assert_called_once()


class TestRedisStateOperations:
    """Redis状态操作测试"""

    def test_set_evolution_state(self):
        """应能设置进化状态"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            manager.set_evolution_state("task-1", {"status": "running", "progress": 50})

            mock_client.setex.assert_called_once()

    def test_get_evolution_state(self):
        """应能获取进化状态"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_client.get.return_value = '{"status": "running"}'
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            state = manager.get_evolution_state("task-1")

            assert state["status"] == "running"

    def test_get_nonexistent_evolution_state(self):
        """获取不存在的进化状态应返回None"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_client.get.return_value = None
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            state = manager.get_evolution_state("nonexistent")

            assert state is None

    def test_delete_evolution_state(self):
        """应能删除进化状态"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            manager.delete_evolution_state("task-1")

            mock_client.delete.assert_called_once()


class TestRedisConnectionOperations:
    """Redis连接操作测试"""

    def test_register_connection(self):
        """应能注册WebSocket连接"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            manager.register_connection("task-1", "connection-id-123")

            mock_client.setex.assert_called_once()

    def test_unregister_connection(self):
        """应能注销WebSocket连接"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            manager.unregister_connection("task-1")

            mock_client.delete.assert_called_once()

    def test_get_active_connections(self):
        """应能获取活跃连接列表"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_client.keys.return_value = ["connection:task-1", "connection:task-2"]
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            connections = manager.get_active_connections()

            assert len(connections) == 2
            assert "task-1" in connections
            assert "task-2" in connections


class TestRedisHealthCheck:
    """Redis健康检查测试"""

    def test_health_check_success(self):
        """健康检查应返回True当Redis可用"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            is_healthy = manager.health_check()

            assert is_healthy is True

    def test_health_check_failure(self):
        """健康检查应返回False当Redis不可用"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_client.ping.side_effect = Exception("Connection refused")
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()
            is_healthy = manager.health_check()

            assert is_healthy is False

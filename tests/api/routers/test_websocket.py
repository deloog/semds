"""测试WebSocket路由"""

from unittest.mock import MagicMock


class TestWebSocketConnection:
    """WebSocket连接测试"""

    def test_websocket_endpoint_exists(self):
        """WebSocket端点应存在并可连接"""
        from api.routers.monitor import evolution_websocket

        # 验证端点函数存在
        assert evolution_websocket is not None
        assert callable(evolution_websocket)

    def test_websocket_connections_dict_exists(self):
        """连接字典应存在"""
        from api.routers import monitor

        # 验证connections字典存在
        assert hasattr(monitor, "connections")
        assert isinstance(monitor.connections, dict)


class TestSystemStats:
    """系统统计API测试"""

    def test_get_system_stats_endpoint_exists(self):
        """系统统计端点应存在"""
        from unittest.mock import MagicMock

        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        # 创建mock数据库会话
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query
        mock_db.query.return_value = mock_query

        # 覆盖依赖
        app.dependency_overrides[get_db_session] = lambda: mock_db

        try:
            client = TestClient(app)
            response = client.get("/api/stats")

            # 端点存在
            assert response.status_code == 200
        finally:
            del app.dependency_overrides[get_db_session]

    def test_get_system_stats_returns_correct_structure(self):
        """系统统计应返回正确结构（使用mock）"""
        import asyncio

        from api.routers.monitor import get_system_stats

        # 创建mock数据库会话
        mock_db = MagicMock()

        # 设置query().filter().count()的返回值
        mock_query = MagicMock()
        mock_query.count.return_value = 10
        mock_query.filter.return_value = mock_query
        mock_db.query.return_value = mock_query

        # 运行异步函数
        result = asyncio.run(get_system_stats(mock_db))

        # 验证返回结构
        assert "total_tasks" in result
        assert "active_tasks" in result
        assert "completed_tasks" in result
        assert "total_generations" in result

        assert result["total_tasks"] == 10


class TestActiveTasks:
    """活跃任务API测试"""

    def test_get_active_tasks_endpoint_exists(self):
        """活跃任务端点应存在"""
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)
        response = client.get("/api/active-tasks")

        assert response.status_code == 200

        data = response.json()
        assert "active_tasks" in data
        assert "count" in data
        assert isinstance(data["active_tasks"], list)


class TestWebSocketConnectionLimits:
    """WebSocket连接限制测试"""

    def test_websocket_has_max_connections_config(self):
        """应配置最大连接数限制"""
        from api.routers.monitor import MAX_WEBSOCKET_CONNECTIONS

        assert isinstance(MAX_WEBSOCKET_CONNECTIONS, int)
        assert MAX_WEBSOCKET_CONNECTIONS > 0
        assert MAX_WEBSOCKET_CONNECTIONS <= 1000  # 合理上限


class TestMonitorImports:
    """监控模块导入测试"""

    def test_monitor_module_imports(self):
        """监控模块应能正确导入"""
        from api.routers import monitor

        # 验证主要组件存在
        assert hasattr(monitor, "router")
        assert hasattr(monitor, "connections")
        assert hasattr(monitor, "active_evolutions")
        assert hasattr(monitor, "evolution_websocket")
        assert hasattr(monitor, "get_system_stats")
        assert hasattr(monitor, "send_progress_updates")

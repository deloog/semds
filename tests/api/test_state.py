"""测试API状态管理模块"""


class TestStateManager:
    """状态管理器测试"""

    def test_state_module_exists(self):
        """状态管理模块应存在"""
        from api import state

        assert hasattr(state, "active_evolutions")
        assert hasattr(state, "connections")

    def test_active_evolutions_is_dict(self):
        """active_evolutions应为字典"""
        from api.state import active_evolutions

        assert isinstance(active_evolutions, dict)

    def test_connections_is_dict(self):
        """connections应为字典"""
        from api.state import connections

        assert isinstance(connections, dict)

    def test_active_evolutions_shared_across_modules(self):
        """active_evolutions应在模块间共享"""
        from api.routers import evolution, monitor
        from api.state import active_evolutions

        # 验证各模块引用的是同一个对象
        assert monitor.active_evolutions is active_evolutions
        assert evolution.active_evolutions is active_evolutions

    def test_connections_shared_across_modules(self):
        """connections应在模块间共享"""
        from api.routers import monitor
        from api.state import connections

        # 验证monitor模块引用的是同一个connections
        assert monitor.connections is connections


class TestStateOperations:
    """状态操作测试"""

    def test_active_evolutions_can_add_task(self):
        """可以添加活跃任务"""
        from api.state import active_evolutions

        # 添加任务
        active_evolutions["test-task-1"] = {
            "status": "running",
            "current_gen": 0,
            "progress": 0.5,
        }

        assert "test-task-1" in active_evolutions
        assert active_evolutions["test-task-1"]["status"] == "running"

        # 清理
        del active_evolutions["test-task-1"]

    def test_connections_can_add_websocket(self):
        """可以添加WebSocket连接"""
        from api.state import connections

        # 添加mock连接
        mock_ws = "mock-websocket-object"
        connections["test-task-2"] = mock_ws

        assert "test-task-2" in connections
        assert connections["test-task-2"] == mock_ws

        # 清理
        del connections["test-task-2"]

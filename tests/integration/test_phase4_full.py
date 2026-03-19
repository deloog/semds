"""Phase 4完整集成测试

验证整个Phase 4功能链路的完整性，包括：
- 任务创建到删除的完整生命周期
- 进化控制流程
- 审批流程
- WebSocket连接
- 监控界面访问
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone


@pytest.fixture
def auth_headers():
    """提供认证头"""
    from api.auth.jwt import create_access_token

    token = create_access_token(data={"sub": "user-123", "role": "user"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_user():
    """创建mock用户"""
    user = MagicMock()
    user.id = "user-123"
    user.username = "testuser"
    user.role = "admin"  # 使用admin角色以获得完整权限
    return user


@pytest.fixture
def test_client(mock_user):
    """提供配置好的测试客户端"""
    from api.main import app
    from api.dependencies import get_db_session
    from api.auth.dependencies import get_current_user

    # Mock数据库会话
    mock_session = MagicMock()

    def mock_get_db():
        yield mock_session

    app.dependency_overrides[get_db_session] = mock_get_db
    app.dependency_overrides[get_current_user] = lambda: mock_user

    client = TestClient(app)
    yield client, mock_session

    # 清理
    del app.dependency_overrides[get_db_session]
    del app.dependency_overrides[get_current_user]


class TestPhase4HealthCheck:
    """健康检查集成测试"""

    def test_health_endpoint_returns_ok(self, test_client):
        """健康检查端点应返回OK状态"""
        client, _ = test_client

        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestPhase4TaskLifecycle:
    """任务生命周期集成测试"""

    def test_full_task_lifecycle(self, test_client):
        """完整任务生命周期：创建->查询->删除"""
        client, mock_session = test_client

        # Mock查询结果
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.name = "integration_test"
        mock_task.description = "Integration test task"
        mock_task.status = "pending"
        mock_task.current_generation = 0
        mock_task.best_score = 0.0
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.updated_at = datetime.now(timezone.utc)
        mock_task.owner_id = "user-123"

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_task
        mock_session.query.return_value = query_mock

        # 1. 创建任务
        create_response = client.post(
            "/api/tasks",
            json={
                "name": "integration_test",
                "description": "Integration test task",
                "target_function_signature": "def test(): pass",
                "test_code": "def test(): assert True",
            },
        )
        assert create_response.status_code == 201

        # 2. 查询任务列表
        list_response = client.get("/api/tasks")
        assert list_response.status_code == 200

        # 3. 查询单个任务
        get_response = client.get("/api/tasks/task-123")
        assert get_response.status_code == 200

        # 4. 删除任务
        delete_response = client.delete("/api/tasks/task-123")
        assert delete_response.status_code == 200


class TestPhase4EvolutionControl:
    """进化控制集成测试"""

    def test_evolution_control_flow(self, test_client):
        """进化控制流程：启动->暂停->恢复->中止"""
        client, mock_session = test_client

        # Mock任务
        mock_task = MagicMock()
        mock_task.id = "task-evo-123"
        mock_task.status = "pending"
        mock_task.owner_id = "user-123"

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_task
        mock_session.query.return_value = query_mock

        # 1. 启动进化
        start_response = client.post("/api/tasks/task-evo-123/start")
        assert start_response.status_code == 200

        # 更新任务状态为running
        mock_task.status = "running"

        # 2. 暂停进化
        pause_response = client.post("/api/tasks/task-evo-123/pause")
        assert pause_response.status_code == 200

        # 更新任务状态为paused
        mock_task.status = "paused"

        # 3. 恢复进化
        resume_response = client.post("/api/tasks/task-evo-123/resume")
        assert resume_response.status_code == 200

        # 4. 中止进化
        abort_response = client.post("/api/tasks/task-evo-123/abort")
        assert abort_response.status_code == 200


class TestPhase4GenerationHistory:
    """进化历史集成测试"""

    def test_generation_history_flow(self, test_client):
        """进化历史查询流程"""
        client, mock_session = test_client

        # Mock任务
        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.owner_id = "user-123"

        # Mock查询结果
        query_mock = MagicMock()
        query_mock.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )
        query_mock.filter.return_value.first.return_value = mock_task
        mock_session.query.return_value = query_mock

        # 1. 获取进化历史
        history_response = client.get("/api/tasks/task-123/generations")
        assert history_response.status_code == 200

        # 2. 获取最佳实现
        best_response = client.get("/api/tasks/task-123/best")
        # 可能返回404（如果没有最佳实现）或200
        assert best_response.status_code in [200, 404]


class TestPhase4ApprovalFlow:
    """审批流程集成测试"""

    def test_approval_workflow(self, test_client):
        """完整审批流程：创建->查询->批准"""
        client, mock_session = test_client

        # Mock审批请求
        mock_approval = MagicMock()
        mock_approval.id = "approval-123"
        mock_approval.task_id = "task-123"
        mock_approval.generation_id = "gen-456"
        mock_approval.code = "def test(): pass"
        mock_approval.reason = "需要审批"
        mock_approval.status = "pending"
        mock_approval.created_at = datetime.now(timezone.utc)
        mock_approval.reviewed_at = None
        mock_approval.reviewer_comment = None

        query_mock = MagicMock()
        query_mock.filter.return_value.order_by.return_value.all.return_value = [
            mock_approval
        ]
        query_mock.filter.return_value.first.return_value = mock_approval
        mock_session.query.return_value = query_mock

        # Mock add/commit/refresh
        def mock_add(obj):
            from datetime import datetime, timezone

            if not hasattr(obj, "id") or obj.id is None:
                obj.id = "mock-approval-id"
            if not hasattr(obj, "created_at") or obj.created_at is None:
                obj.created_at = datetime.now(timezone.utc)

        mock_session.add.side_effect = mock_add

        # 1. 获取待审批列表
        pending_response = client.get("/api/approvals/pending")
        assert pending_response.status_code == 200

        # 2. 批准请求
        approve_response = client.post(
            "/api/approvals/approval-123/approve",
            json={"approved": True, "comment": "LGTM"},
        )
        assert approve_response.status_code == 200


class TestPhase4SystemStats:
    """系统统计集成测试"""

    def test_system_stats_endpoint(self, test_client):
        """系统统计端点应返回正确结构"""
        client, mock_session = test_client

        # Mock计数查询
        mock_session.query.return_value.count.return_value = 0
        mock_session.query.return_value.filter.return_value.count.return_value = 0

        response = client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "active_tasks" in data
        assert "completed_tasks" in data
        assert "total_generations" in data


class TestPhase4MonitorUI:
    """监控界面集成测试"""

    def test_monitor_page_accessible(self, test_client):
        """监控界面应可访问"""
        client, _ = test_client

        response = client.get("/monitor")

        # 可能重定向到index.html
        assert response.status_code in [200, 307]


class TestPhase4WebSocket:
    """WebSocket集成测试"""

    def test_websocket_endpoint_exists(self, test_client):
        """WebSocket端点应存在"""
        client, _ = test_client

        # WebSocket连接测试需要特殊处理
        # 这里只验证端点配置正确
        from api.main import app

        # 检查路由中是否包含WebSocket路径
        routes = [route.path for route in app.routes]
        websocket_paths = [r for r in routes if "ws" in r.lower()]

        # 应该有WebSocket路由
        assert len(websocket_paths) > 0 or any(
            "ws" in str(type(r)).lower() for r in app.routes
        )


class TestPhase4FullWorkflow:
    """Phase 4完整工作流集成测试"""

    def test_end_to_end_workflow(self, test_client):
        """端到端完整工作流测试"""
        client, mock_session = test_client

        # Mock所有必要的数据库操作
        mock_task = MagicMock()
        mock_task.id = "e2e-task-123"
        mock_task.name = "e2e_test"
        mock_task.description = "End to end test"
        mock_task.status = "pending"
        mock_task.current_generation = 0
        mock_task.best_score = 0.0
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.updated_at = datetime.now(timezone.utc)
        mock_task.owner_id = "user-123"

        query_mock = MagicMock()
        query_mock.filter.return_value.first.return_value = mock_task
        query_mock.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = (
            []
        )
        query_mock.count.return_value = 1
        mock_session.query.return_value = query_mock

        # 1. 创建任务
        create_response = client.post(
            "/api/tasks",
            json={
                "name": "e2e_test",
                "description": "End to end test task",
                "target_function_signature": "def calculate(x): return x * 2",
                "test_code": "def test_calculate(): assert calculate(5) == 10",
            },
        )
        assert create_response.status_code == 201

        # 2. 健康检查
        health_response = client.get("/health")
        assert health_response.status_code == 200

        # 3. 启动进化
        mock_task.status = "pending"  # 确保状态允许启动
        start_response = client.post(f"/api/tasks/{mock_task.id}/start")
        assert start_response.status_code == 200

        # 4. 查询任务
        get_response = client.get(f"/api/tasks/{mock_task.id}")
        assert get_response.status_code == 200

        # 5. 查询进化历史
        history_response = client.get(f"/api/tasks/{mock_task.id}/generations")
        assert history_response.status_code == 200

        # 6. 中止进化
        abort_response = client.post(f"/api/tasks/{mock_task.id}/abort")
        assert abort_response.status_code == 200

        # 7. 删除任务
        delete_response = client.delete(f"/api/tasks/{mock_task.id}")
        assert delete_response.status_code == 200

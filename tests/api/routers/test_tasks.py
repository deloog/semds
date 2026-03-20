"""测试任务管理路由"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db_session():
    """提供mock数据库会话"""
    session = MagicMock()

    # 模拟查询链式调用
    query_mock = MagicMock()
    session.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None
    query_mock.all.return_value = []

    return session, query_mock


@pytest.fixture
def auth_headers():
    """提供认证头"""
    from api.auth.jwt import create_access_token

    token = create_access_token(data={"sub": "user-123", "role": "user"})
    return {"Authorization": f"Bearer {token}"}


class TestCreateTask:
    """创建任务测试"""

    def test_create_task_returns_201_and_task_data(self, mock_db_session, auth_headers):
        """创建任务应返回201和任务数据"""
        from api.dependencies import get_db_session
        from api.main import app

        session, _ = mock_db_session

        # 模拟refresh操作
        def mock_refresh(obj):
            obj.id = "test-task-id-123"
            obj.status = "pending"
            obj.current_generation = 0
            obj.best_score = 0.0

        session.refresh.side_effect = mock_refresh

        # 覆盖依赖
        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            task_data = {
                "name": "calculator_task",
                "description": "计算器进化任务",
                "target_function_signature": (
                    "def calculate(a: float, b: float, op: str) -> float:"
                ),
                "test_code": "def test_add(): assert calculate(1, 2, '+') == 3",
            }

            response = client.post("/api/tasks", json=task_data, headers=auth_headers)

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == "calculator_task"
            assert data["status"] == "pending"
            assert "id" in data

            # 验证数据库操作被调用
            session.add.assert_called_once()
            session.commit.assert_called_once()
        finally:
            del app.dependency_overrides[get_db_session]

    def test_create_task_with_invalid_data_returns_422(self, auth_headers):
        """无效数据应返回422"""
        from api.main import app

        client = TestClient(app)

        # 缺少必需字段
        invalid_data = {
            "name": "test"
            # 缺少 description, target_function_signature, test_code
        }

        response = client.post("/api/tasks", json=invalid_data, headers=auth_headers)

        assert response.status_code == 422

    def test_create_task_with_empty_name_returns_422(self, auth_headers):
        """空名称应返回422"""
        from api.main import app

        client = TestClient(app)

        task_data = {
            "name": "",
            "description": "test",
            "target_function_signature": "def test():",
            "test_code": "pass",
        }

        response = client.post("/api/tasks", json=task_data, headers=auth_headers)

        assert response.status_code == 422


class TestListTasks:
    """列出任务测试"""

    def test_list_tasks_returns_all_tasks(self, mock_db_session, auth_headers):
        """应返回用户的任务列表"""
        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session

        # 模拟返回的任务列表
        mock_task = MagicMock()
        mock_task.id = "task-1"
        mock_task.name = "test_task"
        mock_task.description = "test description"
        mock_task.status = "pending"
        mock_task.current_generation = 0
        mock_task.best_score = 0.0
        mock_task.target_function_signature = "def test():"
        mock_task.test_file_path = "tests/test.py"
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.updated_at = datetime.now(timezone.utc)
        query_mock.all.return_value = [mock_task]

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.get("/api/tasks", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
        finally:
            del app.dependency_overrides[get_db_session]

    def test_list_tasks_with_status_filter(self, mock_db_session, auth_headers):
        """应支持按状态过滤"""
        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session
        query_mock.all.return_value = []

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.get("/api/tasks?status=pending", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        finally:
            del app.dependency_overrides[get_db_session]


class TestGetTask:
    """获取任务详情测试"""

    def test_get_existing_task_returns_task(self, mock_db_session, auth_headers):
        """获取存在的任务应返回详情"""
        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session

        # 模拟找到任务 - 任务属于当前用户(user-123)
        mock_task = MagicMock()
        mock_task.id = "test-task-id"
        mock_task.name = "test_task"
        mock_task.description = "test description"
        mock_task.status = "pending"
        mock_task.current_generation = 0
        mock_task.best_score = 0.0
        mock_task.target_function_signature = "def test():"
        mock_task.test_file_path = "tests/test.py"
        mock_task.owner_id = "user-123"  # 设置所有者
        mock_task.created_at = datetime.now(timezone.utc)
        mock_task.updated_at = datetime.now(timezone.utc)
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.get("/api/tasks/test-task-id", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "test-task-id"
            assert data["name"] == "test_task"
        finally:
            del app.dependency_overrides[get_db_session]

    def test_get_nonexistent_task_returns_404(self, mock_db_session, auth_headers):
        """获取不存在的任务应返回404"""
        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session
        query_mock.first.return_value = None

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.get("/api/tasks/nonexistent-id", headers=auth_headers)

            assert response.status_code == 404
            data = response.json()
            assert "error" in data or "detail" in data
        finally:
            del app.dependency_overrides[get_db_session]


class TestPathTraversalProtection:
    """路径遍历防护测试"""

    def test_task_name_with_path_traversal_is_sanitized(self, mock_db_session):
        """包含路径遍历字符的任务名应被清理"""
        from api.routers.tasks import sanitize_filename

        # 测试sanitize_filename函数
        # ../../../etc/passwd -> 先替换/为_，再替换..为_ -> ______etc_passwd
        assert sanitize_filename("../../../etc/passwd") == "______etc_passwd"
        assert sanitize_filename("task<name>") == "task_name_"
        assert sanitize_filename("task:name|?*") == "task_name___"
        assert sanitize_filename("task..name") == "task_name"
        assert sanitize_filename("  task  ") == "task"

        # 测试过长名称被截断
        long_name = "a" * 200
        assert len(sanitize_filename(long_name)) == 100


class TestDeleteTask:
    """删除任务测试"""

    @pytest.fixture
    def admin_auth_headers(self):
        """提供管理员认证头（用于删除等需要ADMIN权限的操作）"""
        from api.auth.jwt import create_access_token

        token = create_access_token(data={"sub": "admin-1", "role": "admin"})
        return {"Authorization": f"Bearer {token}"}

    def test_delete_existing_task_returns_success(
        self, mock_db_session, admin_auth_headers
    ):
        """ADMIN删除存在的任务应成功"""
        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session

        # 模拟找到任务
        mock_task = MagicMock()
        mock_task.id = "task-to-delete"
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.delete(
                "/api/tasks/task-to-delete", headers=admin_auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data

            # 验证删除操作
            session.delete.assert_called_once_with(mock_task)
            session.commit.assert_called_once()
        finally:
            del app.dependency_overrides[get_db_session]

    def test_delete_task_forbidden_for_user(self, mock_db_session, auth_headers):
        """普通用户删除任务应返回403（USER角色没有DELETE权限）"""
        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session

        # 模拟找到任务 - 任务属于当前用户
        mock_task = MagicMock()
        mock_task.id = "task-to-delete"
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.delete("/api/tasks/task-to-delete", headers=auth_headers)

            # USER角色没有DELETE权限，应返回403
            assert response.status_code == 403
        finally:
            del app.dependency_overrides[get_db_session]

    def test_delete_nonexistent_task_returns_404(self, mock_db_session, auth_headers):
        """删除不存在的任务应返回404"""
        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session
        query_mock.first.return_value = None

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.delete("/api/tasks/nonexistent-id", headers=auth_headers)

            assert response.status_code == 404
            data = response.json()
            assert "error" in data or "detail" in data
        finally:
            del app.dependency_overrides[get_db_session]

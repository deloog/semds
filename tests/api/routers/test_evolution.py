"""测试进化控制路由"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone


@pytest.fixture
def auth_headers():
    """提供认证头"""
    from api.auth.jwt import create_access_token

    token = create_access_token(data={"sub": "user-123", "role": "user"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_db_session():
    """提供mock数据库会话"""
    session = MagicMock()
    query_mock = MagicMock()
    session.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None
    return session, query_mock


@pytest.fixture
def mock_pending_task():
    """创建一个pending状态的任务mock"""
    task = MagicMock()
    task.id = "task-123"
    task.name = "test_task"
    task.status = "pending"
    task.current_generation = 0
    task.best_score = 0.0
    task.max_generations = 50
    task.owner_id = "user-123"
    return task


@pytest.fixture
def mock_user():
    """创建mock用户"""
    user = MagicMock()
    user.id = "user-123"
    user.username = "testuser"
    user.role = "user"
    return user


class TestStartEvolution:
    """启动进化测试"""

    def test_start_evolution_returns_success(
        self, mock_db_session, mock_pending_task, mock_user, auth_headers
    ):
        """启动进化应返回成功"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session
        query_mock.first.return_value = mock_pending_task

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post("/api/tasks/task-123/start", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "task_id" in data

            # 验证任务状态被更新
            assert mock_pending_task.status == "running"
            session.commit.assert_called_once()
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_start_nonexistent_task_returns_404(
        self, mock_db_session, mock_user, auth_headers
    ):
        """启动不存在的任务应返回404"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session
        query_mock.first.return_value = None

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/tasks/nonexistent-id/start", headers=auth_headers
            )

            assert response.status_code == 404
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_start_already_running_evolution_returns_400(
        self, mock_db_session, mock_user, auth_headers
    ):
        """启动已在运行的进化应返回400"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.status = "running"  # 已经在运行
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post("/api/tasks/task-123/start", headers=auth_headers)

            assert response.status_code == 400
            data = response.json()
            assert "error" in data or "detail" in data
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]


class TestPauseEvolution:
    """暂停进化测试"""

    def test_pause_running_evolution_returns_success(
        self, mock_db_session, mock_user, auth_headers
    ):
        """暂停运行中的进化应成功"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.status = "running"
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post("/api/tasks/task-123/pause", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert mock_task.status == "paused"
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_pause_not_running_evolution_returns_400(
        self, mock_db_session, mock_user, auth_headers
    ):
        """暂停未运行的进化应返回400"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.status = "pending"  # 未运行
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post("/api/tasks/task-123/pause", headers=auth_headers)

            assert response.status_code == 400
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]


class TestResumeEvolution:
    """恢复进化测试"""

    def test_resume_paused_evolution_returns_success(
        self, mock_db_session, mock_user, auth_headers
    ):
        """恢复暂停的进化应成功"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.status = "paused"
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post("/api/tasks/task-123/resume", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert mock_task.status == "running"
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_resume_nonexistent_task_returns_404(
        self, mock_db_session, mock_user, auth_headers
    ):
        """恢复不存在的任务应返回404"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session
        query_mock.first.return_value = None

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/tasks/nonexistent-id/resume", headers=auth_headers
            )

            assert response.status_code == 404
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_resume_from_running_state_returns_400(
        self, mock_db_session, mock_user, auth_headers
    ):
        """从running状态恢复应返回400"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.status = "running"  # running状态不允许恢复
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post("/api/tasks/task-123/resume", headers=auth_headers)

            assert response.status_code == 400
            data = response.json()
            assert "error" in data or "detail" in data
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_resume_from_aborted_state_returns_400(
        self, mock_db_session, mock_user, auth_headers
    ):
        """从aborted状态恢复应返回400"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.status = "aborted"  # aborted状态不允许恢复
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post("/api/tasks/task-123/resume", headers=auth_headers)

            assert response.status_code == 400
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]


class TestAbortEvolution:
    """中止进化测试"""

    def test_abort_evolution_returns_success(
        self, mock_db_session, mock_user, auth_headers
    ):
        """中止进化应返回成功"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.status = "running"
        mock_task.owner_id = "user-123"
        query_mock.first.return_value = mock_task

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post("/api/tasks/task-123/abort", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert mock_task.status == "aborted"
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_abort_nonexistent_task_returns_404(
        self, mock_db_session, mock_user, auth_headers
    ):
        """中止不存在的任务应返回404"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session
        query_mock.first.return_value = None

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/tasks/nonexistent-id/abort", headers=auth_headers
            )

            assert response.status_code == 404
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

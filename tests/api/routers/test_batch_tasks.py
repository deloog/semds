"""测试批量任务操作API"""

from unittest.mock import MagicMock

import pytest  # noqa: F401


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

    # 模拟查询链式调用
    query_mock = MagicMock()
    session.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None
    query_mock.all.return_value = []

    return session, query_mock


class TestBatchCreateTasks:
    """批量创建任务测试"""

    def test_batch_create_tasks_success(self, auth_headers, mock_db_session):
        """批量创建任务应成功"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session

        # 模拟数据库刷新操作，给任务分配ID
        def mock_refresh(obj):
            if not obj.id:
                obj.id = f"task-{obj.name}"
            if not obj.status:
                obj.status = "pending"
            obj.created_at = obj.created_at or MagicMock()
            obj.updated_at = obj.updated_at or MagicMock()

        session.refresh.side_effect = mock_refresh

        # 覆盖依赖
        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            tasks_data = {
                "tasks": [
                    {
                        "name": "task-1",
                        "description": "任务1",
                        "target_function_signature": "def f1(): pass",
                        "test_code": "def test_f1(): pass",
                    },
                    {
                        "name": "task-2",
                        "description": "任务2",
                        "target_function_signature": "def f2(): pass",
                        "test_code": "def test_f2(): pass",
                    },
                ]
            }

            response = client.post(
                "/api/tasks/batch", json=tasks_data, headers=auth_headers
            )

            # 验证响应
            assert response.status_code == 201
            data = response.json()
            assert len(data) == 2
            assert data[0]["name"] == "task-1"
            assert data[1]["name"] == "task-2"

            # 验证数据库操作
            assert session.add.call_count == 2
            session.commit.assert_called_once()
        finally:
            del app.dependency_overrides[get_db_session]

    def test_batch_create_tasks_empty_list(self, auth_headers, mock_db_session):
        """批量创建空任务列表应返回错误"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        session, _ = mock_db_session
        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.post(
                "/api/tasks/batch", json={"tasks": []}, headers=auth_headers
            )

            assert response.status_code == 400
        finally:
            del app.dependency_overrides[get_db_session]

    def test_batch_create_tasks_validation_error(self, auth_headers, mock_db_session):
        """批量创建包含无效数据应返回验证错误"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session
        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            # 空名称会在Pydantic验证层被拒绝
            tasks_data = {
                "tasks": [
                    {
                        "name": "valid-task",
                        "description": "有效任务",
                        "target_function_signature": "def f(): pass",
                        "test_code": "def test_f(): pass",
                    },
                    {
                        "name": "",  # 无效：空名称
                        "description": "无效任务",
                        "target_function_signature": "def f(): pass",
                        "test_code": "def test_f(): pass",
                    },
                ]
            }

            response = client.post(
                "/api/tasks/batch", json=tasks_data, headers=auth_headers
            )

            # Pydantic会在验证层返回422错误
            assert response.status_code == 422
        finally:
            del app.dependency_overrides[get_db_session]


class TestBatchPauseTasks:
    """批量暂停任务测试"""

    def test_batch_pause_tasks_success(self, auth_headers, mock_db_session):
        """批量暂停任务应成功"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app
        from api.schemas import TaskStatus
        from storage.models import Task

        session, query_mock = mock_db_session

        # 创建模拟任务 - 使用枚举值作为status
        mock_task = MagicMock(spec=Task)
        mock_task.id = "task-1"
        mock_task.status = TaskStatus.RUNNING  # 使用枚举值而非字符串
        mock_task.owner_id = "user-123"
        mock_task.name = "Test Task"

        # 模拟IN查询
        def mock_in_filter(*args, **kwargs):
            query_mock.all.return_value = [mock_task]
            return query_mock

        query_mock.filter.side_effect = mock_in_filter

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            request_data = {"task_ids": ["task-1"]}

            response = client.post(
                "/api/tasks/batch/pause", json=request_data, headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "paused" in data
            assert "failed" in data
            assert "task-1" in data["paused"]
        finally:
            del app.dependency_overrides[get_db_session]

    def test_batch_pause_empty_list(self, auth_headers, mock_db_session):
        """批量暂停空列表应返回错误"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        session, _ = mock_db_session
        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            response = client.post(
                "/api/tasks/batch/pause", json={"task_ids": []}, headers=auth_headers
            )

            assert response.status_code == 400
        finally:
            del app.dependency_overrides[get_db_session]


class TestBatchResumeTasks:
    """批量恢复任务测试"""

    def test_batch_resume_tasks_success(self, auth_headers, mock_db_session):
        """批量恢复任务应成功"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app
        from api.schemas import TaskStatus
        from storage.models import Task

        session, query_mock = mock_db_session

        # 创建模拟暂停状态的任务 - 使用枚举值作为status
        mock_task = MagicMock(spec=Task)
        mock_task.id = "task-1"
        mock_task.status = TaskStatus.PAUSED  # 使用枚举值而非字符串
        mock_task.owner_id = "user-123"

        # 模拟IN查询
        def mock_in_filter(*args, **kwargs):
            query_mock.all.return_value = [mock_task]
            return query_mock

        query_mock.filter.side_effect = mock_in_filter

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            request_data = {"task_ids": ["task-1"]}

            response = client.post(
                "/api/tasks/batch/resume", json=request_data, headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "resumed" in data
            assert "failed" in data
            assert "task-1" in data["resumed"]
        finally:
            del app.dependency_overrides[get_db_session]


class TestBatchAbortTasks:
    """批量中止任务测试"""

    def test_batch_abort_tasks_success(self, auth_headers, mock_db_session):
        """批量中止任务应成功"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app
        from api.schemas import TaskStatus
        from storage.models import Task

        session, query_mock = mock_db_session

        # 创建模拟运行状态的任务 - 使用枚举值作为status
        mock_task = MagicMock(spec=Task)
        mock_task.id = "task-1"
        mock_task.status = TaskStatus.RUNNING  # 使用枚举值而非字符串
        mock_task.owner_id = "user-123"

        # 模拟IN查询
        def mock_in_filter(*args, **kwargs):
            query_mock.all.return_value = [mock_task]
            return query_mock

        query_mock.filter.side_effect = mock_in_filter

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            request_data = {"task_ids": ["task-1"]}

            response = client.post(
                "/api/tasks/batch/abort", json=request_data, headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "aborted" in data
            assert "failed" in data
            assert "task-1" in data["aborted"]
        finally:
            del app.dependency_overrides[get_db_session]


class TestBatchDeleteTasks:
    """批量删除任务测试"""

    def test_batch_delete_tasks_success(self, auth_headers, mock_db_session):
        """批量删除任务应成功"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app
        from api.schemas import TaskStatus
        from storage.models import Task

        session, query_mock = mock_db_session

        # 创建模拟任务 - 使用枚举值作为status
        mock_task = MagicMock(spec=Task)
        mock_task.id = "task-1"
        mock_task.owner_id = "user-123"
        mock_task.name = "Test Task"
        mock_task.status = TaskStatus.PENDING  # 使用枚举值而非字符串

        # 模拟IN查询
        def mock_in_filter(*args, **kwargs):
            query_mock.all.return_value = [mock_task]
            return query_mock

        query_mock.filter.side_effect = mock_in_filter

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            request_data = {"task_ids": ["task-1"]}

            response = client.post(
                "/api/tasks/batch/delete", json=request_data, headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert "deleted" in data
            assert "failed" in data
            assert "task-1" in data["deleted"]
        finally:
            del app.dependency_overrides[get_db_session]


class TestBatchOperationValidation:
    """批量操作验证测试"""

    def test_batch_operation_requires_auth(self, mock_db_session):
        """批量操作需要认证"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        session, _ = mock_db_session
        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            # 不带认证头
            response = client.post(
                "/api/tasks/batch/pause", json={"task_ids": ["task-1"]}
            )

            # 应返回401未授权
            assert response.status_code == 401
        finally:
            del app.dependency_overrides[get_db_session]

    def test_batch_operation_task_not_found(self, auth_headers, mock_db_session):
        """批量操作任务不存在应记录在失败列表"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        session, query_mock = mock_db_session

        # 模拟IN查询返回空列表（任务不存在）
        def mock_in_filter(*args, **kwargs):
            query_mock.all.return_value = []
            return query_mock

        query_mock.filter.side_effect = mock_in_filter

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            request_data = {"task_ids": ["nonexistent-task"]}

            response = client.post(
                "/api/tasks/batch/pause", json=request_data, headers=auth_headers
            )

            assert response.status_code == 200
            data = response.json()
            assert len(data["failed"]) == 1
            assert "nonexistent-task" in [f["task_id"] for f in data["failed"]]
        finally:
            del app.dependency_overrides[get_db_session]


class TestBatchOperationLimits:
    """批量操作限制测试"""

    def test_batch_operation_max_limit(self, auth_headers, mock_db_session):
        """批量操作应有最大数量限制"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        session, _ = mock_db_session
        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            # 超过最大限制（假设为100）
            request_data = {"task_ids": [f"task-{i}" for i in range(101)]}

            response = client.post(
                "/api/tasks/batch/pause", json=request_data, headers=auth_headers
            )

            assert response.status_code == 400
            assert "exceeds maximum" in response.json()["detail"].lower()
        finally:
            del app.dependency_overrides[get_db_session]

    def test_batch_operation_duplicate_task_ids(self, auth_headers, mock_db_session):
        """批量操作中重复的task_id应处理多次（每次独立检查状态）"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app
        from api.schemas import TaskStatus
        from storage.models import Task

        session, query_mock = mock_db_session

        # 创建模拟任务 - 使用枚举值作为status
        mock_task = MagicMock(spec=Task)
        mock_task.id = "task-1"
        mock_task.status = TaskStatus.RUNNING  # 使用枚举值而非字符串
        mock_task.owner_id = "user-123"

        # 模拟IN查询返回任务列表
        def mock_in_filter(*args, **kwargs):
            query_mock.all.return_value = [mock_task]
            return query_mock

        query_mock.filter.side_effect = mock_in_filter

        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            # 重复的task_id
            request_data = {"task_ids": ["task-1", "task-1", "task-1"]}

            response = client.post(
                "/api/tasks/batch/pause", json=request_data, headers=auth_headers
            )

            # 应该成功处理 - 第一个成功，后面因为状态已变而失败
            assert response.status_code == 200
            data = response.json()
            # 第一个成功暂停，后面的因为状态不再是RUNNING而失败
            assert len(data["paused"]) == 1
            assert len(data["failed"]) == 2  # 后两个因为状态已变而失败
        finally:
            del app.dependency_overrides[get_db_session]

    def test_batch_operation_empty_task_id(self, auth_headers, mock_db_session):
        """批量操作中空task_id应返回400"""
        from fastapi.testclient import TestClient

        from api.dependencies import get_db_session
        from api.main import app

        session, _ = mock_db_session
        app.dependency_overrides[get_db_session] = lambda: session

        try:
            client = TestClient(app)

            # 包含空字符串task_id
            request_data = {"task_ids": ["", "task-1"]}

            response = client.post(
                "/api/tasks/batch/pause", json=request_data, headers=auth_headers
            )

            assert response.status_code == 400
            assert "empty" in response.json()["detail"].lower()
        finally:
            del app.dependency_overrides[get_db_session]

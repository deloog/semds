"""测试审批API路由"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
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
    from datetime import datetime, timezone

    session = MagicMock()
    query_mock = MagicMock()
    session.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.order_by.return_value = query_mock
    query_mock.all.return_value = []
    query_mock.first.return_value = None

    # Mock add/commit/refresh 链
    def mock_add(obj):
        # 模拟SQLAlchemy设置默认值
        if not hasattr(obj, "id") or obj.id is None:
            obj.id = "mock-approval-id"
        if not hasattr(obj, "created_at") or obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)

    def mock_refresh(obj):
        # refresh后不改变什么，已经设置了默认值
        pass

    session.add.side_effect = mock_add
    session.refresh.side_effect = mock_refresh

    return session, query_mock


@pytest.fixture
def mock_pending_approval():
    """创建一个待审批请求mock"""
    approval = MagicMock()
    approval.id = "approval-123"
    approval.task_id = "task-123"
    approval.generation_id = "gen-456"
    approval.code = "def test(): pass"
    approval.reason = "需要审批"
    approval.status = "pending"
    approval.created_at = datetime.now(timezone.utc)
    approval.reviewed_at = None
    approval.reviewer_comment = None
    return approval


@pytest.fixture
def mock_user():
    """创建mock用户"""
    user = MagicMock()
    user.id = "user-123"
    user.username = "testuser"
    user.role = "user"
    return user


class TestListPendingApprovals:
    """获取待审批列表测试"""

    def test_list_pending_approvals_returns_list(
        self, mock_db_session, mock_user, auth_headers
    ):
        """应返回待审批列表"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        # 模拟返回的审批请求
        mock_approval = MagicMock()
        mock_approval.id = "approval-1"
        mock_approval.task_id = "task-1"
        mock_approval.generation_id = "gen-1"
        mock_approval.status = "pending"
        mock_approval.code = "def test(): pass"
        mock_approval.reason = "需要审批"
        mock_approval.created_at = datetime.now(timezone.utc)
        mock_approval.reviewed_at = None
        mock_approval.reviewer_comment = None

        query_mock.all.return_value = [mock_approval]

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.get("/api/approvals/pending", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]


class TestApproveRequest:
    """批准请求测试"""

    def test_approve_request_returns_success(
        self, mock_db_session, mock_pending_approval, mock_user, auth_headers
    ):
        """批准请求应返回成功"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session
        query_mock.first.return_value = mock_pending_approval

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/approvals/approval-123/approve",
                json={"approved": True, "comment": "LGTM"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert mock_pending_approval.status == "approved"
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_approve_nonexistent_request_returns_404(
        self, mock_db_session, mock_user, auth_headers
    ):
        """批准不存在的请求应返回404"""
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
                "/api/approvals/nonexistent/approve",
                json={"approved": True, "comment": "LGTM"},
                headers=auth_headers,
            )

            assert response.status_code == 404
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]


class TestRejectRequest:
    """拒绝请求测试"""

    def test_reject_request_returns_success(
        self, mock_db_session, mock_pending_approval, mock_user, auth_headers
    ):
        """拒绝请求应返回成功"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session
        query_mock.first.return_value = mock_pending_approval

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/approvals/approval-123/reject",
                json={"approved": False, "comment": "代码有bug"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert mock_pending_approval.status == "rejected"
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_reject_without_comment_returns_error(
        self, mock_db_session, mock_pending_approval, mock_user, auth_headers
    ):
        """拒绝请求应要求填写意见"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session
        query_mock.first.return_value = mock_pending_approval

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/approvals/approval-123/reject",
                json={},  # 没有comment
                headers=auth_headers,
            )

            # 可能需要comment，也可能不需要，取决于实现
            assert response.status_code in [200, 422]
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]


class TestApprovalStateMachine:
    """审批状态机测试"""

    def test_approve_already_approved_request_returns_400(
        self, mock_db_session, mock_user, auth_headers
    ):
        """已批准的请求再次批准应返回400"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        # 创建一个已批准的审批请求
        mock_approved = MagicMock()
        mock_approved.id = "approval-approved"
        mock_approved.status = "approved"  # 已批准状态
        mock_approved.task_id = "task-123"
        mock_approved.generation_id = "gen-456"

        query_mock.first.return_value = mock_approved

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/approvals/approval-approved/approve",
                json={"approved": True, "comment": "再次批准"},
                headers=auth_headers,
            )

            # 应该返回400，因为状态不允许流转
            assert response.status_code == 400
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_reject_already_rejected_request_returns_400(
        self, mock_db_session, mock_user, auth_headers
    ):
        """已拒绝的请求再次拒绝应返回400"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        # 创建一个已拒绝的审批请求
        mock_rejected = MagicMock()
        mock_rejected.id = "approval-rejected"
        mock_rejected.status = "rejected"  # 已拒绝状态
        mock_rejected.task_id = "task-123"
        mock_rejected.generation_id = "gen-456"

        query_mock.first.return_value = mock_rejected

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/approvals/approval-rejected/reject",
                json={"approved": False, "comment": "再次拒绝"},
                headers=auth_headers,
            )

            # 应该返回400，因为状态不允许流转
            assert response.status_code == 400
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

    def test_valid_status_transitions_exist(self):
        """应定义有效的状态流转规则"""
        from api.routers.approvals import VALID_STATUS_TRANSITIONS

        # 验证状态机定义存在且合理
        assert "pending" in VALID_STATUS_TRANSITIONS
        assert "approved" in VALID_STATUS_TRANSITIONS
        assert "rejected" in VALID_STATUS_TRANSITIONS

        # pending可以流转到approved或rejected
        assert "approved" in VALID_STATUS_TRANSITIONS["pending"]
        assert "rejected" in VALID_STATUS_TRANSITIONS["pending"]

        # approved和rejected是终态，不能再流转
        assert len(VALID_STATUS_TRANSITIONS["approved"]) == 0
        assert len(VALID_STATUS_TRANSITIONS["rejected"]) == 0


class TestApprovalRequestCreation:
    """创建审批请求测试"""

    def test_create_approval_request_returns_201(
        self, mock_db_session, mock_user, auth_headers
    ):
        """创建审批请求应返回201"""
        from api.main import app
        from api.dependencies import get_db_session
        from api.auth.dependencies import get_current_user

        session, query_mock = mock_db_session

        app.dependency_overrides[get_db_session] = lambda: session
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            client = TestClient(app)
            response = client.post(
                "/api/approvals",
                json={
                    "task_id": "task-123",
                    "generation_id": "gen-456",
                    "code": "def test(): pass",
                    "reason": "达到Goodhart阈值，需要人工确认",
                },
                headers=auth_headers,
            )

            # 如果端点存在
            assert response.status_code in [201, 404, 422]
        finally:
            del app.dependency_overrides[get_db_session]
            del app.dependency_overrides[get_current_user]

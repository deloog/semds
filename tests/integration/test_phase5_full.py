"""Phase 5 完整集成测试"""

import pytest  # noqa: F401
from unittest.mock import MagicMock, patch


class TestPhase5Authentication:
    """Phase 5 认证系统集成测试"""

    def test_authentication_end_to_end(self):
        """端到端认证流程"""
        from api.auth.jwt import create_access_token, verify_token
        from api.auth.models import User, UserRole

        # 创建用户
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_secret",
            role=UserRole.USER,
        )

        # 创建token
        token = create_access_token(data={"sub": user.id, "role": user.role.value})

        # 验证token
        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == user.id
        assert payload["role"] == user.role.value

    def test_permission_check_integration(self):
        """权限检查集成测试"""
        from api.auth.decorators import check_permission
        from api.auth.permissions import TaskPermission
        from api.auth.models import User, UserRole

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # 用户应有 READ 权限
        check_permission(user, TaskPermission.READ)

        # 验证通过无异常
        assert True


class TestPhase5WebSocket:
    """Phase 5 WebSocket集成测试"""

    def test_websocket_auth_integration(self):
        """WebSocket认证集成"""
        from api.auth.jwt import create_access_token
        from api.routers.monitor import verify_websocket_token

        # 创建token
        token = create_access_token(data={"sub": "user-123", "role": "user"})

        # WebSocket验证
        payload = verify_websocket_token(token)

        assert payload is not None
        assert payload["sub"] == "user-123"

    def test_websocket_permission_integration(self):
        """WebSocket权限集成"""
        from api.auth.models import User, UserRole
        from api.routers.monitor import check_task_permission

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # 模拟用户自己的任务
        mock_task = MagicMock()
        mock_task.owner_id = "user-123"

        # 检查权限
        has_permission = check_task_permission(user, mock_task)

        assert has_permission is True


class TestPhase5TaskManager:
    """Phase 5 任务管理集成测试"""

    def test_task_manager_and_scheduler_integration(self):
        """任务管理器和调度器集成"""
        from factory.task_manager import TaskManager
        from factory.task_scheduler import TaskScheduler, Priority

        # 创建调度器并添加任务
        scheduler = TaskScheduler()
        scheduler.add_task("task-1", {"name": "任务1"})
        scheduler.set_task_priority("task-1", Priority.HIGH)

        # 创建任务管理器并注册任务
        manager = TaskManager()
        manager.register_task("task-1", {"name": "任务1"})

        # 启动任务
        manager.start_task("task-1")

        assert manager.get_task_status("task-1") == "running"

    def test_task_manager_and_isolation_integration(self):
        """任务管理器和隔离管理器集成"""
        from factory.task_manager import TaskManager
        from factory.isolation_manager import IsolationManager
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建隔离环境
            isolation = IsolationManager(base_dir=tmpdir)
            isolation.create_environment("task-1")
            isolation.set_task_strategy("task-1", {"timeout": 300})

            # 创建任务管理器
            manager = TaskManager()
            manager.register_task("task-1", {"name": "任务1"})

            # 验证两者独立工作
            assert isolation.validate_environment("task-1") is True
            assert manager.get_task_status("task-1") == "pending"


class TestPhase5RedisState:
    """Phase 5 Redis状态集成测试"""

    def test_redis_state_manager_integration(self):
        """Redis状态管理器集成"""
        from api.state_redis import RedisStateManager

        with patch("api.state_redis.redis.Redis.from_url") as mock_from_url:
            mock_client = MagicMock()
            mock_from_url.return_value = mock_client

            manager = RedisStateManager()

            # 设置状态
            manager.set_evolution_state("task-1", {"status": "running", "progress": 50})

            # 验证调用
            mock_client.setex.assert_called_once()

    def test_state_migration_integration(self):
        """状态迁移工具集成"""
        from api.state_migration import StateMigration
        from api import state as memory_state

        # 准备内存状态
        memory_state.active_evolutions = {
            "task-1": {"status": "running"},
        }

        with patch("api.state_migration.get_state_manager") as mock_get_manager:
            mock_destination = MagicMock()
            mock_get_manager.return_value = mock_destination

            # 执行迁移
            migrator = StateMigration()
            result = migrator.migrate_all()

            assert result["evolution_states"] == 1

        # 清理
        memory_state.active_evolutions = {}


class TestPhase5FullWorkflow:
    """Phase 5 完整工作流测试"""

    def test_complete_phase5_workflow(self):
        """完整Phase 5工作流

        模拟用户登录 -> 创建任务 -> 调度执行 -> 状态存储的流程
        """
        from api.auth.jwt import create_access_token
        from api.auth.models import User, UserRole
        from factory.task_manager import TaskManager
        from factory.task_scheduler import TaskScheduler, Priority

        # 1. 用户登录获取token
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )
        token = create_access_token(data={"sub": user.id, "role": user.role.value})

        # 2. 创建任务调度器并添加任务
        scheduler = TaskScheduler()
        scheduler.add_task("task-1", {"name": "进化任务"})
        scheduler.set_task_priority("task-1", Priority.HIGH)

        # 3. 任务管理器注册并启动
        manager = TaskManager()
        manager.register_task("task-1", {"name": "进化任务"})
        manager.start_task("task-1")

        # 4. 验证token和任务状态
        from api.auth.jwt import verify_token

        payload = verify_token(token)
        assert payload["sub"] == user.id
        assert manager.get_task_status("task-1") == "running"

        # 5. 完成工作流
        manager.complete_task("task-1")
        assert manager.get_task_status("task-1") == "completed"


class TestPhase5Security:
    """Phase 5 安全性集成测试"""

    def test_admin_can_access_any_task(self):
        """管理员应能访问任何任务"""
        from api.auth.models import User, UserRole
        from api.routers.monitor import check_task_permission

        admin = User(
            id="admin-1",
            username="admin",
            email="admin@example.com",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )

        # 其他用户的任务
        mock_task = MagicMock()
        mock_task.owner_id = "user-999"

        has_permission = check_task_permission(admin, mock_task)

        assert has_permission is True

    def test_user_cannot_access_others_task(self):
        """用户不应能访问他人任务"""
        from api.auth.models import User, UserRole
        from api.routers.monitor import check_task_permission

        user = User(
            id="user-123",
            username="user",
            email="user@example.com",
            hashed_password="hashed",
            role=UserRole.USER,
        )

        # 其他用户的任务
        mock_task = MagicMock()
        mock_task.owner_id = "user-999"

        has_permission = check_task_permission(user, mock_task)

        assert has_permission is False

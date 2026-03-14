"""测试状态迁移工具"""

import pytest  # noqa: F401
from unittest.mock import MagicMock, patch


class TestStateMigrationInitialization:
    """状态迁移工具初始化测试"""

    def test_migration_tool_initialization(self):
        """迁移工具应正确初始化"""
        from api.state_migration import StateMigration

        migrator = StateMigration()

        assert migrator.source is not None
        assert migrator.destination is not None


class TestStateMigrationEvolution:
    """进化状态迁移测试"""

    def test_migrate_evolution_state(self):
        """应能迁移进化状态"""
        from api.state_migration import StateMigration

        migrator = StateMigration()

        # 模拟源数据
        migrator.source.active_evolutions = {
            "task-1": {"status": "running", "progress": 50},
            "task-2": {"status": "completed", "progress": 100},
        }

        with patch.object(migrator.destination, "set_evolution_state") as mock_set:
            count = migrator.migrate_evolution_states()

            assert count == 2
            assert mock_set.call_count == 2

    def test_migrate_empty_evolution_state(self):
        """空进化状态应返回0"""
        from api.state_migration import StateMigration

        migrator = StateMigration()
        migrator.source.active_evolutions = {}

        count = migrator.migrate_evolution_states()

        assert count == 0


class TestStateMigrationConnections:
    """连接状态迁移测试"""

    def test_migrate_connections(self):
        """应能迁移连接状态"""
        from api.state_migration import StateMigration

        migrator = StateMigration()

        # 模拟源数据
        migrator.source.connections = {
            "task-1": MagicMock(),
            "task-2": MagicMock(),
        }

        with patch.object(migrator.destination, "register_connection") as mock_reg:
            count = migrator.migrate_connections()

            assert count == 2
            assert mock_reg.call_count == 2


class TestStateMigrationAll:
    """全量迁移测试"""

    def test_migrate_all(self):
        """应能迁移所有状态"""
        from api.state_migration import StateMigration

        migrator = StateMigration()

        migrator.source.active_evolutions = {"task-1": {"status": "running"}}
        migrator.source.connections = {"task-1": MagicMock()}

        with (
            patch.object(migrator, "migrate_evolution_states") as mock_evol,
            patch.object(migrator, "migrate_connections") as mock_conn,
        ):
            mock_evol.return_value = 1
            mock_conn.return_value = 1

            result = migrator.migrate_all()

            assert result["evolution_states"] == 1
            assert result["connections"] == 1


class TestStateMigrationVerification:
    """迁移验证测试"""

    def test_verify_migration_success(self):
        """验证成功应返回True"""
        from api.state_migration import StateMigration

        migrator = StateMigration()

        with (
            patch.object(migrator.destination, "get_evolution_state") as mock_get,
            patch.object(migrator.destination, "get_active_connections") as mock_conns,
        ):
            mock_get.return_value = {"status": "running"}
            mock_conns.return_value = ["task-1"]

            is_valid = migrator.verify_migration(["task-1"])

            assert is_valid is True

    def test_verify_migration_failure(self):
        """验证失败应返回False"""
        from api.state_migration import StateMigration

        migrator = StateMigration()

        with patch.object(migrator.destination, "get_evolution_state") as mock_get:
            mock_get.return_value = None

            is_valid = migrator.verify_migration(["task-1"])

            assert is_valid is False


class TestStateMigrationDryRun:
    """试运行测试"""

    def test_dry_run(self):
        """试运行应返回要迁移的数据统计"""
        from api.state_migration import StateMigration

        migrator = StateMigration()
        migrator.source.active_evolutions = {"task-1": {}, "task-2": {}}
        migrator.source.connections = {"task-1": MagicMock()}

        stats = migrator.dry_run()

        assert stats["evolution_states"] == 2
        assert stats["connections"] == 1

"""测试隔离管理器"""

import pytest
from pathlib import Path


class TestIsolationManagerInitialization:
    """隔离管理器初始化测试"""

    def test_isolation_manager_initialization(self):
        """隔离管理器应正确初始化"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager(base_dir="/tmp/test_isolation")

        assert manager.base_dir == Path("/tmp/test_isolation")

    def test_isolation_manager_default_base_dir(self):
        """隔离管理器应使用默认基础目录"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()

        assert "isolated_envs" in str(manager.base_dir)


class TestIsolationManagerEnvironment:
    """隔离环境管理测试"""

    def test_create_isolated_environment(self):
        """应能为任务创建隔离环境"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        env_path = manager.create_environment("task-1")

        assert "task-1" in str(env_path)
        assert env_path.exists()

    def test_create_duplicate_environment_raises_error(self):
        """创建重复环境应抛出错误"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")

        with pytest.raises(ValueError, match="Environment already exists"):
            manager.create_environment("task-1")

    def test_get_environment_path(self):
        """应能获取任务环境路径"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")

        env_path = manager.get_environment_path("task-1")

        assert "task-1" in str(env_path)

    def test_get_nonexistent_environment_raises_error(self):
        """获取不存在的环境应抛出错误"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()

        with pytest.raises(KeyError, match="Environment not found"):
            manager.get_environment_path("nonexistent")


class TestIsolationManagerStrategy:
    """策略隔离测试"""

    def test_set_task_strategy(self):
        """应能设置任务策略"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")

        manager.set_task_strategy("task-1", {"timeout": 300, "max_iterations": 100})

        assert "task-1" in manager._strategies
        assert manager._strategies["task-1"]["timeout"] == 300

    def test_get_task_strategy(self):
        """应能获取任务策略"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")
        manager.set_task_strategy("task-1", {"timeout": 300})

        strategy = manager.get_task_strategy("task-1")

        assert strategy["timeout"] == 300

    def test_get_default_strategy_for_unset_task(self):
        """未设置策略的任务应返回默认值"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")

        strategy = manager.get_task_strategy("task-1")

        assert strategy == {}

    def test_strategy_isolation_between_tasks(self):
        """不同任务的策略应相互隔离"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")
        manager.create_environment("task-2")

        manager.set_task_strategy("task-1", {"timeout": 100})
        manager.set_task_strategy("task-2", {"timeout": 200})

        strategy1 = manager.get_task_strategy("task-1")
        strategy2 = manager.get_task_strategy("task-2")

        assert strategy1["timeout"] == 100
        assert strategy2["timeout"] == 200


class TestIsolationManagerCleanup:
    """环境清理测试"""

    def test_remove_environment(self):
        """应能移除任务环境"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")

        manager.remove_environment("task-1")

        assert "task-1" not in manager._environments
        assert "task-1" not in manager._strategies

    def test_remove_nonexistent_environment_raises_error(self):
        """移除不存在的环境应抛出错误"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()

        with pytest.raises(KeyError, match="Environment not found"):
            manager.remove_environment("nonexistent")

    def test_list_environments(self):
        """应能列出所有环境"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")
        manager.create_environment("task-2")

        envs = manager.list_environments()

        assert "task-1" in envs
        assert "task-2" in envs


class TestIsolationManagerValidation:
    """环境验证测试"""

    def test_validate_environment_exists(self):
        """应能验证环境是否存在"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()
        manager.create_environment("task-1")

        assert manager.validate_environment("task-1") is True

    def test_validate_environment_not_exists(self):
        """验证不存在的环境应返回False"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager()

        assert manager.validate_environment("nonexistent") is False

    def test_environment_persistence_check(self, tmp_path):
        """环境目录应在文件系统上存在"""
        from factory.isolation_manager import IsolationManager

        manager = IsolationManager(base_dir=str(tmp_path))
        env_path = manager.create_environment("task-1")

        assert env_path.exists()
        assert env_path.is_dir()

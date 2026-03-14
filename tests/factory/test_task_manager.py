"""测试任务管理器"""

import pytest


class TestTaskManagerInitialization:
    """任务管理器初始化测试"""

    def test_task_manager_initialization(self):
        """任务管理器应正确初始化"""
        from factory.task_manager import TaskManager

        manager = TaskManager(max_concurrent_tasks=3)

        assert manager.max_concurrent == 3
        assert len(manager._tasks) == 0
        assert manager._running == 0

    def test_task_manager_default_max_concurrent(self):
        """任务管理器应使用默认并发数"""
        from factory.task_manager import TaskManager

        manager = TaskManager()

        assert manager.max_concurrent == 5  # 默认值


class TestTaskManagerTaskRegistration:
    """任务注册测试"""

    def test_register_task(self):
        """应能注册新任务"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        task_id = manager.register_task("task-1", {"name": "测试任务"})

        assert task_id == "task-1"
        assert "task-1" in manager._tasks
        assert manager._tasks["task-1"]["status"] == "pending"

    def test_register_duplicate_task_raises_error(self):
        """注册重复任务应抛出错误"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        manager.register_task("task-1", {"name": "测试任务"})

        with pytest.raises(ValueError, match="Task already exists"):
            manager.register_task("task-1", {"name": "重复任务"})


class TestTaskManagerTaskStatus:
    """任务状态管理测试"""

    def test_update_task_status(self):
        """应能更新任务状态"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        manager.register_task("task-1", {"name": "测试任务"})

        manager.update_task_status("task-1", "running")

        assert manager._tasks["task-1"]["status"] == "running"

    def test_update_nonexistent_task_raises_error(self):
        """更新不存在的任务应抛出错误"""
        from factory.task_manager import TaskManager

        manager = TaskManager()

        with pytest.raises(KeyError, match="Task not found"):
            manager.update_task_status("nonexistent", "running")

    def test_get_task_status(self):
        """应能获取任务状态"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        manager.register_task("task-1", {"name": "测试任务"})
        manager.update_task_status("task-1", "running")

        status = manager.get_task_status("task-1")

        assert status == "running"

    def test_get_nonexistent_task_status_raises_error(self):
        """获取不存在的任务状态应抛出错误"""
        from factory.task_manager import TaskManager

        manager = TaskManager()

        with pytest.raises(KeyError, match="Task not found"):
            manager.get_task_status("nonexistent")


class TestTaskManagerConcurrency:
    """并发控制测试"""

    def test_can_start_task_when_under_limit(self):
        """并发数未达限制时应能启动任务"""
        from factory.task_manager import TaskManager

        manager = TaskManager(max_concurrent_tasks=2)

        assert manager.can_start_task() is True

    def test_cannot_start_task_when_at_limit(self):
        """并发数达限制时不应能启动任务"""
        from factory.task_manager import TaskManager

        manager = TaskManager(max_concurrent_tasks=1)
        manager.register_task("task-1", {"name": "任务1"})
        manager.update_task_status("task-1", "running")
        manager._running = 1

        assert manager.can_start_task() is False

    def test_start_task_increments_running_count(self):
        """启动任务应增加运行计数"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        manager.register_task("task-1", {"name": "任务1"})

        manager.start_task("task-1")

        assert manager._running == 1
        assert manager._tasks["task-1"]["status"] == "running"

    def test_complete_task_decrements_running_count(self):
        """完成任务应减少运行计数"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        manager.register_task("task-1", {"name": "任务1"})
        manager.start_task("task-1")

        manager.complete_task("task-1")

        assert manager._running == 0
        assert manager._tasks["task-1"]["status"] == "completed"


class TestTaskManagerCleanup:
    """任务清理测试"""

    def test_remove_task(self):
        """应能移除任务"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        manager.register_task("task-1", {"name": "测试任务"})

        manager.remove_task("task-1")

        assert "task-1" not in manager._tasks

    def test_remove_running_task_decrements_count(self):
        """移除运行中的任务应减少运行计数"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        manager.register_task("task-1", {"name": "任务1"})
        manager.start_task("task-1")

        manager.remove_task("task-1")

        assert manager._running == 0

    def test_get_all_tasks(self):
        """应能获取所有任务"""
        from factory.task_manager import TaskManager

        manager = TaskManager()
        manager.register_task("task-1", {"name": "任务1"})
        manager.register_task("task-2", {"name": "任务2"})

        tasks = manager.get_all_tasks()

        assert len(tasks) == 2
        assert "task-1" in tasks
        assert "task-2" in tasks

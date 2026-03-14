"""测试任务调度器"""

import pytest


class TestTaskSchedulerInitialization:
    """任务调度器初始化测试"""

    def test_task_scheduler_initialization(self):
        """任务调度器应正确初始化"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()

        assert scheduler._queue == []
        assert scheduler._priorities == {}


class TestTaskSchedulerPriority:
    """任务优先级管理测试"""

    def test_set_task_priority(self):
        """应能设置任务优先级"""
        from factory.task_scheduler import TaskScheduler, Priority

        scheduler = TaskScheduler()
        scheduler.set_task_priority("task-1", Priority.HIGH)

        assert scheduler._priorities["task-1"] == Priority.HIGH

    def test_get_task_priority(self):
        """应能获取任务优先级"""
        from factory.task_scheduler import TaskScheduler, Priority

        scheduler = TaskScheduler()
        scheduler.set_task_priority("task-1", Priority.NORMAL)

        priority = scheduler.get_task_priority("task-1")

        assert priority == Priority.NORMAL

    def test_get_default_priority_for_unset_task(self):
        """未设置优先级的任务应返回默认值"""
        from factory.task_scheduler import TaskScheduler, Priority

        scheduler = TaskScheduler()

        priority = scheduler.get_task_priority("task-1")

        assert priority == Priority.NORMAL


class TestTaskSchedulerQueue:
    """任务队列测试"""

    def test_add_task_to_queue(self):
        """应能将任务加入队列"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        scheduler.add_task("task-1", {"name": "任务1"})

        assert len(scheduler._queue) == 1
        assert scheduler._queue[0].id == "task-1"

    def test_add_duplicate_task_raises_error(self):
        """添加重复任务应抛出错误"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        scheduler.add_task("task-1", {"name": "任务1"})

        with pytest.raises(ValueError, match="Task already in queue"):
            scheduler.add_task("task-1", {"name": "任务1"})

    def test_get_next_task_returns_highest_priority(self):
        """应返回优先级最高的任务"""
        from factory.task_scheduler import TaskScheduler, Priority

        scheduler = TaskScheduler()
        scheduler.set_task_priority("task-2", Priority.HIGH)
        scheduler.add_task("task-1", {"name": "低优先级"})
        scheduler.add_task("task-2", {"name": "高优先级"})
        scheduler.set_task_priority("task-2", Priority.HIGH)
        scheduler.set_task_priority("task-1", Priority.LOW)

        next_task = scheduler.get_next_task()

        assert next_task["id"] == "task-2"

    def test_get_next_task_returns_none_when_empty(self):
        """队列为空时应返回None"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()

        next_task = scheduler.get_next_task()

        assert next_task is None

    def test_get_next_task_removes_from_queue(self):
        """获取任务后应从队列中移除"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        scheduler.add_task("task-1", {"name": "任务1"})

        scheduler.get_next_task()

        assert len(scheduler._queue) == 0

    def test_same_priority_fifo_order(self):
        """相同优先级应按FIFO顺序"""
        from factory.task_scheduler import TaskScheduler, Priority

        scheduler = TaskScheduler()
        scheduler.add_task("task-1", {"name": "任务1"})
        scheduler.add_task("task-2", {"name": "任务2"})
        # 相同优先级
        scheduler.set_task_priority("task-1", Priority.NORMAL)
        scheduler.set_task_priority("task-2", Priority.NORMAL)

        first = scheduler.get_next_task()
        second = scheduler.get_next_task()

        assert first["id"] == "task-1"
        assert second["id"] == "task-2"


class TestTaskSchedulerRemove:
    """任务移除测试"""

    def test_remove_task_from_queue(self):
        """应从队列中移除任务"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        scheduler.add_task("task-1", {"name": "任务1"})

        scheduler.remove_task("task-1")

        assert len(scheduler._queue) == 0
        assert "task-1" not in scheduler._priorities

    def test_remove_nonexistent_task_raises_error(self):
        """移除不存在的任务应抛出错误"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()

        with pytest.raises(KeyError, match="Task not found"):
            scheduler.remove_task("nonexistent")


class TestTaskSchedulerSize:
    """队列大小测试"""

    def test_queue_size(self):
        """应能获取队列大小"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        assert scheduler.queue_size() == 0

        scheduler.add_task("task-1", {"name": "任务1"})
        assert scheduler.queue_size() == 1

        scheduler.add_task("task-2", {"name": "任务2"})
        assert scheduler.queue_size() == 2

    def test_is_empty(self):
        """应能检查队列是否为空"""
        from factory.task_scheduler import TaskScheduler

        scheduler = TaskScheduler()
        assert scheduler.is_empty() is True

        scheduler.add_task("task-1", {"name": "任务1"})
        assert scheduler.is_empty() is False

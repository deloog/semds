"""任务管理器模块

提供多任务并发管理功能，包括任务注册、状态管理、并发控制等。
对应 SEMDS_v1.1_SPEC.md 多任务并发管理需求。
"""

import threading
from datetime import datetime, timezone
from typing import Any, Dict


class TaskManager:
    """任务管理器

    管理任务的注册、状态变更和并发控制。
    支持最大并发数限制，防止资源过载。

    Attributes:
        max_concurrent: 最大并发任务数
        _tasks: 任务字典，key为task_id，value为任务信息
        _running: 当前运行中的任务数

    Example:
        >>> manager = TaskManager(max_concurrent_tasks=3)
        >>> manager.register_task("task-1", {"name": "测试任务"})
        >>> manager.start_task("task-1")
        >>> manager.complete_task("task-1")
    """

    DEFAULT_MAX_CONCURRENT = 5  # 默认最大并发数

    def __init__(self, max_concurrent_tasks: int = DEFAULT_MAX_CONCURRENT):
        """初始化任务管理器

        Args:
            max_concurrent_tasks: 最大并发任务数，默认为5

        Raises:
            ValueError: 如果max_concurrent_tasks小于1
        """
        if max_concurrent_tasks < 1:
            raise ValueError("max_concurrent_tasks must be at least 1")

        self.max_concurrent = max_concurrent_tasks
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._running = 0
        self._lock = threading.Lock()  # 线程锁，保证并发安全

    def register_task(self, task_id: str, task_info: Dict[str, Any]) -> str:
        """注册新任务

        将任务添加到管理器中，初始状态为pending。

        Args:
            task_id: 任务唯一标识
            task_info: 任务信息字典

        Returns:
            任务ID

        Raises:
            ValueError: 如果任务ID已存在
        """
        with self._lock:
            if task_id in self._tasks:
                raise ValueError(f"Task already exists: {task_id}")

            self._tasks[task_id] = {
                **task_info,
                "id": task_id,
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
                "started_at": None,
                "completed_at": None,
            }

            return task_id

    def update_task_status(self, task_id: str, status: str) -> None:
        """更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态

        Raises:
            KeyError: 如果任务不存在
        """
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            self._tasks[task_id]["status"] = status

            if status == "running":
                self._tasks[task_id]["started_at"] = datetime.now(timezone.utc)
            elif status in ("completed", "failed"):
                self._tasks[task_id]["completed_at"] = datetime.now(timezone.utc)

    def get_task_status(self, task_id: str) -> str:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态字符串

        Raises:
            KeyError: 如果任务不存在
        """
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            return self._tasks[task_id]["status"]

    def can_start_task(self) -> bool:
        """检查是否可以启动新任务

        根据当前运行任务数和最大并发数判断。

        Returns:
            True如果可以启动，False如果已达到并发限制
        """
        with self._lock:
            return self._running < self.max_concurrent

    def start_task(self, task_id: str) -> None:
        """启动任务

        将任务状态更新为running，并增加运行计数。

        Args:
            task_id: 任务ID

        Raises:
            KeyError: 如果任务不存在
            RuntimeError: 如果已达到并发限制
        """
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            if self._running >= self.max_concurrent:
                raise RuntimeError("Max concurrent tasks reached")

            self._running += 1
            self._tasks[task_id]["status"] = "running"
            self._tasks[task_id]["started_at"] = datetime.now(timezone.utc)

    def complete_task(self, task_id: str) -> None:
        """完成任务

        将任务状态更新为completed，并减少运行计数。

        Args:
            task_id: 任务ID

        Raises:
            KeyError: 如果任务不存在
        """
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            if self._tasks[task_id]["status"] == "running":
                self._running -= 1

            self._tasks[task_id]["status"] = "completed"
            self._tasks[task_id]["completed_at"] = datetime.now(timezone.utc)

    def remove_task(self, task_id: str) -> None:
        """移除任务

        从管理器中删除任务。如果任务正在运行，会减少运行计数。

        Args:
            task_id: 任务ID

        Raises:
            KeyError: 如果任务不存在
        """
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            # 如果任务正在运行，减少计数
            if self._tasks[task_id]["status"] == "running":
                self._running -= 1

            del self._tasks[task_id]

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务

        Returns:
            任务字典的副本
        """
        with self._lock:
            return dict(self._tasks)

    def get_task_info(self, task_id: str) -> Dict[str, Any]:
        """获取任务详细信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典

        Raises:
            KeyError: 如果任务不存在
        """
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"Task not found: {task_id}")

            return dict(self._tasks[task_id])


__all__ = ["TaskManager"]

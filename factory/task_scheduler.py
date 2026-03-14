"""任务调度器模块

提供基于优先级的任务队列调度功能。
支持高/中/低优先级，相同优先级按FIFO顺序处理。
对应 SEMDS_v1.1_SPEC.md 任务队列调度需求。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Dict, List, Optional


class Priority(IntEnum):
    """任务优先级枚举

    数值越小优先级越高（方便堆排序）
    """

    CRITICAL = 0  # 紧急
    HIGH = 1  # 高
    NORMAL = 2  # 正常（默认）
    LOW = 3  # 低


@dataclass
class TaskQueueItem:
    """任务队列项

    包含任务信息和排序所需的元数据。
    """

    id: str
    data: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    enqueued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __lt__(self, other: "TaskQueueItem") -> bool:
        """比较方法，用于优先级排序

        优先级数值小的排在前面，相同优先级按入队时间FIFO。
        """
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.enqueued_at < other.enqueued_at


class TaskScheduler:
    """任务调度器

    管理任务队列，支持优先级调度和FIFO顺序。

    Attributes:
        _queue: 任务队列列表
        _priorities: 任务优先级字典
        _task_ids: 用于快速检查任务是否存在

    Example:
        >>> scheduler = TaskScheduler()
        >>> scheduler.add_task("task-1", {"name": "重要任务"})
        >>> scheduler.set_task_priority("task-1", Priority.HIGH)
        >>> next_task = scheduler.get_next_task()
    """

    def __init__(self):
        """初始化任务调度器"""
        self._queue: List[TaskQueueItem] = []
        self._priorities: Dict[str, Priority] = {}
        self._task_ids: set = set()

    def set_task_priority(self, task_id: str, priority: Priority) -> None:
        """设置任务优先级

        Args:
            task_id: 任务ID
            priority: 优先级枚举值
        """
        self._priorities[task_id] = priority

    def get_task_priority(self, task_id: str) -> Priority:
        """获取任务优先级

        Args:
            task_id: 任务ID

        Returns:
            优先级枚举值，未设置则返回NORMAL
        """
        return self._priorities.get(task_id, Priority.NORMAL)

    def add_task(self, task_id: str, task_data: Dict[str, Any]) -> None:
        """添加任务到队列

        Args:
            task_id: 任务ID
            task_data: 任务数据字典

        Raises:
            ValueError: 如果任务已在队列中
        """
        if task_id in self._task_ids:
            raise ValueError(f"Task already in queue: {task_id}")

        priority = self.get_task_priority(task_id)
        item = TaskQueueItem(id=task_id, data=task_data, priority=priority)

        self._queue.append(item)
        self._task_ids.add(task_id)

        # 重新排序队列（保持优先级顺序）
        self._queue.sort()

    def get_next_task(self) -> Optional[Dict[str, Any]]:
        """获取下一个任务

        返回优先级最高的任务，相同优先级按FIFO。

        Returns:
            任务数据字典，队列为空则返回None
        """
        if not self._queue:
            return None

        item = self._queue.pop(0)
        self._task_ids.discard(item.id)

        return {"id": item.id, **item.data}

    def remove_task(self, task_id: str) -> None:
        """从队列中移除任务

        Args:
            task_id: 任务ID

        Raises:
            KeyError: 如果任务不存在
        """
        if task_id not in self._task_ids:
            raise KeyError(f"Task not found: {task_id}")

        self._queue = [item for item in self._queue if item.id != task_id]
        self._task_ids.discard(task_id)
        self._priorities.pop(task_id, None)

    def queue_size(self) -> int:
        """获取队列大小

        Returns:
            队列中的任务数量
        """
        return len(self._queue)

    def is_empty(self) -> bool:
        """检查队列是否为空

        Returns:
            True如果队列为空
        """
        return len(self._queue) == 0

    def peek_next_task(self) -> Optional[Dict[str, Any]]:
        """查看下一个任务（不移除）

        Returns:
            任务数据字典，队列为空则返回None
        """
        if not self._queue:
            return None

        item = self._queue[0]
        return {"id": item.id, **item.data}


__all__ = ["TaskScheduler", "Priority", "TaskQueueItem"]

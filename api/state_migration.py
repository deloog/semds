"""状态迁移工具模块

支持将内存状态迁移到Redis，用于多Worker部署升级。
对应 SEMDS_v1.1_SPEC.md 状态迁移需求。
"""

from typing import Any, Dict, List, Optional

from api import state as memory_state
from api.state_redis import RedisStateManager, get_state_manager


class StateMigration:
    """状态迁移工具

    将内存状态（api.state）迁移到Redis（api.state_redis）。
    支持试运行、全量迁移和迁移验证。

    Attributes:
        source: 源状态（内存）
        destination: 目标状态（Redis）

    Example:
        >>> migrator = StateMigration()
        >>> stats = migrator.dry_run()  # 试运行
        >>> result = migrator.migrate_all()  # 执行迁移
        >>> is_valid = migrator.verify_migration(task_ids)  # 验证
    """

    def __init__(
        self,
        source: Optional[Any] = None,
        destination: Optional[RedisStateManager] = None,
    ):
        """初始化迁移工具

        Args:
            source: 源状态模块，默认为内存状态
            destination: 目标状态管理器，默认为Redis
        """
        self.source = source or memory_state
        self.destination = destination or get_state_manager()

    def migrate_evolution_states(self) -> int:
        """迁移进化状态

        Returns:
            迁移的任务数量
        """
        count = 0
        for task_id, state in list(self.source.active_evolutions.items()):
            self.destination.set_evolution_state(task_id, state)
            count += 1
        return count

    def migrate_connections(self) -> int:
        """迁移连接状态

        Note:
            WebSocket连接对象无法序列化，只记录连接标识。

        Returns:
            迁移的连接数量
        """
        count = 0
        for task_id in list(self.source.connections.keys()):
            # 使用task_id作为connection_id（简化处理）
            self.destination.register_connection(task_id, task_id)
            count += 1
        return count

    def migrate_all(self) -> Dict[str, int]:
        """执行全量迁移

        Returns:
            迁移结果统计
        """
        return {
            "evolution_states": self.migrate_evolution_states(),
            "connections": self.migrate_connections(),
        }

    def verify_migration(self, task_ids: List[str]) -> bool:
        """验证迁移结果

        检查指定任务的状态是否正确迁移。

        Args:
            task_ids: 要验证的任务ID列表

        Returns:
            True如果验证通过
        """
        for task_id in task_ids:
            # 验证进化状态
            state = self.destination.get_evolution_state(task_id)
            if state is None:
                return False

        return True

    def dry_run(self) -> Dict[str, int]:
        """试运行

        返回要迁移的数据统计，不实际执行迁移。

        Returns:
            数据统计
        """
        return {
            "evolution_states": len(self.source.active_evolutions),
            "connections": len(self.source.connections),
        }


__all__ = ["StateMigration"]

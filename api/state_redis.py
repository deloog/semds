"""Redis状态存储模块

使用Redis替代内存存储，支持多Worker部署和状态持久化。
故障时自动降级到内存存储。
对应 SEMDS_v1.1_SPEC.md Redis持久化需求。
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import redis

# 导入内存状态作为降级备份
from api import state as memory_state

logger = logging.getLogger(__name__)


class RedisStateManager:
    """Redis状态管理器

    使用Redis存储共享状态，包括进化任务状态和WebSocket连接信息。
    支持自动过期（TTL）和状态持久化。

    Attributes:
        redis_url: Redis连接URL
        _redis: Redis客户端实例（延迟连接）
        DEFAULT_TTL: 默认过期时间（秒）

    Example:
        >>> manager = RedisStateManager("redis://localhost:6379/0")
        >>> manager.set_evolution_state("task-1", {"status": "running"})
        >>> state = manager.get_evolution_state("task-1")
    """

    DEFAULT_TTL = 3600  # 默认过期时间1小时
    KEY_PREFIX_EVOLUTION = "evolution"
    KEY_PREFIX_CONNECTION = "connection"

    def __init__(self, redis_url: Optional[str] = None):
        """初始化Redis状态管理器

        Args:
            redis_url: Redis连接URL，默认从环境变量获取
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis: Optional[redis.Redis] = None

    def get_client(self) -> redis.Redis:
        """获取Redis客户端

        延迟连接，首次调用时创建连接。

        Returns:
            Redis客户端实例

        Raises:
            redis.ConnectionError: 连接失败时
        """
        if self._redis is None:
            self._redis = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
            )
        return self._redis

    def _make_key(self, prefix: str, task_id: str) -> str:
        """生成Redis键名

        Args:
            prefix: 键前缀
            task_id: 任务ID

        Returns:
            完整键名
        """
        return f"{prefix}:{task_id}"

    def set_evolution_state(
        self, task_id: str, state: Dict[str, Any], ttl: Optional[int] = None
    ) -> None:
        """设置进化状态

        Args:
            task_id: 任务ID
            state: 状态字典
            ttl: 过期时间（秒），默认1小时

        Note:
            Redis故障时降级到内存存储
        """
        try:
            client = self.get_client()
            key = self._make_key(self.KEY_PREFIX_EVOLUTION, task_id)
            ttl = ttl or self.DEFAULT_TTL

            client.setex(key, ttl, json.dumps(state))
        except redis.ConnectionError:
            logger.warning(
                f"Redis unavailable, falling back to memory state for {task_id}"
            )
            memory_state.active_evolutions[task_id] = state

    def get_evolution_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取进化状态

        Args:
            task_id: 任务ID

        Returns:
            状态字典，不存在则返回None

        Note:
            Redis故障时降级到内存存储
        """
        try:
            client = self.get_client()
            key = self._make_key(self.KEY_PREFIX_EVOLUTION, task_id)

            data = client.get(key)
            if data is None:
                return None

            return json.loads(data)
        except redis.ConnectionError:
            logger.warning(
                f"Redis unavailable, falling back to memory state for {task_id}"
            )
            return memory_state.active_evolutions.get(task_id)

    def delete_evolution_state(self, task_id: str) -> None:
        """删除进化状态

        Args:
            task_id: 任务ID
        """
        client = self.get_client()
        key = self._make_key(self.KEY_PREFIX_EVOLUTION, task_id)

        client.delete(key)

    def register_connection(
        self, task_id: str, connection_id: str, ttl: Optional[int] = None
    ) -> None:
        """注册WebSocket连接

        Args:
            task_id: 任务ID
            connection_id: 连接标识
            ttl: 过期时间（秒），默认1小时
        """
        client = self.get_client()
        key = self._make_key(self.KEY_PREFIX_CONNECTION, task_id)
        ttl = ttl or self.DEFAULT_TTL

        client.setex(key, ttl, connection_id)

    def unregister_connection(self, task_id: str) -> None:
        """注销WebSocket连接

        Args:
            task_id: 任务ID
        """
        client = self.get_client()
        key = self._make_key(self.KEY_PREFIX_CONNECTION, task_id)

        client.delete(key)

    def get_active_connections(self) -> List[str]:
        """获取活跃连接列表

        Returns:
            任务ID列表
        """
        client = self.get_client()
        pattern = f"{self.KEY_PREFIX_CONNECTION}:*"

        keys = client.keys(pattern)
        # 提取task_id（去掉前缀）
        prefix_len = len(self.KEY_PREFIX_CONNECTION) + 1  # +1 for colon
        return [key[prefix_len:] for key in keys]

    def health_check(self) -> bool:
        """健康检查

        检查Redis连接是否正常。

        Returns:
            True如果连接正常，False如果异常
        """
        try:
            client = self.get_client()
            return client.ping()
        except Exception:
            return False

    def close(self) -> None:
        """关闭Redis连接"""
        if self._redis is not None:
            self._redis.close()
            self._redis = None


# 全局实例（单例模式）
_state_manager: Optional[RedisStateManager] = None


def get_state_manager() -> RedisStateManager:
    """获取全局状态管理器实例

    Returns:
        RedisStateManager实例
    """
    global _state_manager
    if _state_manager is None:
        _state_manager = RedisStateManager()
    return _state_manager


def reset_state_manager() -> None:
    """重置全局状态管理器（用于测试）"""
    global _state_manager
    if _state_manager is not None:
        _state_manager.close()
    _state_manager = None


__all__ = [
    "RedisStateManager",
    "get_state_manager",
    "reset_state_manager",
]

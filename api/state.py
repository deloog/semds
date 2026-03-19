"""API全局状态管理

统一管理跨模块的共享状态，避免重复定义和数据不一致。

注意：当前使用内存存储，多Worker部署时需要改用Redis。
"""

from typing import Dict, Any

# WebSocket连接存储
# key: task_id, value: WebSocket对象
connections: Dict[str, Any] = {}

# 活跃进化任务状态存储
# key: task_id, value: 任务状态字典
# TODO(Phase 5): 迁移到Redis，支持多Worker部署和持久化
active_evolutions: Dict[str, Dict[str, Any]] = {}


__all__ = [
    "connections",
    "active_evolutions",
]

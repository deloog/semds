"""隔离管理器模块

提供任务间策略隔离功能，确保不同任务的配置、环境相互独立。
对应 SEMDS_v1.1_SPEC.md 任务隔离需求。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class IsolationManager:
    """隔离管理器

    管理任务的隔离环境，包括文件系统隔离和策略隔离。
    每个任务拥有独立的目录和策略配置。

    Attributes:
        base_dir: 隔离环境基础目录
        _environments: 环境字典，key为task_id，value为环境路径
        _strategies: 策略字典，key为task_id，value为策略配置

    Example:
        >>> manager = IsolationManager("/tmp/isolated_envs")
        >>> manager.create_environment("task-1")
        >>> manager.set_task_strategy("task-1", {"timeout": 300})
        >>> strategy = manager.get_task_strategy("task-1")
    """

    DEFAULT_BASE_DIR = "isolated_envs"  # 默认基础目录

    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        """初始化隔离管理器

        Args:
            base_dir: 隔离环境基础目录，默认为当前目录下的isolated_envs
        """
        if base_dir is None:
            base_dir = self.DEFAULT_BASE_DIR

        self.base_dir = Path(base_dir)
        self._environments: Dict[str, Path] = {}
        self._strategies: Dict[str, Dict[str, Any]] = {}

    def create_environment(self, task_id: str) -> Path:
        """创建隔离环境

        为任务创建独立的文件系统目录。

        Args:
            task_id: 任务ID

        Returns:
            环境目录路径

        Raises:
            ValueError: 如果环境已存在
        """
        if task_id in self._environments:
            raise ValueError(f"Environment already exists: {task_id}")

        env_path = self.base_dir / task_id
        env_path.mkdir(parents=True, exist_ok=True)

        self._environments[task_id] = env_path
        return env_path

    def get_environment_path(self, task_id: str) -> Path:
        """获取环境路径

        Args:
            task_id: 任务ID

        Returns:
            环境目录路径

        Raises:
            KeyError: 如果环境不存在
        """
        if task_id not in self._environments:
            raise KeyError(f"Environment not found: {task_id}")

        return self._environments[task_id]

    def set_task_strategy(self, task_id: str, strategy: Dict[str, Any]) -> None:
        """设置任务策略

        Args:
            task_id: 任务ID
            strategy: 策略配置字典

        Note:
            如果环境不存在，会自动创建
        """
        if task_id not in self._environments:
            self.create_environment(task_id)

        self._strategies[task_id] = strategy.copy()

    def get_task_strategy(self, task_id: str) -> Dict[str, Any]:
        """获取任务策略

        Args:
            task_id: 任务ID

        Returns:
            策略配置字典，未设置则返回空字典

        Raises:
            KeyError: 如果环境不存在
        """
        if task_id not in self._environments:
            raise KeyError(f"Environment not found: {task_id}")

        return self._strategies.get(task_id, {}).copy()

    def remove_environment(self, task_id: str) -> None:
        """移除环境

        删除任务的隔离环境和策略配置。

        Args:
            task_id: 任务ID

        Raises:
            KeyError: 如果环境不存在
        """
        if task_id not in self._environments:
            raise KeyError(f"Environment not found: {task_id}")

        # 删除目录（如果存在）
        env_path = self._environments[task_id]
        if env_path.exists():
            import shutil

            shutil.rmtree(env_path)

        # 清理记录
        del self._environments[task_id]
        self._strategies.pop(task_id, None)

    def list_environments(self) -> List[str]:
        """列出所有环境

        Returns:
            任务ID列表
        """
        return list(self._environments.keys())

    def validate_environment(self, task_id: str) -> bool:
        """验证环境是否存在

        Args:
            task_id: 任务ID

        Returns:
            True如果环境存在
        """
        return task_id in self._environments

    def cleanup_all(self) -> None:
        """清理所有环境

        删除所有隔离环境和基础目录。
        """
        for task_id in list(self._environments.keys()):
            try:
                self.remove_environment(task_id)
            except Exception:
                pass  # 忽略清理错误

        # 尝试删除基础目录
        if self.base_dir.exists():
            import shutil

            shutil.rmtree(self.base_dir, ignore_errors=True)


__all__ = ["IsolationManager"]

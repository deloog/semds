"""权限模型定义"""

from enum import Enum
from typing import Set

from api.auth.models import UserRole


class TaskPermission(str, Enum):
    """任务权限

    用于控制对任务相关操作的访问权限。
    """

    CREATE = "task:create"
    READ = "task:read"
    UPDATE = "task:update"
    DELETE = "task:delete"
    CONTROL = "task:control"  # 启动/暂停/恢复/中止


class ApprovalPermission(str, Enum):
    """审批权限

    用于控制对审批相关操作的访问权限。
    """

    CREATE = "approval:create"
    READ = "approval:read"
    APPROVE = "approval:approve"
    REJECT = "approval:reject"


class RolePermissions:
    """角色权限映射

    定义不同角色拥有的权限集合，提供权限查询接口。
    """

    _ROLE_PERMISSIONS = {
        UserRole.USER: {
            TaskPermission.CREATE,
            TaskPermission.READ,
            TaskPermission.UPDATE,
            TaskPermission.CONTROL,
            ApprovalPermission.READ,
            ApprovalPermission.APPROVE,
            ApprovalPermission.REJECT,
        },
        UserRole.ADMIN: {
            # Admin拥有所有权限
            TaskPermission.CREATE,
            TaskPermission.READ,
            TaskPermission.UPDATE,
            TaskPermission.DELETE,
            TaskPermission.CONTROL,
            ApprovalPermission.CREATE,
            ApprovalPermission.READ,
            ApprovalPermission.APPROVE,
            ApprovalPermission.REJECT,
        },
    }

    @classmethod
    def get_permissions(cls, role: UserRole) -> Set[str]:
        """获取角色的权限集合

        Args:
            role: 用户角色

        Returns:
            该角色拥有的权限集合，如果角色不存在则返回空集合
        """
        return cls._ROLE_PERMISSIONS.get(role, set())

    @classmethod
    def has_permission(cls, role: UserRole, permission: Enum) -> bool:
        """检查角色是否有特定权限

        Args:
            role: 用户角色
            permission: 权限枚举值

        Returns:
            如果角色拥有该权限返回 True，否则返回 False
        """
        return permission in cls.get_permissions(role)


__all__ = [
    "TaskPermission",
    "ApprovalPermission",
    "RolePermissions",
]

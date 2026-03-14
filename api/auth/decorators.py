"""权限装饰器

提供权限检查功能和用于 FastAPI 依赖注入的装饰器工厂。
"""

from typing import Callable, TypeVar

from fastapi import HTTPException, status

from api.auth.models import User, UserRole
from api.auth.permissions import RolePermissions

# 定义权限类型变量，用于类型注解
PermissionType = TypeVar("PermissionType")


def check_permission(user: User, permission) -> None:
    """检查用户权限

    验证用户是否拥有指定的权限。管理员角色(ADMIN)自动通过所有权限检查。

    Args:
        user: 用户对象
        permission: 权限枚举值（如 TaskPermission.READ）

    Raises:
        HTTPException: 403 如果没有权限

    Example:
        >>> user = User(id="1", username="user", email="a@b.com",
        ...             hashed_password="hashed", role=UserRole.USER)
        >>> check_permission(user, TaskPermission.READ)  # 通过
        >>> check_permission(user, TaskPermission.DELETE)  # 抛出 403
    """
    # Admin 拥有所有权限，跳过检查
    if user.role == UserRole.ADMIN:
        return

    # 检查用户是否有指定权限
    if not RolePermissions.has_permission(user.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value}",
        )


def require_permission(permission) -> Callable[[User], User]:
    """权限检查装饰器工厂

    创建一个 FastAPI 依赖函数，用于检查用户是否有指定权限。

    Args:
        permission: 权限枚举值（如 TaskPermission.READ）

    Returns:
        依赖函数，接收 User 参数，返回 User 或抛出 403 异常

    Example:
        >>> from fastapi import Depends
        >>>
        >>> @router.post("/tasks")
        >>> def create_task(
        ...     user: User = Depends(require_permission(TaskPermission.CREATE))
        ... ):
        ...     pass
    """

    def dependency(user: User) -> User:
        """权限检查依赖函数

        Args:
            user: 当前用户（由 FastAPI 依赖系统注入）

        Returns:
            User: 通过权限检查的用户对象

        Raises:
            HTTPException: 403 如果没有权限
        """
        check_permission(user, permission)
        return user

    return dependency


__all__ = [
    "check_permission",
    "require_permission",
]

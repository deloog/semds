"""认证模型定义"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """用户角色枚举

    - USER: 普通用户，可创建和管理自己的任务
    - ADMIN: 管理员，可管理所有任务和用户
    """

    USER = "user"
    ADMIN = "admin"


@dataclass
class User:
    """用户模型

    Attributes:
        id: 用户唯一标识
        username: 用户名
        email: 邮箱地址
        hashed_password: 哈希后的密码
        role: 用户角色
        is_active: 账户是否激活
        created_at: 创建时间
    """

    id: str
    username: str
    email: str
    hashed_password: str
    role: UserRole = field(default=UserRole.USER)
    is_active: bool = field(default=True)
    created_at: Optional[datetime] = field(default=None)

    def __post_init__(self):
        """后初始化处理"""
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class Token:
    """Token模型

    Attributes:
        access_token: 访问令牌
        token_type: 令牌类型
        expires_in: 过期时间（秒）
    """

    access_token: str
    token_type: str = field(default="bearer")
    expires_in: int = field(default=3600)


__all__ = [
    "UserRole",
    "User",
    "Token",
]

"""JWT Token处理"""

import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from jose import JWTError, jwt

# 默认配置（将被环境变量覆盖）
_DEFAULT_SECRET_KEY = "your-secret-key-change-in-production"
_DEFAULT_ALGORITHM = "HS256"
_DEFAULT_EXPIRE_MINUTES = 30


def _get_secret_key() -> str:
    """获取JWT密钥（支持环境变量）"""
    return os.getenv("JWT_SECRET_KEY", _DEFAULT_SECRET_KEY)


def _get_algorithm() -> str:
    """获取JWT算法"""
    return os.getenv("JWT_ALGORITHM", _DEFAULT_ALGORITHM)


def _get_expire_minutes() -> int:
    """获取过期时间（分钟）"""
    return int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(_DEFAULT_EXPIRE_MINUTES))
    )


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问Token

    Args:
        data: Token payload数据，应包含sub(用户ID)和role
        expires_delta: 过期时间增量，默认30分钟

    Returns:
        JWT Token字符串
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=_get_expire_minutes())

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, _get_secret_key(), algorithm=_get_algorithm())
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """验证Token

    Args:
        token: JWT Token字符串

    Returns:
        Token payload字典如果有效，None如果无效或过期
    """
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[_get_algorithm()])
        return payload
    except JWTError:
        return None


# 向后兼容的导出
SECRET_KEY = _get_secret_key()
ALGORITHM = _get_algorithm()
ACCESS_TOKEN_EXPIRE_MINUTES = _get_expire_minutes()

__all__ = [
    "create_access_token",
    "verify_token",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
]

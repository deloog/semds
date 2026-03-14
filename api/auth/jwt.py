"""JWT Token处理"""
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional

from jose import JWTError, jwt


# 配置（从环境变量读取，默认为开发密钥）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问Token
    
    Args:
        data: Token payload数据，应包含sub(用户ID)和role
        expires_delta: 过期时间增量，默认30分钟
        
    Returns:
        JWT Token字符串
        
    Example:
        >>> token = create_access_token(
        ...     data={"sub": "user-123", "role": "user"},
        ...     expires_delta=timedelta(hours=1)
        ... )
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """验证Token
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Token payload字典如果有效，None如果无效或过期
        
    Example:
        >>> payload = verify_token("eyJhbGciOiJIUzI1NiIs...")
        >>> if payload:
        ...     user_id = payload.get("sub")
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


__all__ = [
    "create_access_token",
    "verify_token",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
]

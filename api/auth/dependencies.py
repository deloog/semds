"""认证依赖注入

提供FastAPI依赖函数用于保护端点。
"""
from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from api.auth.jwt import verify_token
from api.auth.models import User, UserRole

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


# 用户存储（生产环境应从数据库读取）
_USERS_STORE: Dict[str, dict] = {
    "user-123": {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "role": UserRole.USER,
        "is_active": True
    },
    "admin-1": {
        "id": "admin-1",
        "username": "admin",
        "email": "admin@example.com",
        "role": UserRole.ADMIN,
        "is_active": True
    }
}


def get_user_by_id(user_id: str) -> Optional[User]:
    """通过ID获取用户
    
    从用户存储中查询用户信息。
    TODO(P5+): 实际应从数据库查询
    
    Args:
        user_id: 用户ID
        
    Returns:
        User对象如果存在，None如果不存在
    """
    user_data = _USERS_STORE.get(user_id)
    if not user_data:
        return None
    
    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        hashed_password="hashed",  # 不需要返回真实哈希
        role=user_data["role"],
        is_active=user_data["is_active"]
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户
    
    FastAPI依赖，用于保护端点。从请求中提取并验证JWT Token。
    
    Args:
        token: 从Authorization头提取的Bearer Token
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 401如果Token无效或用户不存在/被禁用
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 验证Token
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    # 提取用户ID
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # 查询用户信息（验证用户是否存在）
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    # 验证用户是否被禁用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户
    
    额外检查用户是否处于激活状态。
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """要求管理员权限
    
    验证当前用户是否具有管理员角色。
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        User: 管理员用户对象
        
    Raises:
        HTTPException: 403如果用户不是管理员
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


__all__ = [
    "oauth2_scheme",
    "get_current_user",
    "get_current_active_user",
    "require_admin",
]

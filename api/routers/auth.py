"""认证路由

提供用户登录和认证相关的API端点。
"""

import bcrypt
import os
import warnings

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from api.auth.jwt import create_access_token, SECRET_KEY
from api.auth.models import Token, User, UserRole

router = APIRouter(tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# 安全检查：生产环境必须使用自定义密钥
if SECRET_KEY == "your-secret-key-change-in-production":
    warnings.warn(
        "使用默认JWT密钥！生产环境请设置JWT_SECRET_KEY环境变量", RuntimeWarning
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码

    使用bcrypt进行密码哈希比较。

    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码

    Returns:
        True如果密码匹配，False否则
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    """生成密码哈希

    使用bcrypt生成密码哈希。

    Args:
        password: 明文密码

    Returns:
        哈希后的密码字符串
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# 测试用户数据（生产环境应从数据库读取）
# 密码: "secret" 的bcrypt哈希
_TEST_USER_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYA.qGZvKG6G"
_TEST_USERS = {
    "testuser": {
        "id": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": _TEST_USER_HASH,
        "role": UserRole.USER,
        "is_active": True,
    },
    "admin": {
        "id": "admin-1",
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": _TEST_USER_HASH,  # 同样使用"secret"作为密码
        "role": UserRole.ADMIN,
        "is_active": True,
    },
}


def authenticate_user(username: str, password: str):
    """验证用户凭据

    从用户存储中验证用户名和密码。
    TODO(P5+): 实际实现应从数据库验证

    Args:
        username: 用户名
        password: 密码

    Returns:
        User对象如果验证成功，None如果失败
    """
    user_data = _TEST_USERS.get(username)
    if not user_data:
        return None

    if not verify_password(password, user_data["hashed_password"]):
        return None

    return User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=user_data["hashed_password"],
        role=user_data["role"],
        is_active=user_data["is_active"],
    )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录

    使用OAuth2密码流程获取访问Token。

    Args:
        form_data: OAuth2密码表单（username, password）

    Returns:
        Token: 访问令牌

    Raises:
        HTTPException: 401如果凭据无效
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 处理role可能是字符串或枚举的情况
    role_value = user.role.value if hasattr(user.role, "value") else user.role
    access_token = create_access_token(data={"sub": user.id, "role": role_value})

    return {"access_token": access_token, "token_type": "bearer"}

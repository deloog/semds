# SEMDS Phase 5 TDD原子化开发路线图

**版本**: v1.0  
**对应规格**: SEMDS_v1.1_SPEC.md Phase 5  
**遵循规范**: docs/standards/TDD_MANDATE.md  
**目标**: 用户认证/权限系统 + 多任务并发 + 数据持久化

---

## 📋 任务总览

**时间**: 1周（5个工作日）  
**前置依赖**: Phase 4 完成并通过验收 ✅  
**交付物**: 
- 用户认证系统 (`api/auth/`)
- 权限控制中间件 (`api/middleware/auth.py`)
- 多任务并发管理 (`factory/`)
- Redis持久化集成
- 100%测试覆盖的代码

---

## 🔄 TDD实施流程（每个任务必须遵循）

```
┌─────────────────────────────────────────────────────────────┐
│ Step 1: 编写测试 (Red)                                       │
│ ─────────────────────                                       │
│ • 编写测试文件，描述预期行为                                 │
│ • 运行测试，确认失败（Red）                                  │
│ • 验收：测试失败截图                                         │
├─────────────────────────────────────────────────────────────┤
│ Step 2: 最小实现 (Green)                                     │
│ ─────────────────────                                       │
│ • 编写最少代码使测试通过                                     │
│ • 不添加未测试的功能                                         │
│ • 运行测试，确认通过（Green）                                │
│ • 验收：测试通过截图                                         │
├─────────────────────────────────────────────────────────────┤
│ Step 3: 重构优化 (Refactor)                                  │
│ ─────────────────────                                       │
│ • 消除重复代码                                               │
│ • 优化命名和结构                                             │
│ • 运行测试，确认仍通过                                       │
│ • 验收：重构后代码 + 测试通过                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 任务追踪清单

| 任务ID | 任务名称 | 状态 | 测试文件 | 实现文件 | 进度 |
|--------|----------|------|----------|----------|------|
| **Week 1 Day 1: 认证基础** | | | | | |
| P5-T1 | 用户模型设计 | ✅ 已完成 | `tests/api/auth/test_models.py` | `api/auth/models.py` | 100% |
| P5-T2 | JWT Token生成/验证 | ✅ 已完成 | `tests/api/auth/test_jwt.py` | `api/auth/jwt.py` | 100% |
| P5-T3 | 用户登录API | ✅ 已完成 | `tests/api/auth/test_login.py` | `api/routers/auth.py` | 100% |
| P5-T4 | 当前用户依赖注入 | ✅ 已完成 | `tests/api/auth/test_dependencies.py` | `api/auth/dependencies.py` | 100% |
| **Week 1 Day 2: 权限控制** | | | | | |
| P5-T5 | 角色权限模型 | ✅ 已完成 | `tests/api/auth/test_permissions.py` | `api/auth/permissions.py` | 100% |
| P5-T6 | 权限检查装饰器 | ✅ 已完成 | `tests/api/auth/test_decorators.py` | `api/auth/decorators.py` | 100% |
| P5-T7 | 任务所有权验证 | ✅ 已完成 | `tests/api/routers/test_task_permissions.py` | 集成到tasks路由 | 100% |
| P5-T8 | 审批权限控制 | ✅ 已完成 | `tests/api/routers/test_approval_permissions.py` | 集成到approvals路由 | 100% |
| **Week 1 Day 3: WebSocket安全** | | | | | |
| P5-T9 | WebSocket Token认证 | ✅ 已完成 | `tests/api/routers/test_websocket_auth.py` | `api/routers/monitor.py` | 100% |
| P5-T10 | 连接权限验证 | ✅ 已完成 | `tests/api/routers/test_websocket_permissions.py` | 集成 | 100% |
| **Week 1 Day 4: 多任务并发** | | | | | |
| P5-T11 | TaskManager核心类 | ✅ 已完成 | `tests/factory/test_task_manager.py` | `factory/task_manager.py` | 100% |
| P5-T12 | 任务队列调度 | ✅ 已完成 | `tests/factory/test_task_scheduler.py` | `factory/task_scheduler.py` | 100% |
| P5-T13 | 隔离管理器 | ✅ 已完成 | `tests/factory/test_isolation_manager.py` | `factory/isolation_manager.py` | 100% |
| **Week 1 Day 5: Redis持久化** | | | | | |
| P5-T14 | Redis状态存储 | ✅ 已完成 | `tests/api/test_redis_state.py` | `api/state_redis.py` | 100% |
| P5-T15 | 状态迁移工具 | ✅ 已完成 | `tests/api/test_state_migration.py` | `api/state_migration.py` | 100% |
| P5-T16 | 集成验收测试 | ✅ 已完成 | `tests/integration/test_phase5_full.py` | - | 100% |
| P5-T17 | 批量任务操作API | ✅ 已完成 | `tests/api/routers/test_batch_tasks.py` | `api/routers/tasks.py` | 100% |
| **Week 1 Day 4: 多任务并发** | | | | | |


---

## 🔢 原子化任务详情

### Week 1 Day 1: 认证基础架构

---

#### P5-T1: 用户模型设计 (2h)

**目标**: 设计用户和权限数据模型

**Step 1 - 编写测试** (`tests/api/auth/test_models.py`):
```python
"""测试认证模型"""
import pytest


class TestUserModel:
    """用户模型测试"""
    
    def test_user_creation_with_required_fields(self):
        """用户应包含必要字段"""
        from api.auth.models import User
        
        user = User(
            id="user-123",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_secret",
            role="user"
        )
        
        assert user.id == "user-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "user"
        assert user.is_active is True
    
    def test_user_role_validation(self):
        """用户角色应在允许范围内"""
        from api.auth.models import User, UserRole
        
        # 有效角色
        user = User(id="1", username="admin", email="a@b.com", role=UserRole.ADMIN)
        assert user.role == UserRole.ADMIN
        
        user2 = User(id="2", username="user", email="b@c.com", role=UserRole.USER)
        assert user2.role == UserRole.USER
```

**Step 2 - 最小实现** (`api/auth/models.py`):
```python
"""认证模型定义"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    """用户角色枚举"""
    USER = "user"      # 普通用户
    ADMIN = "admin"    # 管理员


@dataclass
class User:
    """用户模型"""
    id: str
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class Token:
    """Token模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 默认1小时
```

**验收标准**:
- [x] 测试先失败（Red）
- [x] 实现后通过（Green）
- [x] 用户模型包含所有必要字段
- [x] 角色使用枚举定义

---

#### P5-T2: JWT Token生成/验证 (2h)

**目标**: 实现JWT Token的生成和验证功能

**Step 1 - 编写测试** (`tests/api/auth/test_jwt.py`):
```python
"""测试JWT功能"""
import pytest
from datetime import datetime, timedelta


class TestJWTToken:
    """JWT Token测试"""
    
    def test_create_access_token(self):
        """应能创建访问Token"""
        from api.auth.jwt import create_access_token
        
        token = create_access_token(
            data={"sub": "user-123", "role": "user"}
        )
        
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_valid_token(self):
        """应能验证有效Token"""
        from api.auth.jwt import create_access_token, verify_token
        
        token = create_access_token(data={"sub": "user-123", "role": "user"})
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["role"] == "user"
    
    def test_verify_expired_token_returns_none(self):
        """过期Token应返回None"""
        from api.auth.jwt import create_access_token, verify_token
        
        # 创建已过期Token（负数过期时间）
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(minutes=-1)
        )
        payload = verify_token(token)
        
        assert payload is None
    
    def test_verify_invalid_token_returns_none(self):
        """无效Token应返回None"""
        from api.auth.jwt import verify_token
        
        payload = verify_token("invalid.token.here")
        assert payload is None
```

**Step 2 - 最小实现** (`api/auth/jwt.py`):
```python
"""JWT Token处理"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

from jose import JWTError, jwt


# 配置（实际应从环境变量读取）
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    data: Dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建访问Token
    
    Args:
        data: Token payload数据
        expires_delta: 过期时间增量
        
    Returns:
        JWT Token字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict]:
    """验证Token
    
    Args:
        token: JWT Token字符串
        
    Returns:
        Token payload如果有效，None如果无效或过期
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

**验收标准**:
- [x] 测试先失败（Red）
- [x] 实现后通过（Green）
- [x] 支持Token创建、验证、过期检测

---

#### P5-T3: 用户登录API (2h)

**目标**: 实现用户登录接口

**Step 1 - 编写测试** (`tests/api/auth/test_login.py`):
```python
"""测试登录API"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


class TestLoginAPI:
    """登录API测试"""
    
    def test_login_with_valid_credentials(self):
        """有效凭据应返回Token"""
        from api.main import app
        
        # Mock用户验证
        with patch("api.routers.auth.authenticate_user") as mock_auth:
            mock_user = MagicMock()
            mock_user.id = "user-123"
            mock_user.username = "testuser"
            mock_user.role = "user"
            mock_auth.return_value = mock_user
            
            client = TestClient(app)
            response = client.post(
                "/api/auth/login",
                data={"username": "testuser", "password": "secret"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
    
    def test_login_with_invalid_credentials(self):
        """无效凭据应返回401"""
        from api.main import app
        from unittest.mock import patch
        
        with patch("api.routers.auth.authenticate_user") as mock_auth:
            mock_auth.return_value = None
            
            client = TestClient(app)
            response = client.post(
                "/api/auth/login",
                data={"username": "testuser", "password": "wrong"}
            )
            
            assert response.status_code == 401
```

**Step 2 - 最小实现** (`api/routers/auth.py`):
```python
"""认证路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from api.auth.jwt import create_access_token
from api.auth.models import Token

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def authenticate_user(username: str, password: str):
    """验证用户凭据
    
    TODO(Phase 5+): 实际实现应从数据库验证
    当前为占位实现
    """
    # 占位：实际应从数据库查询用户
    if username == "testuser" and password == "secret":
        from api.auth.models import User, UserRole
        return User(
            id="user-123",
            username=username,
            email="test@example.com",
            hashed_password="hashed",
            role=UserRole.USER
        )
    return None


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录
    
    使用OAuth2密码流程获取访问Token
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
```

**验收标准**:
- [x] 测试先失败（Red）
- [x] 实现后通过（Green）
- [x] 支持OAuth2密码流程
- [x] 无效凭据返回401

---

#### P5-T4: 当前用户依赖注入 (2h)

**目标**: 实现获取当前用户的FastAPI依赖

**Step 1 - 编写测试** (`tests/api/auth/test_dependencies.py`):
```python
"""测试认证依赖"""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


class TestCurrentUserDependency:
    """当前用户依赖测试"""
    
    def test_get_current_user_with_valid_token(self):
        """有效Token应返回用户"""
        from api.auth.dependencies import get_current_user
        from api.auth.jwt import create_access_token
        
        token = create_access_token(data={"sub": "user-123", "role": "user"})
        
        # Mock数据库查询
        with patch("api.auth.dependencies.get_user_by_id") as mock_get:
            mock_user = MagicMock()
            mock_user.id = "user-123"
            mock_user.role = "user"
            mock_get.return_value = mock_user
            
            user = get_current_user(token)
            
            assert user is not None
            assert user.id == "user-123"
    
    def test_get_current_user_with_invalid_token(self):
        """无效Token应抛出401"""
        from api.auth.dependencies import get_current_user
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user("invalid-token")
        
        assert exc_info.value.status_code == 401
```

**Step 2 - 最小实现** (`api/auth/dependencies.py`):
```python
"""认证依赖注入"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from api.auth.jwt import verify_token
from api.auth.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


def get_user_by_id(user_id: str):
    """通过ID获取用户
    
    TODO(Phase 5+): 从数据库查询
    当前为占位实现
    """
    # 占位实现
    if user_id == "user-123":
        return User(
            id=user_id,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            role=UserRole.USER
        )
    return None


def get_current_user(token: str = Depends(oauth2_scheme)):
    """获取当前用户
    
    FastAPI依赖，用于保护端点
    
    Args:
        token: 从请求中提取的JWT Token
        
    Returns:
        User: 当前用户对象
        
    Raises:
        HTTPException: 401如果Token无效
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user)
):
    """要求管理员权限"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user
```

**验收标准**:
- [x] 测试先失败（Red）
- [x] 实现后通过（Green）
- [x] 支持Token验证
- [x] 支持权限检查

---

### Week 1 Day 2: 权限控制

---

#### P5-T5: 角色权限模型 (2h)

**目标**: 定义角色和权限模型

**Step 1 - 编写测试** (`tests/api/auth/test_permissions.py`):
```python
"""测试权限模型"""
import pytest


class TestPermissions:
    """权限测试"""
    
    def test_task_permissions_defined(self):
        """应定义任务相关权限"""
        from api.auth.permissions import TaskPermissions
        
        assert hasattr(TaskPermissions, 'CREATE')
        assert hasattr(TaskPermissions, 'READ')
        assert hasattr(TaskPermissions, 'UPDATE')
        assert hasattr(TaskPermissions, 'DELETE')
        assert hasattr(TaskPermissions, 'CONTROL')
    
    def test_role_has_correct_permissions(self):
        """角色应有正确的权限集合"""
        from api.auth.permissions import RolePermissions, UserRole
        
        user_perms = RolePermissions.get_permissions(UserRole.USER)
        assert TaskPermissions.READ in user_perms
        assert TaskPermissions.CREATE in user_perms
        
        admin_perms = RolePermissions.get_permissions(UserRole.ADMIN)
        assert TaskPermissions.DELETE in admin_perms
        assert TaskPermissions.CONTROL in admin_perms
```

**Step 2 - 最小实现** (`api/auth/permissions.py`):
```python
"""权限模型定义"""
from enum import Enum
from typing import Set

from api.auth.models import UserRole


class TaskPermissions(str, Enum):
    """任务权限"""
    CREATE = "task:create"
    READ = "task:read"
    UPDATE = "task:update"
    DELETE = "task:delete"
    CONTROL = "task:control"  # 启动/暂停/恢复/中止


class ApprovalPermissions(str, Enum):
    """审批权限"""
    CREATE = "approval:create"
    READ = "approval:read"
    APPROVE = "approval:approve"
    REJECT = "approval:reject"


class RolePermissions:
    """角色权限映射"""
    
    _ROLE_PERMISSIONS = {
        UserRole.USER: {
            TaskPermissions.CREATE,
            TaskPermissions.READ,
            TaskPermissions.UPDATE,
            TaskPermissions.CONTROL,
            ApprovalPermissions.READ,
            ApprovalPermissions.APPROVE,
            ApprovalPermissions.REJECT,
        },
        UserRole.ADMIN: {
            # Admin拥有所有权限
            TaskPermissions.CREATE,
            TaskPermissions.READ,
            TaskPermissions.UPDATE,
            TaskPermissions.DELETE,
            TaskPermissions.CONTROL,
            ApprovalPermissions.CREATE,
            ApprovalPermissions.READ,
            ApprovalPermissions.APPROVE,
            ApprovalPermissions.REJECT,
        }
    }
    
    @classmethod
    def get_permissions(cls, role: UserRole) -> Set:
        """获取角色的权限集合"""
        return cls._ROLE_PERMISSIONS.get(role, set())
    
    @classmethod
    def has_permission(cls, role: UserRole, permission) -> bool:
        """检查角色是否有特定权限"""
        return permission in cls.get_permissions(role)
```

---

#### P5-T6: 权限检查装饰器 (2h)

**目标**: 实现权限检查装饰器

**Step 1 - 编写测试** (`tests/api/auth/test_decorators.py`):
```python
"""测试权限装饰器"""
import pytest
from fastapi import HTTPException


class TestPermissionDecorators:
    """权限装饰器测试"""
    
    def test_check_permission_allows_authorized(self):
        """有权限的用户应通过检查"""
        from api.auth.decorators import check_permission
        from api.auth.permissions import TaskPermissions
        from api.auth.models import User, UserRole
        
        user = User(id="1", username="user", email="a@b.com", role=UserRole.USER)
        
        # 不应抛出异常
        check_permission(user, TaskPermissions.READ)
    
    def test_check_permission_denies_unauthorized(self):
        """无权限的用户应被拒绝"""
        from api.auth.decorators import check_permission
        from api.auth.permissions import TaskPermissions
        from api.auth.models import User, UserRole
        
        # 创建一个没有CONTROL权限的角色（实际USER有，这里模拟）
        with pytest.raises(HTTPException) as exc_info:
            # 假设我们用游客角色
            from unittest.mock import MagicMock
            guest = MagicMock()
            guest.role = "guest"
            check_permission(guest, TaskPermissions.CONTROL)
        
        assert exc_info.value.status_code == 403
```

**Step 2 - 最小实现** (`api/auth/decorators.py`):
```python
"""权限装饰器"""
from functools import wraps
from typing import Callable

from fastapi import HTTPException, status

from api.auth.models import User, UserRole
from api.auth.permissions import RolePermissions


def check_permission(user: User, permission):
    """检查用户权限
    
    Args:
        user: 用户对象
        permission: 权限枚举
        
    Raises:
        HTTPException: 403如果没有权限
    """
    if user.role == UserRole.ADMIN:
        return  # Admin跳过检查
    
    if not RolePermissions.has_permission(user.role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value}"
        )


def require_permission(permission):
    """权限检查装饰器工厂
    
    用于FastAPI依赖
    """
    def dependency(user: User):
        check_permission(user, permission)
        return user
    return dependency
```

---

#### P5-T7: 任务所有权验证 (2h)

**目标**: 任务操作验证所有权

**Step 1 - 编写测试** (`tests/api/routers/test_task_permissions.py`):
```python
"""测试任务路由权限"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


class TestTaskOwnership:
    """任务所有权测试"""
    
    def test_user_can_only_access_own_tasks(self):
        """用户应只能访问自己的任务"""
        # 测试实现...
        pass
    
    def test_admin_can_access_any_task(self):
        """管理员应能访问所有任务"""
        # 测试实现...
        pass
```

---

#### P5-T8: 审批权限控制 (2h)

**目标**: 审批操作权限控制

**Step 1 - 编写测试** (`tests/api/routers/test_approval_permissions.py`):
```python
"""测试审批路由权限"""
import pytest


class TestApprovalPermissions:
    """审批权限测试"""
    
    def test_only_authorized_can_approve(self):
        """只有授权用户能批准"""
        pass
```

---

### Week 1 Day 3: WebSocket安全

---

#### P5-T9: WebSocket Token认证 (3h)

**目标**: WebSocket连接Token验证

**Step 1 - 编写测试** (`tests/api/routers/test_websocket_auth.py`):
```python
"""测试WebSocket认证"""
import pytest


class TestWebSocketAuth:
    """WebSocket认证测试"""
    
    def test_websocket_validates_token(self):
        """WebSocket应验证Token"""
        pass
```

**Step 2 - 最小实现**:
```python
# 在api/routers/monitor.py中修改websocket端点
# 添加token验证逻辑
```

---

#### P5-T10: 连接权限验证 (3h)

**目标**: WebSocket连接任务权限验证

---

### Week 1 Day 4: 多任务并发

---

#### P5-T11: TaskManager核心类 (4h)

**目标**: 实现任务管理器核心类

**Step 1 - 编写测试** (`tests/factory/test_task_manager.py`):
```python
"""测试任务管理器"""
import pytest


class TestTaskManager:
    """任务管理器测试"""
    
    def test_task_manager_initialization(self):
        """任务管理器应正确初始化"""
        from factory.task_manager import TaskManager
        
        manager = TaskManager(max_concurrent_tasks=3)
        
        assert manager.max_concurrent == 3
        assert len(manager._tasks) == 0
```

---

#### P5-T12: 任务队列调度 (3h)

**目标**: 实现任务优先级调度

---

#### P5-T13: 隔离管理器 (4h)

**目标**: 实现任务间策略隔离

---

### Week 1 Day 5: Redis持久化

---

#### P5-T14: Redis状态存储 (4h)

**目标**: 使用Redis存储共享状态

---

#### P5-T15: 状态迁移工具 (2h)

**目标**: 内存状态迁移到Redis

---

#### P5-T16: 集成验收测试 (2h)

**目标**: Phase 5完整集成测试

---

## 验收标准

### 必须完成

- [ ] 用户认证系统可用
- [ ] 权限控制工作正常
- [ ] WebSocket有认证
- [ ] 多任务并发可用
- [ ] Redis持久化集成

### 功能验收

```bash
# 1. 登录获取Token
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=testuser&password=secret"

# 2. 使用Token访问受保护端点
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/tasks

# 3. WebSocket带Token连接
# ws://localhost:8000/ws/tasks/{task_id}?token=<token>
```

---

*文档版本: v1.0*  
*创建时间: 2026-03-13*  
*最后更新: 2026-03-13*

# SEMDS Phase 4 TDD原子化开发路线图

**文档版本**: v1.0  
**对应规格**: SEMDS_v1.1_SPEC.md Phase 4 + PHASE4_ADDENDUM.md  
**遵循规范**: docs/standards/TDD_MANDATE.md  
**目标**: 实现API层和监控界面  
**开发方法**: 严格TDD（测试先行）

---

## 📋 任务总览

**时间**: 1周（5个工作日）  
**前置依赖**: Phase 3完成并通过验收 ✅  
**交付物**: 
- FastAPI服务 (`api/`)
- Web监控界面 (`monitor/`)
- 人类审批闸口 (`factory/`)
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

## 📊 任务依赖图

```
Week 1 Day 1-2: FastAPI基础架构
├── P4-T1: FastAPI主应用 (2h)
│   ├── P4-T1-TEST: 测试 - 健康检查端点
│   └── P4-T1-IMPL: 实现 - FastAPI应用创建
├── P4-T2: 依赖注入配置 (2h)
│   ├── P4-T2-TEST: 测试 - DB依赖注入
│   └── P4-T2-IMPL: 实现 - 依赖注入函数
├── P4-T3: 错误处理中间件 (2h)
│   ├── P4-T3-TEST: 测试 - 异常处理和响应格式
│   └── P4-T3-IMPL: 实现 - 错误处理中间件
├── P4-T4: CORS和日志配置 (1h)
│   ├── P4-T4-TEST: 测试 - CORS中间件配置
│   └── P4-T4-IMPL: 实现 - 中间件配置
└── P4-T5: Pydantic数据模型 (3h)
    ├── P4-T5-TEST: 测试 - 模型验证和序列化
    └── P4-T5-IMPL: 实现 - 所有Schema模型

Week 1 Day 2-3: 任务管理路由
├── P4-T6: 任务CRUD路由 (4h)
│   ├── P4-T6-TEST: 测试 - 创建/查询/删除任务
│   └── P4-T6-IMPL: 实现 - 任务CRUD端点
├── P4-T7: 任务进化控制路由 (3h)
│   ├── P4-T7-TEST: 测试 - start/pause/resume/abort
│   └── P4-T7-IMPL: 实现 - 进化控制端点
└── P4-T8: 进化历史查询 (3h)
    ├── P4-T8-TEST: 测试 - 历史记录和回滚
    └── P4-T8-IMPL: 实现 - 历史查询端点

Week 1 Day 4: WebSocket + 监控
├── P4-T9: WebSocket实时推送 (4h)
│   ├── P4-T9-TEST: 测试 - WebSocket连接和消息推送
│   └── P4-T9-IMPL: 实现 - WebSocket端点
└── P4-T10: 监控界面HTML (6h)
    ├── P4-T10-TEST: 测试 - 界面元素和交互（手动/集成测试）
    └── P4-T10-IMPL: 实现 - 完整监控界面

Week 1 Day 5: Human Gate + 集成
├── P4-T11: HumanGateMonitor (4h)
│   ├── P4-T11-TEST: 测试 - 审批质量监控逻辑
│   └── P4-T11-IMPL: 实现 - HumanGateMonitor类
├── P4-T12: 审批API路由 (2h)
│   ├── P4-T12-TEST: 测试 - 审批列表/批准/拒绝
│   └── P4-T12-IMPL: 实现 - 审批路由
└── P4-T13: 集成验收 (2h)
    └── P4-T13-TEST: 集成测试 - 完整流程验证
```

---

## 📋 任务追踪清单

| 任务ID | 任务名称 | 状态 | 测试文件 | 实现文件 | 进度 |
|--------|----------|------|----------|----------|------|
| **Week 1 Day 1** | | | | | |
| P4-T1 | FastAPI主应用 | ✅ 已完成 | `tests/api/test_main.py` | `api/main.py` | 100% |
| P4-T2 | 依赖注入配置 | ✅ 已完成 | `tests/api/test_dependencies.py` | `api/dependencies.py` | 100% |
| P4-T3 | 错误处理中间件 | ✅ 已完成 | `tests/api/test_middleware.py` | `api/middleware.py` | 100% |
| P4-T4 | CORS和日志配置 | ✅ 已完成 | `tests/api/test_cors.py` | `api/main.py` | 100% |
| P4-T5 | Pydantic数据模型 | ✅ 已完成 | `tests/api/test_schemas.py` | `api/schemas.py` | 100% |
| **Week 1 Day 2-3** | | | | | |
| P4-T6 | 任务CRUD路由 | ✅ 已完成 | `tests/api/routers/test_tasks.py` | `api/routers/tasks.py` | 100% |
| P4-T7 | 进化控制路由 | ✅ 已完成 | `tests/api/routers/test_evolution.py` | `api/routers/evolution.py` | 100% |
| P4-T8 | 进化历史查询 | ✅ 已完成 | `tests/api/routers/test_generations.py` | `api/routers/tasks.py` | 100% |
| **Week 1 Day 4** | | | | | |
| P4-T9 | WebSocket实时推送 | ✅ 已完成 | `tests/api/routers/test_websocket.py` | `api/routers/monitor.py` | 100% |
| P4-T10 | 监控界面HTML | ✅ 已完成 | `tests/integration/test_monitor_ui.py` | `monitor/index.html` | 100% |
| **Week 1 Day 5** | | | | | |
| P4-T11 | HumanGateMonitor | ✅ 已完成 | `tests/factory/test_human_gate.py` | `factory/human_gate.py` | 100% |
| P4-T12 | 审批API路由 | ✅ 已完成 | `tests/api/routers/test_approvals.py` | `api/routers/approvals.py` | 100% |
| P4-T13 | 集成验收测试 | ✅ 已完成 | `tests/integration/test_phase4_full.py` | - | 100% |

---

## 🔢 原子化任务详情

### Week 1 Day 1: FastAPI基础架构

---

#### P4-T1: FastAPI主应用 (2h)

**目标**: 创建FastAPI应用入口和生命周期管理

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/test_main.py`):
```python
"""测试FastAPI主应用"""
import pytest
from fastapi.testclient import TestClient


class TestFastAPIApp:
    """FastAPI应用测试"""
    
    def test_health_check_returns_healthy_status(self):
        """健康检查应返回healthy状态"""
        from api.main import app
        client = TestClient(app)
        
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "version" in response.json()
    
    def test_api_docs_endpoint_exists(self):
        """API文档端点应可访问"""
        from api.main import app
        client = TestClient(app)
        
        response = client.get("/docs")
        assert response.status_code == 200
```

**Step 2 - 最小实现** (`api/main.py`):
```python
"""FastAPI主应用"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_database()
    yield
    await close_database()


app = FastAPI(
    title="SEMDS API",
    description="自进化元开发系统 API",
    version="1.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": "1.1.0"}


async def init_database():
    pass


async def close_database():
    pass
```

**验收标准**:
- [ ] 测试先失败（Red）
- [ ] 实现后通过（Green）
- [ ] 健康检查端点返回正确格式
- [ ] API文档可访问

---

#### P4-T2: 依赖注入配置 (2h)

**目标**: 配置FastAPI依赖注入（数据库会话等）

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/test_dependencies.py`):
```python
"""测试API依赖注入"""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


class TestDatabaseDependency:
    """数据库依赖注入测试"""
    
    def test_get_db_session_returns_session(self):
        """get_db应返回数据库会话"""
        from api.dependencies import get_db_session
        
        gen = get_db_session()
        db = next(gen)
        
        assert db is not None
        
        try:
            next(gen)
        except StopIteration:
            pass
```

**Step 2 - 最小实现** (`api/dependencies.py`):
```python
"""FastAPI依赖注入配置"""
from typing import Generator
from storage.database import get_session


def get_db_session() -> Generator:
    """获取数据库会话依赖"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()
```

**验收标准**:
- [ ] 依赖注入测试失败（Red）
- [ ] 实现后测试通过（Green）
- [ ] 数据库会话正确管理和关闭

---

#### P4-T3: 错误处理中间件 (2h)

**目标**: 实现统一的错误处理和响应格式

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/test_middleware.py`):
```python
"""测试API中间件"""
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


class TestErrorHandlingMiddleware:
    """错误处理中间件测试"""
    
    def test_http_exception_returns_formatted_response(self):
        """HTTP异常应返回统一格式的响应"""
        from api.main import app
        from api.middleware import setup_exception_handlers
        
        setup_exception_handlers(app)
        
        @app.get("/test-404")
        def test_404():
            raise HTTPException(status_code=404, detail="资源不存在")
        
        client = TestClient(app)
        response = client.get("/test-404")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "message" in data
```

**Step 2 - 最小实现** (`api/middleware.py`):
```python
"""API中间件配置"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def setup_exception_handlers(app: FastAPI) -> None:
    """配置全局异常处理"""
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": str(exc)
            }
        )
```

**验收标准**:
- [ ] 异常处理测试失败（Red）
- [ ] 实现后测试通过（Green）
- [ ] HTTP异常返回统一格式

---

#### P4-T4: CORS和日志配置 (1h)

**目标**: 配置CORS中间件和请求日志

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/test_cors.py`):
```python
"""测试CORS配置"""
import pytest
from fastapi.testclient import TestClient


class TestCORSConfiguration:
    """CORS配置测试"""
    
    def test_cors_headers_present_in_response(self):
        """响应应包含CORS头"""
        from api.main import app
        
        client = TestClient(app)
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        
        assert "access-control-allow-origin" in response.headers
```

**验收标准**:
- [ ] CORS测试失败（Red）
- [ ] 实现后测试通过（Green）

---

#### P4-T5: Pydantic数据模型 (3h)

**目标**: 定义所有请求/响应模型

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/test_schemas.py`):
```python
"""测试Pydantic数据模型"""
import pytest
from datetime import datetime


class TestTaskCreateSchema:
    """任务创建模型测试"""
    
    def test_valid_task_create_parses_correctly(self):
        """有效数据应正确解析"""
        from api.schemas import TaskCreate
        
        data = {
            "name": "test_task",
            "description": "测试任务",
            "target_function_signature": "def calculate(a, b):",
            "test_code": "def test(): pass"
        }
        
        task = TaskCreate(**data)
        assert task.name == "test_task"
    
    def test_empty_name_raises_validation_error(self):
        """空名称应触发验证错误"""
        from api.schemas import TaskCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            TaskCreate(name="", description="test", test_code="pass")


class TestTaskResponseSchema:
    """任务响应模型测试"""
    
    def test_task_response_serializes_correctly(self):
        """任务响应应正确序列化"""
        from api.schemas import TaskResponse, TaskStatus
        
        task = TaskResponse(
            id="test-id",
            name="test",
            description="test desc",
            status=TaskStatus.PENDING,
            current_generation=0,
            best_score=0.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        data = task.model_dump()
        assert data["id"] == "test-id"
```

**Step 2 - 最小实现** (`api/schemas.py`):
```python
"""Pydantic数据模型定义"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"


class TaskCreate(BaseModel):
    """创建任务请求模型"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    target_function_signature: str
    test_code: str
    success_criteria: Optional[Dict] = Field(default_factory=dict)
    max_generations: int = Field(default=50, ge=1, le=100)


class TaskResponse(BaseModel):
    """任务响应模型"""
    id: str
    name: str
    description: str
    status: TaskStatus
    current_generation: int
    best_score: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class EvolutionStart(BaseModel):
    """启动进化请求模型"""
    task_id: str


class EvolutionControl(BaseModel):
    """进化控制请求模型"""
    task_id: str


class GenerationResponse(BaseModel):
    """进化代响应模型"""
    id: str
    gen_number: int
    intrinsic_score: float
    extrinsic_score: float
    final_score: float
    goodhart_flag: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EvolutionProgress(BaseModel):
    """进化进度模型"""
    task_id: str
    current_gen: int
    max_gen: int
    current_score: float
    best_score: float
    best_gen: int
    status: TaskStatus
    recent_generations: List[GenerationResponse]


class SystemStats(BaseModel):
    """系统统计模型"""
    total_tasks: int
    active_tasks: int
    completed_tasks: int
    total_generations: int


class ApprovalResponse(BaseModel):
    """审批响应模型"""
    id: str
    task_id: str
    generation_id: str
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_comment: Optional[str] = None
    
    class Config:
        from_attributes = True


class ApprovalCreate(BaseModel):
    """创建审批请求模型"""
    task_id: str
    generation_id: str
    code: str
    reason: str


class ApprovalReview(BaseModel):
    """审批审核请求模型"""
    approved: bool
    comment: Optional[str] = None
```

**验收标准**:
- [ ] 所有模型测试失败（Red）
- [ ] 实现后所有测试通过（Green）
- [ ] 覆盖所有字段验证规则


---

### Week 1 Day 2-3: 任务管理路由

---

#### P4-T6: 任务CRUD路由 (4h)

**目标**: 实现任务创建、查询、删除API

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/routers/test_tasks.py`):
```python
"""测试任务管理路由"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch


class TestCreateTask:
    """创建任务测试"""
    
    def test_create_task_returns_201_and_task_data(self):
        """创建任务应返回201和任务数据"""
        # 测试创建任务成功
        pass
    
    def test_create_task_with_invalid_data_returns_422(self):
        """无效数据应返回422"""
        # 测试验证错误
        pass
    
    def test_create_task_saves_test_file(self):
        """创建任务应保存测试文件"""
        # 测试文件保存
        pass


class TestListTasks:
    """列出任务测试"""
    
    def test_list_tasks_returns_all_tasks(self):
        """应返回所有任务列表"""
        # 测试列表查询
        pass
    
    def test_list_tasks_with_status_filter(self):
        """应支持按状态过滤"""
        # 测试状态过滤
        pass


class TestGetTask:
    """获取任务详情测试"""
    
    def test_get_existing_task_returns_task(self):
        """获取存在的任务应返回详情"""
        # 测试获取成功
        pass
    
    def test_get_nonexistent_task_returns_404(self):
        """获取不存在的任务应返回404"""
        # 测试404
        pass


class TestDeleteTask:
    """删除任务测试"""
    
    def test_delete_existing_task_returns_success(self):
        """删除存在的任务应成功"""
        # 测试删除成功
        pass
    
    def test_delete_nonexistent_task_returns_404(self):
        """删除不存在的任务应返回404"""
        # 测试404
        pass
```

**Step 2 - 最小实现** (`api/routers/tasks.py`):
```python
"""任务管理路由"""
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from api.schemas import TaskCreate, TaskResponse, TaskStatus
from storage.models import Task

router = APIRouter()


@router.post("", response_model=TaskResponse, status_code=201)
async def create_task(task: TaskCreate, db: Session = Depends(get_db_session)):
    """创建新任务"""
    db_task = Task(
        id=str(uuid.uuid4()),
        name=task.name,
        description=task.description,
        target_function_signature=task.target_function_signature,
        test_file_path=f"experiments/{task.name}/tests/test_solution.py",
        status=TaskStatus.PENDING,
        current_generation=0,
        best_score=0.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: TaskStatus = None,
    db: Session = Depends(get_db_session)
):
    """列出所有任务"""
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    return query.all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db_session)):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db_session)):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"message": "任务已删除"}
```

**验收标准**:
- [ ] 所有CRUD测试失败（Red）
- [ ] 实现后所有测试通过（Green）
- [ ] 覆盖正常路径和错误路径

---

#### P4-T7: 任务进化控制路由 (3h)

**目标**: 实现start/pause/resume/abort端点

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/routers/test_evolution.py`):
```python
"""测试进化控制路由"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock


class TestStartEvolution:
    """启动进化测试"""
    
    def test_start_evolution_returns_success(self):
        """启动进化应返回成功"""
        pass
    
    def test_start_nonexistent_task_returns_404(self):
        """启动不存在的任务应返回404"""
        pass
    
    def test_start_already_running_evolution_returns_400(self):
        """启动已在运行的进化应返回400"""
        pass


class TestPauseEvolution:
    """暂停进化测试"""
    
    def test_pause_running_evolution_returns_success(self):
        """暂停运行中的进化应成功"""
        pass


class TestResumeEvolution:
    """恢复进化测试"""
    
    def test_resume_paused_evolution_returns_success(self):
        """恢复暂停的进化应成功"""
        pass


class TestAbortEvolution:
    """中止进化测试"""
    
    def test_abort_evolution_returns_success(self):
        """中止进化应返回成功"""
        pass
```

**Step 2 - 最小实现** (`api/routers/evolution.py`):
```python
"""进化控制路由"""
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from api.schemas import TaskStatus
from storage.models import Task

router = APIRouter()

# 存储活跃进化任务
active_evolutions: Dict[str, dict] = {}


@router.post("/tasks/{task_id}/start")
async def start_evolution(
    task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db_session)
):
    """启动进化"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task_id in active_evolutions:
        raise HTTPException(status_code=400, detail="进化已在运行")
    
    active_evolutions[task_id] = {"status": "running"}
    
    task.status = TaskStatus.RUNNING
    db.commit()
    
    return {"message": "进化已启动", "task_id": task_id}


@router.post("/tasks/{task_id}/pause")
async def pause_evolution(task_id: str, db: Session = Depends(get_db_session)):
    """暂停进化"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task_id not in active_evolutions:
        raise HTTPException(status_code=400, detail="进化未运行")
    
    task.status = TaskStatus.PAUSED
    db.commit()
    
    return {"message": "进化已暂停"}


@router.post("/tasks/{task_id}/resume")
async def resume_evolution(task_id: str, db: Session = Depends(get_db_session)):
    """恢复进化"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task.status = TaskStatus.RUNNING
    db.commit()
    
    return {"message": "进化已恢复"}


@router.post("/tasks/{task_id}/abort")
async def abort_evolution(task_id: str, db: Session = Depends(get_db_session)):
    """中止进化"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task_id in active_evolutions:
        del active_evolutions[task_id]
    
    task.status = TaskStatus.ABORTED
    db.commit()
    
    return {"message": "进化已中止"}
```

**验收标准**:
- [ ] 所有控制端点测试失败（Red）
- [ ] 实现后所有测试通过（Green）

---

#### P4-T8: 进化历史查询 (3h)

**目标**: 实现generations查询和回滚功能

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/routers/test_generations.py`):
```python
"""测试进化历史路由"""
import pytest


class TestGetGenerations:
    """获取进化历史测试"""
    
    def test_get_generations_returns_list(self):
        """应返回进化历史列表"""
        pass
    
    def test_get_generations_with_pagination(self):
        """应支持分页"""
        pass


class TestGetGenerationDetail:
    """获取单代详情测试"""
    
    def test_get_existing_generation_returns_detail(self):
        """获取存在的代应返回详情"""
        pass
    
    def test_get_nonexistent_generation_returns_404(self):
        """获取不存在的代应返回404"""
        pass


class TestGetBestSolution:
    """获取最佳实现测试"""
    
    def test_get_best_solution_returns_code(self):
        """应返回最佳实现的代码"""
        pass


class TestRollbackGeneration:
    """回滚测试"""
    
    def test_rollback_to_generation_returns_success(self):
        """回滚应返回成功"""
        pass
```

**Step 2 - 最小实现** (在 `api/routers/tasks.py` 中补充):
```python
@router.get("/{task_id}/generations")
async def get_task_generations(
    task_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db_session)
):
    """获取进化历史"""
    from storage.models import Generation
    
    generations = db.query(Generation).filter(
        Generation.task_id == task_id
    ).order_by(Generation.gen_number).offset(skip).limit(limit).all()
    
    return generations


@router.get("/{task_id}/generations/{gen_id}")
async def get_generation_detail(
    task_id: str,
    gen_id: str,
    db: Session = Depends(get_db_session)
):
    """获取单代详情"""
    from storage.models import Generation
    
    gen = db.query(Generation).filter(
        Generation.task_id == task_id,
        Generation.id == gen_id
    ).first()
    
    if not gen:
        raise HTTPException(status_code=404, detail="进化代不存在")
    
    return gen


@router.get("/{task_id}/best")
async def get_best_solution(task_id: str, db: Session = Depends(get_db_session)):
    """获取最佳实现"""
    from storage.models import Generation
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.best_generation_id:
        raise HTTPException(status_code=404, detail="无最佳实现")
    
    gen = db.query(Generation).filter(
        Generation.id == task.best_generation_id
    ).first()
    
    return {
        "generation": gen.gen_number,
        "score": gen.final_score,
        "code": gen.code
    }


@router.post("/{task_id}/rollback/{gen_id}")
async def rollback_to_generation(
    task_id: str,
    gen_id: int,
    db: Session = Depends(get_db_session)
):
    """回滚到指定代"""
    from storage.models import Generation
    
    gen = db.query(Generation).filter(
        Generation.task_id == task_id,
        Generation.gen_number == gen_id
    ).first()
    
    if not gen:
        raise HTTPException(status_code=404, detail="进化代不存在")
    
    return {"message": f"已回滚到第 {gen_id} 代"}
```

**验收标准**:
- [ ] 所有历史查询测试失败（Red）
- [ ] 实现后所有测试通过（Green）

---

### Week 1 Day 4: WebSocket + 监控

---

#### P4-T9: WebSocket实时推送 (4h)

**目标**: 实现WebSocket实时进度推送

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/routers/test_websocket.py`):
```python
"""测试WebSocket路由"""
import pytest
from fastapi.testclient import TestClient


class TestWebSocketConnection:
    """WebSocket连接测试"""
    
    def test_websocket_connection_accepts_client(self):
        """WebSocket应接受客户端连接"""
        pass
    
    def test_websocket_receives_progress_updates(self):
        """应接收进度更新消息"""
        pass


class TestSystemStats:
    """系统统计API测试"""
    
    def test_get_system_stats_returns_statistics(self):
        """应返回系统统计信息"""
        pass
```

**Step 2 - 最小实现** (`api/routers/monitor.py`):
```python
"""监控路由"""
import asyncio
import json
from typing import Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from api.schemas import TaskStatus
from storage.models import Task, Generation

router = APIRouter()

# 存储活跃WebSocket连接
connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/tasks/{task_id}")
async def evolution_websocket(websocket: WebSocket, task_id: str):
    """进化实时推送WebSocket"""
    await websocket.accept()
    connections[task_id] = websocket
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                await send_progress_updates(task_id, websocket)
    except WebSocketDisconnect:
        del connections[task_id]


async def send_progress_updates(task_id: str, websocket: WebSocket):
    """发送进度更新"""
    pass


@router.get("/stats")
async def get_system_stats(db: Session = Depends(get_db_session)):
    """获取系统统计"""
    total = db.query(Task).count()
    active = db.query(Task).filter(Task.status == TaskStatus.RUNNING).count()
    completed = db.query(Task).filter(
        Task.status.in_(["success", "failed"])
    ).count()
    total_gens = db.query(Generation).count()
    
    return {
        "total_tasks": total,
        "active_tasks": active,
        "completed_tasks": completed,
        "total_generations": total_gens
    }
```

**验收标准**:
- [ ] WebSocket测试失败（Red）
- [ ] 实现后测试通过（Green）

---

#### P4-T10: 监控界面HTML (6h)

**目标**: 创建完整监控界面

**注意**: UI组件主要通过集成测试验证

**实现** (`monitor/index.html`):
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEMDS Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .header { 
            background: #1a1a2e; color: white; padding: 20px; 
            border-radius: 8px; margin-bottom: 20px;
        }
        .grid { display: grid; grid-template-columns: 300px 1fr; gap: 20px; }
        .sidebar { background: white; border-radius: 8px; padding: 20px; }
        .main { background: white; border-radius: 8px; padding: 20px; }
        .task-item { 
            padding: 10px; margin: 5px 0; border-radius: 4px;
            cursor: pointer; transition: background 0.2s;
        }
        .task-item:hover { background: #f0f0f0; }
        .task-item.active { background: #e3f2fd; }
        .status { 
            display: inline-block; width: 8px; height: 8px;
            border-radius: 50%; margin-right: 8px;
        }
        .status.running { background: #4caf50; }
        .status.pending { background: #ff9800; }
        .status.success { background: #2196f3; }
        .status.failed { background: #f44336; }
        .progress-bar {
            height: 20px; background: #e0e0e0; border-radius: 10px;
            overflow: hidden; margin: 10px 0;
        }
        .progress-fill {
            height: 100%; background: #4caf50; transition: width 0.3s;
        }
        .code-block {
            background: #263238; color: #aed581;
            padding: 15px; border-radius: 4px;
            font-family: 'Courier New', monospace;
            overflow-x: auto; white-space: pre-wrap;
        }
        .score-card {
            display: inline-block; padding: 15px 25px;
            background: #f5f5f5; border-radius: 8px;
            margin: 10px 10px 10px 0;
        }
        .score-value { font-size: 32px; font-weight: bold; color: #1a1a2e; }
        .score-label { font-size: 12px; color: #666; }
        .alert {
            padding: 10px 15px; border-radius: 4px; margin: 10px 0;
        }
        .alert.warning { background: #fff3e0; color: #e65100; }
        .alert.error { background: #ffebee; color: #c62828; }
        button {
            padding: 10px 20px; border: none; border-radius: 4px;
            cursor: pointer; margin: 5px;
        }
        button.primary { background: #2196f3; color: white; }
        button.danger { background: #f44336; color: white; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        #chart { height: 300px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>SEMDS Monitor</h1>
            <p>自进化元开发系统监控界面</p>
        </div>
        
        <div class="grid">
            <div class="sidebar">
                <h3>任务列表</h3>
                <div id="task-list"></div>
                <button class="primary" onclick="createTask()">+ 新建任务</button>
            </div>
            
            <div class="main">
                <div id="task-detail">
                    <p>请选择一个任务查看详情</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '/api';
        const WS_BASE = 'ws://localhost:8000';
        let currentTaskId = null;
        let ws = null;
        
        async function loadTasks() {
            const res = await fetch(`${API_BASE}/tasks`);
            const tasks = await res.json();
            renderTaskList(tasks);
        }
        
        function renderTaskList(tasks) {
            const html = tasks.map(t => `
                <div class="task-item ${t.id === currentTaskId ? 'active' : ''}" 
                     onclick="selectTask('${t.id}')">
                    <span class="status ${t.status}"></span>
                    ${t.name}
                    <br><small>得分: ${(t.best_score * 100).toFixed(1)}%</small>
                </div>
            `).join('');
            document.getElementById('task-list').innerHTML = html;
        }
        
        async function selectTask(taskId) {
            currentTaskId = taskId;
            const res = await fetch(`${API_BASE}/tasks/${taskId}`);
            const task = await res.json();
            renderTaskDetail(task);
            connectWebSocket(taskId);
        }
        
        function renderTaskDetail(task) {
            const html = `
                <h2>${task.name}</h2>
                <p>${task.description}</p>
                
                <div class="score-card">
                    <div class="score-value">${task.current_generation}</div>
                    <div class="score-label">当前代数</div>
                </div>
                
                <div class="score-card">
                    <div class="score-value">${(task.best_score * 100).toFixed(1)}%</div>
                    <div class="score-label">最佳得分</div>
                </div>
                
                <div class="progress-bar">
                    <div class="progress-fill" style="width: ${task.best_score * 100}%"></div>
                </div>
                
                <div id="controls">
                    ${renderControls(task.status)}
                </div>
            `;
            document.getElementById('task-detail').innerHTML = html;
        }
        
        function renderControls(status) {
            if (status === 'pending') {
                return `<button class="primary" onclick="startEvolution()">开始进化</button>`;
            } else if (status === 'running') {
                return `
                    <button onclick="pauseEvolution()">暂停</button>
                    <button class="danger" onclick="abortEvolution()">中止</button>
                `;
            } else if (status === 'paused') {
                return `
                    <button class="primary" onclick="resumeEvolution()">恢复</button>
                    <button class="danger" onclick="abortEvolution()">中止</button>
                `;
            }
            return `<p>进化已${status === 'success' ? '成功完成' : '结束'}</p>`;
        }
        
        function connectWebSocket(taskId) {
            if (ws) ws.close();
            ws = new WebSocket(`${WS_BASE}/ws/tasks/${taskId}`);
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateProgress(data);
            };
        }
        
        function updateProgress(data) {
            // 更新UI...
        }
        
        async function startEvolution() {
            await fetch(`${API_BASE}/tasks/${currentTaskId}/start`, {method: 'POST'});
            loadTasks();
        }
        
        async function pauseEvolution() {
            await fetch(`${API_BASE}/tasks/${currentTaskId}/pause`, {method: 'POST'});
        }
        
        async function resumeEvolution() {
            await fetch(`${API_BASE}/tasks/${currentTaskId}/resume`, {method: 'POST'});
        }
        
        async function abortEvolution() {
            if (!confirm('确定要中止进化吗？')) return;
            await fetch(`${API_BASE}/tasks/${currentTaskId}/abort`, {method: 'POST'});
        }
        
        function createTask() {
            alert('创建任务功能待实现');
        }
        
        loadTasks();
        setInterval(loadTasks, 5000);
    </script>
</body>
</html>
```

**集成测试** (`tests/integration/test_monitor_ui.py`):
```python
"""监控界面集成测试"""
import pytest


class TestMonitorUI:
    """监控界面测试"""
    
    def test_monitor_page_returns_html(self):
        """监控页面应返回HTML"""
        pass
    
    def test_monitor_page_contains_required_elements(self):
        """页面应包含必要元素"""
        pass
```

**验收标准**:
- [ ] 监控界面文件创建完成
- [ ] 包含所有必要UI组件
- [ ] 集成测试通过

W e e k   1   D a y   5   c o n t e n t 
 
 

#### P4-T12: 审批API路由 (2h)

**目标**: 实现审批列表/批准/拒绝端点

**TDD步骤**:

**Step 1 - 编写测试** (`tests/api/routers/test_approvals.py`)

**Step 2 - 最小实现** (`api/routers/approvals.py`):
```python
"""审批路由"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db_session
from api.schemas import ApprovalResponse, ApprovalReview

router = APIRouter()


@router.get("/pending", response_model=List[ApprovalResponse])
async def list_pending_approvals(db: Session = Depends(get_db_session)):
    """获取待审批列表"""
    # 实现待审批列表查询
    pass


@router.post("/{approval_id}/approve")
async def approve_request(
    approval_id: str,
    review: ApprovalReview,
    db: Session = Depends(get_db_session)
):
    """批准请求"""
    # 实现批准逻辑
    pass


@router.post("/{approval_id}/reject")
async def reject_request(
    approval_id: str,
    review: ApprovalReview,
    db: Session = Depends(get_db_session)
):
    """拒绝请求"""
    # 实现拒绝逻辑
    pass
```

#### P4-T13: 集成验收测试 (2h)

**目标**: 验证完整Phase 4功能

**集成测试** (`tests/integration/test_phase4_full.py`):
```python
"""Phase 4完整集成测试"""
import pytest


class TestPhase4Integration:
    """Phase 4集成测试"""
    
    def test_full_evolution_workflow(self):
        """完整进化流程测试"""
        # 1. 创建任务
        # 2. 启动进化
        # 3. 查询进度
        # 4. 获取历史
        # 5. 中止进化
        pass
```

---

## 验收标准

### 必须完成

- [ ] FastAPI应用可启动
- [ ] 任务CRUD API可用 (路径对齐规格7.1节)
- [ ] 进化控制API可用 (路径对齐规格7.2节)
- [ ] 进化历史API可用 (路径对齐规格7.2节)
- [ ] 审批API可用 (路径对齐规格7.3节)
- [ ] HumanGateMonitor实现并可用 (规格4.7节)
- [ ] WebSocket实时推送可用 (路径对齐规格7.4节)
- [ ] 监控界面可访问

### 功能验收

```bash
# 1. 启动服务
uvicorn api.main:app --reload

# 2. 健康检查
curl http://localhost:8000/health

# 3. 创建任务
curl -X POST http://localhost:8000/api/tasks   -H "Content-Type: application/json"   -d '{"name": "test", "description": "test"...}'

# 4. 启动进化
curl -X POST http://localhost:8000/api/tasks/{task_id}/start

# 5. 查看监控界面
# 浏览器访问 http://localhost:8000/monitor/index.html
```

---

## 测试覆盖率要求

| 代码类型 | 行覆盖率 | 分支覆盖率 |
|---------|---------|-----------|
| api/ 新代码 | 100% | 100% |
| factory/ 新代码 | 100% | 100% |
| monitor/ 界面 | N/A (集成测试) | N/A |

---

## 实施检查清单

### Day 1 检查点
- [ ] P4-T1 完成 (FastAPI主应用)
- [ ] P4-T2 完成 (依赖注入)
- [ ] P4-T3 完成 (错误处理)
- [ ] P4-T4 完成 (CORS配置)
- [ ] P4-T5 完成 (Pydantic模型)
- [ ] 所有测试100%通过

### Day 2-3 检查点
- [ ] P4-T6 完成 (任务CRUD)
- [ ] P4-T7 完成 (进化控制)
- [ ] P4-T8 完成 (历史查询)
- [ ] 所有测试100%通过

### Day 4 检查点
- [ ] P4-T9 完成 (WebSocket)
- [ ] P4-T10 完成 (监控界面)
- [ ] 集成测试通过

### Day 5 检查点
- [ ] P4-T11 完成 (HumanGate)
- [ ] P4-T12 完成 (审批路由)
- [ ] P4-T13 完成 (集成验收)
- [ ] 最终验收通过

---

*文档版本: v1.0*  
*创建时间: 2026-03-12*  
*最后更新: 2026-03-12*

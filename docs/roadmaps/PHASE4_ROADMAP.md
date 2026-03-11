# SEMDS Phase 4 原子化开发路线图

**文档版本**: v1.0  
**对应规格**: SEMDS_v1.1_SPEC.md Phase 4  
**目标**: 实现API层和监控界面

---

## 📋 Phase 4 任务总览

**时间**: 1周  
**前置依赖**: Phase 3 完成并通过验收  
**交付物**: FastAPI服务 + Web监控界面  
**验收标准**: 可通过HTTP API控制进化，通过Web界面监控

---

## 🎯 任务分解（WBS）

### 4.1 FastAPI 基础架构

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P4-T1 | 创建 FastAPI 主应用 | 2h | - | AI |
| P4-T2 | 配置依赖注入 | 2h | P4-T1 | AI |
| P4-T3 | 实现错误处理中间件 | 2h | P4-T1 | AI |
| P4-T4 | 配置 CORS 和日志 | 1h | P4-T1 | AI |

**详细规格**:
```python
# api/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await init_database()
    yield
    # 关闭时清理
    await close_database()

app = FastAPI(
    title="SEMDS API",
    description="自进化元开发系统 API",
    version="1.1.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需要限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入路由
from api.routers import tasks, evolution, monitor
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(evolution.router, prefix="/api", tags=["evolution"])
app.include_router(monitor.router, prefix="/api", tags=["monitor"])

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.1.0"}
```

---

### 4.2 Pydantic 数据模型

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P4-T5 | 定义请求/响应模型 | 3h | P4-T1 | AI |
| P4-T6 | 定义任务相关模型 | 2h | P4-T5 | AI |
| P4-T7 | 定义进化相关模型 | 2h | P4-T5 | AI |
| P4-T8 | 模型验证单元测试 | 2h | P4-T5-P4-T7 | AI |

**详细规格**:
```python
# api/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"

# ========== 任务管理模型 ==========

class TaskCreate(BaseModel):
    """创建任务请求"""
    name: str = Field(..., min_length=1, max_length=100)
    description: str
    target_function_signature: str
    test_code: str  # 测试代码内容
    success_criteria: Optional[Dict] = Field(default_factory=dict)
    max_generations: int = Field(default=50, ge=1, le=100)

class TaskResponse(BaseModel):
    """任务响应"""
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

# ========== 进化控制模型 ==========

class EvolutionStart(BaseModel):
    """启动进化请求"""
    task_id: str

class EvolutionControl(BaseModel):
    """进化控制请求（暂停/恢复/中止）"""
    task_id: str

class GenerationResponse(BaseModel):
    """进化代响应"""
    id: str
    gen_number: int
    intrinsic_score: float
    extrinsic_score: float
    final_score: float
    goodhart_flag: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== 监控模型 ==========

class EvolutionProgress(BaseModel):
    """进化进度"""
    task_id: str
    current_gen: int
    max_gen: int
    current_score: float
    best_score: float
    best_gen: int
    status: TaskStatus
    recent_generations: List[GenerationResponse]

class SystemStats(BaseModel):
    """系统统计"""
    total_tasks: int
    active_tasks: int
    completed_tasks: int
    total_generations: int
```

---

### 4.3 任务管理路由

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P4-T9 | 实现任务 CRUD | 4h | P4-T5 | AI |
| P4-T10 | 实现任务列表查询 | 2h | P4-T9 | AI |
| P4-T11 | 任务路由单元测试 | 3h | P4-T9,P4-T10 | AI |

**详细规格**:
```python
# api/routers/tasks.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid
from datetime import datetime

from api.schemas import TaskCreate, TaskResponse, TaskStatus
from storage.database import get_db_session
from storage.models import Task

router = APIRouter()

@router.post("", response_model=TaskResponse)
async def create_task(task: TaskCreate, db = Depends(get_db_session)):
    """创建新任务"""
    db_task = Task(
        id=str(uuid.uuid4()),
        name=task.name,
        description=task.description,
        target_function_signature=task.target_function_signature,
        test_file_path=f"experiments/{task.name}/tests/test_solution.py",
        status=TaskStatus.PENDING,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    # 保存测试文件
    # ...
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status: TaskStatus = None,
    db = Depends(get_db_session)
):
    """列出所有任务"""
    query = db.query(Task)
    if status:
        query = query.filter(Task.status == status)
    return query.all()

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db = Depends(get_db_session)):
    """获取任务详情"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task

@router.delete("/{task_id}")
async def delete_task(task_id: str, db = Depends(get_db_session)):
    """删除任务"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    db.delete(task)
    db.commit()
    return {"message": "任务已删除"}

# ========== 规格对齐: 增补API端点以匹配SEMDS_v1.1_SPEC.md 7.2节 ==========

@router.post("/{task_id}/start")
async def start_task_evolution(task_id: str, db = Depends(get_db_session)):
    """启动任务进化"""
    # 调用evolution路由的实现
    pass

@router.post("/{task_id}/pause")
async def pause_task_evolution(task_id: str, db = Depends(get_db_session)):
    """暂停任务进化"""
    pass

@router.post("/{task_id}/resume")
async def resume_task_evolution(task_id: str, db = Depends(get_db_session)):
    """恢复任务进化"""
    pass

@router.post("/{task_id}/abort")
async def abort_task_evolution(task_id: str, db = Depends(get_db_session)):
    """中止任务进化"""
    pass

@router.get("/{task_id}/generations")
async def get_task_generations(
    task_id: str,
    skip: int = 0,
    limit: int = 100,
    db = Depends(get_db_session)
):
    """获取进化历史"""
    from storage.models import Generation
    generations = db.query(Generation).filter(
        Generation.task_id == task_id
    ).order_by(Generation.gen_number).offset(skip).limit(limit).all()
    return generations

@router.get("/{task_id}/generations/{gen_id}")
async def get_generation_detail(task_id: str, gen_id: str, db = Depends(get_db_session)):
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
async def get_best_solution(task_id: str, db = Depends(get_db_session)):
    """获取最佳实现"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.best_generation_id:
        raise HTTPException(status_code=404, detail="无最佳实现")
    
    from storage.models import Generation
    gen = db.query(Generation).filter(Generation.id == task.best_generation_id).first()
    return {
        "generation": gen.gen_number,
        "score": gen.final_score,
        "code": gen.code
    }

@router.post("/{task_id}/rollback/{gen_id}")
async def rollback_to_generation(task_id: str, gen_id: str, db = Depends(get_db_session)):
    """回滚到指定代"""
    from core.version_control import GitManager
    git = GitManager()
    
    gen = db.query(Generation).filter(
        Generation.task_id == task_id,
        Generation.gen_number == gen_id
    ).first()
    
    if not gen:
        raise HTTPException(status_code=404, detail="进化代不存在")
    
    git.rollback_to_generation(f"experiments/{task_id}/solutions/solution.py", gen.git_commit_hash)
    return {"message": f"已回滚到第 {gen_id} 代"}
```

---

### 4.4 进化控制路由

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P4-T12 | 实现进化启动 | 4h | P4-T9 | AI |
| P4-T13 | 实现暂停/恢复/中止 | 3h | P4-T12 | AI |
| P4-T14 | 实现进化历史查询 | 3h | P4-T12 | AI |
| P4-T15 | 实现回滚功能 | 2h | P4-T14 | AI |
| P4-T16 | 进化路由单元测试 | 3h | P4-T12-P4-T15 | AI |

**详细规格**:
```python
# api/routers/evolution.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

from api.schemas import (
    EvolutionStart, EvolutionControl,
    GenerationResponse, EvolutionProgress
)
from evolution.orchestrator import EvolutionOrchestrator

router = APIRouter()

# 存储活跃进化任务
active_evolutions: Dict[str, EvolutionOrchestrator] = {}

@router.post("/tasks/{task_id}/start")
async def start_evolution(
    task_id: str,
    background_tasks: BackgroundTasks,
    db = Depends(get_db_session)
):
    """启动进化"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task_id in active_evolutions:
        raise HTTPException(status_code=400, detail="进化已在运行")
    
    # 创建编排器
    orchestrator = create_orchestrator(task)
    active_evolutions[task_id] = orchestrator
    
    # 后台运行进化
    background_tasks.add_task(run_evolution, task_id, orchestrator)
    
    # 更新任务状态
    task.status = TaskStatus.RUNNING
    db.commit()
    
    return {"message": "进化已启动", "task_id": task_id}

@router.post("/tasks/{task_id}/pause")
async def pause_evolution(task_id: str, db = Depends(get_db_session)):
    """暂停进化"""
    # 实现暂停逻辑
    pass

@router.post("/tasks/{task_id}/resume")
async def resume_evolution(task_id: str, db = Depends(get_db_session)):
    """恢复进化"""
    # 实现恢复逻辑
    pass

@router.post("/tasks/{task_id}/abort")
async def abort_evolution(task_id: str, db = Depends(get_db_session)):
    """中止进化"""
    if task_id in active_evolutions:
        orchestrator = active_evolutions[task_id]
        orchestrator.termination_checker.config.human_abort = True
        return {"message": "进化中止信号已发送"}
    raise HTTPException(status_code=404, detail="进化任务不存在")

@router.get("/tasks/{task_id}/generations", response_model=List[GenerationResponse])
async def get_generations(
    task_id: str,
    skip: int = 0,
    limit: int = 100,
    db = Depends(get_db_session)
):
    """获取进化历史"""
    generations = db.query(Generation).filter(
        Generation.task_id == task_id
    ).order_by(Generation.gen_number).offset(skip).limit(limit).all()
    return generations

@router.get("/tasks/{task_id}/best")
async def get_best_solution(task_id: str, db = Depends(get_db_session)):
    """获取最佳实现"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task or not task.best_generation_id:
        raise HTTPException(status_code=404, detail="无最佳实现")
    
    gen = db.query(Generation).filter(Generation.id == task.best_generation_id).first()
    return {
        "generation": gen.gen_number,
        "score": gen.final_score,
        "code": gen.code
    }

async def run_evolution(task_id: str, orchestrator: EvolutionOrchestrator):
    """后台运行进化"""
    try:
        result = orchestrator.run()
        # 更新任务状态
        # ...
    finally:
        del active_evolutions[task_id]
```

---

### 4.5 WebSocket 实时监控

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P4-T17 | 实现 WebSocket 连接 | 3h | P4-T1 | AI |
| P4-T18 | 实现实时进度推送 | 4h | P4-T17 | AI |
| P4-T19 | WebSocket单元测试 | 2h | P4-T17,P4-T18 | AI |

**规格对齐**: WebSocket路径应为 `/ws/tasks/{task_id}`（见SEMDS_v1.1_SPEC.md 7.4节）

**详细规格**:
```python
# api/routers/monitor.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
import json

router = APIRouter()

# 存储活跃连接
connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/tasks/{task_id}")
async def evolution_websocket(websocket: WebSocket, task_id: str):
    """进化实时推送 WebSocket"""
    await websocket.accept()
    connections[task_id] = websocket
    
    try:
        while True:
            # 接收客户端消息（如暂停/恢复命令）
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                # 开始推送进度
                await send_progress_updates(task_id, websocket)
    except WebSocketDisconnect:
        del connections[task_id]

async def send_progress_updates(task_id: str, websocket: WebSocket):
    """发送进度更新"""
    while task_id in active_evolutions:
        orchestrator = active_evolutions[task_id]
        
        progress = {
            "task_id": task_id,
            "current_gen": orchestrator.current_gen,
            "current_score": orchestrator.best_score,
            "best_score": orchestrator.best_score,
            "best_gen": orchestrator.best_gen,
            "status": "running"
        }
        
        await websocket.send_json(progress)
        await asyncio.sleep(1)  # 每秒更新

@router.get("/stats")
async def get_system_stats(db = Depends(get_db_session)):
    """获取系统统计"""
    total = db.query(Task).count()
    active = db.query(Task).filter(Task.status == TaskStatus.RUNNING).count()
    completed = db.query(Task).filter(Task.status.in_(["success", "failed"])).count()
    total_gens = db.query(Generation).count()
    
    return {
        "total_tasks": total,
        "active_tasks": active,
        "completed_tasks": completed,
        "total_generations": total_gens
    }
```

---

### 4.6 监控界面 HTML

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P4-T20 | 创建监控界面 HTML | 6h | P4-T17 | AI |
| P4-T21 | 实现任务列表组件 | 3h | P4-T20 | AI |
| P4-T22 | 实现进化进度组件 | 4h | P4-T20 | AI |
| P4-T23 | 实现代码展示组件 | 2h | P4-T20 | AI |
| P4-T24 | 界面集成测试 | 2h | P4-T20-P4-T23 | AI |

**详细规格**:
```html
<!-- monitor/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEMDS Monitor</title>
    <style>
        /* 内联CSS样式 */
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
            <h1>🧬 SEMDS Monitor</h1>
            <p>自进化元开发系统监控界面</p>
        </div>
        
        <div class="grid">
            <!-- 左侧任务列表 -->
            <div class="sidebar">
                <h3>任务列表</h3>
                <div id="task-list"></div>
                <button class="primary" onclick="createTask()">+ 新建任务</button>
            </div>
            
            <!-- 右侧详情 -->
            <div class="main">
                <div id="task-detail">
                    <p>请选择一个任务查看详情</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 内联JavaScript
        const API_BASE = '/api';
        const WS_BASE = 'ws://localhost:8000';
        let currentTaskId = null;
        let ws = null;
        
        // 加载任务列表
        async function loadTasks() {
            const res = await fetch(`${API_BASE}/tasks`);
            const tasks = await res.json();
            renderTaskList(tasks);
        }
        
        // 渲染任务列表
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
        
        // 选择任务
        async function selectTask(taskId) {
            currentTaskId = taskId;
            const res = await fetch(`${API_BASE}/tasks/${taskId}`);
            const task = await res.json();
            renderTaskDetail(task);
            connectWebSocket(taskId);
        }
        
        // 渲染任务详情
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
                
                <div id="chart">[得分趋势图]</div>
                
                <div id="latest-code">
                    <h4>最新代码</h4>
                    <div class="code-block">加载中...</div>
                </div>
            `;
            document.getElementById('task-detail').innerHTML = html;
        }
        
        // 渲染控制按钮
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
        
        // WebSocket连接
        function connectWebSocket(taskId) {
            if (ws) ws.close();
            
            ws = new WebSocket(`${WS_BASE}/ws/tasks/${taskId}`);
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateProgress(data);
            };
        }
        
        // 更新进度
        function updateProgress(data) {
            // 更新UI...
        }
        
        // 控制函数
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
            // 打开创建任务对话框
            alert('创建任务功能待实现');
        }
        
        // 初始化
        loadTasks();
        setInterval(loadTasks, 5000);  // 每5秒刷新任务列表
    </script>
</body>
</html>
```

---

## 📊 任务依赖图

```
P4-T1 (FastAPI主应用)
    ├── P4-T2 (依赖注入)
    ├── P4-T3 (错误处理)
    ├── P4-T4 (CORS/日志)
    └── P4-T5 (Pydantic模型)
        ├── P4-T6 (任务模型)
        ├── P4-T7 (进化模型)
        └── P4-T8 (模型测试)
            ├── P4-T9 (任务CRUD)
            │   ├── P4-T10 (任务列表)
            │   └── P4-T11 (测试)
            ├── P4-T12 (进化启动)
            │   ├── P4-T13 (暂停/恢复/中止)
            │   ├── P4-T14 (历史查询)
            │   ├── P4-T15 (回滚)
            │   └── P4-T16 (测试)
            └── P4-T17 (WebSocket)
                ├── P4-T18 (实时推送)
                ├── P4-T19 (测试)
                └── P4-T20 (监控界面)
                    ├── P4-T21 (任务列表组件)
                    ├── P4-T22 (进度组件)
                    ├── P4-T23 (代码展示)
                    └── P4-T24 (测试)
```

---

## ✅ 验收标准

### 必须完成
- [ ] FastAPI应用可启动
- [ ] 任务CRUD API可用 (路径对齐规格7.1节)
- [ ] 进化控制API可用 (路径对齐规格7.2节: /api/tasks/{id}/start|pause|resume|abort)
- [ ] 进化历史API可用 (路径对齐规格7.2节: /api/tasks/{id}/generations|best|rollback)
- [ ] 审批API可用 (路径对齐规格7.3节: /api/approvals/*)
- [ ] HumanGateMonitor实现并可用 (规格4.7节)
- [ ] WebSocket实时推送可用 (路径对齐规格7.4节: /ws/tasks/{id})
- [ ] 监控界面可访问

### 功能验收
```bash
# 1. 启动服务
uvicorn api.main:app --reload

# 2. 健康检查
curl http://localhost:8000/health
# 期望: {"status": "healthy", "version": "1.1.0"}

# 3. 创建任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"name": "test", "description": "test", "target_function_signature": "def add(a, b):", "test_code": "..."}'

# 4. 启动进化
curl -X POST http://localhost:8000/api/tasks/{task_id}/start

# 5. 查看监控界面
# 浏览器访问 http://localhost:8000/monitor/index.html
```

---

**最后更新**: 2026-03-07  
**前置**: [Phase 3路线图](./PHASE3_ROADMAP.md)  
**后续**: [Phase 5路线图](./PHASE5_ROADMAP.md)

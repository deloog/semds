# SEMDS Phase 5 原子化开发路线图

**文档版本**: v1.0  
**对应规格**: SEMDS_v1.1_SPEC.md Phase 5  
**目标**: 实现多任务并发进化，支持任务间策略隔离

---

## 📋 Phase 5 任务总览

**时间**: 1周  
**前置依赖**: Phase 4 完成并通过验收  
**交付物**: 多任务并发管理系统  
**验收标准**: 可同时运行多个进化任务，任务间策略相互隔离不干扰

---

## 🎯 任务分解（WBS）

### 5.1 任务管理器（Task Manager）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P5-T1 | 实现 TaskManager 核心类 | 4h | - | AI |
| P5-T2 | 实现任务队列管理 | 3h | P5-T1 | AI |
| P5-T3 | 实现任务优先级调度 | 3h | P5-T2 | AI |
| P5-T4 | 实现任务状态机 | 3h | P5-T1 | AI |
| P5-T5 | 任务管理器单元测试 | 4h | P5-T1-P5-T4 | AI |

**详细规格**:
```python
# factory/task_manager.py

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class TaskState(Enum):
    """任务状态机"""
    PENDING = auto()      # 等待调度
    QUEUED = auto()       # 在队列中
    RUNNING = auto()      # 正在进化
    PAUSED = auto()       # 暂停
    COMPLETED = auto()    # 成功完成
    FAILED = auto()       # 失败终止
    ABORTED = auto()      # 人工中止

@dataclass
class TaskHandle:
    """任务句柄，用于外部控制"""
    task_id: str
    name: str
    priority: TaskPriority
    state: TaskState
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_callback: Optional[Callable] = None

@dataclass
class TaskSpecification:
    """任务规格"""
    name: str
    description: str
    target_function_signature: str
    test_code: str
    success_criteria: Dict
    max_generations: int = 50
    priority: TaskPriority = TaskPriority.NORMAL

class TaskManager:
    """
    任务管理器
    
    职责:
    - 管理多任务生命周期
    - 任务队列和优先级调度
    - 并发控制（限制同时运行的任务数）
    - 任务间资源分配
    """
    
    def __init__(
        self,
        max_concurrent_tasks: int = 3,
        max_queued_tasks: int = 10
    ):
        self.max_concurrent = max_concurrent_tasks
        self.max_queued = max_queued_tasks
        
        # 任务存储
        self._tasks: Dict[str, TaskHandle] = {}
        self._task_specs: Dict[str, TaskSpecification] = {}
        
        # 队列
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        
        # 运行中任务
        self._running: Dict[str, asyncio.Task] = {}
        
        # 执行器
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
        
        # 锁
        self._lock = asyncio.Lock()
        
        # 调度器状态
        self._scheduler_running = False
        self._scheduler_task: Optional[asyncio.Task] = None
    
    async def submit_task(
        self,
        spec: TaskSpecification
    ) -> TaskHandle:
        """
        提交新任务
        
        Args:
            spec: 任务规格
            
        Returns:
            TaskHandle: 任务句柄
            
        Raises:
            QueueFullError: 队列已满
        """
        async with self._lock:
            # 检查队列容量
            if self._queue.qsize() >= self.max_queued:
                raise QueueFullError(f"任务队列已满 (max={self.max_queued})")
            
            task_id = str(uuid.uuid4())
            handle = TaskHandle(
                task_id=task_id,
                name=spec.name,
                priority=spec.priority,
                state=TaskState.PENDING,
                created_at=datetime.utcnow()
            )
            
            self._tasks[task_id] = handle
            self._task_specs[task_id] = spec
            
            # 加入优先级队列 (优先级值越小越优先)
            await self._queue.put((-spec.priority.value, task_id))
            handle.state = TaskState.QUEUED
            
            return handle
    
    async def start_scheduler(self):
        """启动任务调度器"""
        if self._scheduler_running:
            return
            
        self._scheduler_running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
    
    async def stop_scheduler(self):
        """停止任务调度器"""
        self._scheduler_running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        while self._scheduler_running:
            try:
                # 检查并发限制
                if len(self._running) >= self.max_concurrent:
                    await asyncio.sleep(0.1)
                    continue
                
                # 获取下一个任务
                try:
                    _, task_id = await asyncio.wait_for(
                        self._queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                async with self._lock:
                    handle = self._tasks.get(task_id)
                    if not handle or handle.state != TaskState.QUEUED:
                        continue
                    
                    # 启动任务
                    handle.state = TaskState.RUNNING
                    handle.started_at = datetime.utcnow()
                    
                    task_coroutine = self._run_evolution_task(task_id)
                    self._running[task_id] = asyncio.create_task(task_coroutine)
                    
            except Exception as e:
                print(f"调度器错误: {e}")
    
    async def _run_evolution_task(self, task_id: str):
        """运行单个进化任务"""
        try:
            spec = self._task_specs[task_id]
            handle = self._tasks[task_id]
            
            # 创建隔离上下文
            from factory.isolation_manager import IsolationManager
            isolation = IsolationManager()
            context = await isolation.create_isolated_context(task_id)
            
            # 创建进化编排器
            orchestrator = self._create_orchestrator(spec, context)
            
            # 运行进化
            result = await orchestrator.run()
            
            # 更新状态
            async with self._lock:
                if result.success:
                    handle.state = TaskState.COMPLETED
                else:
                    handle.state = TaskState.FAILED
                handle.completed_at = datetime.utcnow()
                
        except Exception as e:
            async with self._lock:
                handle = self._tasks.get(task_id)
                if handle:
                    handle.state = TaskState.FAILED
                    handle.completed_at = datetime.utcnow()
        finally:
            async with self._lock:
                if task_id in self._running:
                    del self._running[task_id]
    
    def _create_orchestrator(self, spec: TaskSpecification, context):
        """为任务创建进化编排器"""
        # 导入各组件
        from evolution.orchestrator import EvolutionOrchestrator
        from evolution.code_generator import CodeGenerator
        from evolution.test_runner import TestRunner
        from evolution.dual_evaluator import DualEvaluator
        from evolution.strategy_optimizer import StrategyOptimizer
        from evolution.termination_checker import TerminationChecker
        from core.version_control import GitManager
        import os
        
        # 创建隔离的策略优化器
        strategy_optimizer = StrategyOptimizer(task_id=context.task_id)
        
        return EvolutionOrchestrator(
            task=spec,
            code_generator=CodeGenerator(api_key=os.getenv("ANTHROPIC_API_KEY")),
            test_runner=TestRunner(),
            dual_evaluator=DualEvaluator(),
            strategy_optimizer=strategy_optimizer,
            termination_checker=TerminationChecker(),
            git_manager=GitManager(repo_path=context.workspace_path)
        )
    
    async def pause_task(self, task_id: str) -> bool:
        """暂停任务"""
        async with self._lock:
            handle = self._tasks.get(task_id)
            if not handle or handle.state != TaskState.RUNNING:
                return False
            
            # 发送暂停信号
            if task_id in self._running:
                # 通过 orchestrator 的终止检查器实现暂停
                pass
            
            handle.state = TaskState.PAUSED
            return True
    
    async def resume_task(self, task_id: str) -> bool:
        """恢复任务"""
        async with self._lock:
            handle = self._tasks.get(task_id)
            if not handle or handle.state != TaskState.PAUSED:
                return False
            
            # 重新加入队列
            await self._queue.put((-handle.priority.value, task_id))
            handle.state = TaskState.QUEUED
            return True
    
    async def abort_task(self, task_id: str) -> bool:
        """中止任务"""
        async with self._lock:
            handle = self._tasks.get(task_id)
            if not handle:
                return False
            
            if task_id in self._running:
                # 取消运行中的任务
                self._running[task_id].cancel()
                del self._running[task_id]
            
            handle.state = TaskState.ABORTED
            handle.completed_at = datetime.utcnow()
            return True
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        handle = self._tasks.get(task_id)
        if not handle:
            return None
        
        return {
            "task_id": handle.task_id,
            "name": handle.name,
            "state": handle.state.name,
            "priority": handle.priority.name,
            "created_at": handle.created_at.isoformat(),
            "started_at": handle.started_at.isoformat() if handle.started_at else None,
            "completed_at": handle.completed_at.isoformat() if handle.completed_at else None
        }
    
    def list_tasks(
        self,
        state: Optional[TaskState] = None
    ) -> List[Dict]:
        """列出所有任务"""
        tasks = []
        for handle in self._tasks.values():
            if state and handle.state != state:
                continue
            tasks.append(self.get_task_status(handle.task_id))
        return tasks
    
    def get_system_stats(self) -> Dict:
        """获取系统统计"""
        states = {}
        for handle in self._tasks.values():
            states[handle.state.name] = states.get(handle.state.name, 0) + 1
        
        return {
            "total_tasks": len(self._tasks),
            "running_tasks": len(self._running),
            "queued_tasks": self._queue.qsize(),
            "max_concurrent": self.max_concurrent,
            "max_queued": self.max_queued,
            "by_state": states
        }

class QueueFullError(Exception):
    """队列已满异常"""
    pass
```

**TDD要求**:
```python
# tests/factory/test_task_manager.py

import pytest
import asyncio
from factory.task_manager import TaskManager, TaskSpecification, TaskPriority, TaskState

@pytest.mark.asyncio
async def test_submit_task():
    """测试提交任务"""
    manager = TaskManager()
    spec = TaskSpecification(
        name="test_task",
        description="Test task",
        target_function_signature="def add(a, b):",
        test_code="assert add(1, 2) == 3"
    )
    
    handle = await manager.submit_task(spec)
    assert handle.task_id is not None
    assert handle.state == TaskState.QUEUED

@pytest.mark.asyncio
async def test_task_priority_queue():
    """测试优先级队列"""
    manager = TaskManager(max_concurrent_tasks=1)
    
    # 提交不同优先级的任务
    low = TaskSpecification(name="low", priority=TaskPriority.LOW, ...)
    high = TaskSpecification(name="high", priority=TaskPriority.HIGH, ...)
    
    await manager.submit_task(low)
    await manager.submit_task(high)
    
    # 高优先级应该先出队
    # 验证调度顺序

@pytest.mark.asyncio
async def test_concurrent_limit():
    """测试并发限制"""
    manager = TaskManager(max_concurrent_tasks=2)
    
    # 提交3个任务
    # 验证最多只有2个在运行

@pytest.mark.asyncio
async def test_abort_task():
    """测试中止任务"""
    manager = TaskManager()
    spec = TaskSpecification(...)
    handle = await manager.submit_task(spec)
    
    result = await manager.abort_task(handle.task_id)
    assert result is True
    assert manager.get_task_status(handle.task_id)["state"] == "ABORTED"
```

---

### 5.2 隔离管理器（Isolation Manager）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P5-T6 | 实现 IsolationManager 类 | 4h | - | AI |
| P5-T7 | 实现文件系统隔离 | 3h | P5-T6 | AI |
| P5-T8 | 实现策略状态隔离 | 3h | P5-T6 | AI |
| P5-T9 | 实现Git分支隔离 | 2h | P5-T6 | AI |
| P5-T10 | 隔离管理器单元测试 | 4h | P5-T6-P5-T9 | AI |

**详细规格**:
```python
# factory/isolation_manager.py

from dataclasses import dataclass
from pathlib import Path
import shutil
import os

@dataclass
class IsolatedContext:
    """
    隔离上下文
    
    每个任务有完全独立的：
    - 工作目录
    - 策略状态
    - Git分支
    - 数据库命名空间
    """
    task_id: str
    workspace_path: str      # 独立工作目录
    strategy_state_path: str # 策略状态文件
    git_branch: str          # Git分支名
    db_namespace: str        # 数据库命名空间前缀

class IsolationManager:
    """
    隔离管理器
    
    核心职责：确保不同任务的进化策略相互隔离，防止"策略污染"。
    
    策略污染示例：
    - 任务A：计算器进化，激进变异策略效果好
    - 任务B：字符串处理，保守策略效果好
    - 如果不隔离，任务A的激进策略数据会影响任务B的选择
    """
    
    def __init__(self, base_path: str = ".isolated"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    async def create_isolated_context(self, task_id: str) -> IsolatedContext:
        """
        为任务创建隔离上下文
        
        Args:
            task_id: 任务唯一标识
            
        Returns:
            IsolatedContext: 隔离上下文
        """
        task_workspace = self.base_path / task_id
        task_workspace.mkdir(exist_ok=True)
        
        # 创建子目录结构
        (task_workspace / "code").mkdir(exist_ok=True)
        (task_workspace / "strategies").mkdir(exist_ok=True)
        (task_workspace / "logs").mkdir(exist_ok=True)
        
        # 策略状态文件路径
        strategy_state_path = task_workspace / "strategies" / "thompson_state.json"
        
        # 初始化空的策略状态
        await self._init_strategy_state(strategy_state_path)
        
        # Git分支名
        git_branch = f"evolution/{task_id}"
        await self._create_git_branch(git_branch)
        
        return IsolatedContext(
            task_id=task_id,
            workspace_path=str(task_workspace / "code"),
            strategy_state_path=str(strategy_state_path),
            git_branch=git_branch,
            db_namespace=f"task_{task_id.replace('-', '_')}"
        )
    
    async def _init_strategy_state(self, path: Path):
        """初始化策略状态文件"""
        import json
        initial_state = {
            "arms": {},  # Thompson Sampling 臂状态
            "version": 1
        }
        with open(path, 'w') as f:
            json.dump(initial_state, f, indent=2)
    
    async def _create_git_branch(self, branch_name: str):
        """创建Git分支"""
        import subprocess
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                capture_output=True,
                check=False
            )
        except Exception:
            # 分支可能已存在
            pass
    
    async def cleanup_context(self, task_id: str) -> bool:
        """
        清理隔离上下文
        
        任务完成后清理资源，但保留策略状态用于分析。
        """
        task_workspace = self.base_path / task_id
        if not task_workspace.exists():
            return False
        
        # 保留策略状态，删除代码和日志
        code_dir = task_workspace / "code"
        logs_dir = task_workspace / "logs"
        
        if code_dir.exists():
            shutil.rmtree(code_dir)
        if logs_dir.exists():
            shutil.rmtree(logs_dir)
        
        return True
    
    async def archive_context(self, task_id: str, archive_path: str) -> bool:
        """
        归档隔离上下文
        
        将任务的所有数据打包归档。
        """
        task_workspace = self.base_path / task_id
        if not task_workspace.exists():
            return False
        
        archive_file = Path(archive_path) / f"{task_id}.tar.gz"
        shutil.make_archive(
            str(archive_file).replace('.tar.gz', ''),
            'gztar',
            task_workspace
        )
        return True
    
    def get_context(self, task_id: str) -> Optional[IsolatedContext]:
        """获取已存在的隔离上下文"""
        task_workspace = self.base_path / task_id
        if not task_workspace.exists():
            return None
        
        strategy_state_path = task_workspace / "strategies" / "thompson_state.json"
        
        return IsolatedContext(
            task_id=task_id,
            workspace_path=str(task_workspace / "code"),
            strategy_state_path=str(strategy_state_path),
            git_branch=f"evolution/{task_id}",
            db_namespace=f"task_{task_id.replace('-', '_')}"
        )
    
    def list_isolated_tasks(self) -> List[str]:
        """列出所有已隔离的任务ID"""
        if not self.base_path.exists():
            return []
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]
    
    def verify_isolation(self, task_id_a: str, task_id_b: str) -> bool:
        """
        验证两个任务的隔离性
        
        检查：
        - 工作目录不同
        - 策略状态文件不同
        - Git分支不同
        """
        ctx_a = self.get_context(task_id_a)
        ctx_b = self.get_context(task_id_b)
        
        if not ctx_a or not ctx_b:
            return False
        
        return (
            ctx_a.workspace_path != ctx_b.workspace_path and
            ctx_a.strategy_state_path != ctx_b.strategy_state_path and
            ctx_a.git_branch != ctx_b.git_branch and
            ctx_a.db_namespace != ctx_b.db_namespace
        )
```

**关键设计决策**:

1. **策略隔离原则**: 每个任务的 Thompson Sampling 状态完全独立
2. **Git分支隔离**: 每个任务有独立的Git分支，历史不混杂
3. **文件系统隔离**: 每个任务有独立的工作目录
4. **保留策略状态**: 即使任务完成，策略状态也保留用于后续分析

**TDD要求**:
```python
# tests/factory/test_isolation_manager.py

import pytest
import asyncio
from factory.isolation_manager import IsolationManager, IsolatedContext

@pytest.mark.asyncio
async def test_create_isolated_context():
    """测试创建隔离上下文"""
    manager = IsolationManager()
    ctx = await manager.create_isolated_context("task-123")
    
    assert ctx.task_id == "task-123"
    assert os.path.exists(ctx.workspace_path)
    assert os.path.exists(ctx.strategy_state_path)

@pytest.mark.asyncio
async def test_strategy_isolation():
    """测试策略状态隔离"""
    manager = IsolationManager()
    
    ctx_a = await manager.create_isolated_context("task-a")
    ctx_b = await manager.create_isolated_context("task-b")
    
    # 策略状态文件路径应该不同
    assert ctx_a.strategy_state_path != ctx_b.strategy_state_path
    
    # 修改任务A的策略状态
    import json
    with open(ctx_a.strategy_state_path, 'r') as f:
        state_a = json.load(f)
    state_a["arms"]["test"] = {"alpha": 10, "beta": 1}
    with open(ctx_a.strategy_state_path, 'w') as f:
        json.dump(state_a, f)
    
    # 任务B的策略状态不应受影响
    with open(ctx_b.strategy_state_path, 'r') as f:
        state_b = json.load(f)
    assert "test" not in state_b["arms"]

@pytest.mark.asyncio
async def test_verify_isolation():
    """测试隔离性验证"""
    manager = IsolationManager()
    
    await manager.create_isolated_context("task-a")
    await manager.create_isolated_context("task-b")
    
    assert manager.verify_isolation("task-a", "task-b") is True
    assert manager.verify_isolation("task-a", "task-a") is False
```

---

### 5.3 策略持久化升级

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P5-T11 | 升级 StrategyOptimizer 支持隔离 | 3h | P5-T8 | AI |
| P5-T12 | 实现策略状态加载/保存 | 2h | P5-T11 | AI |
| P5-T13 | 策略持久化测试 | 2h | P5-T11,P5-T12 | AI |

**详细规格**:
```python
# evolution/strategy_optimizer.py 升级

class StrategyOptimizer:
    """
    Thompson Sampling策略优化器（支持隔离）
    
    升级点：
    - 支持从隔离上下文加载/保存状态
    - 每个任务独立的策略空间
    """
    
    def __init__(
        self,
        task_id: str,
        state_path: Optional[str] = None
    ):
        self.task_id = task_id
        self.state_path = state_path
        self.arms: Dict[str, StrategyArm] = {}
        self._initialize_arms()
        
        # 如果有状态路径，加载已有状态
        if state_path and os.path.exists(state_path):
            self._load_state()
    
    def _load_state(self):
        """从文件加载策略状态"""
        import json
        with open(self.state_path, 'r') as f:
            data = json.load(f)
        
        for key, arm_data in data.get("arms", {}).items():
            self.arms[key] = StrategyArm(
                key=key,
                alpha=arm_data.get("alpha", 1.0),
                beta=arm_data.get("beta", 1.0),
                total_uses=arm_data.get("uses", 0)
            )
    
    def _save_state(self):
        """保存策略状态到文件"""
        if not self.state_path:
            return
        
        import json
        data = {
            "arms": {
                key: {
                    "alpha": arm.alpha,
                    "beta": arm.beta,
                    "uses": arm.total_uses
                }
                for key, arm in self.arms.items()
            },
            "version": 1
        }
        
        with open(self.state_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def report_result(self, strategy: dict, success: bool, score: float):
        """报告结果并保存状态"""
        key = self._strategy_to_key(strategy)
        if key in self.arms:
            self.arms[key].update(success)
            self._save_state()  # 每次更新后保存
```

---

### 5.4 API 路由升级

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P5-T14 | 升级任务管理API | 3h | P5-T5 | AI |
| P5-T15 | 实现批量任务操作 | 2h | P5-T14 | AI |
| P5-T16 | 实现系统监控API | 2h | P5-T14 | AI |
| P5-T17 | API测试 | 2h | P5-T14-P5-T16 | AI |

**详细规格**:
```python
# api/routers/tasks.py 升级（多任务支持）

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from factory.task_manager import TaskManager, TaskSpecification, TaskPriority

router = APIRouter()

# 全局任务管理器实例
task_manager = TaskManager(max_concurrent_tasks=3)

@router.post("/batch", response_model=List[TaskResponse])
async def create_batch_tasks(tasks: List[TaskCreate]):
    """批量创建任务"""
    handles = []
    for task in tasks:
        spec = TaskSpecification(...)
        handle = await task_manager.submit_task(spec)
        handles.append(handle)
    return handles

@router.get("/stats")
async def get_task_statistics():
    """获取任务统计"""
    return task_manager.get_system_stats()

@router.post("/batch/pause")
async def pause_all_tasks():
    """暂停所有运行中任务"""
    running = task_manager.list_tasks(state=TaskState.RUNNING)
    for task in running:
        await task_manager.pause_task(task["task_id"])
    return {"paused": len(running)}
```

---

### 5.5 Phase 5 集成测试

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P5-T18 | 创建 Phase 5 演示脚本 | 3h | P5-T5,P5-T10 | AI |
| P5-T19 | 多任务并发集成测试 | 4h | P5-T18 | AI |
| P5-T20 | 隔离性验证测试 | 3h | P5-T19 | AI |

**详细规格**:
```python
#!/usr/bin/env python3
"""
SEMDS Phase 5 演示脚本

验证: 多任务并发进化 + 策略隔离
"""

import asyncio
from factory.task_manager import TaskManager, TaskSpecification, TaskPriority
from factory.isolation_manager import IsolationManager

async def main():
    print("=" * 60)
    print("SEMDS Phase 5 演示 - 多任务并发")
    print("=" * 60)
    
    # 1. 初始化任务管理器
    print("\n[1/5] 初始化任务管理器...")
    manager = TaskManager(max_concurrent_tasks=2, max_queued_tasks=5)
    await manager.start_scheduler()
    
    # 2. 提交多个任务
    print("\n[2/5] 提交3个并发任务...")
    tasks = [
        TaskSpecification(
            name="calculator_basic",
            description="基础计算器",
            target_function_signature="def calc(a, b, op):",
            test_code="...",
            priority=TaskPriority.HIGH
        ),
        TaskSpecification(
            name="string_reverse",
            description="字符串反转",
            target_function_signature="def reverse(s):",
            test_code="...",
            priority=TaskPriority.NORMAL
        ),
        TaskSpecification(
            name="list_sum",
            description="列表求和",
            target_function_signature="def sum_list(lst):",
            test_code="...",
            priority=TaskPriority.LOW
        )
    ]
    
    handles = []
    for spec in tasks:
        handle = await manager.submit_task(spec)
        handles.append(handle)
        print(f"  提交: {spec.name} (ID: {handle.task_id})")
    
    # 3. 验证隔离性
    print("\n[3/5] 验证任务隔离性...")
    isolation = IsolationManager()
    for i, h1 in enumerate(handles):
        for h2 in handles[i+1:]:
            is_isolated = isolation.verify_isolation(h1.task_id, h2.task_id)
            print(f"  {h1.task_id[:8]} <-> {h2.task_id[:8]}: {'✓ 已隔离' if is_isolated else '✗ 未隔离'}")
    
    # 4. 监控运行状态
    print("\n[4/5] 监控任务运行 (5秒刷新)...")
    for _ in range(6):  # 监控30秒
        await asyncio.sleep(5)
        stats = manager.get_system_stats()
        print(f"  运行中: {stats['running_tasks']}, 队列中: {stats['queued_tasks']}, 总计: {stats['total_tasks']}")
    
    # 5. 查看结果
    print("\n[5/5] 任务状态汇总...")
    for handle in handles:
        status = manager.get_task_status(handle.task_id)
        print(f"  {status['name']}: {status['state']}")
    
    # 停止调度器
    await manager.stop_scheduler()
    
    print("\n" + "=" * 60)
    print("Phase 5 演示完成!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📊 任务依赖图

```
P5-T1 (TaskManager核心)
    ├── P5-T2 (任务队列)
    │   └── P5-T3 (优先级调度)
    ├── P5-T4 (状态机)
    └── P5-T5 (测试)

P5-T6 (IsolationManager)
    ├── P5-T7 (文件系统隔离)
    ├── P5-T8 (策略状态隔离)
    ├── P5-T9 (Git分支隔离)
    └── P5-T10 (测试)

P5-T11 (策略持久化升级) ← 依赖 P5-T8
    ├── P5-T12 (加载/保存)
    └── P5-T13 (测试)

P5-T14 (API升级) ← 依赖 P5-T5
    ├── P5-T15 (批量操作)
    ├── P5-T16 (系统监控)
    └── P5-T17 (测试)

P5-T18 (演示脚本) ← 依赖 P5-T5, P5-T10
    ├── P5-T19 (集成测试)
    └── P5-T20 (隔离性验证)
```

---

## ✅ 验收标准

### 必须完成
- [ ] TaskManager 实现并通过测试
- [ ] IsolationManager 实现并通过测试
- [ ] 策略状态隔离验证通过
- [ ] 多任务并发API升级完成
- [ ] 演示脚本可运行

### 功能验收
```bash
# 1. 运行多任务演示
python demo_phase5.py

# 2. 期望输出:
# - 成功提交多个任务
# - 任务按优先级调度
# - 并发限制生效（最多2个同时运行）
# - 隔离性验证通过
# - 各任务状态正确更新

# 3. 运行隔离性测试
pytest tests/factory/test_isolation_manager.py -v

# 4. 运行集成测试
pytest tests/integration/test_multi_task.py -v
```

### 性能验收
- 同时运行3个任务，系统响应时间 < 200ms
- 任务间策略状态完全隔离，无交叉污染
- 队列满时优雅拒绝，不崩溃

---

## 📁 交付目录结构

```
semds/
├── factory/                        # Layer 2：应用工厂（新增）
│   ├── __init__.py
│   ├── task_manager.py             # 新增: P5-T1-P5-T5
│   └── isolation_manager.py        # 新增: P5-T6-P5-T10
│
├── evolution/
│   └── strategy_optimizer.py       # 升级: P5-T11-P5-T13
│
├── api/
│   └── routers/
│       └── tasks.py                # 升级: P5-T14-P5-T17
│
├── tests/
│   ├── factory/
│   │   ├── test_task_manager.py    # 新增: P5-T5
│   │   └── test_isolation_manager.py # 新增: P5-T10
│   └── integration/
│       └── test_multi_task.py      # 新增: P5-T19
│
├── demo_phase5.py                  # 新增: P5-T18
└── .isolated/                      # 运行时生成：隔离目录
```

---

## 🎯 与规格文档的对照

| 规格要求 | Phase 5 实现 |
|---------|-------------|
| `factory/task_manager.py` | ✅ P5-T1-P5-T5 |
| `factory/isolation_manager.py` | ✅ P5-T6-P5-T10 |
| 多任务并发 | ✅ P5-T1 实现 |
| 策略隔离 | ✅ P5-T8 实现 |
| 任务优先级 | ✅ P5-T3 实现 |
| 并发控制 | ✅ max_concurrent 参数 |

---

## 🔗 与前置阶段的关联

| 前置阶段 | Phase 5 依赖点 |
|---------|--------------|
| Phase 1-3 | 进化循环核心逻辑 |
| Phase 4 | FastAPI集成、WebSocket |
| 规格文档 | 目录结构、三层架构、策略隔离原则 |

---

**最后更新**: 2026-03-07  
**前置**: [Phase 4路线图](./PHASE4_ROADMAP.md)  
**状态**: 📝 待实施

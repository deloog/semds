# SEMDS 架构设计规范

**版本**: v1.0  
**架构**: 三层防崩溃架构  
**状态**: 强制执行

---

## 🏗️ 三层架构概览

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Application Factory (应用工厂层)                    │
│ - 接受编程任务输入                                           │
│ - 管理多任务并发进化                                         │
│ - 隔离不同任务的进化策略                                     │
├─────────────────────────────────────────────────────────────┤
│ Layer 1: Skills Library (技能库层)                           │
│ - 存储已验证的代码模板                                       │
│ - A/B测试不同策略的效果                                      │
│ - 策略版本管理                                               │
├─────────────────────────────────────────────────────────────┤
│ Layer 0: Core Kernel (核心内核层) 【不可修改】               │
│ - safe_write: 四层防护写入机制                               │
│ - sandbox_execute: subprocess沙盒执行                        │
│ - version_control: Git自动提交                               │
│ - 递归终止保障                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 📜 Layer 0: Core Kernel（核心内核层）

### 🚨 关键原则
**本层代码永不被系统自动修改，只能由人类手动更新。**

这是整个系统的信任锚点，类比DNA复制酶的保真机制。

### 核心组件

#### 1. safe_write - 安全写入
```python
def safe_write(filepath: str, content: str) -> Result:
    """四层防护安全写入。
    
    防护层:
    1. 备份现有文件
    2. 验证内容语法
    3. 原子写入操作
    4. 审计日志记录
    """
```

**必须保证**:
- 写入失败时原文件不受影响
- 所有写入都有审计日志
- 危险路径自动拦截

#### 2. sandbox_execute - 沙盒执行
```python
def sandbox_execute(
    code: str,
    timeout: float = 10.0,
    memory_limit: str = "128m",
    network: bool = False
) -> ExecutionResult:
    """在隔离沙盒中执行代码。
    
    隔离级别:
    - Phase 1: subprocess + seccomp
    - Phase 2: subprocess + tempfile (当前使用)
    - Phase 3: 更严格的容器 + seccomp
    """
```

**必须保证**:
- 代码无法访问宿主机文件系统
- 资源使用受限（CPU/内存/时间）
- 网络隔离（除非显式允许）

#### 3. version_control - 版本控制
```python
def commit_generation(
    task_id: str,
    generation: Generation,
    message: str
) -> CommitResult:
    """自动提交代码到Git。
    
    每个generation都有对应的Git提交，支持:
    - 完整历史回溯
    - 任意代回滚
    - 代码diff比较
    """
```

### Layer 0 更新流程
```
人类发起修改请求
    ↓
人工审查修改必要性
    ↓
在隔离环境测试修改
    ↓
人工确认并手动合并
    ↓
更新系统信任锚点版本
```

---

## 📚 Layer 1: Skills Library（技能库层）

### 职责
- 存储已验证的代码模板
- 管理进化策略库
- 策略效果追踪

### 组件设计

#### 1. Template Registry（模板注册表）
```python
class TemplateRegistry:
    """已验证代码模板注册表。"""
    
    def register(
        self,
        template_id: str,
        code: str,
        task_type: str,
        validation_results: ValidationReport
    ) -> None:
        """注册经过验证的代码模板。"""
        
    def find_similar(
        self,
        task_description: str,
        min_similarity: float = 0.8
    ) -> List[CodeTemplate]:
        """查找相似任务的模板。"""
```

#### 2. Strategy Library（策略库）
```python
class StrategyLibrary:
    """进化策略库，支持A/B测试。"""
    
    def register_strategy(
        self,
        strategy: EvolutionStrategy,
        ab_test_enabled: bool = True
    ) -> None:
        """注册新策略，可选择是否参与A/B测试。"""
        
    def select_strategy(
        self,
        task_context: TaskContext,
        method: SelectionMethod = SelectionMethod.THOMPSON_SAMPLING
    ) -> EvolutionStrategy:
        """根据上下文选择最优策略。"""
```

#### 3. Performance Tracker（性能追踪）
```python
class PerformanceTracker:
    """追踪策略和模板的实际表现。"""
    
    def record_outcome(
        self,
        strategy_id: str,
        task_type: str,
        success: bool,
        generations_needed: int,
        final_score: float
    ) -> None:
        """记录策略执行结果。"""
```

---

## 🏭 Layer 2: Application Factory（应用工厂层）

### 职责
- 任务接收和解析
- 多任务并发管理
- 结果汇总和报告

### 核心组件

#### 1. Task Orchestrator（任务编排器）
```python
class TaskOrchestrator:
    """管理多个进化任务的并发执行。"""
    
    def submit_task(
        self,
        task_spec: TaskSpecification,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> TaskHandle:
        """提交新任务。"""
        
    def get_task_status(self, task_id: str) -> TaskStatus:
        """查询任务状态。"""
        
    def pause_task(self, task_id: str) -> None:
        """暂停任务。"""
        
    def resume_task(self, task_id: str) -> None:
        """恢复任务。"""
```

#### 2. Evolution Engine（进化引擎）
```python
class EvolutionEngine:
    """单个任务的进化循环。"""
    
    def __init__(
        self,
        task: Task,
        strategy_selector: StrategySelector,
        code_generator: CodeGenerator,
        evaluator: Evaluator
    ):
        self.task = task
        self.generation = 0
        self.history: List[Generation] = []
        
    async def evolve(self) -> EvolutionResult:
        """执行进化循环直到终止条件。"""
        while not self.should_terminate():
            strategy = self.select_strategy()
            code = await self.generate(strategy)
            score = await self.evaluate(code)
            self.record_generation(code, score)
            
        return self.compile_result()
```

#### 3. Isolation Manager（隔离管理器）
```python
class IsolationManager:
    """确保不同任务的进化相互隔离。"""
    
    def create_isolated_context(self, task_id: str) -> IsolatedContext:
        """为任务创建隔离的执行环境。
        
        隔离内容包括:
        - 独立的文件系统视图
        - 独立的策略状态
        - 独立的Git分支
        """
```

---

## 🔄 层间通信规范

### 通信方向
```
Layer 2 → Layer 1: 调用策略库，获取模板
Layer 2 → Layer 0: 请求沙盒执行，安全写入
Layer 1 → Layer 0: 验证模板，提交版本
```

### 禁止的通信
```
❌ Layer 1 直接修改 Layer 0
❌ Layer 2 直接修改 Layer 1 的内部状态
❌ 跨层直接访问数据库
```

### 接口设计原则
```python
# ✅ 明确定义的接口
class SandboxInterface(Protocol):
    def execute(self, code: str, config: SandboxConfig) -> ExecutionResult: ...

class StrategyInterface(Protocol):
    def select(self, context: Context) -> Strategy: ...

# ❌ 直接访问内部
evolution_engine.sandbox._container  # 禁止
```

---

## 📊 数据流

```
用户提交任务
    ↓
[Layer 2] TaskOrchestrator 解析任务
    ↓
[Layer 2] 创建隔离上下文
    ↓
[Layer 1] StrategyLibrary 选择初始策略
    ↓
[Layer 2] EvolutionEngine 开始进化循环
    ↓
    ┌─────────────────────────────────────┐
    │ 循环内：                            │
    │ [Layer 1] 获取策略 →               │
    │ [Layer 2] 生成代码 →               │
    │ [Layer 0] 沙盒执行 →               │
    │ [Layer 2] 评估结果 →               │
    │ [Layer 0] 提交版本                 │
    └─────────────────────────────────────┘
    ↓
[Layer 2] 生成报告，返回结果
```

---

## 🛡️ 安全边界

### Layer 0 保护
```python
# 只有Layer 0可以执行文件系统操作
class CoreKernel:
    @privileged
    def safe_write(self, ...):  # 受保护的方法
        ...

# Layer 1/2 必须通过接口调用
class ApplicationLayer:
    def save_code(self, code: str):
        # ✅ 正确：通过Layer 0接口
        self.kernel.safe_write(filepath, code)
        
        # ❌ 错误：直接写入
        # with open(filepath, 'w') as f:
        #     f.write(code)
```

### 隔离保障
```python
# 每个任务有独立的：
- 文件系统命名空间
- 策略状态（Thompson Sampling参数）
- Git分支
- 数据库记录空间
```

---

## 📈 扩展性设计

### 水平扩展（Phase 5）
```
┌──────────────────────────────────────────┐
│           Load Balancer                  │
└──────────────┬───────────────────────────┘
               │
    ┌──────────┼──────────┐
    ↓          ↓          ↓
┌───────┐ ┌───────┐ ┌───────┐
│Node 1 │ │Node 2 │ │Node 3 │
└───────┘ └───────┘ └───────┘
   ↑          ↑          ↑
   └──────────┼──────────┘
              ↓
       ┌──────────┐
       │Shared DB │
       └──────────┘
```

### 插件系统
```python
class PluginInterface(Protocol):
    """扩展点接口。"""
    
    def register_hooks(self, system: System) -> None:
        """注册扩展钩子。"""
        
    def on_generation_completed(
        self,
        generation: Generation
    ) -> None:
        """每代完成后的回调。"""
```

---

## 🎯 架构决策记录 (ADR)

### ADR-001: 三层架构
**状态**: 已接受  
**背景**: 需要防止AI失控修改关键代码  
**决策**: 采用三层架构，核心层不可变  
**后果**: 增加复杂性，但提高安全性

### ADR-002: Layer 0 人工控制
**状态**: 已接受  
**背景**: AI可能生成危险的core kernel修改  
**决策**: Core Kernel只能人工修改  
**后果**: 更新较慢，但确保系统稳定

### ADR-003: 策略隔离
**状态**: 已接受  
**背景**: 不同任务的进化经验不应相互污染  
**决策**: 每个任务独立的策略状态  
**后果**: 更多内存使用，但防止策略污染

---

**违反架构规范的代码不得进入生产环境**

# SEMDS v1.1 — 自进化元开发系统
## 完整需求规格文档（可独立实施版）

**文档版本**：v1.1  
**定位**：v1.0原始愿景（AI自主代码进化）+ 吸收v2.x工程精华  
**目标**：此文档可直接交付开发团队实施，无需参考任何前序版本  
**首个实验目标**：计算器函数进化实验（从零开始，通过测试驱动进化出可靠实现）

---

## 一、系统定位与核心命题

### 1.1 系统是什么

SEMDS是一个**AI自主代码进化框架**。

它的工作方式是：给定一个编程任务和测试用例，系统由AI自动生成代码实现，在沙盒中执行并打分，根据分数调整策略，再次生成更好的实现，如此循环直到达到验收标准或触发终止条件。

人类的角色是：**监督者与目标设定者**，而不是代码编写者。

### 1.2 核心循环（一句话）

```
LLM生成代码 → 沙盒执行 → 测试评分 → 策略调整 → 再次生成
```

### 1.3 系统不是什么

- 不是决策记录系统（那是v3.1的方向，已放弃）
- 不是修改LLM权重的系统（当前技术不可行）
- 不是完全自主运行无需人工干预的系统（关键决策仍需人类批准）

---

## 二、技术栈推荐

| 层次 | 技术选择 | 理由 |
|------|----------|------|
| 主语言 | Python 3.11+ | 生态完整，AI库丰富 |
| API层 | FastAPI | 轻量，异步支持好 |
| 代码执行沙盒 | Docker容器 | 真正的隔离，不只是进程级 |
| 代码测试 | pytest + subprocess | 标准测试框架 |
| 策略优化 | Thompson Sampling（自实现） | 多臂老虎机，适合小样本收敛 |
| 进化历史存储 | SQLite（via SQLAlchemy） | 轻量，无需部署独立数据库 |
| 版本控制 | Git（subprocess调用） | 每代进化自动提交，支持回滚 |
| AI调用 | Claude API（claude-sonnet-4-20250514） | 代码生成质量高 |
| 前端（监控界面） | 单文件HTML + 内联JS | 无需框架，快速迭代 |
| 双轨评估（防Goodhart） | 独立评估模块 | 见第四章 |

---

## 三、系统架构

### 3.1 三层防崩溃架构

```
┌─────────────────────────────────────────────────────┐
│  Layer 2: Application Factory（应用工厂层）          │
│  - 接受编程任务输入                                   │
│  - 管理多任务并发进化                                 │
│  - 隔离不同任务的进化策略                             │
├─────────────────────────────────────────────────────┤
│  Layer 1: Skills Library（技能库层）                  │
│  - 存储已验证的代码模板和进化策略                     │
│  - A/B测试不同策略的效果                              │
│  - 策略版本管理                                       │
├─────────────────────────────────────────────────────┤
│  Layer 0: Core Kernel（核心内核层）【不可修改】       │
│  - safe_write：四层防护写入机制                       │
│  - sandbox_execute：Docker沙盒执行                    │
│  - version_control：Git自动提交                       │
│  - 递归终止保障                                       │
└─────────────────────────────────────────────────────┘
```

**关键设计原则**：Layer 0的代码永远不被系统自动修改，只能由人类手动更新。这是整个系统的信任锚点，类比DNA复制酶的保真机制。

### 3.2 核心数据流

```
用户提交任务
     ↓
Orchestrator解析任务规格（目标函数 + 测试用例）
     ↓
StrategySelector选择初始策略（Thompson Sampling）
     ↓
CodeGenerator调用Claude API生成代码
     ↓
SandboxExecutor在Docker容器中执行代码
     ↓
TestRunner运行测试用例，收集通过率
     ↓
DualEvaluator进行双轨评分（内生分 + 外生验证分）
     ↓
EvolutionLogger记录本代结果到SQLite + Git提交
     ↓
TerminationChecker检查是否满足终止条件
     ↓
[继续] StrategyOptimizer更新Thompson Sampling参数
     ↓
[循环] 返回CodeGenerator
     ↓
[终止] 输出最佳实现 + 进化报告
```

---

## 四、核心机制详解

### 4.1 沙盒执行（SandboxExecutor）

**为什么用Docker而不是subprocess**：LLM生成的代码可能通过合法系统调用实现恶意行为（写临时文件再执行、网络请求等），进程级隔离（seccomp）无法完全拦截语义层危险，需要容器级隔离。

```python
# 沙盒执行规格
class SandboxConfig:
    image: str = "python:3.11-slim"  # 最小化镜像
    timeout_seconds: int = 10         # 执行超时
    memory_limit: str = "128m"        # 内存限制
    network_disabled: bool = True     # 禁止网络
    read_only_filesystem: bool = True # 只读文件系统（代码注入为内存文件）
    max_output_bytes: int = 1_000_000 # 输出大小限制
```

执行流程：
1. 将生成的代码写入临时文件（在宿主机）
2. 将测试文件挂载为只读卷
3. 在容器中运行`pytest test_file.py -v --tb=short`
4. 捕获stdout/stderr
5. 解析pytest输出，提取通过/失败/错误信息
6. 销毁容器

### 4.2 双轨评估（DualEvaluator）——防Goodhart定律

**问题**：如果只用测试通过率作为进化的驱动指标，系统会学会"打测试游戏"——找到刚好能通过测试但实际上是脆弱实现的代码。这是Goodhart定律在进化系统中的具体表现。

**解决方案**：双轨评估，任何一轨单独无法驱动进化。

```
内生评估轨（测试通过率）:
  - 运行预设测试用例
  - 计算通过率 pass_rate
  - 测量执行时间 latency
  - 统计代码行数 loc（惩罚过度复杂）

外生验证轨（行为一致性）:
  - 随机生成边界用例（AI生成，不依赖预设测试）
  - 与参考实现对比输出（如果存在参考实现）
  - 代码静态分析（ast模块，检查危险模式）
  - 异常处理完整性检查

综合评分公式:
  score = 0.6 * pass_rate 
        + 0.2 * consistency_score 
        + 0.1 * (1 - latency_penalty)
        + 0.1 * (1 - complexity_penalty)

Goodhart检测触发条件:
  如果 pass_rate > 0.9 但 consistency_score < 0.5:
    标记为"疑似Goodhart现象"，通知人类审查
    不允许此代进入Skills Library
```

### 4.3 策略优化（Thompson Sampling）

SEMDS使用多臂老虎机算法为每次进化选择最优生成策略。

```python
# 策略配置空间（Strategy Configuration Space）
STRATEGY_DIMENSIONS = {
    "mutation_type": [
        "conservative",    # 保守变异：微调现有代码
        "aggressive",      # 激进变异：重写核心逻辑
        "hybrid"           # 混合：保留结构，替换算法
    ],
    "validation_mode": [
        "lightweight",     # 轻量验证：只跑核心测试
        "comprehensive"    # 全量验证：跑所有测试
    ],
    "generation_temperature": [0.2, 0.5, 0.8]  # Claude温度参数
}

# Thompson Sampling状态（每个策略组合独立维护）
class StrategyArm:
    alpha: float = 1.0  # 成功次数 + 先验
    beta: float = 1.0   # 失败次数 + 先验
    
    def sample(self) -> float:
        return numpy.random.beta(self.alpha, self.beta)
    
    def update(self, success: bool):
        if success: self.alpha += 1
        else: self.beta += 1
```

**策略隔离原则**：不同任务的Thompson Sampling状态相互独立，禁止一个任务的进化经验影响另一个任务的策略选择。这防止了"策略污染"问题。

### 4.4 进化终止条件（RTD - Recursive Termination Design）

系统必须有明确的终止条件，防止无限循环消耗资源。

```python
class TerminationConditions:
    # 成功终止
    success_threshold: float = 0.95     # 内生评分达到0.95
    consistency_threshold: float = 0.90  # 外生一致性达到0.90
    
    # 强制终止（任一触发即终止）
    max_generations: int = 50           # 最大进化代数
    max_wall_time_minutes: int = 60     # 最长运行时间
    stagnation_generations: int = 10    # 连续N代无改进则终止
    goodhart_consecutive: int = 3       # 连续N代触发Goodhart则暂停等待人工审查
    
    # 人工干预触发
    human_abort: bool = False           # 人类可随时中止
```

### 4.5 安全写入（safe_write）——四层防护

```python
def safe_write(filepath: str, content: str) -> bool:
    """
    核心内核层函数，永远不被系统自动修改。
    
    四层防护：
    1. 备份：写入前备份现有文件到.bak
    2. 验证：content通过语法检查和静态分析
    3. 原子写入：写入临时文件，验证后原子替换
    4. 审计：记录所有写入操作到不可篡改的audit.log
    """
    # Layer 1: 备份
    backup_path = filepath + f".bak.{timestamp()}"
    if os.path.exists(filepath):
        shutil.copy2(filepath, backup_path)
    
    # Layer 2: 验证
    if not validate_python_syntax(content):
        return False
    if not pass_static_analysis(content):
        return False
    
    # Layer 3: 原子写入
    tmp_path = filepath + ".tmp"
    with open(tmp_path, 'w') as f:
        f.write(content)
    os.replace(tmp_path, filepath)  # 原子操作
    
    # Layer 4: 审计
    append_audit_log(filepath, content, timestamp())
    
    return True
```

### 4.6 Git自动版本控制

每代进化自动提交，支持回滚到任意代。

```python
def commit_generation(task_id: str, gen_id: int, code: str, score: float):
    """进化前自动提交，失败可回滚"""
    git_add(f"tasks/{task_id}/gen_{gen_id}.py")
    git_commit(f"[{task_id}] gen{gen_id}: score={score:.3f}")

def rollback_to_generation(task_id: str, gen_id: int):
    """回滚到指定代"""
    git_checkout(f"tasks/{task_id}/gen_{gen_id}.py")
```

### 4.7 人类监督闸口（Human Gate）

L2级决策（影响系统结构的变更）必须经过人类确认，且系统会监测人类是否真正在认真审查。

```python
class HumanGateMonitor:
    """
    监测人类审查质量，防止"橡皮图章"退化。
    触发条件：连续批准率>98%（可能是无脑批准）
    """
    def check_approval_quality(self, recent_reviews: List[Review]) -> bool:
        approval_rate = sum(r.approved for r in recent_reviews) / len(recent_reviews)
        avg_review_time = sum(r.duration_seconds for r in recent_reviews) / len(recent_reviews)
        
        if approval_rate > 0.98 and avg_review_time < 5:
            # 几乎全批且平均5秒内完成 = 可能没有真正在看
            self.alert_human("警告：检测到可能的审查质量退化，请认真检查下一个提案")
            return False  # 要求更长的审查时间
        return True
```

---

## 五、文件结构

```
semds/
├── core/                          # Layer 0：核心内核【人类手动维护，禁止自动修改】
│   ├── kernel.py                  # safe_write, sandbox_execute, version_control
│   ├── audit.log                  # 不可篡改的操作审计日志
│   └── docker_manager.py          # Docker沙盒管理
│
├── evolution/                     # Layer 1：进化引擎
│   ├── orchestrator.py            # 总调度器，管理进化循环
│   ├── code_generator.py          # 调用Claude API生成代码
│   ├── test_runner.py             # 在沙盒中执行测试
│   ├── dual_evaluator.py          # 双轨评估（内生+外生）
│   ├── strategy_optimizer.py      # Thompson Sampling策略优化
│   └── termination_checker.py     # 终止条件检查
│
├── skills/                        # Layer 1：技能库
│   ├── templates/                 # 代码生成模板
│   │   ├── python_function.j2     # Jinja2模板
│   │   └── class_implementation.j2
│   └── strategies/                # 已验证的进化策略
│       └── strategy_registry.json
│
├── factory/                       # Layer 2：应用工厂
│   ├── task_manager.py            # 任务管理，支持并发进化
│   ├── human_gate.py              # 人类审批闸口
│   └── isolation_manager.py       # 任务间策略隔离
│
├── api/                           # API层
│   ├── main.py                    # FastAPI入口
│   ├── routers/
│   │   ├── tasks.py               # 任务CRUD
│   │   ├── evolution.py           # 进化控制（启动/暂停/中止）
│   │   └── monitor.py             # 监控数据
│   └── schemas.py                 # Pydantic数据模型
│
├── storage/                       # 数据层
│   ├── models.py                  # SQLAlchemy模型
│   ├── database.py                # SQLite连接管理
│   └── semds.db                   # SQLite数据库文件
│
├── monitor/                       # 监控前端
│   └── index.html                 # 单文件监控界面（内联CSS+JS）
│
├── experiments/                   # 实验目录
│   └── calculator/                # 首个实验：计算器进化
│       ├── task_spec.json         # 任务规格
│       └── tests/
│           └── test_calculator.py # 测试用例
│
├── docker/
│   ├── Dockerfile.sandbox         # 沙盒执行环境
│   └── docker-compose.yml        # 本地开发环境
│
├── requirements.txt
├── .env.example                   # 环境变量模板
└── README.md
```

---

## 六、数据模型

### 6.1 任务（Task）

```python
class Task(Base):
    __tablename__ = "tasks"
    
    id: str                    # UUID
    name: str                  # 任务名称（如"calculator_evolution"）
    description: str           # 自然语言描述
    target_function_signature: str  # 目标函数签名（如"def calculate(a, b, op) -> float"）
    test_file_path: str        # 测试文件路径
    status: str                # pending | running | paused | success | failed | aborted
    current_generation: int    # 当前代数
    best_score: float          # 历史最高分
    best_generation_id: str    # 最高分对应的代ID
    created_at: datetime
    updated_at: datetime
```

### 6.2 进化代（Generation）

```python
class Generation(Base):
    __tablename__ = "generations"
    
    id: str                    # UUID
    task_id: str               # 外键
    gen_number: int            # 代数编号（0, 1, 2...）
    code: str                  # 生成的代码
    strategy_used: dict        # 使用的策略配置（JSON）
    
    # 双轨评分
    intrinsic_score: float     # 内生分（测试通过率）
    extrinsic_score: float     # 外生分（一致性验证）
    final_score: float         # 综合分
    
    # 执行细节
    test_pass_rate: float      # 测试通过率
    test_results: dict         # 各测试用例结果（JSON）
    execution_time_ms: float   # 执行时间
    sandbox_logs: str          # 沙盒输出日志
    
    # 状态标记
    goodhart_flag: bool        # 是否触发Goodhart检测
    human_reviewed: bool       # 是否经过人类审查
    
    git_commit_hash: str       # Git提交哈希
    created_at: datetime
```

### 6.3 策略状态（StrategyState）

```python
class StrategyState(Base):
    __tablename__ = "strategy_states"
    
    task_id: str               # 任务级隔离
    strategy_key: str          # 策略组合的唯一键
    alpha: float               # Thompson Sampling: 成功计数
    beta: float                # Thompson Sampling: 失败计数
    total_uses: int
    last_used: datetime
```

---

## 七、API规格

### 7.1 任务管理

```
POST   /api/tasks                    创建新任务
GET    /api/tasks                    列出所有任务
GET    /api/tasks/{task_id}          获取任务详情
DELETE /api/tasks/{task_id}          删除任务

POST   /api/tasks/{task_id}/start    启动进化
POST   /api/tasks/{task_id}/pause    暂停进化
POST   /api/tasks/{task_id}/resume   恢复进化
POST   /api/tasks/{task_id}/abort    中止进化
```

### 7.2 进化监控

```
GET    /api/tasks/{task_id}/generations          获取进化历史
GET    /api/tasks/{task_id}/generations/{gen_id} 获取单代详情
GET    /api/tasks/{task_id}/best                 获取最佳实现
POST   /api/tasks/{task_id}/rollback/{gen_id}    回滚到指定代
```

### 7.3 人类审批

```
GET    /api/approvals/pending                    待审批列表
POST   /api/approvals/{approval_id}/approve      批准
POST   /api/approvals/{approval_id}/reject       拒绝（附原因）
```

### 7.4 实时监控（WebSocket）

```
WS     /ws/tasks/{task_id}           实时推送进化进度
```

---

## 八、首个实验规格：计算器进化实验

### 8.1 任务规格（task_spec.json）

```json
{
  "name": "calculator_evolution",
  "description": "进化出一个可靠的四则运算计算器函数",
  "target_function_signature": "def calculate(a: float, b: float, op: str) -> float",
  "requirements": [
    "支持操作符: +, -, *, /",
    "除零时抛出ValueError",
    "操作符无效时抛出ValueError",
    "支持负数和浮点数"
  ],
  "success_criteria": {
    "intrinsic_score_threshold": 0.95,
    "extrinsic_score_threshold": 0.90,
    "max_generations": 20
  }
}
```

### 8.2 测试用例（test_calculator.py）

```python
import pytest
from solution import calculate

class TestBasicOperations:
    def test_addition(self): assert calculate(2, 3, '+') == 5
    def test_subtraction(self): assert calculate(5, 3, '-') == 2
    def test_multiplication(self): assert calculate(4, 3, '*') == 12
    def test_division(self): assert calculate(10, 2, '/') == 5.0

class TestEdgeCases:
    def test_division_by_zero(self):
        with pytest.raises(ValueError): calculate(1, 0, '/')
    
    def test_invalid_operator(self):
        with pytest.raises(ValueError): calculate(1, 2, '%')
    
    def test_negative_numbers(self): assert calculate(-3, -2, '*') == 6
    def test_float_numbers(self): assert abs(calculate(0.1, 0.2, '+') - 0.3) < 1e-9
    def test_large_numbers(self): assert calculate(1e10, 1e10, '+') == 2e10
    def test_zero_operand(self): assert calculate(0, 5, '+') == 5

class TestReturnType:
    def test_returns_numeric(self):
        result = calculate(4, 2, '/')
        assert isinstance(result, (int, float))
```

### 8.3 期望进化路径

```
Gen 0: LLM冷启动，生成基础实现 → 预期得分0.5-0.7
Gen 1-3: 修复明显错误（除零处理，类型返回）→ 预期得分0.75-0.85
Gen 4-8: 边界用例改进（浮点精度，负数）→ 预期得分0.88-0.95
Gen 9+: 微调优化或Goodhart检测触发 → 评估是否进入Skills Library
```

---

## 九、Claude API调用规格

### 9.1 代码生成Prompt模板

```python
GENERATION_PROMPT = """
你是一个Python专家，任务是实现以下函数规格。

## 任务描述
{task_description}

## 目标函数签名
```python
{function_signature}
```

## 需求列表
{requirements}

## 前代实现（如有）
```python
{previous_code}
```

## 前代得分
- 内生分（测试通过率）: {intrinsic_score}
- 失败的测试用例: {failed_tests}
- 外生分（一致性验证）: {extrinsic_score}

## 本代进化策略
- 变异类型: {mutation_type}
- 重点改进方向: {improvement_focus}

## 要求
1. 只输出函数实现代码，不要包含测试代码
2. 不要使用任何外部库
3. 代码必须完整可执行
4. 不要添加任何解释文字

```python
"""

EXTRACTION_PATTERN = r"```python\n(.*?)\n```"
```

### 9.2 外生验证用例生成Prompt

```python
EDGE_CASE_GENERATION_PROMPT = """
给定以下函数规格，生成10个边界测试用例（JSON格式）。
这些用例不能与现有测试重复，重点关注：
- 极端值（最大/最小/零）
- 类型边界
- 可能触发bug的特殊组合

函数: {function_signature}
需求: {requirements}
现有测试覆盖的场景: {existing_test_scenarios}

只输出JSON数组，格式：
[{"input": {...}, "expected_output": ..., "description": "..."}, ...]
"""
```

---

## 十、监控界面规格

### 10.1 主界面布局

```
┌─────────────────────────────────────────────────────────┐
│  SEMDS Monitor                              [刷新] [设置] │
├─────────────────────────────────────────────────────────┤
│  任务列表（左栏）   │  进化详情（右栏）                    │
│  ─────────────     │  ──────────────────────────────     │
│  [任务名称]         │  当前代数: 12/50                    │
│  状态: 运行中       │  当前得分: 0.87                     │
│  最佳分: 0.91       │  最佳得分: 0.91 (Gen 9)            │
│                    │                                     │
│  [计算器进化] ✓     │  [得分趋势折线图]                   │
│  [任务二] ...       │                                     │
│                    │  最新代码:                          │
│  [+ 新建任务]       │  ┌─────────────────────────────┐   │
│                    │  │ def calculate(a, b, op):    │   │
│                    │  │     ...                     │   │
│                    │  └─────────────────────────────┘   │
│                    │                                     │
│                    │  测试结果: 19/20 通过               │
│                    │  Goodhart警告: 无                   │
│                    │  [暂停] [中止] [查看详情]            │
└─────────────────────────────────────────────────────────┘
```

### 10.2 待实现的核心UI组件

1. 任务列表（含状态图标）
2. 进化进度条（当前代/最大代）
3. 得分趋势折线图（内生分 + 外生分双线）
4. 最新生成代码展示（语法高亮）
5. 测试结果列表（哪些通过/哪些失败）
6. Goodhart警告提示
7. 人工审批弹窗

---

## 十一、验收标准

### 11.1 系统级验收

| 验收项 | 标准 | 验证方法 |
|--------|------|----------|
| 核心循环可运行 | 计算器实验跑通一次完整循环 | 手动触发，查看日志 |
| 沙盒隔离有效 | 生成代码无法访问宿主文件系统 | 植入测试文件访问代码，确认被拦截 |
| Git版本控制 | 每代均有Git提交，可成功回滚 | 检查Git日志，执行回滚 |
| 双轨评估运行 | 内生分和外生分均有值 | 查看Generation记录 |
| Thompson Sampling更新 | 策略选择随历史数据变化 | 运行10代后查看StrategyState |
| Goodhart检测 | 植入刻意"打游戏"的代码被检测 | 手动提交高pass_rate但低一致性代码 |
| API响应时间 | 非执行接口<200ms | 压测 |
| WebSocket实时推送 | 监控界面实时更新 | 运行时观察UI |

### 11.2 计算器实验验收

| 验收项 | 标准 |
|--------|------|
| 能跑完至少10代 | 不崩溃，有完整记录 |
| 最终得分 | 综合分≥0.90 |
| 人类可读报告 | 导出包含每代得分和策略的报告 |

---

## 十二、分阶段实施建议

### Phase 1（第一周）：核心骨架
1. 搭建目录结构
2. 实现 `core/kernel.py`（safe_write + audit_log，暂不含Docker）
3. 实现 `evolution/code_generator.py`（Claude API调用）
4. 实现最简单的测试执行（subprocess，不用Docker）
5. 验证：能跑通一次生成→测试→打分循环

### Phase 2（第二周）：Docker沙盒
1. 配置Docker沙盒环境
2. 替换Phase 1的subprocess执行
3. 实现 `safe_write` 的Docker版本
4. 验证：确认代码无法访问宿主文件系统

### Phase 3（第三周）：进化循环
1. 实现 `evolution/strategy_optimizer.py`（Thompson Sampling）
2. 实现 `evolution/dual_evaluator.py`（双轨评估 + Goodhart检测）
3. 实现 `evolution/termination_checker.py`
4. 实现Git自动版本控制
5. 跑通计算器实验的完整进化循环

### Phase 4（第四周）：API + 监控界面
1. 实现FastAPI路由
2. 实现WebSocket实时推送
3. 实现监控界面HTML
4. 实现人类审批流程

### Phase 5（可选）：多任务并发
1. 实现 `factory/task_manager.py`
2. 实现 `factory/isolation_manager.py`（策略隔离）
3. 测试多任务并发不互相干扰

---

## 十三、给Kimi多Agent开发团队的起始Prompt

将以下内容作为第一轮提交给Kimi：

---

```
你是一个Python高级工程师，我需要你基于以下规格文档，分阶段实现SEMDS（自进化元开发系统）v1.1。

请按以下顺序实施Phase 1（第一周任务）：

## 目标
实现能跑通一次完整"生成→测试→评分"循环的最小系统。

## 要求完成的文件
1. semds/core/kernel.py
   - safe_write函数（四层防护，暂时用文件系统实现，不含Docker）
   - append_audit_log函数
   
2. semds/evolution/code_generator.py
   - CodeGenerator类，调用Claude API（claude-sonnet-4-20250514）
   - 使用我在规格中提供的GENERATION_PROMPT模板
   - 需要一个extract_code方法从Claude回复中提取代码块
   
3. semds/evolution/test_runner.py
   - TestRunner类，用subprocess执行pytest
   - 解析pytest输出，返回pass_rate和failed_tests列表
   - 暂时不用Docker（Phase 2再加）

4. semds/storage/models.py + database.py
   - Task和Generation的SQLAlchemy模型
   - SQLite连接管理

5. semds/experiments/calculator/tests/test_calculator.py
   - 使用我在规格中提供的测试用例

6. 一个能运行的演示脚本 demo_phase1.py
   - 创建一个计算器任务
   - 调用Claude API生成代码
   - 运行测试
   - 打印结果
   不需要进化循环，只是单次验证流程

## 技术约束
- Python 3.11+
- 所有API密钥从环境变量读取（ANTHROPIC_API_KEY）
- 不使用框架（Phase 4再加FastAPI）
- 代码需有docstring

## 参考文档
[粘贴本完整规格文档]

请先确认你理解了需求，然后一次性生成所有文件。
```

---

## 十四、风险与注意事项

1. **Docker依赖**：本地开发需要安装Docker Desktop，务必在Phase 1就确认开发环境有Docker，而不是等到Phase 2才发现问题。

2. **Claude API成本**：每代进化调用2-3次Claude API（代码生成+外生验证用例生成），计算器实验20代约需40-60次API调用，注意成本控制。

3. **Thompson Sampling的样本量**：在前5代内数据量不足，Thompson Sampling可能表现不如随机选择，这是正常的，不要在早期就调整算法。

4. **多AI协作的目标守护**：如果你将来继续用Kimi、DeepSeek、Claude协作迭代这个系统，确保在每轮协作开始时明确声明"我们正在实现v1.1规格第X节的Y功能"，防止再次发生范式漂移。

5. **最小完整性原则**：任何新增功能在加入系统前，先问"这是在解决核心进化循环的问题，还是在给系统加装饰？"前者加，后者留到后续版本。

---

*文档结束。此文档为SEMDS v1.1的完整独立实施规格，无需参考任何前序版本文档。*

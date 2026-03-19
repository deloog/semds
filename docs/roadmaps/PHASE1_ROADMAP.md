# SEMDS Phase 1 原子化开发路线图

**文档版本**: v1.0  
**对应规格**: SEMDS_v1.1_SPEC.md Phase 1  
**目标**: 实现能跑通一次完整"生成→测试→评分"循环的最小系统

---

## 📋 Phase 1 任务总览

**时间**: 1周  
**交付物**: 可运行的最小骨架系统  
**验收标准**: 能完成单次"生成→测试→评分"循环

---

## 🎯 任务分解（WBS）

### 1.1 项目骨架搭建

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P1-T1 | 创建目录结构 | 1h | - | AI |
| P1-T2 | 创建requirements.txt | 0.5h | - | AI |
| P1-T3 | 创建.env.example | 0.5h | - | AI |
| P1-T4 | 初始化Git仓库 | 0.5h | - | AI |

**验收标准**:
```bash
# 目录结构符合规格
tree semds/  # 显示 core/, evolution/, storage/, experiments/ 等

# 依赖文件完整
pip install -r requirements.txt  # 成功
```

---

### 1.2 Core Kernel 层（Layer 0）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P1-T5 | 实现 safe_write() 函数 | 4h | P1-T1 | AI |
| P1-T6 | 实现 append_audit_log() | 2h | P1-T5 | AI |
| P1-T7 | 实现内核层单元测试 | 3h | P1-T5,P1-T6 | AI |

**详细规格**:
```python
# semds/core/kernel.py

def safe_write(filepath: str, content: str) -> bool:
    """
    四层防护写入机制（Phase 1简化版）
    
    防护层:
    1. 备份: 写入前备份到 .bak.{timestamp}
    2. 验证: 检查Python语法 (ast.parse)
    3. 原子写入: 写入.tmp后原子替换
    4. 审计: 记录到 audit.log
    
    Returns:
        bool: 写入成功返回True
    """
    pass

def append_audit_log(filepath: str, content: str, timestamp: float):
    """记录写入操作到审计日志"""
    pass
```

**TDD要求**:
- 先写 `tests/core/test_kernel.py`
- 测试用例必须覆盖:
  - 正常写入
  - 备份文件生成
  - 语法错误拒绝写入
  - 审计日志记录

**验收标准**:
```python
# 测试100%通过
pytest tests/core/test_kernel.py -v

# 功能验证
from core.kernel import safe_write
safe_write("/tmp/test.py", "def foo(): pass")  # 返回True
# 检查: /tmp/test.py 存在
# 检查: /tmp/test.py.bak.{timestamp} 存在
# 检查: audit.log 有记录
```

---

### 1.3 代码生成器（Code Generator）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P1-T8 | 实现 Claude API 调用封装 | 3h | P1-T1 | AI |
| P1-T9 | 实现 Prompt 模板系统 | 2h | P1-T8 | AI |
| P1-T10 | 实现代码提取逻辑 | 2h | P1-T9 | AI |
| P1-T11 | 代码生成器单元测试 | 3h | P1-T8-P1-T10 | AI |

**详细规格**:
```python
# semds/evolution/code_generator.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class GenerationContext:
    """代码生成上下文"""
    task_description: str
    function_signature: str
    requirements: list[str]
    previous_code: Optional[str] = None
    intrinsic_score: Optional[float] = None
    failed_tests: Optional[list] = None
    strategy: Optional[dict] = None

class CodeGenerator:
    """
    调用Claude API生成代码
    
    Phase 1简化: 只实现基础生成功能，不含策略优化
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "claude-sonnet-4-20250514"
    
    def generate(self, context: GenerationContext) -> str:
        """
        生成代码实现
        
        Args:
            context: 生成上下文
            
        Returns:
            生成的Python代码字符串
        """
        pass
    
    def _build_prompt(self, context: GenerationContext) -> str:
        """构建Prompt"""
        pass
    
    def _extract_code(self, response: str) -> str:
        """
        从Claude响应中提取代码块
        
        使用正则: r"```python\n(.*?)\n```"
        """
        pass
```

**Prompt模板** (来自规格文档):
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

## 本代进化策略
- 变异类型: {mutation_type}

## 要求
1. 只输出函数实现代码，不要包含测试代码
2. 不要使用任何外部库
3. 代码必须完整可执行
4. 不要添加任何解释文字

```python
"""
```

**TDD要求**:
- Mock Claude API响应
- 测试代码提取逻辑
- 测试Prompt构建

---

### 1.4 测试运行器（Test Runner）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P1-T12 | 实现 subprocess 执行 pytest | 3h | P1-T1 | AI |
| P1-T13 | 实现 pytest 输出解析 | 3h | P1-T12 | AI |
| P1-T14 | 测试运行器单元测试 | 3h | P1-T12,P1-T13 | AI |

**详细规格**:
```python
# semds/evolution/test_runner.py

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class TestResult:
    """单个测试结果"""
    test_name: str
    passed: bool
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None

@dataclass
class TestRunReport:
    """测试运行报告"""
    pass_rate: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    results: List[TestResult]
    stdout: str
    stderr: str

class TestRunner:
    """
    在本地环境执行测试（Phase 1简化版，不含Docker）
    
    Phase 2将替换为Docker沙盒执行
    """
    
    def run_tests(
        self,
        solution_path: str,
        test_file_path: str,
        timeout_seconds: int = 10
    ) -> TestRunReport:
        """
        执行测试
        
        Args:
            solution_path: 被测代码文件路径
            test_file_path: 测试文件路径
            timeout_seconds: 执行超时时间
            
        Returns:
            TestRunReport: 测试报告
        """
        pass
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> TestRunReport:
        """解析pytest输出"""
        pass
```

**TDD要求**:
- 创建 mock_test_file.py 和 mock_solution.py
- 测试通过/失败场景
- 测试超时处理
- 测试异常捕获

---

### 1.5 数据层（Storage）

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P1-T15 | 定义 SQLAlchemy 模型 | 3h | P1-T1 | AI |
| P1-T16 | 实现 SQLite 连接管理 | 2h | P1-T15 | AI |
| P1-T17 | 实现数据库初始化 | 2h | P1-T16 | AI |

**详细规格**:
```python
# semds/storage/models.py

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Task(Base):
    """任务模型"""
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True)  # UUID
    name = Column(String, nullable=False)
    description = Column(String)
    target_function_signature = Column(String)
    test_file_path = Column(String)
    status = Column(String, default="pending")  # pending|running|paused|success|failed|aborted
    current_generation = Column(Integer, default=0)
    best_score = Column(Float, default=0.0)
    best_generation_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Generation(Base):
    """进化代模型"""
    __tablename__ = "generations"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False)
    gen_number = Column(Integer, nullable=False)
    code = Column(String)
    strategy_used = Column(JSON)
    intrinsic_score = Column(Float)
    extrinsic_score = Column(Float, default=0.0)  # Phase 1为0
    final_score = Column(Float)
    test_pass_rate = Column(Float)
    test_results = Column(JSON)
    execution_time_ms = Column(Float)
    sandbox_logs = Column(String)
    goodhart_flag = Column(Boolean, default=False)  # Phase 1为False
    git_commit_hash = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class StrategyState(Base):
    """策略状态模型 (Thompson Sampling状态)"""
    __tablename__ = "strategy_states"
    
    id = Column(String, primary_key=True)
    task_id = Column(String, nullable=False, index=True)  # 任务级隔离
    strategy_key = Column(String, nullable=False)  # 策略组合唯一键
    alpha = Column(Float, default=1.0)  # 成功计数
    beta = Column(Float, default=1.0)   # 失败计数
    total_uses = Column(Integer, default=0)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 唯一约束：每个任务的每种策略只有一条记录
    __table_args__ = (
        UniqueConstraint('task_id', 'strategy_key', name='uix_task_strategy'),
    )
```

---

### 1.6 计算器实验测试用例

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P1-T18 | 创建计算器测试文件 | 1h | P1-T1 | AI |

**详细规格** (直接来自规格文档):
```python
# semds/experiments/calculator/tests/test_calculator.py

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

---

### 1.7 Phase 1 演示脚本

| 任务ID | 任务 | 估算 | 依赖 | 负责人 |
|-------|------|------|------|--------|
| P1-T19 | 创建 demo_phase1.py | 4h | P1-T5-P1-T18 | AI |

**详细规格**:
```python
#!/usr/bin/env python3
"""
SEMDS Phase 1 演示脚本

验证: 单次"生成→测试→评分"循环
"""

import os
import uuid
from datetime import datetime

# 导入各模块
from core.kernel import safe_write
from evolution.code_generator import CodeGenerator, GenerationContext
from evolution.test_runner import TestRunner
from storage.models import Task, Generation
from storage.database import init_db, get_session

def main():
    print("=" * 60)
    print("SEMDS Phase 1 演示")
    print("=" * 60)
    
    # 1. 初始化数据库
    print("\n[1/5] 初始化数据库...")
    init_db()
    
    # 2. 创建任务
    print("\n[2/5] 创建计算器进化任务...")
    task_id = str(uuid.uuid4())
    task = Task(
        id=task_id,
        name="calculator_evolution",
        description="进化出一个可靠的四则运算计算器函数",
        target_function_signature="def calculate(a: float, b: float, op: str) -> float",
        test_file_path="experiments/calculator/tests/test_calculator.py"
    )
    
    # 3. 生成代码
    print("\n[3/5] 调用Claude API生成代码...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("错误: 未设置 ANTHROPIC_API_KEY 环境变量")
        return
    
    generator = CodeGenerator(api_key)
    context = GenerationContext(
        task_description="实现一个四则运算计算器",
        function_signature="def calculate(a: float, b: float, op: str) -> float",
        requirements=[
            "支持操作符: +, -, *, /",
            "除零时抛出ValueError",
            "操作符无效时抛出ValueError",
            "支持负数和浮点数"
        ],
        mutation_type="initial"
    )
    
    generated_code = generator.generate(context)
    print(f"生成代码:\n{generated_code}\n")
    
    # 4. 保存代码
    solution_path = f"experiments/calculator/solutions/gen_0.py"
    safe_write(solution_path, generated_code)
    print(f"[4/5] 代码已保存到 {solution_path}")
    
    # 5. 运行测试
    print("\n[5/5] 运行测试...")
    runner = TestRunner()
    report = runner.run_tests(
        solution_path=solution_path,
        test_file_path=task.test_file_path
    )
    
    # 6. 输出结果
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    print(f"通过率: {report.pass_rate * 100:.1f}%")
    print(f"总测试数: {report.total_tests}")
    print(f"通过: {report.passed_tests}")
    print(f"失败: {report.failed_tests}")
    print(f"\n失败的测试:")
    for result in report.results:
        if not result.passed:
            print(f"  - {result.test_name}: {result.error_message}")
    
    print("\n" + "=" * 60)
    print("Phase 1 演示完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
```

---

## 📊 任务依赖图

```
P1-T1 (目录结构)
    ├── P1-T5 (safe_write)
    │       └── P1-T6 (audit_log)
    │           └── P1-T7 (内核测试)
    │
    ├── P1-T8 (Claude API)
    │       └── P1-T9 (Prompt模板)
    │           └── P1-T10 (代码提取)
    │               └── P1-T11 (生成器测试)
    │
    ├── P1-T12 (pytest执行)
    │       └── P1-T13 (输出解析)
    │           └── P1-T14 (测试器测试)
    │
    ├── P1-T15 (SQL模型)
    │       └── P1-T16 (连接管理)
    │           └── P1-T17 (数据库初始化)
    │
    ├── P1-T18 (计算器测试)
    │
    └── P1-T19 (演示脚本)
            ↑ 依赖所有上游任务
```

---

## ✅ 验收标准

### 必须完成
- [ ] 目录结构符合规格
- [ ] `core/kernel.py` 实现并通过测试
- [ ] `evolution/code_generator.py` 实现并通过测试
- [ ] `evolution/test_runner.py` 实现并通过测试
- [ ] `storage/models.py` 定义完成
- [ ] 计算器测试文件完整
- [ ] `demo_phase1.py` 可运行

### 功能验收
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量
export ANTHROPIC_API_KEY="your-api-key"

# 3. 运行演示
python demo_phase1.py

# 4. 期望输出
# - 成功调用Claude API
# - 生成代码保存到 experiments/calculator/solutions/gen_0.py
# - 运行测试并输出通过率
# - 无异常崩溃
```

### 测试验收
```bash
# 所有单元测试通过
pytest tests/ -v --tb=short

# 覆盖率（Phase 1建议≥80%）
pytest tests/ --cov=core,evolution,storage --cov-report=term-missing
```

---

## 📁 交付目录结构

```
semds/
├── core/
│   ├── __init__.py
│   ├── kernel.py           ← P1-T5,P1-T6
│   └── audit.log           ← P1-T6
│
├── evolution/
│   ├── __init__.py
│   ├── code_generator.py   ← P1-T8-P1-T10
│   └── test_runner.py      ← P1-T12,P1-T13
│
├── storage/
│   ├── __init__.py
│   ├── models.py           ← P1-T15
│   └── database.py         ← P1-T16,P1-T17
│
├── experiments/
│   └── calculator/
│       ├── solutions/      ← 运行时生成
│       └── tests/
│           └── test_calculator.py  ← P1-T18
│
├── tests/
│   ├── __init__.py
│   ├── core/
│   │   └── test_kernel.py  ← P1-T7
│   └── evolution/
│       ├── test_code_generator.py  ← P1-T11
│       └── test_test_runner.py     ← P1-T14
│
├── demo_phase1.py          ← P1-T19
├── requirements.txt        ← P1-T2
├── .env.example            ← P1-T3
└── README.md
```

---

## 🎯 关键约束

### TDD强制
- 每个功能模块必须有对应的测试文件
- 测试必须先写，后实现功能
- 测试覆盖率≥80%（Phase 1标准）

### 质量门禁
- 所有测试100%通过
- 代码通过flake8静态检查
- 关键函数有docstring

### AI行为规范
- 诚实报告进度
- 不创建V2版本文件
- 测试失败时修改代码，不修改测试

---

## 📝 进度报告模板

```markdown
## Phase 1 进度报告

**日期**: YYYY-MM-DD  
**总体进度**: X%

### 已完成
- [x] 任务ID - 任务名称

### 进行中
- [ ] 任务ID - 任务名称 (X%)

### 待完成
- [ ] 任务ID - 任务名称

### 阻塞/风险
- [描述]

### 质量指标
- 测试通过率: X%
- 代码覆盖率: X%
```

---

**最后更新**: 2026-03-07  
**维护者**: AI开发团队 + 人类监督员

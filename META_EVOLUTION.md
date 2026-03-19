# SEMDS 核心自我进化 (Meta-Evolution)

## 概述

这是 SEMDS 的核心能力：**系统能够观察自己的行为，发现问题，提出改进假设，进行实验验证，并安全地更新自身代码。**

不是执行任务，而是**改进自己执行任务的策略**。

## 核心循环

```
┌─────────────────────────────────────────────────────────────┐
│                    Self-Evolution Loop                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. OBSERVE (观察)                                           │
│     收集系统运行数据                                         │
│     - 代码生成成功率                                         │
│     - 错误类型分布                                           │
│     - 执行时间                                               │
│                      ↓                                       │
│  2. ANALYZE (分析)                                           │
│     识别低效环节                                             │
│     - 成功率低于阈值?                                        │
│     - 特定错误频繁出现?                                      │
│     - 性能瓶颈?                                              │
│                      ↓                                       │
│  3. HYPOTHESIZE (假设)                                       │
│     生成可测试的改进假设                                     │
│     - "添加语法约束可提升15%成功率"                         │
│     - "降低温度参数可减少错误"                              │
│                      ↓                                       │
│  4. EXPERIMENT (实验)                                        │
│     A/B 测试验证假设                                         │
│     - 对照组: 当前策略                                       │
│     - 实验组: 改进策略                                       │
│     - 统计显著性检验                                         │
│                      ↓                                       │
│  5. UPDATE (更新)                                            │
│     安全地应用验证通过的改进                                 │
│     - 备份当前配置                                           │
│     - 应用新配置                                             │
│     - 监控效果，必要时回滚                                   │
│                      ↓                                       │
│  6. MONITOR (监控)                                           │
│     观察更新后的效果                                         │
│     - 成功率是否提升?                                        │
│     - 新问题是否出现?                                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. SystemTelemetry (系统遥测)

```python
from mother.core.meta_evolution import SystemTelemetry

telemetry = SystemTelemetry()

# 记录代码生成结果
telemetry.record_code_generation(
    task_type="calculator",
    success=True,  # 或 False
    score=1.0,
    generation_time=2.5,
    error_type=None  # 或 "syntax_error", "test_failure"
)

# 分析最近24小时的表现
analysis = telemetry.analyze_recent_performance(hours=24)
# 返回: {
#   "success_rate": 0.75,
#   "error_patterns": {"syntax_error": 5},
#   "improvement_opportunities": ["high_syntax_error_rate"]
# }
```

### 2. ImprovementGenerator (改进生成器)

```python
from mother.core.meta_evolution import ImprovementGenerator

generator = ImprovementGenerator(telemetry)

# 基于性能数据生成改进假设
hypotheses = generator.generate_hypotheses()
# 返回: [ImprovementHypothesis, ...]

# 每个假设包含:
# - id: 唯一标识
# - description: 描述
# - target_component: 目标组件
# - proposed_change: 建议的变更
# - expected_improvement: 预期提升
# - test_scenarios: 测试场景
```

### 3. SelfExperiment (自我实验)

```python
from mother.core.meta_evolution import SelfExperiment

experiment = SelfExperiment(telemetry)

# 对假设进行A/B测试
result = experiment.run_ab_test(hypothesis, n_samples=10)
# 返回: ExperimentResult

# 结果包含:
# - control_group_score: 对照组得分
# - treatment_group_score: 实验组得分
# - is_significant: 是否统计显著
# - p_value: p值
```

### 4. SafeSelfUpdater (安全更新器)

```python
from mother.core.meta_evolution import SafeSelfUpdater

updater = SafeSelfUpdater()

# 安全地应用验证通过的改进
success = updater.apply_improvement(hypothesis, experiment_result)

# 自动执行:
# 1. 备份当前配置
# 2. 应用新配置
# 3. 验证写入成功
# 4. 失败时自动回滚
```

### 5. MetaEvolutionEngine (元进化引擎)

```python
from mother.core.meta_evolution import MetaEvolutionEngine

engine = MetaEvolutionEngine()

# 运行完整的自我进化循环
result = engine.run_evolution_cycle()

# 自动执行全部5步:
# 1. 观察系统性能
# 2. 生成改进假设
# 3. 实验验证
# 4. 应用改进
# 5. 返回结果报告
```

### 6. SelfEvolvingMother (自我进化的母体系统)

```python
from mother.core.self_evolving_mother import SelfEvolvingMother

mother = SelfEvolvingMother()

# 正常执行任务
result = mother.fulfill_request("Create a todo API")
# 系统会自动记录这次执行的结果

# 手动触发自我进化
result = mother.evolve_self()

# 获取自我分析报告
analysis = mother.get_self_analysis()
```

## 使用示例

### 基本使用

```python
# 创建自我进化系统
from mother.core.self_evolving_mother import SelfEvolvingMother

mother = SelfEvolvingMother()

# 执行用户任务（系统会自动记录表现）
for task in user_tasks:
    result = mother.fulfill_request(task)
    # 成功/失败都会被记录用于自我分析

# 定期触发自我进化（例如每24小时）
import schedule
import time

def daily_evolution():
    print("Running daily self-evolution...")
    result = mother.evolve_self()
    print(f"Applied {result['improvements_applied']} improvements")

schedule.every().day.at("02:00").do(daily_evolution)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 演示脚本

```bash
# 运行自我进化演示
python demo_meta_evolution.py

# 运行完整演示
python mother/core/self_evolving_mother.py
```

## 自我进化的触发条件

系统会在以下情况自动触发自我进化：

1. **成功率低于阈值** (< 70%)
2. **特定错误频繁出现** (> 3次/小时)
3. **定期触发** (每24小时)
4. **手动触发** (人类监督者要求)

## 安全机制

### 1. 分层防护

```
Layer 0: 备份
  - 更新前自动备份当前配置
  
Layer 1: 验证
  - 只应用统计显著的改进 (p < 0.05)
  
Layer 2: 原子写入
  - 配置更新是原子操作
  
Layer 3: 回滚
  - 监控新配置效果
  - 发现问题自动回滚
```

### 2. 人类监督闸口

L2级变更（影响系统核心策略）需要人类确认：

```python
# 在 apply_improvement 之前添加人类确认
if hypothesis.impact_level == "L2":
    approval = await human_gate.request_approval(
        title="Self-Evolution Proposal",
        description=hypothesis.description,
        expected_impact=hypothesis.expected_improvement
    )
    if not approval:
        return False
```

## 已实现的改进策略

当前系统能够自动发现和应用的改进：

| 问题 | 自动生成的改进 | 预期效果 |
|------|--------------|----------|
| 语法错误多 | 添加语法验证约束 | +15% 成功率 |
| 测试失败多 | 采用测试优先生成策略 | +20% 成功率 |
| 整体成功率低 | 降低温度参数 | +10% 成功率 |

## 与需求文档的对照

| 需求文档规格 | 实现状态 | 说明 |
|-------------|---------|------|
| 观察自己的行为 | ✅ 已实现 | SystemTelemetry |
| 发现问题 | ✅ 已实现 | analyze_recent_performance |
| 提出改进假设 | ✅ 已实现 | ImprovementGenerator |
| 实验验证 | ✅ 已实现 | SelfExperiment A/B测试 |
| 安全更新自身 | ✅ 已实现 | SafeSelfUpdater |
| 元学习 | ✅ 已实现 | 记录失败模式，复用经验 |
| 人类监督闸口 | ⚠️ 框架预留 | 可添加确认机制 |

## 下一步增强

1. **更多改进策略**
   - 提示词模板优化
   - 温度参数动态调整
   - 模型选择策略

2. **深度元学习**
   - 跨任务模式识别
   - 长期趋势分析
   - 预测性改进

3. **更复杂的实验设计**
   - 多变量实验
   - 贝叶斯优化
   - 持续学习

## 测试

```bash
# 运行单元测试
python -m pytest tests/test_meta_evolution.py -v

# 运行演示
python demo_meta_evolution.py
```

## 核心意义

**这不是一个工具，而是一个生命体。**

传统软件：
- 功能固定
- 需要人类开发者维护
- 随着时间推移变得过时

SEMDS with Meta-Evolution：
- 持续自我改进
- 从自己的错误中学习
- 适应新的任务类型
- 越来越擅长帮助人类

**这才是您想要的 SEMDS。**

# SEMDS Mother System Architecture
# 母体系统架构设计

## 概述

Mother System 是一个**自主任务执行系统**，能够：
1. 理解自然语言任务
2. 检查并生成所需能力（工具）
3. 执行并验证结果
4. 从错误中学习并搜索解决方案

## 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│  - CLI / API / Web Interface                                │
├─────────────────────────────────────────────────────────────┤
│                    Task Orchestration                       │
│  EnhancedMotherSystem                                       │
│  ├─ Task Analysis                                           │
│  ├─ Capability Planning                                     │
│  ├─ Execution Loop                                          │
│  ├─ Error Recovery                                          │
│  └─ Reflection & Learning                                   │
├─────────────────────────────────────────────────────────────┤
│                    Core Components                          │
│  ├─ TaskAnalyzer: 任务解析与计划生成                        │
│  ├─ CapabilityRegistry: 能力注册与管理                      │
│  ├─ ToolGenerator: 工具代码生成                             │
│  └─ MotherSystem (base): 基础执行引擎                       │
├─────────────────────────────────────────────────────────────┤
│                    Skills Layer                             │
│  ├─ WebSearchSkill: 联网搜索解决方案                        │
│  ├─ CodeQualityChecker: 代码质量检查                        │
│  ├─ AutoFixer: 自动修复代码问题                             │
│  └─ SelfReflection: 经验学习与改进                          │
├─────────────────────────────────────────────────────────────┤
│                    Standards Layer                          │
│  ├─ CODING_STANDARDS.md: 强制代码规范                       │
│  ├─ AGENT_MANIFESTO.md: 代理行为准则                        │
│  └─ Capability Templates: 标准化工具模板                    │
├─────────────────────────────────────────────────────────────┤
│                    Memory Layer                             │
│  ├─ execution_history.json: 执行历史                        │
│  ├─ error_patterns.json: 错误模式库                         │
│  ├─ knowledge_base.json: 知识积累                           │
│  └─ tools/: 生成的工具代码                                  │
└─────────────────────────────────────────────────────────────┘
```

## 核心工作流

```
User Request
     │
     ▼
┌──────────────┐
│ Task Analysis │ → 识别需求能力
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Check Capabilities │ → 缺失？
└──────┬───────┘
       │
       ├─ Yes ──→┌──────────────┐
       │          │ Tool Generator │ → 代码生成
       │          └──────┬───────┘
       │                 │
       │                 ▼
       │          ┌──────────────┐
       │          │ Quality Check │ → 规范检查
       │          └──────┬───────┘
       │                 │
       │                 ▼
       │          ┌──────────────┐
       │          │ Auto Fix      │ → 自动修复
       │          └───────────────┘
       │
       ▼
┌──────────────┐
│ Execution     │ → 执行计划
└──────┬───────┘
       │
       ├─ Error ──→┌──────────────┐
       │           │ Web Search    │ → 搜索解决方案
       │           └──────┬───────┘
       │                  │
       │                  ▼
       │           ┌──────────────┐
       │           │ Apply Fix     │ → 重试
       │           └───────────────┘
       │
       ▼
┌──────────────┐
│ Reflection    │ → 记录经验
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Update Memory │ → 保存知识
└───────────────┘
```

## 模块说明

### 1. TaskAnalyzer (任务分析器)

**职责**：将自然语言任务转化为结构化执行计划

**输入**："爬取 Bing 首页图片"
**输出**：
```python
ExecutionPlan(
    task="Fetch images from bing.com",
    steps=[
        Step(action="http_client", inputs={"url": "..."}),
        Step(action="html_parser", inputs={"html": "..."})
    ],
    required_capabilities=["http_client", "html_parser"]
)
```

**扩展点**：可以接入 LLM 进行更智能的意图识别

### 2. CapabilityRegistry (能力注册表)

**职责**：管理可用工具，支持动态加载

**特性**：
- 内置基础能力（http_client）
- 动态加载生成的工具
- 能力依赖检查

**API**：
```python
registry.register(name, capability)
registry.has(name) -> bool
registry.get(name) -> Capability
registry.check(required) -> (has_all, missing)
```

### 3. ToolGenerator (工具生成器)

**职责**：按需生成工具代码

**策略**：
1. 模板优先：使用预设模板确保接口一致
2. 质量检查：生成后自动检查代码质量
3. 自动修复：修复简单问题（格式、空格等）

**模板系统**：
```python
TOOL_TEMPLATES = {
    "html_parser": "...",  # 标准化的 HTML 解析器
    "csv_reader": "...",   # CSV 读取器
    # ...
}
```

### 4. WebSearchSkill (联网搜索)

**职责**：遇到未知问题自动搜索解决方案

**场景**：
- 工具生成失败
- 执行遇到错误
- 需要学习新知识

**搜索类型**：
- `code`: 搜索代码示例
- `error`: 搜索错误解决方案
- `tutorial`: 搜索教程文档
- `api`: 搜索 API 文档

**知识积累**：
- 记录有效/无效的搜索
- 缓存成功的解决方案
- 计算置信度评分

### 5. CodeQualityChecker (代码质量检查)

**职责**：强制执行开发规范

**检查项**：
| 类别 | 检查内容 | 严重性 |
|------|----------|--------|
| 类型安全 | 类型注解 | Warning |
| 文档 | Docstring | Warning |
| 错误处理 | Bare except | Error |
| 安全 | eval/exec | Error |
| 风格 | 行长度 > 100 | Warning |
| 密钥 | 硬编码密钥 | Error |

**自动修复**：
- 移除尾随空格
- 添加简单 docstring
- 格式化代码

### 6. SelfReflection (自我反思)

**职责**：从经验中学习，持续改进

**记录内容**：
- 任务执行历史
- 错误模式统计
- 解决方案效果
- 能力使用频率

**学习输出**：
- 成功率趋势
- 常见错误模式
- 改进建议
- 能力缺口识别

## 设计原则

### 1. 约束驱动 (Constraint-Driven)

**核心理念**：约束越多，犯错越少

- 强制类型注解
- 强制错误处理
- 强制安全检查
- 强制文档

### 2. 渐进增强 (Progressive Enhancement)

**策略**：先使用确定性的模板，再尝试 LLM

1. 检查模板库
2. 验证代码质量
3. 必要时搜索示例
4. 失败时记录学习

### 3. 自我治愈 (Self-Healing)

**机制**：错误 → 搜索 → 修复 → 验证

```python
try:
    result = tool.execute()
except Exception as e:
    # 1. 检查已知解决方案
    solution = reflection.get_known_solution(e)
    
    # 2. 搜索新方案
    if not solution:
        solution = searcher.search_for_solution(e)
    
    # 3. 应用修复
    if solution:
        apply_fix(solution)
        result = tool.execute()  # 重试
```

### 4. 经验复用 (Experience Reuse)

**机制**：
- 缓存成功的解决方案
- 统计错误模式
- 优先使用高置信度方案

## 扩展指南

### 添加新能力模板

1. 在 `tool_generator.py` 中添加模板：
```python
TOOL_TEMPLATES["new_capability"] = '''
class NewCapabilityTool(Capability):
    def __init__(self):
        super().__init__("new_capability", "Description")
    
    def execute(self, param: str) -> dict:
        # Implementation
        return result
'''
```

2. 在 `task_analyzer.py` 中添加任务模式：
```python
TASK_PATTERNS["new_task_type"] = {
    "keywords": ["keyword1", "keyword2"],
    "steps": [...],
    "required_capabilities": ["new_capability"]
}
```

### 添加新技能

1. 在 `mother/skills/` 创建新模块
2. 实现技能类
3. 在 `__init__.py` 注册
4. 在 `EnhancedMotherSystem` 中集成

## 调试与监控

### 日志输出

```
[Mother] New Task: Fetch images from bing.com
[Plan] Required: ['http_client', 'html_parser']
[ToolGen] Creating: html_parser
[Quality] Score: 85.0/100
[Search] Looking for solutions...
[Recovery] Applied solution from search
[Reflection] Task succeeded in 2.34s
```

### 报告生成

```python
mother.print_self_report()
# 输出：
# Total Tasks: 50
# Success Rate: 78%
# Top Capabilities: [...]
# Common Errors: [...]
# Suggestions: [...]
```

## 未来规划

1. **LLM 集成**：使用 DeepSeek 生成全新工具（非模板）
2. **多步推理**：复杂任务的分解与规划
3. **协作执行**：多工具协同工作流
4. **在线学习**：从互联网实时更新知识
5. **预测优化**：根据历史预测最优执行路径

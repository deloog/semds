# SEMDS Mother System - Complete Architecture
# 完整架构设计

## 系统总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         User Input                                         │
└───────────────────────────┬─────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Intent Engine (Local Model - Qwen 3.5 4B)                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌───────────────────┐   │
│  │ Intent Classifier   │  │ Context Manager     │  │ Model Router      │   │
│  │  • Classify intent  │  │  • Resolve refs     │  │  • Route to model │   │
│  │  • Assess complexity│  │  • Manage history   │  │  • Balance cost   │   │
│  │  • Extract entities │  │  • Summarize context│  │  • Track usage    │   │
│  └─────────────────────┘  └─────────────────────┘  └───────────────────┘   │
└───────────────────────────┬─────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
┌──────────────────┐ ┌──────────────┐ ┌──────────────────────┐
│ Local Model      │ │ Template     │ │ DeepSeek API         │
│ (Ollama/Qwen)    │ │ Router       │ │ (Strong Model)       │
│                  │ │              │ │                      │
│ • Simple chat    │ │ • Fill       │ │ • Complex code gen   │
│ • Intent confirm │ │   templates  │ │ • Deep explanation   │
│ • Entity extract │ │ • 100% safe  │ │ • Algorithm design   │
│ • Context sum    │ │ • Zero cost  │ │ • High quality       │
│                  │ │              │ │ • Paid               │
└──────────────────┘ └──────────────┘ └──────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Output                                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 核心原则

### 1. 分层架构

| 层级 | 职责 | 组件 |
|------|------|------|
| **Interface** | 用户交互 | CLI, API, Web |
| **Intent** | 理解用户意图 | Intent Classifier, Context Manager |
| **Routing** | 决定处理路径 | Model Router |
| **Execution** | 执行任务 | Local Model, Templates, DeepSeek |
| **Memory** | 存储状态 | Context DB, Examples DB |

### 2. 模型分工

| 模型 | 职责 | 能力要求 |
|------|------|----------|
| **Local 4B** | 意图识别、上下文管理 | 文本分类、信息抽取 |
| **Templates** | 代码生成（确定） | 填充变量、零生成 |
| **DeepSeek** | 复杂生成、深度推理 | 高质量代码、算法设计 |

### 3. 成本控制

```
简单任务 (70%)  →  Local/Template  →  $0
中等任务 (20%)  →  Hybrid          →  $0.02
复杂任务 (10%)  →  DeepSeek        →  $0.05

Average cost per task: $0.01 (vs $0.05 pure DeepSeek)
Savings: 80%
```

---

## 模块详解

### 1. Intent Engine (`mother/intent_engine/`)

**职责**：理解用户，决定后续处理

**子模块**：
- `intent_classifier.py` - 意图识别、复杂度评估
- `context_manager.py` - 上下文管理、指代消解
- `model_router.py` - 模型路由、执行调度

**关键类**：
```python
UserIntent:
  - intent_type: code_generation/debug_help/explanation/...
  - complexity: simple/medium/complex
  - suggested_model: local/template/hybrid/deepseek
  - entities: {url, code_block, function_name}
  - context_needed: bool
```

---

### 2. LLM Tutor (`mother/llm_tutor/`)

**职责**：积累知识，提升生成质量

**子模块**：
- `template_router.py` - 模板填充（推荐方案✅）
- `code_tutor.py` - 教学方案（暂停⏸️）
- `few_shot_optimizer.py` - Few-shot 优化
- `iterative_trainer.py` - 迭代训练（暂停⏸️）

**推荐方案**：
> 使用 Template Router，放弃训练本地模型

理由：
- 4B 模型不适合复杂代码生成
- 模板填充质量更高（90+ 分）
- 无需训练，立即可用

---

### 3. Core System (`mother/core/`)

**职责**：任务执行、工具管理

**子模块**：
- `mother_system.py` - 基础执行引擎
- `enhanced_mother.py` - 增强版（集成所有功能）
- `task_analyzer.py` - 任务分析
- `capability_registry.py` - 能力注册
- `tool_generator.py` - 工具生成
- `enhanced_tool_generator.py` - 增强版（带质量检查）

---

### 4. Skills (`mother/skills/`)

**职责**：特定能力封装

**子模块**：
- `web_search.py` - 联网搜索
- `code_quality.py` - 代码质量检查
- `code_optimizer.py` - 代码优化
- `self_reflection.py` - 自我反思

---

## 数据流

### 完整处理流程

```
1. User Input
   "Write a function to fetch weather data"

2. Intent Classification
   Intent: code_generation
   Complexity: simple
   Entities: {topic: "weather data"}
   Suggested: template

3. Context Resolution
   Check history: User previously asked for Python
   Resolve refs: N/A
   Extract knowledge: preferred_language=Python

4. Model Routing
   Decision: template (simple code generation)

5. Execution
   Template Router:
   - Select: http_get template
   - Extract: func_name="fetch_weather"
   - Fill: Generate code

6. Quality Check
   Score: 95/100
   Issues: None

7. Output
   Return generated code to user

8. Memory Update
   Add to conversation history
   Record successful template usage
```

---

## 使用场景

### 场景 1：简单代码生成

```
User: "Write a function to parse CSV"
↓
Intent: code_generation, simple
Model: template
Cost: $0
Output: 90+ 分代码
```

### 场景 2：复杂算法优化

```
User: "Optimize this sorting for 1M elements"
↓
Intent: code_review, complex
Model: deepseek
Cost: $0.05
Context: Previous code + requirements
Output: High-quality optimized code
```

### 场景 3：多轮对话

```
User: "Write Python code to download images"
Assistant: [Code generated]
User: "Make it async"
↓
Intent: code_generation, simple
Context: Previous code + "async" requirement
Model: hybrid (local summarize + deepseek generate)
Output: Updated async code
```

### 场景 4：调试帮助

```
User: "I'm getting KeyError 'user'"
↓
Intent: debug_help, simple
Model: hybrid
  - Local: Extract error info
  - DeepSeek: Analyze root cause
Cost: $0.02
Output: Explanation + fix suggestion
```

---

## 运行命令

```bash
# 1. 测试意图识别
python mother/intent_engine/intent_classifier.py

# 2. 测试上下文管理
python mother/intent_engine/context_manager.py

# 3. 测试模型路由
python mother/intent_engine/model_router.py

# 4. 完整演示
python mother/demo_intent_engine.py

# 5. 测试模板路由
python mother/llm_tutor/template_router.py

# 6. 代码质量检查
python mother/skills/code_optimizer.py

# 7. Mother System 演示
python mother/demo.py
python mother/demo_enhanced.py
```

---

## 未来路线图

### Phase 1: 当前 (已完成✅)
- ✅ Intent Engine (规则 + 预留本地模型接口)
- ✅ Template Router (模板填充)
- ✅ Context Manager (对话历史、指代消解)
- ✅ Code Quality Checker (自动检查)

### Phase 2: 近期 (下周)
- 🔄 接入 Ollama 本地模型
- 🔄 扩展模板库 (10-20 个常用模板)
- 🔄 优化 Intent Classifier (用本地模型确认)

### Phase 3: 中期 (下月)
- 📋 上下文压缩优化 (用本地模型摘要)
- 📋 Few-shot 示例积累
- 📋 个性化路由 (学习用户习惯)

### Phase 4: 远期
- 📋 多模型 ensemble
- 📋 强化学习优化路由策略
- 📋 自动模板生成 (DeepSeek 生成新模板)

---

## 总结

### 核心设计

> **"让合适的模型做合适的事"**

| 任务 | 模型 | 原因 |
|------|------|------|
| 意图识别 | Local 4B | 文本分类任务 |
| 上下文管理 | Local 4B | 信息整理任务 |
| 简单代码 | Template | 确定性、零成本 |
| 复杂代码 | DeepSeek | 高质量、推理能力 |

### 优势

1. **成本效益**：80% 任务用本地/模板处理（免费）
2. **质量保证**：复杂任务用 DeepSeek（高质量）
3. **用户体验**：简单任务快速响应（本地）
4. **可扩展性**：模块化设计，易于添加新模板

### 关键文件

```
mother/
├── intent_engine/          # 意图识别与上下文
│   ├── intent_classifier.py
│   ├── context_manager.py
│   └── model_router.py
├── llm_tutor/              # 知识积累
│   └── template_router.py  # 推荐方案
├── skills/                 # 能力模块
│   └── code_optimizer.py
├── core/                   # 核心系统
│   └── enhanced_mother.py
└── ARCHITECTURE_COMPLETE.md  # 本文档
```

---

**这就是 SEMDS Mother System 的完整架构设计。**

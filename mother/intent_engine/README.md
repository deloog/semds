# SEMDS Intent Engine
# 意图识别与上下文管理系统

## 核心理念

**本地模型（Qwen 3.5 4B）作为"智能路由器"和"上下文管理器"**

不是让本地模型生成代码（它不擅长），而是让它：
1. **理解用户意图**（分类任务 - 擅长）
2. **管理对话上下文**（信息整理 - 擅长）
3. **决定用哪个模型处理**（决策任务 - 擅长）

---

## 架构

```
User Input
    │
    ▼
┌───────────────────────────────────────────────────────────────────┐
│ Intent Classifier (Local Model / Rules)                          │
│  • 识别意图类型（code_gen, debug, explain...）                    │
│  • 评估复杂度（simple/medium/complex）                            │
│  • 提取实体（URL, code blocks）                                   │
│  • 估计置信度                                                     │
└──────────────────────┬────────────────────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────────────────────┐
│ Context Manager (Local Model)                                    │
│  • 指代消解（this/it/that → 具体内容）                           │
│  • 维护对话历史                                                   │
│  • 提取和累积知识                                                 │
│  • 为外部模型生成上下文摘要                                       │
└──────────────────────┬────────────────────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────────────────────┐
│ Model Router                                                      │
│  simple_chat  ────────► Local Model                              │
│  simple_code  ────────► Template                                 │
│  medium_task  ────────► Hybrid (local + deepseek)                │
│  complex_task ────────► DeepSeek                                 │
└──────────────────────┬────────────────────────────────────────────┘
                       │
                       ▼
┌───────────────────────────────────────────────────────────────────┐
│                        Response                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 组件说明

### 1. Intent Classifier（意图识别器）

**文件**：`intent_classifier.py`

**功能**：
- 识别 8 种意图类型：`code_generation`, `code_review`, `debug_help`, `explanation`, `web_search`, `simple_chat`, `task_orchestration`, `unknown`
- 评估 3 级复杂度：`simple`, `medium`, `complex`
- 提取实体：URL, code blocks, function names
- 建议模型：`local`, `template`, `hybrid`, `deepseek`

**实现方式**：
- 规则匹配（快速、确定）
- 本地模型确认（复杂情况）

**使用示例**：
```python
from mother.intent_engine.intent_classifier import classify_intent

intent = classify_intent("Write a function to fetch data")
print(intent.intent_type)      # code_generation
print(intent.complexity)       # simple
print(intent.suggested_model)  # template
```

---

### 2. Context Manager（上下文管理器）

**文件**：`context_manager.py`

**功能**：
- **指代消解**：将 "it", "this", "that" 替换为具体指代
- **知识提取**：从对话中提取用户偏好（如喜欢的语言、常用配置）
- **上下文摘要**：为外部模型生成精简的上下文（减少 token 消耗）

**为什么用本地模型**：
- 这些是"信息整理"任务，4B 模型可以胜任
- 减少外部模型调用的 token 消耗（省钱）
- 本地访问速度快（用户体验好）

**使用示例**：
```python
from mother.intent_engine.context_manager import ContextManager

cm = ContextManager()
session_id = "user_123"

# 添加消息
cm.add_message(session_id, "user", "I want Python code")
cm.add_message(session_id, "assistant", "Here's the code...", "deepseek")

# 指代消解
resolved = cm.resolve_references(session_id, "Make it async")
# 输出: "Make 'the Python code' async"

# 获取上下文摘要
context = cm.summarize_for_external_model(session_id, "Add error handling")
```

---

### 3. Model Router（模型路由器）

**文件**：`model_router.py`

**路由策略**：

| 意图 | 简单 | 中等 | 复杂 |
|------|------|------|------|
| simple_chat | Local | Local | - |
| explanation | Local | Hybrid | DeepSeek |
| code_generation | Template | Hybrid | DeepSeek |
| code_review | Local | Hybrid | DeepSeek |
| debug_help | Hybrid | Hybrid | DeepSeek |
| task_orchestration | Hybrid | - | DeepSeek |

**完整流程**：
```python
from mother.intent_engine.model_router import process_user_input

result = process_user_input(
    text="Write a function to fetch JSON",
    session_id="user_123"
)

print(result['intent'])        # code_generation
print(result['model_used'])    # template
print(result['cost'])          # $0 (free)
```

---

## 优势

### 1. 成本优化

| 方案 | 每次调用成本 | 质量 |
|------|-------------|------|
| 纯 DeepSeek | $0.05 | 高 |
| 纯本地模型 | $0 | 低 |
| **Intent Engine** | **$0-0.05** | **按需调整** |

**智能路由示例**：
- "Hello" → Local (免费)
- "Write function" → Template (免费)
- "Optimize algorithm" → DeepSeek ($0.05)

### 2. 能力最大化

**本地模型做擅长的**：
- ✅ 文本分类（意图识别）
- ✅ 信息抽取（实体提取）
- ✅ 文本摘要（上下文管理）
- ✅ 简单决策（模型路由）

**外部模型做擅长的**：
- ✅ 复杂代码生成
- ✅ 深度问题解答
- ✅ 算法优化

### 3. 用户体验

- **快速响应**：简单任务本地处理（毫秒级）
- **上下文感知**：多轮对话保持连贯
- **成本透明**：用户知道用了什么模型

---

## 运行演示

```bash
python mother/demo_intent_engine.py
```

**输出示例**：
```
Input: "Write a function to fetch data from API"
  Intent: code_generation
  Complexity: simple
  Confidence: 90%
  Suggested Model: template
  Needs Context: True

Input: "First download data, then parse, finally save to DB"
  Intent: task_orchestration
  Complexity: complex
  Confidence: 70%
  Suggested Model: deepseek
```

---

## 集成到 Mother System

修改 `enhanced_mother.py`：

```python
from mother.intent_engine.model_router import process_user_input

class EnhancedMotherSystem:
    def execute(self, task_description: str, session_id: str = "default"):
        # 使用 Intent Engine 处理用户输入
        result = process_user_input(task_description, session_id)
        
        # 根据路由结果执行
        if result['model_used'] == 'template':
            return self.template_router.generate(task_description)
        elif result['model_used'] == 'deepseek':
            return self.deepseek.generate(task_description, result['context'])
        # ...
```

---

## 未来扩展

1. **Local Model Integration**: 接入 Ollama 进行真正的本地意图识别
2. **Learning**: 根据用户反馈调整路由策略
3. **Multi-turn Optimization**: 优化多轮对话的上下文压缩
4. **Personalization**: 学习用户习惯，个性化路由

---

## 总结

> **"最好的架构是让每个组件做它最擅长的事。"**

本地模型（4B）的定位：
- ❌ 不写复杂代码
- ✅ 做智能路由决策
- ✅ 管理上下文状态

这是**务实且高效**的架构设计。

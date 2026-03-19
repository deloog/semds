# SEMDS LLM Tutor
# SEMDS 提升本地模型编程能力方案

## 概述

让 SEMDS 作为"编程教练"，帮助本地模型（Qwen 3.5）提升代码生成质量。通过三层增强系统，在不重新训练模型的情况下显著提升输出质量。

## 核心洞察

> **不需要重新训练模型，只需优化输入（Prompt）和提供反馈。**

传统方法：重新训练本地模型（需要 GPU 集群、数小时/天、大量数据）
我们的方法：**Prompt Engineering 自动化**（即时生效、零成本）

---

## 三层架构

### Layer 1: Code Tutor（编程教练）

**职责**：对比本地模型输出与黄金标准，生成改进建议

**流程**：
```
本地模型生成代码 → SEMDS 评估质量 → 如果分数低
    ↓
DeepSeek 生成改进版本 → 记录对比示例 → 提取经验教训
```

**关键代码**：
```python
from mother.llm_tutor.code_tutor import CodeTutor

tutor = CodeTutor()
session = tutor.teach(
    task="Write HTTP client",
    student_code=local_model_output,
    max_iterations=3
)
# 返回改进后的代码和质量评分
```

---

### Layer 2: Few-shot Optimizer（示例优化器）

**职责**：积累 "好代码 vs 坏代码" 对比库，生成优化后的 Prompt

**原理**：
- 本地模型是 few-shot learner（看例子就能学）
- 给模型看 "坏代码→好代码" 的对比
- 模型自动学会写出更好的代码

**示例库结构**：
```python
{
  "task": "Fetch data from URL",
  "bad": "def fetch(url): return requests.get(url).text",
  "good": "def fetch(url: str) -> str:...",  # 带类型检查、错误处理
  "improvements": ["Type hints", "Input validation", "Timeout"]
}
```

**生成优化提示**：
```python
from mother.llm_tutor.few_shot_optimizer import get_enhanced_prompt

prompt = get_enhanced_prompt(
    task_type="http_client",
    task="Download image from URL"
)
# 返回包含 SYSTEM 指令 + 示例 + 新任务的完整提示
```

---

### Layer 3: Iterative Trainer（迭代训练器）

**职责**：闭环训练，持续改进

**流程**：
```
1. 本地模型生成代码
2. SEMDS 评估（CodeOptimizer 检查质量）
3. 如果分数 < 目标：
   - 生成具体反馈
   - 本地模型根据反馈重新生成
   - 记录改进示例
4. 循环直到达标或达到最大迭代次数
```

**关键代码**：
```python
from mother.llm_tutor.iterative_trainer import train_local_model

session = train_local_model(
    task="Parse CSV file",
    task_type="parser",
    max_iterations=5,
    target_score=80  # 目标质量分数
)
# 返回训练会话记录，包括每次迭代的改进
```

---

## 完整工作流

```
                    User Task
                        │
                        ▼
    ┌───────────────────────────────────────┐
    │ Layer 2: Few-shot Optimizer           │
    │ - 加载相关示例（http_client/parser）  │
    │ - 生成增强 Prompt                     │
    └──────────────┬────────────────────────┘
                   │
                   ▼
    ┌───────────────────────────────────────┐
    │ Local Model (Qwen 3.5)                │
    │ - 接收增强 Prompt                     │
    │ - 生成代码（质量提升）                │
    └──────────────┬────────────────────────┘
                   │
                   ▼
    ┌───────────────────────────────────────┐
    │ Layer 1: Code Tutor                   │
    │ - SEMDS 评估代码质量                  │
    │ - 如果质量不够：                      │
    │   * DeepSeek 生成黄金标准             │
    │   * 生成改进建议                      │
    └──────────────┬────────────────────────┘
                   │
                   ▼
    ┌───────────────────────────────────────┐
    │ Layer 3: Iterative Trainer            │
    │ - 记录到示例库                        │
    │ - 更新 Few-shot 库                    │
    │ - 下次生成质量更高                    │
    └───────────────────────────────────────┘
```

---

## 数据积累

每次训练会话都会积累数据：

```
mother/llm_tutor/
├── examples.json              # 学习示例（好 vs 坏）
├── few_shot_examples/         # Few-shot 库
│   ├── http_client.json
│   ├── parser.json
│   └── file_reader.json
├── training_sessions.json     # 训练会话记录
└── README.md                  # 本文档
```

**飞轮效应**：
1. 训练越多 → 示例库越丰富
2. 示例越丰富 → Few-shot Prompt 质量越高
3. Prompt 质量越高 → 本地模型输出越好
4. 循环...

---

## 实际使用

### 方法 1：直接训练本地模型

```python
from mother.llm_tutor.iterative_trainer import train_local_model

# 训练本地模型完成特定任务
session = train_local_model(
    task="Write CSV parser with validation",
    task_type="parser"
)

print(f"Improvement: {session.improvement:+.1f} points")
print(f"Final score: {session.final_score}/100")
```

### 方法 2：生成优化提示

```python
from mother.llm_tutor.few_shot_optimizer import get_enhanced_prompt

# 获取增强提示
prompt = get_enhanced_prompt("http_client", "Download image from URL")

# 发送给本地模型
response = ollama.generate(model="qwen3.5:4b", prompt=prompt)
```

### 方法 3：在 Mother System 中集成

修改 `enhanced_mother.py`：

```python
from mother.llm_tutor.few_shot_optimizer import FewShotOptimizer

class EnhancedMotherSystem:
    def __init__(self):
        self.few_shot = FewShotOptimizer()
    
    def generate_tool(self, capability):
        # 使用增强提示生成本地模型代码
        prompt = self.few_shot.get_prompt_for_ollama(
            task_type=capability,
            new_task=f"Write {capability} tool"
        )
        
        # 本地模型生成
        code = local_model.generate(prompt)
        
        # SEMDS 检查
        score = self.code_checker.check(code)
        
        if score < 80:
            # 质量不够，用 DeepSeek 改进
            code = self.teacher_model.improve(code)
        
        return code
```

---

## 优势

| 方面 | 传统微调 | SEMDS Tutor |
|------|---------|-------------|
| **成本** | GPU 集群、数小时 | 零成本、即时 |
| **数据** | 需要大量标注数据 | 自动生成对比数据 |
| **效果** | 永久提升但昂贵 | 渐进提升但免费 |
| **风险** | 可能训坏模型 | 无风险，可随时调整 |
| **迭代** | 慢（训练-测试-再训练） | 快（生成-评估-改进） |

---

## 运行演示

```bash
# 查看完整演示
python mother/demo_llm_tutor.py

# 测试编程教练
python mother/llm_tutor/code_tutor.py

# 测试 Few-shot 优化
python mother/llm_tutor/few_shot_optimizer.py

# 运行实际训练（需要 Ollama 运行）
python mother/llm_tutor/iterative_trainer.py
```

---

## 未来扩展

1. **自动 Prompt 优化**：用进化算法优化 Prompt 模板
2. **多模型对比**：同时训练多个本地模型，选择最佳
3. **知识蒸馏**：将 DeepSeek 的推理能力蒸馏到本地模型
4. **强化学习**：用 RLHF 方法训练本地模型

---

> **"最好的模型不是训练出来的，是教出来的。"**

SEMDS 作为教师，本地模型作为学生，通过持续反馈和示例学习，实现能力的持续提升。

# Phase 1.5: 约束强化设计

## 目标

在 Phase 1 中我们验证了：**明确的约束比重试机制更有效**

Phase 1.5 的目标是将这一洞察系统化，建立可复用的约束注入机制。

## 核心设计

### 1. TaskSpec 标准格式

```python
@dataclass
class TaskSpec:
    name: str                          # 任务名称
    description: str                   # 任务描述
    function_signature: str            # 函数签名（约束核心）
    constraints: List[str]             # 额外约束列表
    examples: List[Example]            # 输入输出示例
    test_cases: Optional[List[Test]]   # 测试用例（可选）
```

### 2. ConstraintsInjector

将约束自动注入到 LLM 提示词中：

```python
class ConstraintsInjector:
    def inject(self, task_spec: TaskSpec, base_prompt: str) -> str:
        # 在提示词中强化约束
        constraints_text = "\n".join(f"- {c}" for c in task_spec.constraints)
        return f"""
{base_prompt}

【重要约束】
{constraints_text}

函数签名必须严格为: {task_spec.function_signature}
违反以上约束将导致代码无法运行。
"""
```

### 3. 验证场景

选择3个不同复杂度的问题验证约束效果：

1. **字符串计算器**（已完成 ✓）
   - 约束：函数名 evaluate，参数 expression
   
2. **列表排序**（待实现）
   - 约束：函数名 sort_list，参数 lst，返回 List[int]
   
3. **文件解析器**（待实现）
   - 约束：函数名 parse_file，参数 filepath，返回 Dict

## 成功指标

- 约束违规率 < 5%
- 首次生成通过率 > 90%
- 平均重试次数 < 0.5

## 下一步

实现 ConstraintsInjector 并验证3个场景。

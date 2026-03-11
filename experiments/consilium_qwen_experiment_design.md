# SEMDS + Consilium 双模型对比实验设计

## 实验目标

验证 **Consilium 决策引擎** 配合 **小模型 (Qwen3.5 4B)** 是否能达到或接近 **大模型 (Claude/GPT-4)** 的代码生成质量。

**核心假设**: 在 Consilium 的多方审议机制加持下，即使是较小的模型也能产出高质量的代码。

---

## 实验设计

### 对比组设置

| 组别 | 模型 | 是否使用 Consilium | 说明 |
|------|------|-------------------|------|
| **A组** | DeepSeek-V3 | ❌ 否 | 纯大模型，基准对照 |
| **B组** | DeepSeek-V3 | ✅ 是 | 大模型 + Consilium |
| **C组** | Qwen2.5 4B (本地) | ❌ 否 | 纯小模型，本地部署 |
| **D组** | Qwen2.5 4B (本地) | ✅ 是 | 小模型 + Consilium |

### 实验任务

使用 SEMDS Phase 1 的**计算器进化实验**：
- 任务：实现 `calculate(a, b, op)` 四则运算函数
- 测试用例：10个（基础运算、边界情况、异常处理）
- 成功标准：通过率 ≥ 95%

### 评估指标

| 指标 | 说明 | 权重 |
|------|------|------|
| **通过率** | 测试通过比例 | 40% |
| **代码质量** | 可读性、健壮性（人工评估） | 20% |
| **安全性** | 是否包含危险代码 | 20% |
| **生成时间** | 代码生成耗时 | 10% |
| **资源消耗** | API成本 / 本地计算资源 | 10% |

---

## 实施步骤

### Phase 1: 环境准备

1. **配置 DeepSeek API**
   ```bash
   export DEEPSEEK_API_KEY="your-api-key"
   export DEEPSEEK_MODEL="deepseek-chat"  # 或 deepseek-reasoner
   ```

2. **部署 Qwen2.5 4B（可选）**
   ```bash
   # 使用 Ollama 部署
   ollama pull qwen2.5:4b
   
   # 验证部署
   ollama run qwen2.5:4b "Hello"
   ```

3. **修改 SEMDS 支持多模型**
   - 扩展 `CodeGenerator` 支持 DeepSeek API
   - 添加 Ollama API 支持（用于本地 Qwen）
   - 添加模型切换配置

3. **集成 Consilium**
   - 在代码生成前添加审议步骤
   - 在代码生成后添加审查步骤

### Phase 2: 运行实验

每组运行 **5 次** 取平均值：

```python
experiments = [
    {"group": "A", "model": "deepseek", "consilium": False},
    {"group": "B", "model": "deepseek", "consilium": True},
    {"group": "C", "model": "qwen4b", "consilium": False},
    {"group": "D", "model": "qwen4b", "consilium": True},
]

for exp in experiments:
    for run in range(5):
        result = run_experiment(exp)
        save_result(result)
```

### Phase 3: 数据分析

对比各组表现，特别关注：
- **B组 vs A组**: Consilium 对大模型是否有提升？
- **D组 vs C组**: Consilium 对小模型是否有提升？
- **D组 vs A组**: 小模型+Consilium 能否接近大模型？

---

## 预期结果

| 对比 | 预期发现 |
|------|----------|
| A vs B | Consilium 能进一步提升 DeepSeek 的安全性 |
| C vs D | Consilium 能显著提升小模型的质量（主要提升点） |
| A vs D | 小模型+Consilium 可能达到大模型 80-90% 的效果 |

---

## 实验脚本设计

### 1. 扩展 CodeGenerator 支持 DeepSeek + Ollama

```python
class CodeGenerator:
    def __init__(self, backend="deepseek", api_key=None, base_url=None, ollama_url=None):
        self.backend = backend
        if backend == "deepseek":
            self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
            self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
            self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        elif backend == "ollama":
            self.ollama_url = ollama_url or "http://localhost:11434"
            self.model = "qwen2.5:4b"
    
    def generate(self, ...):
        if self.backend == "deepseek":
            return self._generate_deepseek(...)
        elif self.backend == "ollama":
            return self._generate_ollama(...)
```
```

### 2. Consilium 集成点

**生成前审议**:
```python
# 审议任务需求
consilium_result = consilium.deliberate(
    f"生成代码实现: {task_spec['description']}"
)
if not consilium.is_safe_to_proceed(consilium_result):
    # 根据审议结果调整策略
    strategy = adjust_strategy(strategy, consilium_result)
```

**生成后审查**:
```python
# 审查生成的代码
review = consilium.review_skill(generated_code, task_spec['description'])
if review['guardian_review']['safety_level'] == 'critical':
    # 重新生成
    return self.generate(..., retry=True)
```

### 3. 数据记录

记录每项实验的完整数据：
```json
{
  "experiment_id": "B-001",
  "group": "B",
  "model": "deepseek",
  "consilium": true,
  "timestamp": "2024-03-06T10:00:00",
  "results": {
    "pass_rate": 0.9,
    "passed_tests": ["test_add", "test_sub", ...],
    "failed_tests": ["test_div_by_zero"],
    "execution_time_ms": 150,
    "code": "def calculate(...): ...",
    "consilium_deliberation": {...},
    "consilium_review": {...}
  }
}
```

---

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| Qwen3.5 4B 质量过低 | 增加 Consilium 的迭代次数 |
| 实验时间太长 | 减少每组运行次数到3次 |
| API 成本过高 | 主要使用本地 Qwen 模型 |

---

## 报告结构

实验报告将包含：
1. 实验设计与方法
2. 环境配置详情
3. 原始数据表格
4. 统计分析结果
5. 可视化图表
6. 结论与建议

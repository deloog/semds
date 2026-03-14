# SEMDS 用户使用指南

**版本**: Phase 3  
**适用对象**: 研究人员、开发者  
**最后更新**: 2026-03-12

---

## 目录

1. [快速开始](#快速开始)
2. [配置说明](#配置说明)
3. [运行实验](#运行实验)
4. [自定义任务](#自定义任务)
5. [结果解读](#结果解读)
6. [故障排除](#故障排除)

---

## 快速开始

### 1. 环境要求

- **Python**: 3.10+
- **操作系统**: Windows / Linux / macOS
- **Git**: 用于版本控制

### 2. 安装步骤

```bash
# 1. 克隆仓库
git clone <repository-url>
cd semds

# 2. 创建虚拟环境
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 验证安装
make test
```

### 3. 配置 API Keys

创建 `.env` 文件：

```bash
# 必需：选择一个 LLM API
DEEPSEEK_API_KEY=your-deepseek-key
# 或
ANTHROPIC_API_KEY=your-anthropic-key
# 或
OPENAI_API_KEY=your-openai-key

# 可选：默认后端
LLM_BACKEND=deepseek  # 可选: deepseek, anthropic, openai
```

**获取 API Keys**:
- Deepseek: https://platform.deepseek.com/
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/

---

## 配置说明

### 核心配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `max_generations` | 最大进化代数 | 50 |
| `success_threshold` | 成功阈值（0-1） | 0.9 |
| `stagnation_generations` | 停滞检测代数 | 5 |
| `temperature` | LLM 温度参数 | 0.5-0.8 |

### 配置示例

```python
from evolution.termination_checker import TerminationConfig

config = TerminationConfig(
    max_generations=20,
    success_threshold=0.85,
    stagnation_generations=4
)
```

---

## 运行实验

### 1. 快速实验（推荐新手）

```bash
# 使用 Deepseek API 运行计算器实验
python experiments/phase3_calculator_demo_real.py
```

**预期输出**:
```
======================================================================
SEMDS Phase 3 - 计算器进化实验 (Deepseek API)
======================================================================
...
最佳得分: 0.9800
是否成功: True
终止原因: Success: 98% >= 90%
```

### 2. Mock 实验（无需 API）

```bash
# 验证系统完整性（无需 API Key）
python experiments/phase3_mock_stress_test.py
```

### 3. 古德哈特检测验证

```bash
# 验证过拟合检测功能
python experiments/phase3_goodhart_validation_final.py
```

---

## 自定义任务

### 创建新任务

创建文件 `experiments/my_custom_task.py`:

```python
"""自定义任务示例"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evolution.orchestrator import EvolutionOrchestrator
from evolution.code_generator import CodeGenerator
from evolution.termination_checker import TerminationConfig

def run_my_task():
    # 1. 配置代码生成器
    code_generator = CodeGenerator(
        api_key="your-api-key",  # 或从环境变量读取
        model="deepseek-chat",
        backend="deepseek",
    )
    
    # 2. 配置终止条件
    config = TerminationConfig(
        success_threshold=0.90,
        max_generations=15,
        stagnation_generations=4
    )
    
    # 3. 创建编排器
    orchestrator = EvolutionOrchestrator(
        task_id="my_custom_task",
        code_generator=code_generator,
        termination_config=config,
    )
    
    # 4. 定义任务
    requirements = [
        "实现一个函数 factorial(n) 计算阶乘",
        "处理 n=0 返回 1",
        "n<0 时抛出 ValueError",
    ]
    
    test_code = """
assert factorial(0) == 1
assert factorial(1) == 1
assert factorial(5) == 120
assert factorial(10) == 3628800
"""
    
    # 5. 运行进化
    result = orchestrator.evolve(
        requirements=requirements,
        test_code=test_code,
        max_generations=15,
    )
    
    # 6. 输出结果
    print(f"总代数: {result.generations}")
    print(f"最佳得分: {result.best_score:.4f}")
    print(f"成功: {result.success}")
    print(f"最佳代码:\n{result.best_code}")
    
    return result

if __name__ == "__main__":
    run_my_task()
```

### 运行自定义任务

```bash
python experiments/my_custom_task.py
```

---

## 结果解读

### 标准输出字段

| 字段 | 说明 | 解读 |
|------|------|------|
| `generations` | 实际运行代数 | 受限于 max_generations 或提前终止 |
| `best_score` | 最佳代码得分 | 0-1 之间，>= success_threshold 为成功 |
| `success` | 是否成功 | 是否达到 success_threshold |
| `termination_reason` | 终止原因 | 成功/代数限制/停滞检测 |

### 终止原因类型

| 原因 | 说明 | 建议 |
|------|------|------|
| `Success` | 达到成功阈值 | 正常结束 ✅ |
| `Max generations reached` | 达到最大代数 | 可能需要提高 max_generations |
| `Stagnation` | 多代无改进 | 可能需要调整策略或任务难度 |

### 得分构成

```
Final Score = (Intrinsic × 0.4 + Extrinsic × 0.4) × (1 - Goodhart Penalty)

Intrinsic (内生):  代码质量（语法、结构、文档）
Extrinsic (外生):  行为一致性（安全性、边界情况）
Goodhart Penalty:  过拟合惩罚（0-0.2）
```

---

## 故障排除

### 常见问题

#### 1. API Key 错误

```
ValueError: Deepseek API key is required
```

**解决**:
- 检查 `.env` 文件是否存在
- 确认 API Key 正确
- 确认环境变量已加载: `python -c "import os; print(os.getenv('DEEPSEEK_API_KEY'))"`

#### 2. 测试运行失败

```
Test execution error: ...
```

**解决**:
- 确认 pytest 已安装: `pip install pytest`
- 检查测试代码语法
- 查看详细日志: 在 `TestRunner` 中设置 `verbose=True`

#### 3. 所有代码得分都很低

**可能原因**:
- 任务描述不清晰
- 测试代码与要求不匹配
- LLM 温度参数过高导致不稳定

**解决**:
```python
# 降低温度，提高稳定性
CodeGenerator(
    api_key="...",
    default_temperature=0.3,  # 降低温度
)
```

#### 4. 生成代码为空或格式错误

**解决**:
- 检查代码提取逻辑
- 确认 LLM 返回格式包含 ```python 代码块
- 查看 `raw_response` 调试

### 调试技巧

```python
# 启用详细日志
orchestrator = EvolutionOrchestrator(
    task_id="debug",
    code_generator=code_generator,
)

# 运行单代并查看详细结果
result = orchestrator.run_single_generation(
    generation=1,
    requirements=["..."],
    test_code="...",
)

print(f"代码: {result.code}")
print(f"得分: {result.score}")
print(f"评估报告: {result.evaluation_report}")
```

---

## API 参考

### CodeGenerator

```python
CodeGenerator(
    api_key: str = None,           # API Key（默认从环境变量）
    model: str = "deepseek-chat",  # 模型名称
    default_temperature: float = 0.5,
    backend: str = "deepseek",     # 后端: deepseek/anthropic/openai
)

generate(
    task_spec: dict,               # 任务规格
    temperature: float = None,     # 临时温度覆盖
) -> dict                         # {success, code, raw_response, error}
```

### EvolutionOrchestrator

```python
EvolutionOrchestrator(
    task_id: str,
    code_generator: CodeGenerator = None,
    termination_config: TerminationConfig = None,
)

evolve(
    requirements: List[str],       # 功能需求列表
    test_code: str,                # 测试代码
    max_generations: int = 50,
) -> EvolutionResult
```

### TerminationConfig

```python
TerminationConfig(
    success_threshold: float = 0.9,
    max_generations: int = 50,
    stagnation_generations: int = 5,
)
```

---

## 最佳实践

### 1. 任务设计

- **需求清晰**: 明确输入输出
- **测试全面**: 包含边界情况和正常情况
- **粒度适中**: 每个任务只解决一个问题

### 2. 测试代码编写

```python
# 好的测试代码
test_code = """
# 正常情况
assert factorial(5) == 120

# 边界情况
assert factorial(0) == 1
assert factorial(1) == 1

# 错误处理
try:
    factorial(-1)
    assert False, "Should raise ValueError"
except ValueError:
    pass
"""
```

### 3. 成本控制

- 使用 `max_generations` 限制代数
- 使用 Mock 实验进行开发测试
- 监控 API 调用次数

---

## 获取帮助

- **查看日志**: 设置 `verbose=True` 获取详细输出
- **阅读测试**: `tests/` 目录包含使用示例
- **检查文档**: `docs/` 目录包含架构说明

---

**维护者**: SEMDS Team  
**问题反馈**: 请提交 Issue

# Mother System Tool Design Principles
# 工具设计原则总结

## 核心原则

### 1. 极简主义 (Minimalism)
> "简单是可靠的先决条件。" —— Dijkstra

**要求**：
- 代码行数 < 100（复杂工具 < 200）
- 无未使用导入
- 无冗余变量
- 单一职责

**执行方式**：
- 预设精简模板
- 自动检查代码行数
- 检测未使用导入

---

### 2. 安全优先 (Security First)
> "绝不信任输入。"

**强制检查**：
| 检查项 | 级别 | 说明 |
|--------|------|------|
| 无 eval/exec | Error | 禁止危险函数 |
| 输入类型验证 | Error | `isinstance()` 检查 |
| 输入大小限制 | Error | 防止内存攻击 |
| 路径遍历防护 | Error | 验证文件路径 |
| SSRF 防护 | Warning | 禁止内网地址访问 |

**执行方式**：
- 静态分析检查危险函数
- 模板内置输入验证
- 自动检测硬编码密钥

---

### 3. 健壮性 (Robustness)
> "早失败，快失败，优雅处理。"

**要求**：
- 具体异常类型（禁止裸 except）
- 超时控制（网络/IO 操作）
- 资源限制（大小、数量）
- 优雅错误返回（不崩溃）

**模板标准结构**：
```python
def execute(self, input_data: str) -> dict:
    # 1. 输入验证
    if not isinstance(input_data, str):
        return {"error": "Invalid type", "data": None}
    
    if len(input_data) > self.MAX_SIZE:
        return {"error": "Input too large", "data": None}
    
    # 2. 核心逻辑（带错误处理）
    try:
        result = self._process(input_data)
        return {"success": True, "data": result, "error": None}
    except ValueError as e:
        return {"success": False, "error": str(e), "data": None}
    except Exception as e:
        return {"success": False, "error": "Internal error", "data": None}
```

---

## 执行机制

### 不是提示词，是代码约束

传统方式（会"漂"）：
```python
# ❌ 不好的方式：依赖提示词
prompt = "请写安全的代码..."
code = llm.generate(prompt)  # 可能忘记部分要求
```

我们的方式（强制执行）：
```python
# ✅ 好的方式：代码模板 + 自动检查
template = MINIMAL_TEMPLATES["http_client"]  # 预设符合原则的模板
code = fill_template(template)
code = auto_optimize(code)  # 自动修复问题
checks = run_security_audit(code)  # 安全检查
if not checks.passed:
    raise Exception("Security check failed")
```

---

## 工具质量报告

运行测试生成的工具质量：

```
html_parser:    100/100  ✓ 极简 ✓ 安全 ✓ 健壮
csv_reader:      95/100  ✓ 极简 ✓ 安全 ✓ 健壮
json_parser:    100/100  ✓ 极简 ✓ 安全 ✓ 健壮
http_client:     85/100  ✓ 极简 ✓ 安全 ✓ 健壮 (有1个警告)
file_reader:    100/100  ✓ 极简 ✓ 安全 ✓ 健壮

Average Score:   96/100
```

---

## 使用方式

### 生成符合原则的工具

```python
from mother.core.enhanced_tool_generator import generate_minimal_tool

# 自动生成符合所有原则的工具
code = generate_minimal_tool("csv_reader")
# 输出：包含输入验证、大小限制、错误处理的精简代码
```

### 检查现有代码

```python
from mother.skills.code_optimizer import optimize_code

result = optimize_code(your_code)
print(f"Score: {result['optimized_score']}/100")
print(f"Issues: {len(result['issues'])}")
print(f"Fixed: {result['optimized_code']}")
```

---

## 文件结构

```
mother/
├── standards/
│   ├── TOOL_DESIGN_PRINCIPLES.md    # 原则文档
│   ├── CODING_STANDARDS.md          # 编码规范
│   └── AGENT_MANIFESTO.md           # 代理行为准则
├── skills/
│   ├── code_optimizer.py            # 代码优化器
│   ├── web_search.py                # 联网搜索
│   ├── code_quality.py              # 代码质量检查
│   └── self_reflection.py           # 自我反思
├── core/
│   ├── enhanced_tool_generator.py   # 增强版工具生成器
│   └── enhanced_mother.py           # 增强版母体系统
└── tools/                           # 生成的工具代码
    ├── html_parser.py               # 100分
    ├── csv_reader.py                # 95分
    ├── json_parser.py               # 100分
    ├── http_client.py               # 85分
    └── file_reader.py               # 100分
```

---

## 运行测试

```bash
# 测试所有模板生成
python mother/test_principles.py

# 查看原则演示
python mother/demo_principles.py

# 运行增强版 Mother System
python mother/demo_enhanced.py
```

---

> **关键洞察**：原则通过**代码模板**和**自动检查**强制执行，不依赖容易遗忘的提示词。这确保了每次生成的工具都符合极简、安全、健壮的标准。

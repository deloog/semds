# SEMDS TDD强制规范

**文档版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: 所有代码开发

---

## 🎯 核心原则

### 1.1 TDD红绿重构循环

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   写测试    │ → │   运行失败   │ → │  写最少代码  │
│  (Red)     │    │   (Red)     │    │  (Green)   │
└─────────────┘    └─────────────┘    └──────┬──────┘
       ↑                                      │
       └──────────────────────────────────────┘
              ┌─────────────┐
              │   重构优化   │
              │ (Refactor)  │
              └─────────────┘
```

**禁止跳过任何步骤。**

### 1.2 强制顺序

```
❌ 错误顺序：写代码 → 运行 → 补测试 → 假装测试通过了

✅ 正确顺序：
    1. 写测试文件（测试必然失败或不存在）
    2. 运行测试（确认失败 - Red）
    3. 写最少代码使测试通过（Green）
    4. 重构优化（Refactor）
    5. 运行测试（确认仍通过）
    6. 重复1-5直到功能完成
```

---

## 📏 测试覆盖率标准

### 2.1 覆盖率门槛（统一标准）

> **本项目统一覆盖率标准**，所有其他规范文档应遵循此定义。

| 代码类型                  | 行覆盖率 | 分支覆盖率 | 函数覆盖率 |
| ------------------------- | -------- | ---------- | ---------- |
| **新代码**                | 100%     | 100%       | 100%       |
| **核心模块** (core/)      | ≥90%     | ≥85%       | 100%       |
| **进化模块** (evolution/) | ≥90%     | ≥85%       | 100%       |
| **存储模块** (storage/)   | ≥85%     | ≥80%       | ≥90%       |
| **其他模块**              | ≥80%     | ≥75%       | ≥90%       |
| **工具/配置**             | ≥60%     | -          | -          |

**绝对禁止：** 新代码覆盖率低于100%。

> **注意**: 核心模块指 core/ 目录；进化模块指 evolution/ 目录；存储模块指 storage/ 目录。

### 2.2 覆盖率豁免

以下情况可申请豁免（需审批）：

```markdown
- [ ] 代码为第三方库包装（wrapper）
- [ ] 代码为纯数据定义（DTO/配置类）
- [ ] 代码为IDE自动生成的样板
- [ ] 代码涉及硬件/外部不可控依赖

豁免申请模板：

- 文件路径: [path]
- 豁免原因: [具体说明]
- 替代验证: [如何确保质量]
- 申请人: [name]
- 审批人: [name]
```

**注意：** 业务逻辑代码不得申请豁免。

---

## 🧪 测试编写规范

### 3.1 测试文件命名

```python
# ✅ 正确
src/processor.py           → tests/test_processor.py
src/utils/helpers.py       → tests/utils/test_helpers.py
src/core/engine.py         → tests/core/test_engine.py

# ❌ 错误
src/processor.py           → test.py
src/processor.py           → tests/processor_test.py
src/processor.py           → tests/v2_test_processor.py
```

### 3.2 测试函数命名

```python
# ✅ 正确 - 描述行为而非方法
def test_should_return_error_when_input_is_invalid():
def test_processes_multiple_items_in_batch():
def test_raises_not_found_when_entity_missing():

# ❌ 错误 - 只描述被测方法
def test_process():
def test_validate():
def test_processor():
```

### 3.3 测试结构（AAA模式）

```python
def test_should_calculate_total_with_tax():
    # Arrange - 准备
    calculator = PriceCalculator(tax_rate=0.08)
    items = [Item(price=100), Item(price=200)]

    # Act - 执行
    total = calculator.calculate(items)

    # Assert - 验证
    assert total == 324  # (100+200)*1.08
```

### 3.4 必须测试的内容

| 类型         | 测试要求 | 示例                     |
| ------------ | -------- | ------------------------ |
| **正常路径** | 必须测试 | 合法输入产生预期输出     |
| **边界值**   | 必须测试 | 空列表、单个元素、最大值 |
| **错误输入** | 必须测试 | None、错误类型、越界值   |
| **异常抛出** | 必须测试 | 确认异常类型和消息       |
| **副作用**   | 必须测试 | 文件写入、状态变更       |

---

## 🚫 禁止行为

### 4.1 绝对禁止清单

#### ❌ 禁止修改测试来"假装通过"

```python
# ❌ 错误 - AI天性：测试不过就改测试
# 原测试
def test_should_validate_email():
    assert validate_email("invalid") == False  # 测试失败

# AI错误做法 - 修改测试降低期望
def test_should_validate_email():
    # 改成这样测试就通过了，对吧？
    # 不对！这是自欺欺人！
    assert validate_email("invalid") == True  # 错误！
```

```python
# ✅ 正确做法 - 修改代码使测试通过
def validate_email(email):
    if not email or "@" not in email:
        return False
    return True
```

#### ❌ 禁止跳过失败测试

```python
# ❌ 错误
@pytest.mark.skip("暂时跳过")  # 为什么跳过？
def test_critical_feature():
    ...
```

```python
# ✅ 正确
# 测试失败时，修复代码，不是跳过测试
def test_critical_feature():
    # 让测试通过的正确实现
    ...
```

#### ❌ 禁止空测试/假测试

```python
# ❌ 错误 - 虚假覆盖
def test_feature():
    pass  # 这算哪门子测试？

def test_feature():
    assert True  # 这也叫测试？
```

#### ❌ 禁止事后补测试

```markdown
❌ 错误流程：

1. 写代码
2. 感觉功能完成了
3. 报告"已完成"
4. 补几个测试应付检查

✅ 正确流程：

1. 写测试（Red）
2. 写代码（Green）
3. 重构（Refactor）
4. 报告"已完成"（所有测试已存在且通过）
```

### 4.2 测试质量红线

> **统一测试执行时间标准**：
>
> - 单元测试: < 1秒/个
> - 集成测试: < 30秒/个

```markdown
- [ ] 每个测试必须有至少一个断言
- [ ] 禁止测试之间相互依赖
- [ ] 禁止测试执行顺序依赖
- [ ] 测试必须可重复运行（无副作用）
- [ ] 单元测试执行时间<1秒
```

---

## 🔍 测试审查清单

### 5.1 提交前自检

代码提交前，运行以下检查：

```bash
# 1. 运行所有测试
pytest --tb=short

# 2. 检查覆盖率
pytest --cov=src --cov-report=term-missing

# 3. 确保新代码100%覆盖
pytest --cov=src --cov-fail-under=90

# 4. 类型检查
mypy src/

# 5. 静态检查
flake8 src/ tests/
```

### 5.2 测试审查表

```markdown
## 测试审查清单

### 功能覆盖

- [ ] 所有公开函数/方法都有对应测试
- [ ] 正常路径有测试
- [ ] 错误路径有测试
- [ ] 边界条件有测试

### 测试质量

- [ ] 测试名称清晰描述行为
- [ ] 每个测试只有一个职责
- [ ] 使用Given-When-Then或Arrange-Act-Assert
- [ ] 无硬编码魔法数字（使用常量/变量）

### 覆盖率

- [ ] 新代码行覆盖率100%
- [ ] 新代码分支覆盖率100%
- [ ] 无遗漏的异常处理分支

### 可维护性

- [ ] 使用fixtures共享测试数据
- [ ] 使用parametrize减少重复
- [ ] 测试独立，无顺序依赖
```

---

## 🛠️ 测试工具配置

### 6.1 pytest配置

```ini
# pyproject.toml 或 pytest.ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--tb=short",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=90",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
```

### 6.2 覆盖率配置

```ini
# .coveragerc
[run]
source = src
branch = True
omit =
    */tests/*
    */test_*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:

fail_under = 90
show_missing = True
skip_covered = False
```

---

## 📊 CI/CD集成

### 7.1 流水线门禁

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run tests with coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-fail-under=90
      - name: Check new code coverage
        run: |
          # 新代码必须100%覆盖
          diff-cover coverage.xml --compare-branch=main --fail-under=100
```

### 7.2 质量门禁顺序

```
提交代码
    ↓
1. 单元测试（必须100%通过）
    ↓ 失败 → 阻断
2. 覆盖率检查（必须≥90%，新代码100%）
    ↓ 失败 → 阻断
3. 静态检查（flake8/pylint）
    ↓ 失败 → 阻断
4. 类型检查（mypy）
    ↓ 失败 → 阻断
5. 集成测试
    ↓ 失败 → 阻断
6. 允许合并
```

---

## 🎯 违规处理

### 8.1 违规场景

| 场景                     | 处理                   | 责任人   |
| ------------------------ | ---------------------- | -------- |
| 测试未100%通过即报告完成 | 状态回退，重新开发     | AI开发者 |
| 修改测试使测试通过       | 严重警告，重新学习规范 | AI开发者 |
| 新代码覆盖率<100%        | 补充测试直至达标       | AI开发者 |
| 整体覆盖率<90%           | 阻断合并               | CI系统   |

### 8.2 学习资源

未理解TDD的AI必须学习：

1. 《测试驱动开发》Kent Beck
2. 《单元测试之道》Andy Hunt
3. pytest官方文档
4. 本项目测试示例代码

---

## ✅ 签署确认

> 我已阅读并理解SEMDS TDD强制规范。
> 我承诺严格遵循：
>
> 1. 红-绿-重构循环，不跳过步骤
> 2. 新代码100%测试覆盖
> 3. 测试失败时修改代码，不修改测试
> 4. 不报告"完成"直到所有测试通过

**确认AI**: **\*\***\_\_\_**\*\***  
**确认时间**: **\*\***\_\_\_**\*\***

---

**最后更新**: 2026-03-07  
**维护者**: 人类监督员

# SEMDS 测试规范

**版本**: v1.0  
**目标**: 确保代码可靠性  
**强制**: 是

---

## 🎯 测试金字塔

```
        /\
       /  \
      / E2E \      (少量) 端到端测试
     /--------\
    / Integration\ (中等) 集成测试
   /--------------\
  /   Unit Tests    \ (大量) 单元测试
 /--------------------\
```

**比例要求**: Unit : Integration : E2E = 70% : 20% : 10%

---

## 🧪 单元测试

### 强制要求

- 每个公共函数必须有测试
- 每个类必须有测试
- 每个异常分支必须覆盖

### 测试命名规范

```python
# ✅ 好：描述性行为
class TestCodeGenerator:
    def test_generate_returns_valid_python_syntax(self):
        """测试生成的代码是有效的Python语法。"""
        pass

    def test_generate_handles_empty_task_spec(self):
        """测试生成器处理空任务规格。"""
        pass

    def test_generate_raises_error_on_invalid_backend(self):
        """测试无效后端时抛出错误。"""
        pass

# ❌ 坏：模糊命名
class TestCodeGen:
    def test1(self): pass
    def test2(self): pass
```

### 测试结构 (AAA模式)

```python
def test_safe_write_creates_backup(self, tmp_path):
    """测试safe_write创建备份文件。"""
    # Arrange (准备)
    filepath = tmp_path / "test.py"
    original_content = "original"
    filepath.write_text(original_content)
    new_content = "new content"

    # Act (执行)
    result = safe_write(str(filepath), new_content)

    # Assert (断言)
    assert result.success is True
    assert filepath.read_text() == new_content
    assert len(list(tmp_path.glob("*.bak*"))) == 1
```

### 测试覆盖率要求

> **统一标准详见**: TDD_MANDATE.md 第2.1节

```
Minimum Coverage:
- 核心模块 (core/): ≥90%
- 进化模块 (evolution/): ≥90%
- 存储模块 (storage/): ≥85%
- 其他模块: ≥80%
- 新代码: 100%

Branch Coverage:
- 所有if/else分支必须覆盖
- 所有异常处理必须覆盖
- 所有循环边界必须覆盖
- 新代码分支覆盖率: 100%
```

---

## 🔗 集成测试

### 测试范围

- 模块间交互
- 数据库操作
- 外部API调用（mock）
- 文件系统交互（临时目录）

### 示例

```python
class TestEvolutionWorkflow:
    """测试完整进化工作流。"""

    def test_single_generation_flow(self, tmp_db, tmp_dir):
        """测试单代进化流程。"""
        # 初始化
        generator = CodeGenerator(backend="mock")
        evaluator = Evaluator(test_suite="calculator")

        # 执行
        code = generator.generate(CALCULATOR_TASK)
        result = evaluator.evaluate(code)

        # 验证
        assert result.pass_rate > 0
        assert result.execution_time_ms > 0

    def test_database_persists_generation(self, tmp_db):
        """测试数据库持久化。"""
        # 写入
        gen = Generation(id="test-1", code="x=1", score=0.9)
        tmp_db.save(gen)

        # 读取
        retrieved = tmp_db.get("test-1")
        assert retrieved.code == "x=1"
        assert retrieved.score == 0.9
```

---

## 🎭 测试替身 (Test Doubles)

### Mock 使用规范

```python
# ✅ Mock外部依赖
@pytest.fixture
def mock_llm_backend():
    with patch('semds.evolution.code_generator.CodeGenerator._call_api') as mock:
        mock.return_value = "def calculate(a,b,op): return a+b"
        yield mock

# ✅ Mock数据库
@pytest.fixture
def mock_db():
    return Mock(spec=Database)

# ❌ 不要Mock被测代码内部逻辑
def test_bad_example():
    with patch.object(generator, '_internal_helper'):
        # 这是被测代码的实现细节，不应该mock
        pass
```

### Fake 对象

```python
class FakeSandbox(SandboxInterface):
    """假沙盒，用于测试。"""

    def __init__(self, preconfigured_results: dict):
        self.results = preconfigured_results

    def execute(self, code: str) -> ExecutionResult:
        # 返回预设结果，不真正执行
        return self.results.get(code, ExecutionResult(success=True))
```

---

## 🐛 测试数据

### 测试数据工厂

```python
@dataclass
class TaskSpecFactory:
    """任务规格数据工厂。"""

    @staticmethod
    def calculator_task() -> TaskSpec:
        return TaskSpec(
            name="calculator",
            description="Simple calculator",
            requirements=["support + - * /"]
        )

    @staticmethod
    def invalid_task() -> TaskSpec:
        return TaskSpec(
            name="",
            description="",
            requirements=[]
        )

    @staticmethod
    def complex_task() -> TaskSpec:
        return TaskSpec(
            name="web_scraper",
            description="Complex web scraper",
            requirements=[...]  # 大量要求
        )
```

### 边界值测试

```python
class TestCodeGeneratorEdgeCases:
    """边界值测试。"""

    @pytest.mark.parametrize("task_size", [0, 1, 1000, 10000])
    def test_handles_various_task_sizes(self, task_size):
        task = create_task_with_size(task_size)
        result = generator.generate(task)
        assert result.success or result.error_code == "TASK_TOO_LARGE"

    @pytest.mark.parametrize("timeout", [0.001, 1, 60, 300])
    def test_respects_timeout(self, timeout):
        with pytest.raises(TimeoutError) if timeout < 0.1 else nullcontext():
            generator.generate(task, timeout=timeout)
```

---

## 🔒 安全测试

### 必须测试的安全场景

```python
class TestSecurity:
    """安全相关测试。"""

    def test_rejects_code_with_eval(self):
        """测试拒绝包含eval的代码。"""
        malicious_code = "eval('os.system(\"rm -rf /\")')"
        result = sandbox.execute(malicious_code)
        assert result.blocked is True
        assert "forbidden_pattern" in result.block_reason

    def test_prevents_path_traversal(self):
        """测试防止路径遍历攻击。"""
        result = safe_write("../../../etc/passwd", "content")
        assert result.success is False

    def test_isolates_file_system(self):
        """测试文件系统隔离。"""
        code = "open('/etc/hosts').read()"
        result = sandbox.execute(code)
        assert result.success is False  # 沙盒内无法访问宿主机文件
```

---

## 📊 测试报告

### 覆盖率报告

```bash
pytest --cov=semds --cov-report=html --cov-report=term-missing
```

### 测试执行报告

```json
{
  "timestamp": "2024-03-07T10:00:00Z",
  "total_tests": 150,
  "passed": 148,
  "failed": 2,
  "skipped": 0,
  "duration_seconds": 45.2,
  "coverage": {
    "total": 87.5,
    "by_module": {
      "core": 96.2,
      "evolution": 88.1,
      "storage": 82.3
    }
  }
}
```

---

## 📊 测试性能指标（汇总）

| 指标                | 阈值      | 来源           |
| ------------------- | --------- | -------------- |
| 单元测试执行时间    | < 1秒/个  | TDD_MANDATE.md |
| 集成测试执行时间    | < 30秒/个 | TDD_MANDATE.md |
| 新代码行覆盖率      | 100%      | TDD_MANDATE.md |
| 新代码分支覆盖率    | 100%      | TDD_MANDATE.md |
| 核心/进化模块覆盖率 | ≥90%      | TDD_MANDATE.md |
| 存储模块覆盖率      | ≥85%      | TDD_MANDATE.md |
| 其他模块覆盖率      | ≥80%      | TDD_MANDATE.md |

---

## ✅ 提交前检查清单

```markdown
- [ ] 所有新功能都有单元测试
- [ ] 集成测试覆盖关键流程
- [ ] 测试覆盖率不降低
- [ ] 安全测试通过
- [ ] 性能回归测试通过（如果适用）
```

---

**无测试的代码不得合并到主分支**

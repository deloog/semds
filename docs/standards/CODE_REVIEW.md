# SEMDS 代码审查规范

**文档版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: 所有代码审查

---

## 🎯 三层防护网

根据PreCode Architect思想，建立代码审查三层防护网：

```
┌─────────────────────────────────────────────────────────────┐
│ 第一层: IDE实时防护                                          │
│         ↓ 编码时即时检查                                      │
├─────────────────────────────────────────────────────────────┤
│ 第二层: 预提交钩子拦截                                        │
│         ↓ 提交前强制检查                                      │
├─────────────────────────────────────────────────────────────┤
│ 第三层: CI流水线门禁                                          │
│         ↓ 合并前最终把关                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 第一层：IDE实时防护

### 2.1 配置要求

**必须启用的IDE插件：**

| 工具 | 用途 | 配置位置 |
|-----|------|---------|
| flake8/pylint | Python静态检查 | `.flake8`, `pyproject.toml` |
| mypy | 类型检查 | `pyproject.toml` |
| black | 代码格式化 | `pyproject.toml` |
| isort | 导入排序 | `pyproject.toml` |

### 2.2 实时检查规则

```python
# ❌ IDE应立即标记为错误
import os, sys  # 一行多个导入

def process(x):  # 无类型提示
    return x+1  # 运算符无空格

def bad_function():  # 圈复杂度过高
    if a:
        if b:
            if c:
                if d:
                    return 1
    return 0
```

---

## 🪝 第二层：预提交钩子

### 3.1 强制检查项

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
      
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]
      
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']
      
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
      
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest --tb=short -q
        language: system
        pass_filenames: false
        always_run: true
      
      - id: coverage-check
        name: coverage-check
        entry: pytest --cov=src --cov-fail-under=90
        language: system
        pass_filenames: false
        always_run: true
```

### 3.2 渐进式采纳策略

```markdown
# 阶段1: 警告模式（第1-2周）
- 配置检查工具为警告模式
- 记录违规但不阻断提交
- 团队适应新规范

# 阶段2: 强制模式（第3周起）
- 启用阻断模式
- 任何违规都无法提交
- 允许 `--no-verify` 紧急绕过（需记录审计）
```

### 3.3 紧急绕过

```bash
# 仅在真正紧急时使用
 git commit --no-verify -m "紧急修复生产问题"

# 必须在24小时内补充：
# 1. 在代码中添加注释说明为何绕过
# 2. 创建Issue追踪修复
# 3. 下次提交时修复所有问题
```

---

## 🏭 第三层：CI流水线门禁

### 4.1 流水线配置

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate
on: [push, pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      
      # 门禁1: 代码格式
      - name: Check formatting (Black)
        run: black --check src/ tests/
      
      # 门禁2: 导入排序
      - name: Check import sorting (isort)
        run: isort --check-only src/ tests/
      
      # 门禁3: 静态检查
      - name: Run flake8
        run: flake8 src/ tests/
      
      # 门禁4: 类型检查
      - name: Run mypy
        run: mypy src/
      
      # 门禁5: 单元测试
      - name: Run unit tests
        run: pytest tests/unit --tb=short
      
      # 门禁6: 覆盖率（整体≥90%）
      - name: Check overall coverage
        run: pytest --cov=src --cov-fail-under=90 --cov-report=xml
      
      # 门禁7: 新代码覆盖率（必须100%）
      - name: Check new code coverage
        run: |
          pip install diff-cover
          diff-cover coverage.xml --compare-branch=main --fail-under=100
      
      # 门禁8: 架构测试（ArchUnit风格）
      - name: Run architecture tests
        run: pytest tests/architecture --tb=short
      
      # 门禁9: 安全扫描
      - name: Security scan
        run: |
          pip install bandit safety
          bandit -r src/
          safety check
```

### 4.2 门禁顺序与阻断策略

```
代码提交/PR
    ↓
┌─────────────────────────────────────┐
│ 门禁1: 代码格式 (Black/isort)        │
│ 失败 → 自动修复建议，阻断合并         │
└─────────────────────────────────────┘
    ↓ 通过
┌─────────────────────────────────────┐
│ 门禁2: 静态检查 (flake8)             │
│ 失败 → 手动修复，阻断合并             │
└─────────────────────────────────────┘
    ↓ 通过
┌─────────────────────────────────────┐
│ 门禁3: 类型检查 (mypy)               │
│ 失败 → 手动修复，阻断合并             │
└─────────────────────────────────────┘
    ↓ 通过
┌─────────────────────────────────────┐
│ 门禁4: 单元测试通过率 (100%)         │
│ 失败 → 修复代码，阻断合并             │
└─────────────────────────────────────┘
    ↓ 通过
┌─────────────────────────────────────┐
│ 门禁5: 整体覆盖率 (≥90%)             │
│ 失败 → 补充测试，阻断合并             │
└─────────────────────────────────────┘
    ↓ 通过
┌─────────────────────────────────────┐
│ 门禁6: 新代码覆盖率 (100%)           │
│ 失败 → 补充测试，阻断合并             │
│ ⚠️ 严禁降低此标准让测试通过           │
└─────────────────────────────────────┘
    ↓ 通过
┌─────────────────────────────────────┐
│ 门禁7: 架构合规检查                  │
│ 失败 → 重构代码，阻断合并             │
└─────────────────────────────────────┘
    ↓ 通过
┌─────────────────────────────────────┐
│ 门禁8: 安全扫描                      │
│ 高危漏洞 → 阻断合并                   │
│ 中低漏洞 → 警告，建议修复             │
└─────────────────────────────────────┘
    ↓ 通过
允许合并
```

---

## 🔬 架构合规检查

### 5.1 ArchUnit风格测试

```python
# tests/architecture/test_architecture.py
import pytest
from pathlib import Path

class TestArchitecture:
    """架构合规检查"""
    
    def test_no_circular_imports(self):
        """禁止循环依赖"""
        # 使用import-linter或自定义检查
        result = subprocess.run(
            ["import-linter", "--config", "importlinter.cfg"],
            capture_output=True
        )
        assert result.returncode == 0, "发现循环依赖"
    
    def test_layer_dependencies(self):
        """分层依赖规则"""
        # domain层不依赖其他层
        # application层只依赖domain
        # infrastructure层依赖domain和application
        # interfaces层依赖application
        rules = [
            ("src/domain", []),
            ("src/application", ["src/domain"]),
            ("src/infrastructure", ["src/domain", "src/application"]),
            ("src/interfaces", ["src/application"]),
        ]
        for layer, allowed_deps in rules:
            self._check_layer_dependencies(layer, allowed_deps)
    
    def test_naming_conventions(self):
        """命名规范检查"""
        src_path = Path("src")
        
        # 模块名小写
        for py_file in src_path.rglob("*.py"):
            if "__" in py_file.name:
                continue  # 忽略 __init__.py 等
            assert py_file.stem.islower() or '_' in py_file.stem, \
                f"{py_file} 命名不规范"
    
    def test_no_print_statements(self):
        """禁止print，使用logger"""
        # 扫描源码中的print语句
        pass
    
    def test_test_file_naming(self):
        """测试文件命名规范"""
        test_path = Path("tests")
        for test_file in test_path.rglob("test_*.py"):
            assert test_file.name.startswith("test_"), \
                f"{test_file} 命名不规范"
```

### 5.2 常见反模式检测

| 反模式 | 检测规则 | 风险 | 修复建议 |
|-------|---------|------|---------|
| 大泥球 | 文件>500行，函数>50行 | 可维护性下降 | 拆分模块，单一职责 |
| 上帝类 | 类方法>20个 | 职责过多 | 拆分子类或组合 |
| 重复代码 | 相似度>80% | 维护困难 | 提取公共函数 |
| 深度嵌套 | 缩进>4层 | 可读性差 | 提前返回，提取函数 |
| 魔法数字 | 字面常量无命名 | 意图不明 | 定义为常量 |

---

## 📊 偏离度报告

### 6.1 规范偏离度追踪

```markdown
# 规范偏离度报告

生成时间: 2026-03-07
报告周期: 2026-02-01 至 2026-03-07

## 总体偏离度
- 合规文件: 85%
- 违规文件: 15%
- 趋势: ↓ 较上月降低5%

## 按规则偏离
| 规则 | 违规次数 | 占比 | 趋势 |
|------|---------|------|------|
| 行长度>100 | 45 | 35% | ↓ |
| 缺少类型提示 | 30 | 23% | ↓ |
| 测试覆盖率<90% | 25 | 19% | → |
| 文档缺失 | 20 | 15% | ↑ |
| 其他 | 15 | 12% | → |

## 按模块偏离
[热力图显示各模块合规情况]

## 责任人分布
| 贡献者 | 违规密度 | 主要问题 |
|--------|---------|---------|
| AI-1 | 2.5/文件 | 类型提示 |
| AI-2 | 1.8/文件 | 文档缺失 |

## 改进建议
1. 加强类型提示培训
2. 完善文档模板
3. 增加IDE实时提示
```

### 6.2 质量门禁趋势

```markdown
# CI门禁通过率趋势

| 周次 | 通过率 | 平均修复时间 | 主要失败原因 |
|------|--------|-------------|-------------|
| W1 | 65% | 4h | 格式问题 |
| W2 | 78% | 2.5h | 测试覆盖率 |
| W3 | 85% | 1.5h | 类型检查 |
| W4 | 92% | 1h | 架构测试 |
```

---

## 📝 审查检查清单

### 7.1 提交前自检

```markdown
- [ ] 代码格式化通过 (black/isort)
- [ ] 静态检查无错误 (flake8)
- [ ] 类型检查通过 (mypy)
- [ ] 单元测试100%通过
- [ ] 新代码覆盖率100%
- [ ] 整体覆盖率≥90%
- [ ] 无print语句（使用logger）
- [ ] 无硬编码敏感信息
- [ ] 文档已更新
- [ ] 变更日志已更新
```

### 7.2 AI代码审查清单

```markdown
## AI生成代码专项审查

### 合规性
- [ ] 遵循CODING_STANDARDS.md
- [ ] 遵循TDD_MANDATE.md（先测试后代码）
- [ ] 遵循ARCHITECTURE_GUIDE.md

### 质量
- [ ] 无AI常见错误（索引越界、边界条件）
- [ ] 异常处理完整
- [ ] 无死代码/注释掉的代码
- [ ] 无硬编码的"魔法数字"

### 测试
- [ ] 测试先写，后写代码
- [ ] 测试覆盖所有分支
- [ ] 无虚假测试（assert True）
- [ ] 无跳过的测试

### 安全
- [ ] 无SQL注入风险
- [ ] 无命令注入风险
- [ ] 敏感信息不硬编码
- [ ] 输入已验证

### 性能
- [ ] 无明显的性能问题
- [ ] 无内存泄漏风险
- [ ] 大数据集处理已考虑
```

---

## 🚫 禁止行为

| 行为 | 后果 |
|-----|------|
| 绕过pre-commit hooks | 记录审计日志，严重警告 |
| 修改测试使门禁通过 | 严重违规，代码回退 |
| 虚报"已通过所有检查" | 状态回退，重新审查 |
| 强制合并失败的PR | 阻断权限，通报批评 |
| 忽视架构测试失败 | 技术债务累积，后期重构困难 |

---

**最后更新**: 2026-03-07  
**维护者**: 人类监督员

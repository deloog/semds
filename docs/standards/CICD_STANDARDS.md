# SEMDS CI/CD 规范标准

**版本**: v1.0  
**状态**: 强制执行  
**生效日期**: 2026-03-11

---

## 1. 概述

本文档定义SEMDS项目的CI/CD（持续集成/持续部署）标准，确保所有代码变更通过自动化质量门禁后方可进入主分支。

### 1.1 质量门禁顺序

```
代码提交
    ↓
1. Pre-commit hooks（本地）
    ↓ 失败 → 阻断提交
2. CI: 代码质量检查（Black, isort, flake8, pylint）
    ↓ 失败 → 阻断
3. CI: 类型检查（MyPy严格模式）
    ↓ 失败 → 阻断
4. CI: 单元测试（必须100%通过）
    ↓ 失败 → 阻断
5. CI: 覆盖率检查（新代码100%，核心≥90%）
    ↓ 失败 → 阻断
6. CI: 安全扫描（Bandit, Safety）
    ↓ 失败 → 阻断
7. CI: 集成测试
    ↓ 失败 → 阻断
8. CI: 构建验证
    ↓ 失败 → 阻断
9. 人工代码审查（强制）
    ↓ 未通过 → 阻断
10. 允许合并
```

---

## 2. 本地开发门禁

### 2.1 Pre-commit Hooks

所有提交必须通过 `.pre-commit-config.yaml` 中定义的检查：

```bash
# 安装pre-commit
pip install pre-commit
pre-commit install

# 手动运行所有检查
pre-commit run --all-files

# 提交时自动运行
```

### 2.2 本地检查命令

```bash
# 完整检查（等同于CI）
make check

# 分项检查
make lint        # 代码格式和风格
make type-check  # 类型检查
make test        # 单元测试
make test-cov    # 测试+覆盖率
```

### 2.3 提交前强制检查清单

```markdown
- [ ] `make lint` 无错误
- [ ] `make type-check` 无错误
- [ ] `make test` 100%通过
- [ ] 新代码覆盖率100%
- [ ] `bandit -r .` 无高危漏洞
```

---

## 3. CI/CD Pipeline 详解

### 3.1 触发条件

```yaml
on:
  push:
    branches: [main, develop]      # 推送到主分支触发
  pull_request:
    branches: [main, develop]      # PR触发完整检查
```

### 3.2 Jobs 顺序与依赖

```
lint (代码质量)
  └── type-check (类型检查)
        └── test (单元测试)
              ├── integration-test (集成测试)
              ├── security (安全扫描)
              └── build (构建验证)
```

**并行策略**:
- `lint` 和 `type-check` 可并行
- `test` 依赖两者通过后才启动
- 集成测试、安全扫描、构建验证可并行

### 3.3 各Job详细标准

#### Job 1: lint (代码质量)

| 检查项 | 工具 | 阈值 | 失败策略 |
|--------|------|------|----------|
| 代码格式化 | Black | 无差异 | 阻断 |
| 导入排序 | isort | 无差异 | 阻断 |
| 代码风格 | Flake8 | 0错误 | 阻断 |
| 静态分析 | Pylint | ≥9.0分 | 阻断 |

```yaml
- name: Check Black formatting
  run: black --check --diff .

- name: Check import sorting
  run: isort --check-only --diff .

- name: Run Flake8
  run: flake8 core/ evolution/ storage/ tests/

- name: Run Pylint
  run: pylint core/ evolution/ storage/ --fail-under=9.0
```

#### Job 2: type-check (类型检查)

| 检查项 | 工具 | 模式 | 失败策略 |
|--------|------|------|----------|
| 类型检查 | MyPy | --strict | 阻断 |

```yaml
- name: Run MyPy
  run: mypy core/ evolution/ storage/ --strict --show-error-codes
```

**严格模式启用规则**:
- `disallow_untyped_defs`: 所有函数必须有类型注解
- `disallow_incomplete_defs`: 不允许部分类型注解
- `check_untyped_defs`: 检查未类型注解的函数
- `no_implicit_optional`: 不允许隐式Optional

#### Job 3: test (单元测试)

| 检查项 | 工具 | 阈值 | 失败策略 |
|--------|------|------|----------|
| 测试通过 | pytest | 100% | 阻断 |
| 代码覆盖 | coverage | 核心≥90% | 阻断 |

```yaml
- name: Run tests
  run: pytest tests/ -v --tb=short --cov=core --cov=evolution --cov=storage

- name: Check coverage thresholds
  run: |
    coverage report --include="core/*" --fail-under=90
    coverage report --include="evolution/*" --fail-under=90
    coverage report --include="storage/*" --fail-under=85
```

#### Job 4: security (安全扫描)

| 检查项 | 工具 | 阈值 | 失败策略 |
|--------|------|------|----------|
| 安全漏洞 | Bandit | 无高危 | 阻断 |
| 依赖漏洞 | Safety | 无高危 | 警告 |

```yaml
- name: Run Bandit
  run: bandit -r core/ evolution/ storage/ -ll -ii

- name: Check dependencies
  run: safety check --full-report || true
```

#### Job 5: integration-test (集成测试)

| 检查项 | 工具 | 环境 | 失败策略 |
|--------|------|------|----------|
| Docker测试 | pytest | dind | 阻断 |

```yaml
services:
  docker:
    image: docker:24-dind
    options: --privileged
```

#### Job 6: build (构建验证)

| 检查项 | 工具 | 阈值 | 失败策略 |
|--------|------|------|----------|
| 包构建 | build | 成功 | 阻断 |
| Wheel检查 | check-wheel-contents | 无错误 | 阻断 |
| 元数据 | twine | 无错误 | 阻断 |

---

## 4. 分支保护规则

### 4.1 Main分支保护

```
✓ 需要Pull Request才能合并
✓ 需要1个审查者批准
✓ 需要状态检查通过：
  - lint
  - type-check
  - test (3.11)
  - test (3.12)
  - security
  - build
✓ 需要分支最新
✓ 禁止强制推送
✓ 禁止删除
```

### 4.2 Develop分支保护

```
✓ 需要Pull Request才能合并
✓ 需要状态检查通过（同上）
✓ 需要分支最新
```

---

## 5. 发布流程

### 5.1 版本发布

```bash
# 1. 创建发布分支
git checkout -b release/v1.2.0

# 2. 更新版本号（pyproject.toml, __init__.py）
# 3. 更新CHANGELOG.md
# 4. 提交PR到main

# 5. PR合并后，创建标签
git tag v1.2.0
git push origin v1.2.0

# 6. GitHub Release自动生成
```

### 5.2 热修复流程

```bash
# 1. 从main创建hotfix分支
git checkout -b hotfix/v1.2.1 main

# 2. 修复问题
# 3. 提交PR到main和develop

# 4. 合并后创建标签
git tag v1.2.1
git push origin v1.2.1
```

---

## 6. 监控与告警

### 6.1 CI失败通知

- Slack/Discord webhook通知
- 邮件通知（关键成员）
- PR评论自动更新状态

### 6.2 质量指标监控

| 指标 | 目标 | 告警阈值 |
|------|------|----------|
| CI成功率 | >95% | <90% |
| 平均构建时间 | <5分钟 | >10分钟 |
| 测试覆盖率 | >90% | <85% |
| 安全漏洞 | 0高危 | >0 |

---

## 7. 故障排除

### 7.1 常见CI失败原因

| 失败类型 | 常见原因 | 解决方案 |
|----------|----------|----------|
| Black失败 | 代码未格式化 | 运行 `black .` |
| isort失败 | 导入顺序错误 | 运行 `isort .` |
| MyPy失败 | 类型错误 | 添加/修正类型注解 |
| Flake8失败 | 风格违规 | 根据错误提示修复 |
| 测试失败 | 功能缺陷 | 修复代码或测试 |
| 覆盖率不足 | 缺少测试 | 补充测试用例 |
| Bandit失败 | 安全问题 | 修复安全问题或使用 `# nosec` |

### 7.2 本地复现CI环境

```bash
# 使用Docker复现CI环境
docker run -it --rm -v $(pwd):/workspace python:3.11 bash
cd /workspace
pip install -e ".[dev]"
make check
```

---

## 8. 规范更新

本文档由DevOps团队维护，更新需经技术负责人审批。

---

**批准人**: _____________  
**批准日期**: _____________

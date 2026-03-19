# SEMDS 严格模式开发指南

**版本**: v1.0  
**状态**: 强制执行（自2026-03-11起）  
**适用范围**: 所有AI Agent和开发者

---

## 1. 严格模式宣言

> 质量是SEMDS的生命线。
> 严格模式下，任何质量妥协都是不可接受的。

### 1.1 核心原则

```
┌─────────────────────────────────────────────────────────────┐
│ 原则1: 零容忍                                              │
│   - 测试失败 = 代码未就绪                                   │
│   - 类型错误 = 代码未就绪                                   │
│   - 格式违规 = 代码未就绪                                   │
│   - 安全漏洞 = 代码未就绪                                   │
├─────────────────────────────────────────────────────────────┤
│ 原则2: 完整性优先                                          │
│   - 功能 + 测试 + 文档 = 完整交付                          │
│   - 缺少任何一项 = 未完成                                   │
├─────────────────────────────────────────────────────────────┤
│ 原则3: 过程可追溯                                          │
│   - 所有变更必须经过PR审查                                  │
│   - 所有测试必须在CI中运行                                  │
│   - 所有文档必须同步更新                                    │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 质量标准红线

| 维度 | 红线 | 违规后果 |
|------|------|----------|
| 测试覆盖率 | 新代码<100% | **阻断合并** |
| 单元测试 | 未100%通过 | **阻断合并** |
| 类型检查 | MyPy有错误 | **阻断合并** |
| 代码格式 | Black/isort失败 | **阻断提交** |
| 静态分析 | Pylint<9.0 | **阻断合并** |
| 安全扫描 | Bandit高危漏洞 | **阻断合并** |
| 文档同步 | 公共API无docstring | **要求修改** |

---

## 2. 开发工作流

### 2.1 五步开发法（强制）

```
┌────────────────────────────────────────────────────────────┐
│ Step 1: 需求解析                                            │
├────────────────────────────────────────────────────────────┤
│ • 阅读相关规格文档                                           │
│ • 识别涉及的架构层（Layer 0/1/2）                            │
│ • 评估理解度（<70%必须澄清）                                  │
│ • 输出：需求解析报告 + 测试计划                               │
├────────────────────────────────────────────────────────────┤
│ Step 2: 测试先行（TDD - 强制）                               │
├────────────────────────────────────────────────────────────┤
│ • 写测试文件（必须先失败）                                    │
│ • 验证测试覆盖场景                                           │
│ • 禁止写空测试或假测试                                        │
│ • 输出：测试文件 + 失败截图                                   │
├────────────────────────────────────────────────────────────┤
│ Step 3: 最小实现                                              │
├────────────────────────────────────────────────────────────┤
│ • 写最少代码使测试通过                                        │
│ • 即时质量门禁（每函数检查）                                   │
│ • 不添加未测试的功能                                          │
│ • 输出：实现代码 + 通过截图                                   │
├────────────────────────────────────────────────────────────┤
│ Step 4: 重构优化                                              │
├────────────────────────────────────────────────────────────┤
│ • 消除重复代码（DRY）                                         │
│ • 优化命名（意图表达）                                        │
│ • 确保测试仍通过                                             │
│ • 输出：重构后代码 + 质量报告                                  │
├────────────────────────────────────────────────────────────┤
│ Step 5: 文档同步                                              │
├────────────────────────────────────────────────────────────┤
│ • 更新代码docstring                                          │
│ • 更新相关Markdown文档                                        │
│ • 验证一致性                                                 │
│ • 输出：文档更新 + 最终检查清单                                │
└────────────────────────────────────────────────────────────┘
```

### 2.2 提交前强制检查

```bash
#!/bin/bash
# pre-commit-check.sh - 提交前必须运行

set -e  # 任何命令失败即退出

echo "=== SEMDS 严格模式提交前检查 ==="

# 1. 代码格式
echo "[1/8] Black formatting..."
black --check --diff .

# 2. 导入排序
echo "[2/8] Import sorting..."
isort --check-only --diff .

# 3. 代码风格
echo "[3/8] Flake8 style check..."
flake8 core/ evolution/ storage/ tests/

# 4. 静态分析
echo "[4/8] Pylint static analysis..."
pylint core/ evolution/ storage/ --fail-under=9.0

# 5. 类型检查
echo "[5/8] MyPy type check..."
mypy core/ evolution/ storage/ --strict --show-error-codes

# 6. 单元测试
echo "[6/8] Unit tests..."
pytest tests/ -v --tb=short

# 7. 覆盖率检查
echo "[7/8] Coverage check..."
pytest --cov=core --cov=evolution --cov=storage --cov-fail-under=85 tests/

# 8. 安全扫描
echo "[8/8] Security scan..."
bandit -r core/ evolution/ storage/ -ll -ii

echo "=== 所有检查通过 ==="
```

---

## 3. 质量门禁详解

### 3.1 本地门禁（pre-commit）

**触发时机**: `git commit`  
**阻断策略**: 任何检查失败阻断提交

| 检查项 | 工具 | 配置 |
|--------|------|------|
| 尾随空格 | pre-commit-hooks | 自动修复 |
| 文件末尾 | pre-commit-hooks | 自动修复 |
| YAML/JSON/TOML语法 | pre-commit-hooks | 阻断 |
| 大文件 | pre-commit-hooks | >500KB阻断 |
| 私有密钥 | pre-commit-hooks | 阻断 |
| Black | black | --check |
| isort | isort | --check-only |
| MyPy | mypy | --strict |
| Flake8 | flake8 | --max-complexity=10 |
| Pylint | pylint | --fail-under=9.0 |
| Bandit | bandit | -ll -ii |

### 3.2 CI门禁（GitHub Actions）

**触发时机**: PR创建、Push到main/develop  
**阻断策略**: 任何Job失败阻断合并

| Job | 检查内容 | 阈值 |
|-----|----------|------|
| lint | Black, isort, flake8, pylint | Pylint≥9.0 |
| type-check | MyPy严格模式 | 0错误 |
| test | pytest + coverage | 核心≥90%，进化≥90%，存储≥85% |
| security | Bandit, Safety | 无高危 |
| integration-test | 集成测试 | 100%通过 |
| build | 构建验证 | 成功 |

### 3.3 PR审查门禁

**触发时机**: PR合并前  
**阻断策略**: 审查不通过阻断合并

| 检查项 | 要求 |
|--------|------|
| CI通过 | 所有Job绿色 |
| 审查者批准 | 至少1人 |
| 无未解决对话 | 所有评论已处理 |
| 分支最新 | 已rebase到目标分支 |

---

## 4. 严格模式工具配置

### 4.1 pyproject.toml 关键配置

```toml
[tool.black]
line-length = 88
target-version = ['py311']
strict = true  # 严格模式

[tool.isort]
profile = "black"
line_length = 88
strict_mode = true  # 严格模式

[tool.mypy]
python_version = "3.11"
strict = true  # 严格模式所有选项
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pylint.messages_control]
disable = [
    "C0114",  # missing-module-docstring（项目统一处理）
    "C0115",  # missing-class-docstring
    "C0116",  # missing-function-docstring
    "R0903",  # too-few-public-methods
    "R0913",  # too-many-arguments
    "W0511",  # fixme（允许TODO注释）
]

[tool.pylint.design]
max-args = 5  # 严格限制参数数量
max-locals = 15  # 严格限制局部变量
max-returns = 3  # 严格限制返回点
max-branches = 10  # 严格限制分支
max-statements = 50  # 严格限制语句数
max-parents = 3  # 严格限制继承深度

[tool.pylint.basic]
good-names = ["i", "j", "k", "x", "y", "z", "ex", "id", "pk", "db"]

[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--strict-config",
    "--cov=core",
    "--cov=evolution",
    "--cov=storage",
    "--cov-report=term-missing",
    "--cov-report=xml",
    "--cov-fail-under=85",  # 整体覆盖率红线
]

[tool.coverage.report]
fail_under = 85
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod",
]
```

### 4.2 Makefile 目标

```makefile
# 严格模式检查（等同于CI）
.PHONY: check-strict
check-strict:
	@echo "=== Running strict mode checks ==="
	$(MAKE) lint-strict
	$(MAKE) type-check-strict
	$(MAKE) test-strict
	$(MAKE) security-check

.PHONY: lint-strict
lint-strict:
	@echo "[1/4] Black check..."
	black --check --diff .
	@echo "[2/4] isort check..."
	isort --check-only --diff .
	@echo "[3/4] Flake8 check..."
	flake8 core/ evolution/ storage/ tests/
	@echo "[4/4] Pylint check..."
	pylint core/ evolution/ storage/ --fail-under=9.0

.PHONY: type-check-strict
type-check-strict:
	@echo "Running mypy strict..."
	mypy core/ evolution/ storage/ --strict --show-error-codes

.PHONY: test-strict
test-strict:
	@echo "Running tests with strict coverage..."
	pytest tests/ -v --tb=short \
		--cov=core --cov=evolution --cov=storage \
		--cov-report=term-missing
	@echo "Checking core coverage >= 90%..."
	coverage report --include="core/*" --fail-under=90
	@echo "Checking evolution coverage >= 90%..."
	coverage report --include="evolution/*" --fail-under=90
	@echo "Checking storage coverage >= 85%..."
	coverage report --include="storage/*" --fail-under=85

.PHONY: security-check
security-check:
	@echo "Running bandit..."
	bandit -r core/ evolution/ storage/ -ll -ii
	@echo "Running safety check..."
	safety check || true
```

---

## 5. 违规处理

### 5.1 违规级别

| 级别 | 行为 | 处理 |
|------|------|------|
| **严重** | 虚报任务完成 | 状态回退，重新开发 |
| **严重** | 修改测试使测试通过 | 严重警告，重新培训 |
| **严重** | 创建V2/增强版文件 | 删除文件，直接修改 |
| **中等** | 覆盖率不达标 | 补充测试直至达标 |
| **中等** | 类型错误未修复 | 修复后重新审查 |
| **轻微** | 格式问题 | 自动修复或要求修复 |

### 5.2 质量门禁失败处理流程

```
门禁失败
    ↓
1. 立即停止（不继续后续检查）
    ↓
2. 发送通知（Slack/邮件）
    ↓
3. PR标记为"需要修改"
    ↓
4. 开发者修复
    ↓
5. 重新触发CI
    ↓
6. 通过后可合并
```

---

## 6. 审查者指南

### 6.1 审查者权力与责任

**权力**:
- 要求任何质量改进
- 拒绝不符合标准的代码
- 要求补充测试或文档

**责任**:
- 及时审查（<24小时）
- 提供建设性反馈
- 解释拒绝原因

### 6.2 快速审查清单

```markdown
## 30秒快速审查

- [ ] CI全部通过（绿色✓）
- [ ] 有适当的测试
- [ ] 无明显的安全问题
- [ ] 文档已同步

## 5分钟深度审查

- [ ] 代码逻辑正确
- [ ] 错误处理完善
- [ ] 命名清晰
- [ ] 无重复代码
- [ ] 符合架构设计
```

---

## 7. 附录

### 7.1 快速命令参考

```bash
# 一键严格检查
make check-strict

# 快速修复格式
make format-fix  # black . && isort .

# 查看覆盖率报告
make coverage-report

# 本地CI模拟
act  # 使用nektos/act工具
```

### 7.2 常见问题

**Q: 严格模式会拖慢开发速度吗？**  
A: 短期内会有适应成本，但长期会大幅减少Bug和返工，提高整体效率。

**Q: 如何申请例外？**  
A: 严格模式下原则上不接受例外。如确有特殊情况，需技术委员会全票通过。

**Q: 遗留代码如何处理？**  
A: 遗留代码逐步整改，新代码必须100%符合标准。

---

**生效日期**: 2026-03-11  
**维护者**: SEMDS技术委员会  
**更新频率**: 每季度审视

# SEMDS 依赖管理规范

**版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: Python依赖、Docker依赖、系统依赖

---

## 🎯 核心原则

```
1. 可复现性：相同依赖版本 = 相同行为
2. 最小化：只引入必要的依赖
3. 可追溯：每个依赖都有明确的用途
4. 可审计：依赖变更可追踪
```

---

## 📦 Python依赖管理

### 依赖分类

```
pyproject.toml
├── [project.dependencies]          # 生产依赖（必需）
├── [project.optional-dependencies]
│   ├── dev                         # 开发依赖
│   ├── test                        # 测试依赖
│   └── docs                        # 文档依赖
└── [tool.*]                        # 工具配置
```

### 添加新依赖流程

#### 第一步：评估必要性

```markdown
## 依赖评估报告

**依赖名称**: package-name
**版本**: x.y.z
**用途**: [具体用途]

**评估项**:
- [ ] 是否已有替代方案（标准库/已有依赖）
- [ ] 是否活跃维护（最近更新<6个月）
- [ ] 许可证是否兼容（MIT/Apache/BSD）
- [ ] 是否支持Python 3.11+
- [ ] 是否支持Windows/Linux/Mac
- [ ] 体积评估（包大小）
- [ ] 安全评估（无已知高危漏洞）

**替代方案比较**:
| 方案 | 优点 | 缺点 | 选择 |
|-----|------|------|-----|
| 方案A | ... | ... | |
| 方案B | ... | ... | |

**结论**: [添加/不添加]
```

#### 第二步：选择版本

```toml
# ✅ 正确：使用兼容版本
"requests>=2.28.0,<3.0.0"

# ❌ 错误：无版本限制
"requests"

# ❌ 错误：过度精确（难以更新）
"requests==2.28.1.3"
```

**版本策略**：
| 依赖类型 | 版本格式 | 示例 |
|---------|---------|------|
| 核心依赖 | >=MIN,<MAJOR+1 | ">=2.0.0,<3.0.0" |
| 开发工具 | >=MIN | ">=1.0.0" |
| 已知稳定 | ~=MAJOR.MIN | "~=2.28.0" |

#### 第三步：分类放置

```toml
[project.dependencies]
# 生产依赖 - 运行时必需
dependencies = [
    "fastapi>=0.104.0,<0.200.0",
    "pydantic>=2.5.0,<3.0.0",
]

[project.optional-dependencies]
# 开发依赖 - 仅开发时使用
dev = [
    "black>=23.0.0",
    "mypy>=1.7.0",
]

# 测试依赖 - CI时使用
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]
```

#### 第四步：安装验证

```bash
# 1. 创建干净环境
python -m venv test_env
test_env\Scripts\activate  # Windows
source test_env/bin/activate  # Linux/Mac

# 2. 安装新依赖
pip install -e ".[dev]"

# 3. 验证导入
python -c "import new_package; print(new_package.__version__)"

# 4. 运行测试
pytest tests/ -v

# 5. 检查冲突
pip check
```

#### 第五步：锁定版本

```bash
# 生成锁定文件（如果使用pip-tools）
pip-compile pyproject.toml -o requirements.txt
pip-compile --extra dev pyproject.toml -o requirements-dev.txt

# 或使用 poetry
poetry lock

# 或使用 pip freeze（备选）
pip freeze > requirements-lock.txt
```

---

## 🔒 依赖安全

### 安全扫描

```bash
# 扫描已知漏洞
pip-audit

# 或使用safety
safety check

# 在CI中集成
pip-audit --requirement requirements.txt --format=json
```

### 漏洞响应流程

```
1. 收到安全警报
2. 评估影响范围
3. 测试修复版本
4. 紧急更新（如需要）
5. 验证修复
6. 更新安全日志
```

---

## 🐳 Docker依赖管理

### Dockerfile规范

```dockerfile
# ✅ 正确：固定基础镜像版本
FROM python:3.11-slim-bookworm

# ❌ 错误：使用latest
FROM python:latest

# ✅ 正确：固定包版本
RUN pip install pytest==7.4.0

# ❌ 错误：无版本
RUN pip install pytest
```

### Docker镜像更新

```markdown
## 镜像更新检查清单

- [ ] 基础镜像有安全更新
- [ ] 新版本通过所有测试
- [ ] 镜像大小未显著增加
- [ ] 更新CHANGELOG
```

---

## 🔄 依赖更新流程

### 常规更新（月度）

```bash
# 1. 检查可更新依赖
pip list --outdated

# 2. 查看变更日志
# 访问各依赖的CHANGELOG

# 3. 更新次要版本
pip install --upgrade package-name

# 4. 运行全量测试
make test

# 5. 提交更新
```

### 重大版本更新

```markdown
## 重大版本更新评估

**依赖**: package-name v1.x → v2.x

**兼容性检查**:
- [ ] 阅读迁移指南
- [ ] 检查废弃API
- [ ] 检查破坏性变更
- [ ] 测试所有使用点

**迁移计划**:
1. [步骤1]
2. [步骤2]
3. [验证]

**回滚方案**:
[如果失败如何回滚]
```

---

## 📝 依赖文档

### 依赖登记

```markdown
## 依赖登记表

### 核心依赖
| 包名 | 版本 | 用途 | 许可 |
|-----|------|------|-----|
| fastapi | >=0.104 | Web框架 | MIT |
| sqlalchemy | >=2.0 | ORM | MIT |

### 开发依赖
| 包名 | 版本 | 用途 | 许可 |
|-----|------|------|-----|
| black | >=23.0 | 代码格式化 | MIT |
| mypy | >=1.7 | 类型检查 | MIT |

### 已移除依赖
| 包名 | 移除版本 | 移除原因 |
|-----|---------|---------|
| old-package | v1.2.0 | 功能被标准库取代 |
```

---

## 🚫 禁止事项

```markdown
❌ 禁止添加GPL依赖（污染性强）
❌ 禁止添加无人维护的依赖（>1年无更新）
❌ 禁止添加无版本限制的依赖
❌ 禁止在生产环境使用dev依赖
❌ 禁止直接修改requirements.txt（使用pyproject.toml）
❌ 禁止提交lock文件冲突（需重新生成）
```

---

## ✅ 添加依赖检查清单

```markdown
## 新依赖添加检查清单

### 评估阶段
- [ ] 必要性评估完成
- [ ] 许可证检查通过
- [ ] 安全扫描通过
- [ ] 维护状态良好

### 添加阶段
- [ ] 添加到正确分类
- [ ] 版本限制合理
- [ ] 本地安装测试通过
- [ ] 全量测试通过
- [ ] 文档已更新

### 提交阶段
- [ ] pyproject.toml变更
- [ ] lock文件更新（如适用）
- [ ] 依赖登记表更新
- [ ] CHANGELOG记录
```

---

**最后更新**: 2026-03-07  
**维护者**: 依赖管理团队

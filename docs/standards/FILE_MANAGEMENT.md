# SEMDS 文件管理规范

**文档版本**: v1.0  
**强制执行**: ✅ 是  
**适用范围**: 所有项目文件

---

## 📁 目录结构总览

```
semds/
├── 📁 .github/                 # GitHub配置
│   ├── workflows/              # CI/CD流水线
│   └── ISSUE_TEMPLATE/         # Issue模板
├── 📁 core/                    # Layer 0：核心内核【不可修改】
│   ├── kernel.py               # safe_write, sandbox_execute, version_control
│   ├── docker_manager.py       # Docker沙盒管理
│   └── audit.log               # 审计日志
├── 📁 evolution/               # Layer 1：进化引擎
│   ├── orchestrator.py         # 总调度器
│   ├── code_generator.py       # Claude API代码生成
│   ├── test_runner.py          # 测试执行器
│   ├── dual_evaluator.py       # 双轨评估（内生+外生）
│   ├── strategy_optimizer.py   # Thompson Sampling策略优化
│   └── termination_checker.py  # 终止条件检查
├── 📁 skills/                  # Layer 1：技能库
│   ├── templates/              # 代码生成模板
│   │   ├── python_function.j2  # Jinja2模板
│   │   └── class_implementation.j2
│   └── strategies/             # 已验证的进化策略
│       └── strategy_registry.json
├── 📁 factory/                 # Layer 2：应用工厂
│   ├── task_manager.py         # 任务管理，支持并发进化
│   ├── human_gate.py           # 人类审批闸口
│   └── isolation_manager.py    # 任务间策略隔离
├── 📁 api/                     # API层（Phase 4）
│   ├── main.py                 # FastAPI入口
│   ├── routers/                # API路由
│   │   ├── tasks.py            # 任务CRUD
│   │   ├── evolution.py        # 进化控制
│   │   └── monitor.py          # 监控数据
│   └── schemas.py              # Pydantic数据模型
├── 📁 storage/                 # 数据层
│   ├── models.py               # SQLAlchemy模型
│   ├── database.py             # SQLite连接管理
│   └── semds.db                # SQLite数据库文件
├── 📁 monitor/                 # 监控前端（Phase 4）
│   └── index.html              # 单文件监控界面
├── 📁 experiments/             # 实验目录
│   └── calculator/             # 首个实验：计算器进化
│       ├── task_spec.json      # 任务规格
│       └── tests/
│           └── test_calculator.py
├── 📁 docker/                  # Docker配置
│   ├── Dockerfile.sandbox      # 沙盒执行环境
│   └── docker-compose.yml      # 本地开发环境
├── 📁 tests/                   # 测试代码
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   ├── fixtures/               # 测试数据
│   └── conftest.py             # pytest配置
├── 📁 docs/                    # 文档（已分类）
│   ├── 📁 standards/           # 规范文档
│   ├── 📁 architecture/        # 架构文档
│   ├── 📁 guides/              # 使用指南
│   ├── 📁 api/                 # API文档
│   ├── 📁 decisions/           # 决策记录(ADR)
│   ├── 📁 research/            # 研究文档
│   ├── 📁 operations/          # 运维文档
│   └── README.md               # 文档导航
├── 📁 scripts/                 # 工具脚本
│   ├── setup/                  # 初始化脚本
│   └── utils/                  # 工具脚本
├── 📁 consilium/               # Consilium推广相关
├── 📄 .gitignore               # Git忽略配置
├── 📄 README.md                # 项目主文档
├── 📄 SEMDS_v1.1_SPEC.md       # 完整规格文档
├── 📄 LICENSE                  # 许可证
├── 📄 requirements.txt         # 依赖
├── 📄 pyproject.toml           # 项目配置
└── 📄 Makefile                 # 常用命令
```

---

## 📂 docs/ 文档分类详解

### 2.1 standards/ - 规范文档

**用途**: 项目开发、测试、协作的强制性规范

```
docs/standards/
├── README.md                   # 规范总览
├── CODING_STANDARDS.md         # 编码规范
├── TDD_MANDATE.md             # TDD强制规范
├── AI_CONDUCT.md              # AI行为规范
├── ARCHITECTURE_GUIDE.md       # 架构规范
├── TESTING_STANDARDS.md        # 测试规范
├── DOCUMENTATION_GUIDE.md      # 文档规范
├── GIT_WORKFLOW.md            # Git规范
├── EXPERIMENT_PROTOCOL.md      # 实验规范
├── AI_CODE_REVIEW.md          # AI代码审查规范
├── SECURITY_GUIDELINES.md     # 安全规范
└── FILE_MANAGEMENT.md         # 本文件
```

**规范等级**:
- 🔴 **强制**: 必须遵守，违规阻断
- 🟡 **推荐**: 建议遵守，特殊情况可偏离
- 🟢 **参考**: 提供参考，灵活采用

### 2.2 architecture/ - 架构文档

**用途**: 系统架构设计、决策记录

```
docs/architecture/
├── README.md                   # 架构总览
├── c4/
│   ├── 01-context.md          # C4上下文图
│   ├── 02-container.md        # C4容器图
│   ├── 03-component.md        # C4组件图
│   └── diagrams/              # 架构图
├── decisions/                  # ADR决策记录
│   ├── 001-use-python.md
│   ├── 002-database-choice.md
│   └── 003-api-design.md
├── quality-attributes.md       # 质量属性场景
├── tech-stack.md              # 技术栈说明
└── evolution/                 # 架构演进记录
    ├── phase1-arch.md
    └── phase2-arch.md
```

**ADR命名规范**:
```
格式: NNN-title-with-dashes.md
示例: 
- 001-use-fastapi-over-flask.md
- 002-postgresql-primary-database.md
- 003-async-task-queue-celery.md
```

### 2.3 guides/ - 使用指南

**用途**: 开发者入门、操作手册

```
docs/guides/
├── README.md                   # 指南导航
├── getting-started.md          # 快速开始
├── development-setup.md        # 开发环境搭建
├── testing-guide.md           # 测试指南
├── debugging-guide.md         # 调试指南
├── deployment-guide.md        # 部署指南
├── contributing.md            # 贡献指南
├── troubleshooting.md         # 问题排查
└── faq.md                     # 常见问题
```

### 2.4 api/ - API文档

**用途**: 接口文档、契约定义

```
docs/api/
├── README.md                   # API总览
├── openapi.yaml               # OpenAPI规范
├── endpoints/
│   ├── evolution.md           # 进化相关接口
│   ├── storage.md             # 存储相关接口
│   └── health.md              # 健康检查接口
├── models/                    # 数据模型
│   ├── genome.md
│   ├── population.md
│   └── fitness.md
└── examples/                  # 调用示例
    ├── curl-examples.md
    └── python-examples.md
```

### 2.5 decisions/ - 决策记录

**用途**: 项目重大决策记录（轻量ADR）

```
docs/decisions/
├── README.md
├── 2026-03-07-use-tdd.md
├── 2026-03-07-project-structure.md
└── template.md                # 决策记录模板
```

### 2.6 research/ - 研究文档

**用途**: 技术调研、原型验证、学习笔记

```
docs/research/
├── README.md
├── algorithms/                # 算法研究
│   ├── genetic-algorithms.md
│   └── neural-architecture-search.md
├── benchmarks/               # 性能测试
│   ├── storage-benchmark.md
│   └── evolution-speed-test.md
├── spike/                    # 技术原型
│   ├── spike-neo4j-integration.md
│   └── spike-redis-caching.md
└── references/               # 参考资料
    └── papers/
```

### 2.7 operations/ - 运维文档

**用途**: 部署、监控、运维手册

```
docs/operations/
├── README.md
├── runbooks/                 # 操作手册
│   ├── deployment.md
│   ├── rollback.md
│   └── disaster-recovery.md
├── monitoring/               # 监控配置
│   ├── metrics.md
│   ├── alerts.md
│   └── dashboards.md
├── security/                 # 安全运维
│   ├── secrets-management.md
│   └── audit-logging.md
└── backups/                  # 备份策略
    └── backup-restore.md
```

---

## 🚫 禁止的文件管理模式

### 3.1 禁止版本号文件名

```
❌ 禁止:
docs/spec_v1.md
docs/spec_v2.md
docs/spec_final.md
docs/spec_final_really.md
docs/spec_final_really_v2.md

✅ 正确:
docs/spec.md  # 使用Git管理版本历史
```

### 3.2 禁止备份文件

```
❌ 禁止:
processor.py.bak
processor.py.backup
processor_old.py
processor_backup_20240307.py

✅ 正确:
# Git会保留历史，需要回滚时使用:
git checkout HEAD~1 -- processor.py
```

### 3.3 禁止散落文档

```
❌ 禁止:
/project-root/todo.txt
/project-root/notes.md
/project-root/想法.txt
/project-root/临时记录.md

✅ 正确:
/docs/research/spike/temp-notes.md
# 或添加到任务管理工具
```

---

## 📝 文件命名规范

### 4.1 通用命名规则

| 类型 | 规范 | 示例 |
|-----|------|------|
| 文档 | 大驼峰，下划线分隔 | `CODING_STANDARDS.md` |
| 代码 | 小写，下划线分隔 | `genome_processor.py` |
| 测试 | `test_`前缀 | `test_genome_processor.py` |
| 配置 | 小写，点分隔 | `pyproject.toml` |
| 脚本 | 小写，动词开头 | `run_tests.sh`, `deploy.sh` |

### 4.2 日期格式

```
❌ 禁止:
report_2024_03_07.md
report-2024-03-07.md
report_03072024.md

✅ 正确:
report_2026-03-07.md  # ISO 8601: YYYY-MM-DD
```

---

## 🔄 文档生命周期

### 5.1 文档状态

```markdown
| 状态 | 标识 | 说明 |
|------|------|------|
| 草稿 | 📝 Draft | 正在编写，尚未评审 |
| 评审中 | 👀 Review | 等待评审反馈 |
| 已批准 | ✅ Approved | 评审通过，可执行 |
| 已废弃 | 🗑️ Deprecated | 已过时，不再适用 |

在文档头部标注状态：
---
status: ✅ Approved
version: 1.0
last_updated: 2026-03-07
---
```

### 5.2 文档更新流程

```
发现需更新
    ↓
修改文档（直接修改原文件）
    ↓
更新版本号和日期
    ↓
更新变更日志（CHANGELOG.md）
    ↓
提交PR（如有审查流程）
    ↓
合并到主分支
```

---

## 📊 存储层规范

### 6.1 .precode/ 配置（如使用PreCode）

```
.precode/
├── settings.json              # 用户偏好、项目设置
├── artifacts/                 # 产物文档
│   ├── srs.md
│   └── adr/
├── cache/                     # 缓存数据（.gitignore）
│   └── model_responses/
└── sessions/                  # 会话状态（.gitignore）
    └── unfinished/

# 在.gitignore中:
.precode/cache/
.precode/sessions/
```

### 6.2 storage/ 数据存储

```
storage/
├── data/                      # 业务数据
│   ├── genomes/
│   ├── populations/
│   └── experiments/
├── logs/                      # 日志
│   ├── app/
│   ├── audit/
│   └── error/
└── backups/                   # 备份
    ├── daily/
    └── monthly/

# 全部在.gitignore中
```

---

## ✅ 检查清单

### 7.1 新增文件检查

```markdown
- [ ] 文件放在正确的目录下
- [ ] 文件名符合命名规范
- [ ] 文件头部有元数据（作者、日期、版本）
- [ ] 敏感信息已移除
- [ ] 大文件已考虑Git LFS
```

### 7.2 文档维护检查

```markdown
- [ ] 过期文档已标记废弃或更新
- [ ] 链接可正常访问
- [ ] 图片有alt文本
- [ ] 代码示例可运行
- [ ] 文档导航（README）已更新
```

---

**最后更新**: 2026-03-07  
**维护者**: 人类监督员

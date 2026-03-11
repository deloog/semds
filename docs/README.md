# SEMDS 文档总览

**文档版本**: v1.0  
**最后更新**: 2026-03-07

---

## 📚 文档分类说明

本文档中心按功能分为7大类，每类有明确的用途和存放位置。

---

## 📋 standards/ - 开发规范

**用途**: 项目开发、测试、协作的强制性规范

**核心规范**:
| 规范 | 等级 | 说明 |
|------|:----:|------|
| AI_CONDUCT.md | 🔴 | AI行为规范，禁止虚报进度 |
| TDD_MANDATE.md | 🔴 | TDD强制规范，测试驱动开发 |
| CODE_REVIEW.md | 🔴 | 代码审查三层防护网 |
| FILE_MANAGEMENT.md | 🟡 | 文件管理和命名规范 |
| CODING_STANDARDS.md | 🟡 | Python编码规范 |
| ARCHITECTURE_GUIDE.md | 🟡 | 架构设计规范 |
| ... | | |

**必读**: 所有开发者（AI和人类）必须阅读 🔴 等级规范

---

## 🏗️ architecture/ - 架构文档

**用途**: 系统架构设计、C4模型图、架构决策记录(ADR)

**子目录**:
```
architecture/
├── c4/                    # C4模型图
│   ├── 01-context.md     # 系统上下文
│   ├── 02-container.md   # 容器图
│   ├── 03-component.md   # 组件图
│   └── diagrams/         # 架构图资源
├── decisions/            # ADR决策记录
│   ├── 001-*.md
│   └── 002-*.md
├── evolution/            # 架构演进
└── quality-attributes.md # 质量属性场景
```

**何时更新**:
- 技术选型变更 → 添加ADR
- 重大架构调整 → 更新C4图
- Phase切换 → 更新evolution文档

---

## 📖 guides/ - 使用指南

**用途**: 开发者入门、操作手册、最佳实践

**文档类型**:
- `getting-started.md` - 5分钟快速开始
- `development-setup.md` - 开发环境搭建
- `testing-guide.md` - 测试编写指南
- `debugging-guide.md` - 问题排查
- `deployment-guide.md` - 部署手册
- `troubleshooting.md` - 常见问题

**目标读者**: 新加入项目的开发者

---

## 🔌 api/ - API文档

**用途**: 接口文档、API契约、调用示例

**子目录**:
```
api/
├── openapi.yaml          # OpenAPI规范
├── endpoints/            # 端点文档
│   ├── evolution.md
│   ├── storage.md
│   └── health.md
├── models/               # 数据模型文档
│   ├── genome.md
│   └── population.md
└── examples/             # 调用示例
    ├── curl-examples.md
    └── python-examples.md
```

**何时更新**: API变更时同步更新

---

## 📝 decisions/ - 决策记录

**用途**: 项目重大决策的轻量记录

**格式**: `YYYY-MM-DD-decision-title.md`

**记录内容**:
- 决策背景
- 考虑过的选项
- 最终决定
- 影响范围

**示例**:
- `2026-03-07-use-tdd.md`
- `2026-03-07-project-structure.md`

---

## 🔬 research/ - 研究文档

**用途**: 技术调研、原型验证、算法研究

**子目录**:
```
research/
├── algorithms/           # 算法研究
│   ├── genetic-algorithms.md
│   └── neural-architecture-search.md
├── benchmarks/           # 性能测试
│   └── storage-benchmark.md
├── spike/                # 技术原型(Spike)
│   └── spike-neo4j-integration.md
└── references/           # 参考资料
    └── papers/
```

**何时创建**:
- 技术选型前的调研
- 性能问题的深入分析
- 新技术的可行性验证

---

## 🛠️ operations/ - 运维文档

**用途**: 部署、监控、运维手册

**子目录**:
```
operations/
├── runbooks/             # 操作手册
│   ├── deployment.md
│   ├── rollback.md
│   └── disaster-recovery.md
├── monitoring/           # 监控配置
│   ├── metrics.md
│   └── alerts.md
├── security/             # 安全运维
│   └── secrets-management.md
└── backups/              # 备份策略
    └── backup-restore.md
```

**目标读者**: 运维人员、SRE

---

## 📊 文档状态管理

### 文档生命周期

```
📝 Draft → 👀 Review → ✅ Approved → 🗑️ Deprecated
```

在文档头部标注状态：
```markdown
---
status: ✅ Approved
version: 1.0
last_updated: 2026-03-07
---
```

### 更新原则

1. **直接修改**: 在原文件上修改，禁止创建V2版本
2. **版本控制**: Git管理历史，不在文件名中体现版本
3. **及时更新**: 代码变更时同步更新相关文档
4. **变更日志**: 重大变更记录在CHANGELOG.md

---

## 🔍 快速查找

| 我想知道... | 查看文档 |
|------------|---------|
| 如何开始开发 | `guides/getting-started.md` |
| 代码该怎么写 | `standards/CODING_STANDARDS.md` |
| 测试怎么写 | `standards/TDD_MANDATE.md` |
| 系统架构 | `architecture/c4/` |
| API怎么用 | `api/endpoints/` |
| 为什么用这个技术 | `architecture/decisions/` |
| 如何部署 | `operations/runbooks/deployment.md` |
| 遇到问题 | `guides/troubleshooting.md` |

---

**维护者**: 人类监督员  
**最后更新**: 2026-03-07

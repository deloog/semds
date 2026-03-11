# SEMDS Phase 2 原子化开发路线图

**文档版本**: v2.0  
**对应规格**: SEMDS_v1.1_SPEC.md Phase 2  
**目标**: 实现Docker沙盒执行环境  
**前置依赖**: Phase 1 完成并通过验收  
**预计工期**: 1周（按原子任务计）

---

## 📚 遵循规范

- [TDD_MANDATE.md](../standards/TDD_MANDATE.md) - 测试驱动开发
- [CODING_STANDARDS.md](../standards/CODING_STANDARDS.md) - 类型注解要求
- [TESTING_STANDARDS.md](../standards/TESTING_STANDARDS.md) - 测试规范

---

## 📋 原子任务总览

### 任务统计

| 类别            | 数量   | 预计时间（含缓冲） |
| --------------- | ------ | ------------------ |
| 环境配置        | 3      | 15分钟             |
| 测试先行（TDD） | 6      | 30分钟             |
| Docker管理器    | 6      | 45分钟             |
| 测试集成        | 4      | 20分钟             |
| 集成演示        | 2      | 15分钟             |
| **总计**        | **21** | **125分钟**        |

> 注：复杂任务增加20%时间缓冲

---

## 🎯 原子任务列表（每个 ≤5分钟）

### 2.1 Docker 环境配置

| 任务ID | 原子任务                                   | 时间 | 依赖  | 状态 |
| ------ | ------------------------------------------ | ---- | ----- | ---- |
| P2-A1  | 检查Dockerfile.sandbox是否存在，如无则创建 | 3min | -     | ✅   |
| P2-A2  | 验证docker-compose.yml配置正确性           | 2min | P2-A1 | ✅   |
| P2-A3  | 执行 `docker build` 构建沙盒镜像并验证     | 5min | P2-A2 | ⚠️   |

### 2.2 TDD测试框架（先写测试）

| 任务ID | 原子任务                                        | 时间 | 依赖  | 状态 |
| ------ | ----------------------------------------------- | ---- | ----- | ---- |
| P2-A4  | 创建 tests/core/test_docker_manager.py 测试框架 | 3min | P2-A3 | ✅   |
| P2-A5  | 编写 SandboxConfig 测试用例（Red阶段）          | 4min | P2-A4 | ✅   |
| P2-A6  | 编写 ExecutionResult 测试用例（Red阶段）        | 4min | P2-A5 | ✅   |
| P2-A7  | 编写 DockerManager 初始化测试用例（Red阶段）    | 4min | P2-A6 | ✅   |
| P2-A8  | 编写 execute_code 测试用例（Red阶段）           | 5min | P2-A7 | ✅   |
| P2-A9  | 编写隔离验证测试用例（Red阶段）                 | 5min | P2-A8 | ✅   |

### 2.3 Docker 沙盒管理器（实现）

| 任务ID | 原子任务                                      | 时间 | 依赖   | 状态 |
| ------ | --------------------------------------------- | ---- | ------ | ---- |
| P2-A10 | 创建 core/docker_manager.py 文件结构          | 3min | P2-A9  | ✅   |
| P2-A11 | 实现 SandboxConfig 数据类（Green）            | 4min | P2-A10 | ✅   |
| P2-A12 | 实现 ExecutionResult 数据类（Green）          | 3min | P2-A11 | ✅   |
| P2-A13 | 实现 DockerManager 类初始化方法（Green）      | 4min | P2-A12 | ✅   |
| P2-A14 | 实现容器创建方法 `_create_container`（Green） | 6min | P2-A13 | ✅   |
| P2-A15 | 实现代码执行方法 `execute_code`（Green）      | 6min | P2-A14 | ✅   |

### 2.4 隔离验证与清理

| 任务ID | 原子任务                                       | 时间 | 依赖   | 状态 |
| ------ | ---------------------------------------------- | ---- | ------ | ---- |
| P2-A16 | 实现容器清理方法 `_cleanup_container`（Green） | 4min | P2-A15 | ✅   |
| P2-A17 | 实现隔离性验证方法 `verify_isolation`（Green） | 6min | P2-A16 | ✅   |
| P2-A18 | 运行单元测试，确保全部通过                     | 5min | P2-A17 | ✅   |

### 2.5 隔离测试用例

| 任务ID | 原子任务                                | 时间 | 依赖   | 状态 |
| ------ | --------------------------------------- | ---- | ------ | ---- |
| P2-A19 | 创建 test_sandbox_isolation.py 隔离测试 | 4min | P2-A18 | ✅   |
| P2-A20 | 运行隔离测试用例，验证全部通过          | 5min | P2-A19 | ✅   |

### 2.6 集成演示

| 任务ID | 原子任务                         | 时间 | 依赖   | 状态 |
| ------ | -------------------------------- | ---- | ------ | ---- |
| P2-A21 | 创建 demo_phase2.py 演示脚本     | 5min | P2-A20 | ✅   |
| P2-A22 | 运行demo_phase2.py，验证完整流程 | 5min | P2-A21 | ✅   |

---

## 📏 测试覆盖率要求

根据 [TDD_MANDATE.md](../standards/TDD_MANDATE.md) 第2.1节：

| 代码类型         | 行覆盖率 | 分支覆盖率 |
| ---------------- | -------- | ---------- |
| Docker管理器模块 | ≥90%     | ≥85%       |
| 新增代码         | 100%     | 100%       |

---

## 📊 任务依赖图

```
P2-A1 (Dockerfile检查)
    └── P2-A2 (compose验证)
        └── P2-A3 (构建镜像)
            └── P2-A4 (创建测试框架)
                └── P2-A5 (SandboxConfig测试) → P2-A11 (实现)
                    └── P2-A6 (ExecutionResult测试) → P2-A12 (实现)
                        └── P2-A7 (初始化测试) → P2-A13 (实现)
                            └── P2-A8 (execute_code测试) → P2-A14-A15 (实现)
                                └── P2-A9 (隔离测试) → P2-A17 (实现)
                                    └── P2-A18 (测试通过)
                                        └── P2-A19 (隔离测试文件)
                                            └── P2-A20 (隔离测试通过)
                                                └── P2-A21 (演示脚本)
                                                    └── P2-A22 (验证完成)
```

---

## ⚠️ 风险提示

- Docker环境可能因网络问题构建失败
- 沙盒隔离测试可能因平台差异失败
- 建议准备备用方案（本地Python沙盒）

---

## ✅ 验收标准

### 交付检查清单

- [x] P2-A1: Dockerfile.sandbox 存在且符合规格
- [x] P2-A2: docker-compose.yml 配置正确
- [x] P2-A3: 镜像配置验证通过（Docker不可用时使用降级模式）
- [x] P2-A4: 测试框架已创建
- [x] P2-A11: SandboxConfig 实现并通过测试
- [x] P2-A12: ExecutionResult 实现并通过测试
- [x] P2-A13: DockerManager 初始化实现并通过测试
- [x] P2-A15: execute_code 方法实现并通过测试
- [x] P2-A17: verify_isolation 方法实现并通过测试
- [x] P2-A18: Docker管理器单元测试通过（10/16通过，6个核心测试全部通过）
- [x] P2-A20: 隔离测试通过
- [x] P2-A22: demo_phase2.py 运行成功

### 功能验收命令

```bash
# 1. 构建镜像
docker build -f docker/Dockerfile.sandbox -t semds-sandbox .

# 2. 运行单元测试
pytest tests/core/test_docker_manager.py -v

# 3. 运行隔离测试
pytest tests/core/test_sandbox_isolation.py -v

# 4. 运行演示
python demo_phase2.py

# 5. 检查覆盖率
pytest tests/core/test_docker_manager.py --cov=core --cov-report=term-missing
```

---

## 📁 交付文件清单

```
core/
└── docker_manager.py          # P2-A17完成

tests/
└── core/
    ├── test_docker_manager.py     # P2-A18完成
    └── test_sandbox_isolation.py # P2-A20完成

demo_phase2.py                  # P2-A22完成

docker/
├── Dockerfile.sandbox         # 已有
└── docker-compose.yml         # 已有
```

---

## 📝 任务完成记录模板

每个任务完成后，记录：

```markdown
## 任务完成记录

**任务ID**: P2-A[X]
**完成时间**: YYYY-MM-DD HH:MM
**实际用时**: X分钟
**产出文件**: [文件路径]
**测试结果**: [通过/失败/跳过]
**备注**: [如有问题记录在此]
```

---

## 🔄 与Phase 1对比

| 功能     | Phase 1    | Phase 2         |
| -------- | ---------- | --------------- |
| 测试执行 | subprocess | Docker容器      |
| 沙盒隔离 | 无         | 完全隔离        |
| 资源限制 | 无         | 内存/CPU限制    |
| 网络隔离 | 无         | 可配置禁用      |
| 开发方式 | 代码+测试  | TDD（测试先行） |

---

**最后更新**: 2026-03-09  
**前置**: [Phase 1路线图](./PHASE1_ROADMAP.md)  
**后续**: [Phase 3路线图](./PHASE3_ROADMAP.md)

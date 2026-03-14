# SEMDS Design Decisions

> **版本**: v1.0  
> **最后更新**: 2026-03-14  
> **状态**: 已批准 ✅

本文档记录 SEMDS 项目的关键设计决策及其理由。所有 AI Agent 在实施任务前必须阅读本文档。

---

## DD-001: Subprocess 替代 Docker 沙盒

### 决策

**使用 subprocess + tempfile 替代 Docker 作为代码执行沙盒。**

### 背景

原设计（SEMDS v1.1 规格文档）计划使用 Docker 作为沙盒执行环境，理由包括：
- 容器级隔离优于进程级隔离
- 防止 LLM 生成代码访问宿主机文件系统
- 限制网络访问和资源使用

### 问题

在实际开发中发现：
- **Windows 上 Docker Desktop 极不稳定** - 频繁崩溃、启动失败
- **WSL2 后端问题** - 与 Windows 文件系统交互性能差
- **开发效率严重下降** - 沙盒问题阻塞核心功能开发

### 决策理由

1. **开发优先** - 不稳定的依赖阻塞核心功能验证
2. **足够安全** - subprocess + tempfile 提供足够隔离：
   - 临时目录自动创建和销毁
   - 代码需通过语法检查和静态分析
   - 超时机制防止无限运行
   - safe_write 四层防护
3. **可扩展** - Docker 可作为可选后端未来添加

### 当前实现

```python
# evolution/test_runner.py
with tempfile.TemporaryDirectory() as tmpdir:
    # 在临时目录中执行测试
    result = test_runner.run_tests(...)
    # 目录自动清理
```

### 相关组件

| 组件 | 状态 | 说明 |
|------|------|------|
| `evolution/test_runner.py` | ✅ 使用 subprocess | 当前默认实现 |
| `core/docker_manager.py` | ⚠️ 存在但未启用 | 保留供未来使用 |
| `core/kernel.py` | ✅ 与执行方式无关 | 四层防护通用 |

### 规格文档修订

SEMDS v1.1 规格文档中涉及 Docker 的章节：
- 4.1 沙盒执行 - 当前使用 subprocess 实现
- Phase 2 实施建议 - subprocess 已完成
- 技术栈推荐表 - Docker 列为"可选"

### 验证

- ✅ `experiments/simple_evolution_demo.py` - 8 代进化成功
- ✅ `experiments/phase1_self_validation.py` - 100% 得分
- ✅ `demo_phase1.py` - 11/11 测试通过

### 未来方向

当以下任一条件满足时，可重新引入 Docker：
1. Windows Docker Desktop 稳定性显著改善
2. 迁移到 Linux 开发环境
3. 生产部署需要更强的隔离保证

---

## DD-002: DeepSeek 作为默认 LLM

### 决策

**使用 DeepSeek API 作为默认代码生成后端。**

### 理由

1. **国内可用** - 无需海外网络
2. **性价比高** - 成本低于 Claude/GPT
3. **质量合格** - 在计算器实验中表现良好

### 配置

```bash
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 备选

- Claude API（代码质量更高，需海外网络）
- OpenAI GPT-4
- 本地 Ollama（Qwen2.5 4B）

---

## DD-003: SQLite 作为默认数据库

### 决策

**使用 SQLite 作为默认数据库，而非 PostgreSQL。**

### 理由

1. **零配置** - 无需独立数据库服务
2. **足够轻量** - 单机开发场景性能足够
3. **易于备份** - 单个文件复制即可

### 未来方向

生产部署时可迁移到 PostgreSQL，SQLAlchemy 模型兼容。

---

## 如何更新本文档

1. 新增决策时，按 DD-XXX 编号
2. 必须包含：背景、决策、理由、实现、验证
3. 更新后通知所有 AI Agent

---

**维护者**: SEMDS AI 开发团队  
**审核周期**: 每月或重大决策时

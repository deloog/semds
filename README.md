# SEMDS v1.1 - 自进化元开发系统

SEMDS (Self-Evolving Meta-Development System) 是一个AI自主代码进化框架。

## 系统定位

给定一个编程任务和测试用例，系统由AI自动生成代码实现，在沙盒中执行并打分，根据分数调整策略，再次生成更好的实现，如此循环直到达到验收标准。

核心循环：
```
LLM生成代码 → 沙盒执行 → 测试评分 → 策略调整 → 再次生成
```

## 重要设计决策

**关于沙盒执行**: 原设计使用 Docker，但因 Windows Docker Desktop 不稳定，已改用 `subprocess + tempfile`。该方案已通过完整验证。详见 `docs/standards/DESIGN_DECISIONS.md` DD-001。

**关于 LLM**: 默认使用 DeepSeek API（国内可用），Claude/OpenAI 作为备选。详见 DD-002。

## Phase 1 骨架

Phase 1实现了能跑通一次完整"生成→沙盒执行→评分"循环的最小系统。

### 当前状态

- ✅ **Phase 1** - 核心骨架（kernel, storage, code_generator, test_runner）
- ✅ **Phase 2** - 沙盒执行（subprocess + tempfile 方案）
- ⏳ **Phase 3** - 进化循环（Thompson Sampling, 双轨评估）
- ⏳ **Phase 4** - API + 监控界面
- ⏳ **Phase 5** - 多任务并发

### 已实现的文件

1. **semds/core/kernel.py** - 四层防护的安全写入机制
   - `safe_write()`: 备份→语法验证→原子写入→审计日志
   - `append_audit_log()`: 审计日志记录

2. **semds/evolution/code_generator.py** - 代码生成器
   - `CodeGenerator`类，调用Claude API
   - `generate()`: 生成代码
   - `extract_code()`: 从响应中提取代码块

3. **semds/evolution/test_runner.py** - 测试运行器
   - `TestRunner`类，使用subprocess执行pytest
   - 返回通过率、通过的测试、失败的测试、执行时间

4. **semds/storage/models.py + database.py** - 数据存储
   - `Task`模型: 任务表
   - `Generation`模型: 进化代表
   - SQLite数据库连接管理

5. **semds/experiments/calculator/tests/test_calculator.py** - 测试用例
   - 10个测试用例，覆盖基本运算、边界情况、返回类型

6. **demo_phase1.py** - 演示脚本
   - 单次"生成→测试→存储"流程

### 快速开始

1. 安装依赖
```bash
pip install -r requirements.txt
```

2. 设置环境变量（DeepSeek 推荐）
```bash
export DEEPSEEK_API_KEY='your-api-key'
```

或 Claude（需海外网络）
```bash
export ANTHROPIC_API_KEY='your-api-key'
```

3. 运行演示
```bash
python demo_phase1.py
```

### 项目结构

```
semds/
├── core/                          # Layer 0：核心内核【不可修改】
│   ├── kernel.py                  # safe_write, append_audit_log
│   ├── docker_manager.py          # Docker沙盒管理（可选，未启用）
│   └── audit.log                  # 审计日志
│
├── evolution/                     # Layer 1：进化引擎
│   ├── orchestrator.py            # 总调度器（Phase 3）
│   ├── code_generator.py          # Claude API调用
│   ├── test_runner.py             # pytest执行
│   ├── dual_evaluator.py          # 双轨评估（Phase 3）
│   ├── strategy_optimizer.py      # Thompson Sampling（Phase 3）
│   └── termination_checker.py     # 终止条件（Phase 3）
│
├── skills/                        # Layer 1：技能库
│   ├── templates/                 # 代码生成模板
│   └── strategies/                # 已验证的进化策略
│
├── factory/                       # Layer 2：应用工厂（Phase 5）
│   ├── task_manager.py            # 任务管理，支持并发进化
│   ├── human_gate.py              # 人类审批闸口
│   └── isolation_manager.py       # 任务间策略隔离
│
├── api/                           # API层（Phase 4）
│   ├── main.py                    # FastAPI入口
│   ├── routers/                   # API路由
│   └── schemas.py                 # Pydantic数据模型
│
├── storage/                       # 数据层
│   ├── models.py                  # SQLAlchemy模型
│   ├── database.py                # SQLite连接管理
│   └── semds.db                   # 数据库文件（运行时创建）
│
├── monitor/                       # 监控前端（Phase 4）
│   └── index.html                 # 单文件监控界面
│
├── experiments/                   # 实验目录
│   └── calculator/                # 计算器进化实验
│       └── tests/
│           └── test_calculator.py # 测试用例
│
├── docker/                        # Docker配置
│   ├── Dockerfile.sandbox         # 沙盒执行环境
│   └── docker-compose.yml         # 本地开发环境
│
├── docs/                          # 文档
│   ├── standards/                 # 开发规范
│   ├── roadmaps/                  # 阶段路线图
│   └── ...
│
└── demo_phase*.py                 # 阶段演示脚本
```

## 技术约束

- Python 3.11+
- ANTHROPIC_API_KEY从环境变量读取
- 不使用框架（FastAPI留到Phase 4）
- 代码有docstring

## Phase 2-5 规划

- **Phase 2**: Docker沙盒隔离
- **Phase 3**: 进化循环、Thompson Sampling、双轨评估
- **Phase 4**: FastAPI、WebSocket、监控界面
- **Phase 5**: 多任务并发

## 许可证

MIT

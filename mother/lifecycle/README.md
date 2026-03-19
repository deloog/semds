# SEMDS Lifecycle Management - Subprocess Based

## 概述

Lifecycle模块实现SEMDS的**全生命周期闭环**，**无需Docker**：

```
用户需求 → 代码生成 → 质量检查 → subprocess部署 → 运行监控 → 故障自愈
     ↑________________________________________________________|
```

**特点**:
- ✅ 无需 Docker，直接在 Windows 运行
- ✅ 使用 subprocess + tempfile (符合 DD-001)
- ✅ 进程级隔离，足够安全
- ✅ 自动监控和自愈

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    LifecycleManager                          │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
     ┌─────────▼─────────┐        ┌───────────▼──────────┐
     │ ApplicationDeployer│        │   ServiceMonitor     │
     │   (subprocess)     │        │   (HTTP + Process)   │
     │                    │        │                      │
     │  - 创建临时目录     │        │  - HTTP健康检查       │
     │  - 写入代码文件     │        │  - 进程存活检查       │
     │  - pip安装依赖      │        │  - 告警触发           │
     │  - subprocess启动   │        └───────────┬──────────┘
     └───────────────────┘                      │
                                    ┌───────────▼──────────┐
                                    │     AutoHealer       │
                                    │                      │
                                    │  - 日志分析          │
                                    │  - 进程重启          │
                                    │  - 端口更换          │
                                    │  - 代码热修复        │
                                    └──────────────────────┘
```

## 快速开始

### 部署服务

```python
from mother.lifecycle import LifecycleManager, DeploymentConfig

app_code = '''
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"msg": "Hello from SEMDS"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

with LifecycleManager() as manager:
    result = manager.deploy_service(
        name="hello-api",
        app_code=app_code,
        config=DeploymentConfig(name="hello-api", port=8080),
    )
    
    print(f"Service running at: {result.service_url}")
    print(f"Process ID: {result.process_id}")
```

### 查看状态

```python
# 所有服务
services = manager.list_services()
for name, status in services.items():
    print(f"{name}: {status.health.value} (PID: {status.process_id})")

# 单个服务
status = manager.get_service_status("hello-api")
print(f"Health: {status.health.value}")
print(f"Running: {status.deployment_status.value}")
```

### 停止服务

```python
manager.stop_service("hello-api")
```

## 部署配置

```python
from mother.lifecycle import DeploymentConfig

config = DeploymentConfig(
    name="my-api",
    app_type="fastapi",      # 'fastapi', 'flask', 'cli'
    port=8080,               # 服务端口
    python_version="3.11",   # Python版本
    dependencies=["requests", "redis"],  # pip依赖
    env_vars={"DB_URL": "..."},          # 环境变量
    timeout_seconds=30,      # 启动超时
)
```

## 自愈机制

当服务出现故障时，自动执行：

```
Monitor检测到异常
       │
       ▼
检查进程状态 ──死亡?──→ 重启进程
       │
       ▼
HTTP检查失败 ──连续2次?──→ 尝试修复
       │
       ▼
分析日志
       │
   ┌───┴────┐
   ▼        ▼
端口冲突   缺少健康端点
   │        │
   ▼        ▼
更换端口  热修复代码
   │        │
   └────┬───┘
        ▼
   重新部署
        │
        ▼
   验证修复
```

### 自愈示例

```python
# 自动触发
monitor.on_alert → healer.heal() → deployer.redeploy()

# 手动触发
result = manager.force_heal("my-service")
print(f"Healing: {result.action.value} - {result.message}")
```

## 集成到 Mother System

```python
from mother.core.fullstack_mother import FullStackMotherSystem

mother = FullStackMotherSystem()

# 一句话完成全部
result = mother.fulfill_request("创建一个待办事项API")

print(result)
# {
#   "success": True,
#   "service_url": "http://localhost:8080",
#   "process_id": 12345,
#   "health": "healthy",
#   "auto_healing": True
# }
```

## 技术细节

### 进程管理

```python
# 启动 (cross-platform)
process = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--port", "8080"],
    cwd=work_dir,
    env=env,
    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # Windows
)

# 停止
process.terminate()  # 优雅停止
timeout? process.kill()  # 强制结束
```

### 监控机制

1. **进程检查**: `process.poll() is None`
2. **HTTP检查**: `GET /health` 期望 200
3. **失败阈值**: 连续2次失败标记为 unhealthy
4. **检查间隔**: 默认10秒

### 安全隔离

- 每个服务独立的临时目录
- 依赖安装到目录内 ( `--target` )
- PYTHONPATH 隔离
- 超时机制防止无限运行

## 与 Docker 方案对比

| 特性 | Subprocess (当前) | Docker (原计划) |
|------|-------------------|-----------------|
| 依赖 | 仅Python | Docker Desktop |
| Windows | ✅ 稳定 | ❌ 经常崩溃 |
| 隔离级别 | 进程级 | 容器级 |
| 启动速度 | 快 (秒级) | 慢 (需构建镜像) |
| 资源占用 | 低 | 较高 |
| 生产部署 | 适合开发/测试 | 更适合生产 |

## 运行测试

```bash
# 单元测试 (无需Docker)
python -m pytest tests/test_lifecycle.py -v

# 完整演示
python mother/demo_lifecycle.py
```

## 文件结构

```
mother/lifecycle/
├── __init__.py           # 公共接口
├── deployer.py           # subprocess部署
├── monitor.py            # HTTP+进程监控
├── healer.py             # 自动修复
├── lifecycle_manager.py  # 统一入口
└── README.md             # 本文档

tests/
└── test_lifecycle.py     # 单元测试
```

## 注意事项

1. **端口管理**: 自动检测冲突并更换端口
2. **进程残留**: 异常退出时可能残留，建议定期检查
3. **依赖安装**: 首次启动可能较慢（pip install）
4. **日志**: 进程stdout/stderr通过管道，生产环境建议写入文件

## 未来扩展

当条件满足时可添加：
- Docker后端（生产环境）
- 进程组管理（supervisord/systemd）
- 远程部署（SSH/K8s）

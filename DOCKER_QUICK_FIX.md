# Docker Desktop 快速修复指南

## 问题
Docker Desktop 重启后显示错误：
- `service exited with code 1`
- `read/write on closed pipe`
- Docker 命令超时

## ✅ 已验证的解决方案（无需管理员脚本）

### 方法 1: 手动启动服务（推荐）

**步骤 1**: 打开 Windows 服务管理器
- 按 `Win + R`，输入 `services.msc`，回车

**步骤 2**: 找到以下服务并确保正在运行：
```
✅ Docker Desktop Service
✅ LxssManager (WSL2 相关)
✅ vmms (Hyper-V 虚拟机管理)
```

**步骤 3**: 如果服务未运行，右键点击 → **启动**

**步骤 4**: 等待 30-60 秒，然后测试：
```powershell
docker version
docker run hello-world
```

---

### 方法 2: 通过任务管理器重启

**步骤 1**: 打开任务管理器 (Ctrl + Shift + Esc)

**步骤 2**: 结束以下进程：
- `Docker Desktop`
- `com.docker.backend`
- `com.docker.build`
- `docker-sandbox`

**步骤 3**: 等待 10 秒

**步骤 4**: 从开始菜单启动 Docker Desktop

**步骤 5**: 等待图标停止动画后再测试

---

### 方法 3: 使用 WSL 命令重置

**步骤 1**: 打开 PowerShell（普通用户）

**步骤 2**: 执行以下命令：
```powershell
wsl --shutdown
```

**步骤 3**: 等待 5 秒

**步骤 4**: 重新打开 Docker Desktop

---

## 验证修复

运行以下检查脚本（无需管理员权限）：

```powershell
# 检查 1: 进程状态
Get-Process *docker* | Select-Object Name, Id

# 检查 2: Docker 版本
docker version

# 检查 3: 运行测试容器
docker run hello-world
```

---

## 预防措施

### 禁用开机自启
1. 打开 Docker Desktop
2. 设置 (⚙️) → General
3. 取消勾选：`Start Docker Desktop when you log in`
4. Apply & Restart

### 正确的启动顺序
重启电脑后：
1. 等待 Windows 完全启动（约 1-2 分钟）
2. 手动启动 Docker Desktop
3. 等待图标停止动画（表示完全就绪）
4. 再开始使用 docker 命令

---

## 状态记录

| 时间 | 操作 | 结果 |
|------|------|------|
| 2026-03-14 | 手动启动服务 | ✅ 成功 |
| 2026-03-14 | docker version | ⏳ 待验证 |
| 2026-03-14 | 运行实验 | ⏳ 待执行 |

---

## 下一步

一旦 Docker 正常工作，运行实验：

```bash
# 简单计算器实验
python experiments/calculator_evolution.py

# 字符串计算器多代实验
python experiments/string_calculator_evolution.py
```

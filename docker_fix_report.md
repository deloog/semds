# Docker Desktop 问题诊断与修复报告

## 诊断日期
2026-03-14

## 问题现象
重启电脑后 Docker Desktop 无法正常工作，`docker` 命令超时或无响应

## 诊断结果

### ✅ 已验证正常
1. Docker Desktop 进程正在运行
2. Backend 进程已启动
3. WSL2 集成已启用
4. Docker Desktop 日志显示正常启动

### ⚠️ 发现问题
1. **Docker CLI 与后端通信问题**: Windows 命令行无法连接到 Docker daemon
2. **WSL 集成配置可能损坏**: 重启后 WSL2 后端没有正确暴露 docker socket

## 根本原因
Docker Desktop 使用 WSL2 后端，重启后可能出现以下情况：
1. WSL2 虚拟机未完全初始化
2. Docker Desktop 服务启动顺序问题
3. Windows 与 WSL2 之间的命名管道连接失败

## 修复方案（按优先级排序）

### 方案 1: 重启 Docker Desktop 服务（推荐先尝试）
```powershell
# 以管理员身份运行 PowerShell
# 1. 停止 Docker Desktop
Stop-Process -Name "Docker Desktop" -Force
# 2. 等待 10 秒
Start-Sleep 10
# 3. 启动 Docker Desktop
Start-Process "D:\Docker\Docker\Docker Desktop.exe"
```

### 方案 2: 重置 WSL2 网络栈
```powershell
# 以管理员身份运行
wsl --shutdown
# 等待 5 秒
Start-Sleep 5
# 重新启动 Docker Desktop
```

### 方案 3: 修复 WSL2 集成
```powershell
# 1. 关闭 Docker Desktop
Stop-Process -Name "Docker Desktop" -Force

# 2. 注销并重新注册 docker-desktop
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data

# 3. 重新启动 Docker Desktop（会自动重新安装 WSL distros）
Start-Process "D:\Docker\Docker\Docker Desktop.exe"
```

### 方案 4: 重置 Docker Desktop 到出厂设置
```powershell
# 1. 关闭 Docker Desktop
# 2. 运行以下命令
"D:\Docker\Docker\Docker Desktop.exe" --reset-to-factory-defaults
```

### 方案 5: 完全重新安装 Docker Desktop
```powershell
# 1. 卸载 Docker Desktop
# 2. 清理残留数据
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\Docker"
Remove-Item -Recurse -Force "$env:USERPROFILE\.docker"

# 3. 重新安装
# 下载最新版本从 https://www.docker.com/products/docker-desktop
```

## 推荐的修复步骤

### 立即可执行的修复（无需管理员权限）

```powershell
# 步骤 1: 完全关闭 Docker Desktop
Stop-Process -Name "com.docker.*" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue

# 步骤 2: 等待进程完全退出
Start-Sleep 5

# 步骤 3: 启动 Docker Desktop
& "D:\Docker\Docker\Docker Desktop.exe"
```

### 验证修复

等待 Docker Desktop 完全启动（图标停止动画），然后运行：

```powershell
# 验证 Docker 是否正常工作
docker version
docker run hello-world
```

## 预防措施

1. **禁用 Docker Desktop 开机自启**
   - 设置 → General → Start Docker Desktop when you log in → 取消勾选

2. **手动启动顺序**
   - 重启电脑后等待 30 秒让系统完全初始化
   - 再手动启动 Docker Desktop

3. **启用 Docker Desktop 的自动修复**
   - 设置 → Troubleshoot → Clean / Purge data

## 日志位置

如需进一步诊断，查看以下日志：
- `%LOCALAPPDATA%\Docker\log\host\Docker Desktop.exe.log`
- `%LOCALAPPDATA%\Docker\log\host\com.docker.backend.exe.log`

## 状态跟踪

| 修复步骤 | 状态 | 备注 |
|---------|------|------|
| 重启 Docker Desktop | ⏳ 待执行 | |
| 验证修复 | ⏳ 待执行 | |
| 运行测试 | ⏳ 待执行 | |

---

**下一步行动**: 执行上述"立即可执行的修复"步骤，然后验证 Docker 是否正常工作。

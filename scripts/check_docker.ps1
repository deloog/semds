# Docker 状态检查脚本（无需管理员权限）
# 用于验证 Docker 是否正常工作

Write-Host "=== Docker 状态检查工具 ===" -ForegroundColor Cyan
Write-Host ""

# 检查 1: Docker Desktop 进程
Write-Host "[1/4] 检查 Docker Desktop 进程..." -ForegroundColor Yellow
$dockerProcesses = Get-Process -Name "*docker*" -ErrorAction SilentlyContinue
if ($dockerProcesses) {
    Write-Host "  ✅ Docker 进程正在运行:" -ForegroundColor Green
    $dockerProcesses | Select-Object -First 5 | ForEach-Object {
        Write-Host "     - $($_.Name) (PID: $($_.Id))" -ForegroundColor Gray
    }
} else {
    Write-Host "  ❌ 未找到 Docker 进程" -ForegroundColor Red
}
Write-Host ""

# 检查 2: 测试 docker 命令
Write-Host "[2/4] 测试 docker version 命令..." -ForegroundColor Yellow
try {
    $version = docker version --format '{{.Server.Version}}' 2>$null
    if ($version) {
        Write-Host "  ✅ Docker 守护进程响应正常" -ForegroundColor Green
        Write-Host "     版本: $version" -ForegroundColor Gray
    } else {
        Write-Host "  ❌ Docker 守护进程无响应" -ForegroundColor Red
    }
} catch {
    Write-Host "  ❌ Docker 命令执行失败: $_" -ForegroundColor Red
}
Write-Host ""

# 检查 3: 运行 hello-world 测试
Write-Host "[3/4] 运行 hello-world 容器测试..." -ForegroundColor Yellow
try {
    $output = docker run --rm hello-world 2>&1
    if ($output -match "Hello from Docker") {
        Write-Host "  ✅ 容器运行正常" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️ 容器测试返回异常结果" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ 容器运行失败: $_" -ForegroundColor Red
}
Write-Host ""

# 检查 4: 检查 WSL 状态
Write-Host "[4/4] 检查 WSL 集成状态..." -ForegroundColor Yellow
try {
    $wslList = wsl --list --quiet 2>$null
    $dockerWsl = $wslList | Where-Object { $_ -match "docker" }
    if ($dockerWsl) {
        Write-Host "  ✅ WSL 集成正常" -ForegroundColor Green
        Write-Host "     发现以下 Docker WSL 发行版:" -ForegroundColor Gray
        $dockerWsl | ForEach-Object { Write-Host "       - $_" -ForegroundColor Gray }
    } else {
        Write-Host "  ⚠️ 未找到 Docker WSL 发行版" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ 无法检查 WSL 状态: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== 检查完成 ===" -ForegroundColor Cyan

# 提供建议
Write-Host ""
Write-Host "建议操作:" -ForegroundColor Yellow
Write-Host "  • 如果以上检查都通过，Docker 已正常工作" -ForegroundColor Green
Write-Host "  • 如果守护进程无响应，请尝试:" -ForegroundColor Cyan
Write-Host "     1. 等待 30-60 秒让 Docker 完全启动" -ForegroundColor Gray
Write-Host "     2. 关闭 Docker Desktop 并重新打开" -ForegroundColor Gray
Write-Host "     3. 重启电脑后再次检查" -ForegroundColor Gray
Write-Host ""

# 询问是否运行实验
$response = Read-Host "是否现在运行计算器进化实验? (y/n)"
if ($response -eq 'y' -or $response -eq 'Y') {
    Write-Host ""
    Write-Host "启动简单计算器实验..." -ForegroundColor Cyan
    Set-Location $PSScriptRoot\..
    python experiments\calculator_evolution.py
}

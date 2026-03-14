# Docker Desktop 修复脚本
# 以普通用户权限运行即可

Write-Host "=== Docker Desktop 修复工具 ===" -ForegroundColor Cyan
Write-Host ""

# 步骤 1: 关闭 Docker Desktop
Write-Host "[1/4] 正在关闭 Docker Desktop..." -ForegroundColor Yellow
$processes = @("Docker Desktop", "com.docker.backend", "com.docker.build", "docker-sandbox")
foreach ($proc in $processes) {
    Get-Process -Name $proc -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  - 已停止 $proc" -ForegroundColor Gray
}
Start-Sleep 3

# 步骤 2: 关闭 WSL
Write-Host "[2/4] 正在重置 WSL..." -ForegroundColor Yellow
wsl --shutdown 2>$null
Write-Host "  - WSL 已关闭" -ForegroundColor Gray
Start-Sleep 3

# 步骤 3: 启动 Docker Desktop
Write-Host "[3/4] 正在启动 Docker Desktop..." -ForegroundColor Yellow
$dockerPath = "D:\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerPath) {
    Start-Process $dockerPath
    Write-Host "  - Docker Desktop 已启动" -ForegroundColor Gray
} else {
    Write-Host "  - 错误: 找不到 Docker Desktop.exe" -ForegroundColor Red
    Write-Host "  - 尝试从默认位置启动..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe" -ErrorAction SilentlyContinue
}

# 步骤 4: 等待并验证
Write-Host "[4/4] 等待 Docker Desktop 初始化..." -ForegroundColor Yellow
Write-Host "  - 请等待 30-60 秒..." -ForegroundColor Gray

$maxWait = 60
$waited = 0
while ($waited -lt $maxWait) {
    Start-Sleep 5
    $waited += 5
    Write-Host "  - 已等待 $waited 秒..." -ForegroundColor Gray
    
    # 检查 docker 是否可用
    try {
        $version = docker version --format '{{.Server.Version}}' 2>$null
        if ($version) {
            Write-Host ""
            Write-Host "✅ Docker 已成功启动!" -ForegroundColor Green
            Write-Host "   Docker 版本: $version" -ForegroundColor Green
            Write-Host ""
            Write-Host "运行 'docker run hello-world' 测试..." -ForegroundColor Cyan
            docker run hello-world 2>$null
            Write-Host ""
            Write-Host "修复完成!" -ForegroundColor Green
            exit 0
        }
    } catch {
        # 继续等待
    }
}

Write-Host ""
Write-Host "⚠️ Docker 可能尚未完全启动，请稍后再试" -ForegroundColor Yellow
Write-Host "如果仍有问题，请尝试以下命令:" -ForegroundColor Yellow
Write-Host "  1. wsl --shutdown" -ForegroundColor Cyan
Write-Host "  2. 重新启动 Docker Desktop" -ForegroundColor Cyan

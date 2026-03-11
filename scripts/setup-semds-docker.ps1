# SEMDS Docker 环境配置脚本
# 在Docker Desktop安装完成后运行

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SEMDS Docker 环境配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Docker是否运行
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker未运行"
    }
} catch {
    Write-Error @"
Docker未运行或安装不正确。

请确保：
1. Docker Desktop已完成安装
2. 已重启电脑
3. Docker Desktop已启动（系统托盘中能看到鲸鱼图标）

然后重新运行此脚本。
"@
    exit 1
}

Write-Host "[1/4] Docker运行正常" -ForegroundColor Green
Write-Host "      版本: $(docker --version)" -ForegroundColor Gray

# 构建SEMDS沙盒镜像
Write-Host "[2/4] 构建SEMDS沙盒镜像..." -ForegroundColor Yellow
cd d:\semds

try {
    docker build -f docker/Dockerfile.sandbox -t semds-sandbox:latest .
    Write-Host "      镜像构建成功" -ForegroundColor Green
} catch {
    Write-Error "镜像构建失败: $_"
    exit 1
}

# 验证镜像
Write-Host "[3/4] 验证沙盒镜像..." -ForegroundColor Yellow
$testResult = docker run --rm --network none semds-sandbox:latest python -c "print('SEMDS Sandbox OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "      $testResult" -ForegroundColor Green
} else {
    Write-Warning "镜像验证输出: $testResult"
}

# 检查镜像列表
Write-Host "[4/4] 检查Docker镜像..." -ForegroundColor Yellow
docker images | findstr semds-sandbox

# 运行SEMDS Phase 2测试
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "运行SEMDS Phase 2测试..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

cd d:\semds
python -m pytest tests/core/test_docker_manager.py -v

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SEMDS Docker环境配置完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "您可以运行演示脚本:" -ForegroundColor Cyan
Write-Host "  python demo_phase2.py" -ForegroundColor White
Write-Host ""

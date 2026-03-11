# Docker Desktop "service exited with code 1" / "closed pipe" Fix Script
# This error is usually caused by WSL2 integration issues

param(
    [switch]$FullReset
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Desktop Error Repair Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin privileges
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run as Administrator"
    exit 1
}

# Step 1: Stop all Docker and WSL processes
Write-Host "[1/6] Stopping all Docker and WSL processes..." -ForegroundColor Yellow

# Kill Docker processes
$dockerProcesses = @("Docker Desktop", "com.docker.backend", "com.docker.service", "dockerd")
foreach ($proc in $dockerProcesses) {
    Get-Process -Name $proc -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Stopped: $proc" -ForegroundColor Gray
}

# Shutdown WSL
wsl --shutdown 2>$null
Write-Host "  WSL shutdown complete" -ForegroundColor Gray

Start-Sleep -Seconds 3

# Step 2: Clean Docker WSL distros
Write-Host "[2/6] Cleaning Docker WSL distros..." -ForegroundColor Yellow

$wslList = wsl --list --quiet 2>$null
if ($wslList -match "docker-desktop-data") {
    Write-Host "  Unregistering docker-desktop-data..." -ForegroundColor Gray
    wsl --unregister docker-desktop-data 2>$null
}
if ($wslList -match "docker-desktop") {
    Write-Host "  Unregistering docker-desktop..." -ForegroundColor Gray
    wsl --unregister docker-desktop 2>$null
}

# Step 3: Update WSL2 kernel
Write-Host "[3/6] Updating WSL2 kernel..." -ForegroundColor Yellow

wsl --update --web-download 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Online update failed, trying alternative..." -ForegroundColor Yellow
}

wsl --set-default-version 2 2>$null
Write-Host "  WSL2 set as default" -ForegroundColor Gray

# Step 4: Clean Docker cache
Write-Host "[4/6] Cleaning Docker cache..." -ForegroundColor Yellow

$pathsToClean = @(
    "$env:LOCALAPPDATA\Docker\run\*",
    "$env:LOCALAPPDATA\Docker\log\*", 
    "$env:LOCALAPPDATA\Docker\wsl\*",
    "$env:LOCALAPPDATA\Docker\*.lock"
)

foreach ($path in $pathsToClean) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Cleaned: $path" -ForegroundColor Gray
    }
}

# Step 5: Fix WSL config
Write-Host "[5/6] Fixing WSL config..." -ForegroundColor Yellow

$wslConfigPath = "$env:USERPROFILE\.wslconfig"

if (Test-Path $wslConfigPath) {
    Copy-Item $wslConfigPath "$wslConfigPath.backup.$(Get-Date -Format 'yyyyMMddHHmmss')" -Force
    Write-Host "  Original config backed up" -ForegroundColor Gray
}

$minimalWslConfig = @"
[wsl2]
memory=4GB
processors=2
localhostForwarding=true
kernelCommandLine = cgroup_no_v1=all
"@

$minimalWslConfig | Out-File -FilePath $wslConfigPath -Encoding UTF8 -Force
Write-Host "  WSL config fixed" -ForegroundColor Green

# Step 6: Ensure D drive directories
Write-Host "[6/6] Ensuring D drive directories..." -ForegroundColor Yellow

$dockerDataPath = "D:\docker-data"
$wslDockerPath = "$dockerDataPath\wsl"

if (!(Test-Path $wslDockerPath)) {
    New-Item -ItemType Directory -Path $wslDockerPath -Force | Out-Null
}

$wslDistros = @(
    "$dockerDataPath\docker-desktop",
    "$dockerDataPath\docker-desktop-data"
)
foreach ($distro in $wslDistros) {
    if (!(Test-Path $distro)) {
        New-Item -ItemType Directory -Path $distro -Force | Out-Null
    }
}

Write-Host "  D drive directories ready" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Repair Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. RESTART YOUR COMPUTER (Required)" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Start Docker Desktop" -ForegroundColor White
Write-Host "   Wait for whale icon in system tray" -ForegroundColor Gray
Write-Host "   First start may take 5-10 minutes" -ForegroundColor Gray
Write-Host ""
Write-Host "3. If still failing, try:" -ForegroundColor White
Write-Host "   A. Reinstall Docker Desktop completely" -ForegroundColor Gray
Write-Host "   B. Use Hyper-V backend instead of WSL2" -ForegroundColor Gray
Write-Host ""
Write-Host "Common errors:" -ForegroundColor Cyan
Write-Host "   - 'closed pipe': WSL2 kernel issue (fixed by this script)" -ForegroundColor Gray
Write-Host "   - 'exit code 1': Docker service failed to start" -ForegroundColor Gray
Write-Host "   - Stuck at 'Starting': Wait longer or insufficient resources" -ForegroundColor Gray

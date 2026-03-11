# Complete Docker Desktop uninstall and reinstall
# Use this when all other fixes fail

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Red
Write-Host "Docker Desktop Complete Reinstall" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will COMPLETELY remove Docker Desktop" -ForegroundColor Yellow
Write-Host "and all its data. You will need to reinstall." -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Type 'YES' to continue"

if ($confirm -ne "YES") {
    Write-Host "Cancelled." -ForegroundColor Gray
    exit 0
}

Write-Host ""
Write-Host "[1/5] Stopping all Docker processes..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.Name -match "docker"} | Stop-Process -Force -ErrorAction SilentlyContinue
wsl --shutdown 2>$null
Start-Sleep -Seconds 2

Write-Host "[2/5] Unregistering Docker WSL distros..." -ForegroundColor Yellow
wsl --unregister docker-desktop-data 2>$null
wsl --unregister docker-desktop 2>$null

Write-Host "[3/5] Removing Docker Desktop application..." -ForegroundColor Yellow
$dockerPath = "C:\Program Files\Docker\Docker"
if (Test-Path $dockerPath) {
    Remove-Item -Path $dockerPath -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  Removed: $dockerPath" -ForegroundColor Gray
}

Write-Host "[4/5] Cleaning Docker data directories..." -ForegroundColor Yellow
$pathsToRemove = @(
    "$env:LOCALAPPDATA\Docker",
    "$env:APPDATA\Docker",
    "$env:PROGRAMDATA\DockerDesktop",
    "$env:USERPROFILE\.docker"
)

foreach ($path in $pathsToRemove) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Removed: $path" -ForegroundColor Gray
    }
}

Write-Host "[5/5] Cleaning registry entries..." -ForegroundColor Yellow
Remove-Item -Path "HKLM:\SOFTWARE\Docker Inc." -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path "HKCU:\SOFTWARE\Docker Inc." -Recurse -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Docker Desktop completely removed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. RESTART your computer" -ForegroundColor Yellow
Write-Host "2. Download Docker Desktop from:" -ForegroundColor White
Write-Host "   https://www.docker.com/products/docker-desktop" -ForegroundColor Gray
Write-Host "3. Install with these settings:" -ForegroundColor White
Write-Host "   - Uncheck 'Use WSL 2 instead of Hyper-V'" -ForegroundColor Gray
Write-Host "   - Use Hyper-V backend instead" -ForegroundColor Gray
Write-Host "4. After install, configure data root to D:" -ForegroundColor White
Write-Host "   Edit %USERPROFILE%\.docker\daemon.json" -ForegroundColor Gray
Write-Host "   Set: data-root: D:\\docker-data\\docker" -ForegroundColor Gray

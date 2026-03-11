# Manual Docker Desktop Install Helper
# Run this after nuclear-option if Docker didn't install properly

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Desktop Manual Install Helper" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if installer exists
$installerPath = "$env:TEMP\DockerDesktopInstaller.exe"
$altPath = "$env:TEMP\DockerDesktopInstallers\DockerDesktopInstaller.exe"

$foundInstaller = $null
if (Test-Path $installerPath) {
    $foundInstaller = $installerPath
} elseif (Test-Path $altPath) {
    $foundInstaller = $altPath
}

if (!$foundInstaller) {
    Write-Host "Installer not found in temp. Downloading..." -ForegroundColor Yellow
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile $installerPath -UseBasicParsing
    $foundInstaller = $installerPath
    Write-Host "Downloaded to: $installerPath" -ForegroundColor Green
} else {
    Write-Host "Found installer: $foundInstaller" -ForegroundColor Green
}

Write-Host ""
Write-Host "Starting Docker Desktop Installation..." -ForegroundColor Yellow
Write-Host "This will open a GUI installer window." -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT: During installation:" -ForegroundColor Red
Write-Host "  - Use default settings" -ForegroundColor White
Write-Host "  - When asked about WSL2, UNCHECK it (we want Hyper-V)" -ForegroundColor White
Write-Host "  - Or just use defaults and we'll fix settings after" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to start installer..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Run installer
Write-Host "Starting installer GUI..." -ForegroundColor Green
Start-Process -FilePath $foundInstaller -Wait

Write-Host ""
Write-Host "Installer closed. Checking installation..." -ForegroundColor Yellow

# Check if installed
$dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerExe) {
    Write-Host "SUCCESS! Docker Desktop is installed." -ForegroundColor Green
    Write-Host "Location: $dockerExe" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Start Docker Desktop:" -ForegroundColor White
    Write-Host "   & '$dockerExe'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Wait for whale icon in system tray" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Configure settings (see script below)" -ForegroundColor White
    
    # Create quick start script
    $quickStart = @"
# Quick start Docker Desktop
& "$dockerExe"
Write-Host "Docker Desktop starting... wait for whale icon"
"@
    $quickStart | Out-File -FilePath "D:\docker-data\start-docker.ps1" -Encoding UTF8
    Write-Host ""
    Write-Host "Quick start script created: D:\docker-data\start-docker.ps1" -ForegroundColor Green
} else {
    Write-Warning "Docker Desktop not found after install."
    Write-Host "The installation may have failed or been cancelled." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Try these options:" -ForegroundColor Cyan
    Write-Host "1. Check 'Add or Remove Programs' - is Docker Desktop listed?" -ForegroundColor White
    Write-Host "2. Try downloading manually from docker.com" -ForegroundColor White
    Write-Host "3. Run Windows Update and try again" -ForegroundColor White
}

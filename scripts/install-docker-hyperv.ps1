# Fresh Docker Desktop install with Hyper-V backend
# This avoids WSL2 completely

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Desktop Fresh Install (Hyper-V)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run as Administrator"
    exit 1
}

# Step 1: Enable required Windows features
Write-Host "[1/4] Enabling Windows features..." -ForegroundColor Yellow

dism /Online /Enable-Feature /FeatureName:Microsoft-Hyper-V-All /All /NoRestart 2>$null
dism /Online /Enable-Feature /FeatureName:Containers-DisposableClientVM /All /NoRestart 2>$null

Write-Host "  Windows features enabled (restart required after install)" -ForegroundColor Green

# Step 2: Create D drive directories
Write-Host "[2/4] Creating D drive directories..." -ForegroundColor Yellow
$dockerDataPath = "D:\docker-data"
@("docker", "wsl", "docker-desktop", "docker-desktop-data") | ForEach-Object {
    $dir = "$dockerDataPath\$_"
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Host "  Directories created" -ForegroundColor Green

# Step 3: Download Docker Desktop
Write-Host "[3/4] Downloading Docker Desktop..." -ForegroundColor Yellow
$installer = "$env:TEMP\DockerDesktopInstaller.exe"
$ProgressPreference = 'SilentlyContinue'
try {
    Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile $installer -UseBasicParsing
    Write-Host "  Download complete" -ForegroundColor Green
} catch {
    Write-Error "Download failed. Please download manually from docker.com"
    exit 1
}

# Step 4: Install with Hyper-V (no WSL)
Write-Host "[4/4] Installing Docker Desktop with Hyper-V..." -ForegroundColor Yellow
Write-Host "  This may take several minutes..." -ForegroundColor Gray

# Install without WSL
$process = Start-Process -FilePath $installer -ArgumentList "install", "--quiet", "--always-start-service", "--backend=hyper-v" -Wait -PassThru

if ($process.ExitCode -ne 0) {
    Write-Warning "Install exit code: $($process.ExitCode)"
}

# Configure data root
$daemonConfig = @{
    "data-root" = "$dockerDataPath\docker"
    "storage-driver" = "overlay2"
} | ConvertTo-Json

$dockerConfigDir = "$env:USERPROFILE\.docker"
if (!(Test-Path $dockerConfigDir)) {
    New-Item -ItemType Directory -Path $dockerConfigDir -Force | Out-Null
}
$daemonConfig | Out-File -FilePath "$dockerConfigDir\daemon.json" -Encoding UTF8 -Force

# Disable WSL in Docker settings
$dockerSettings = "$env:APPDATA\Docker\settings.json"
if (Test-Path $dockerSettings) {
    $settings = Get-Content $dockerSettings | ConvertFrom-Json
    $settings.wslEngineEnabled = $false
    $settings | ConvertTo-Json -Depth 10 | Out-File -FilePath $dockerSettings -Encoding UTF8
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "CRITICAL: RESTART YOUR COMPUTER NOW" -ForegroundColor Red
Write-Host ""
Write-Host "After restart:" -ForegroundColor Cyan
Write-Host "1. Start Docker Desktop" -ForegroundColor White
Write-Host "2. Wait for initialization (may take 5-10 min)" -ForegroundColor White
Write-Host "3. Settings > General > Use WSL2 = OFF" -ForegroundColor White
Write-Host "4. Apply & Restart" -ForegroundColor White
Write-Host ""
Write-Host "Data location: $dockerDataPath" -ForegroundColor Gray

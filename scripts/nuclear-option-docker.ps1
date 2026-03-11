# NUCLEAR OPTION: Complete Docker wipe and fresh Hyper-V install
# This is the ultimate fix when everything else fails

param(
    [switch]$SkipDownload
)

$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'

function Write-Header($text) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host $text -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step($num, $total, $text) {
    Write-Host "[$num/$total] $text" -ForegroundColor Yellow
}

Write-Header "DOCKER NUCLEAR RESET - Complete Fresh Install"

# Verify admin
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "THIS MUST RUN AS ADMINISTRATOR! Right-click -> Run as Administrator"
    exit 1
}

$totalSteps = 8
$currentStep = 0

# ============================================================================
# STEP 1: Kill Everything
# ============================================================================
$currentStep++
Write-Step $currentStep $totalSteps "Terminating all Docker and WSL processes..."

$processesToKill = @(
    "Docker Desktop",
    "com.docker.backend", 
    "com.docker.service",
    "com.docker.proxy",
    "com.docker.dev-envs",
    "dockerd",
    "vpnkit",
    "vpnkit-bridge"
)

foreach ($proc in $processesToKill) {
    Get-Process -Name $proc -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "  Killed: $proc" -ForegroundColor DarkGray
}

wsl --shutdown 2>$null
Start-Sleep -Seconds 3
Write-Host "  All processes terminated" -ForegroundColor Green

# ============================================================================
# STEP 2: Unregister Docker WSL (if any)
# ============================================================================
$currentStep++
Write-Step $currentStep $totalSteps "Unregistering Docker WSL distros..."

$wslList = wsl --list --quiet 2>$null
$dockerWSLs = @("docker-desktop", "docker-desktop-data")

foreach ($distro in $dockerWSLs) {
    if ($wslList -match $distro) {
        Write-Host "  Unregistering: $distro" -ForegroundColor DarkGray
        wsl --unregister $distro 2>$null
    }
}
Write-Host "  WSL distros cleaned" -ForegroundColor Green

# ============================================================================
# STEP 3: Uninstall Docker Desktop Application
# ============================================================================
$currentStep++
Write-Step $currentStep $totalSteps "Uninstalling Docker Desktop..."

# Try MSI uninstall first
$dockerUninstall = Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like "*Docker*"}
if ($dockerUninstall) {
    Write-Host "  Found: $($dockerUninstall.Name)" -ForegroundColor DarkGray
    $dockerUninstall.Uninstall() | Out-Null
}

# Remove installation directory
$dockerPaths = @(
    "C:\Program Files\Docker",
    "C:\ProgramData\DockerDesktop",
    "C:\ProgramData\Docker"
)

foreach ($path in $dockerPaths) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Removed: $path" -ForegroundColor DarkGray
    }
}
Write-Host "  Docker Desktop uninstalled" -ForegroundColor Green

# ============================================================================
# STEP 4: Clean All Docker Data
# ============================================================================
$currentStep++
Write-Step $currentStep $totalSteps "Cleaning all Docker data..."

$dataPaths = @(
    "$env:LOCALAPPDATA\Docker",
    "$env:APPDATA\Docker", 
    "$env:USERPROFILE\.docker",
    "$env:PROGRAMDATA\DockerDesktop"
)

foreach ($path in $dataPaths) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Cleaned: $path" -ForegroundColor DarkGray
    }
}
Write-Host "  All data cleaned" -ForegroundColor Green

# ============================================================================
# STEP 5: Enable Windows Features (Hyper-V + Containers)
# ============================================================================
$currentStep++
Write-Step $currentStep $totalSteps "Enabling Windows features (Hyper-V + Containers)..."

$features = @(
    "Microsoft-Hyper-V-All",
    "Microsoft-Hyper-V", 
    "Microsoft-Hyper-V-Management-PowerShell",
    "Microsoft-Hyper-V-Management-Clients",
    "Containers-DisposableClientVM",
    "Containers"
)

foreach ($feature in $features) {
    $result = dism /Online /Enable-Feature /FeatureName:$feature /All /NoRestart 2>&1
    if ($result -match "Error") {
        Write-Host "  Warning: $feature may have issues" -ForegroundColor Yellow
    } else {
        Write-Host "  Enabled: $feature" -ForegroundColor DarkGray
    }
}
Write-Host "  Windows features enabled" -ForegroundColor Green

# ============================================================================
# STEP 6: Prepare D Drive Directories
# ============================================================================
$currentStep++
Write-Step $currentStep $totalSteps "Preparing D drive directories..."

$dockerDataPath = "D:\docker-data"
$subDirs = @("docker", "wsl", "docker-desktop", "docker-desktop-data")

foreach ($dir in $subDirs) {
    $fullPath = "$dockerDataPath\$dir"
    if (!(Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
        Write-Host "  Created: $fullPath" -ForegroundColor DarkGray
    }
}
Write-Host "  D drive ready" -ForegroundColor Green

# ============================================================================
# STEP 7: Download Docker Desktop
# ============================================================================
$currentStep++
Write-Step $currentStep $totalSteps "Downloading Docker Desktop..."

$installerPath = "$env:TEMP\DockerDesktopInstaller.exe"

if (!$SkipDownload -or !(Test-Path $installerPath)) {
    try {
        Write-Host "  Downloading from Docker..." -ForegroundColor DarkGray
        Invoke-WebRequest -Uri "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe" -OutFile $installerPath -UseBasicParsing
        Write-Host "  Download complete: $installerPath" -ForegroundColor Green
    } catch {
        Write-Error "Download failed! Please manually download from: https://www.docker.com/products/docker-desktop"
        exit 1
    }
} else {
    Write-Host "  Using existing installer" -ForegroundColor Green
}

# ============================================================================
# STEP 8: Install with HYPER-V Backend
# ============================================================================
$currentStep++
Write-Step $currentStep $totalSteps "Installing Docker Desktop (Hyper-V backend)..."
Write-Host "  This will take 5-10 minutes. Please wait..." -ForegroundColor Magenta

# Install with Hyper-V explicitly (NO WSL2)
$installArgs = @(
    "install",
    "--quiet",
    "--always-start-service"
)

$process = Start-Process -FilePath $installerPath -ArgumentList $installArgs -PassThru

# Show progress while waiting
$dots = 0
while (!$process.HasExited) {
    Write-Host "." -NoNewline -ForegroundColor Cyan
    Start-Sleep -Seconds 5
    $dots++
    if ($dots -gt 60) {  # 5 minutes timeout check
        Write-Host ""
        Write-Host "  Still installing... (this is normal)" -ForegroundColor Yellow
        $dots = 0
    }
}

Write-Host ""
if ($process.ExitCode -eq 0) {
    Write-Host "  Installation completed successfully" -ForegroundColor Green
} else {
    Write-Warning "Installation exit code: $($process.ExitCode)"
    Write-Host "  This may still be OK - checking..." -ForegroundColor Yellow
}

# ============================================================================
# POST-INSTALL CONFIGURATION
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Configuring Docker Settings..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Wait a moment for files to be created
Start-Sleep -Seconds 3

# Configure daemon.json for D drive
Write-Host "[Config] Setting data root to D drive..." -ForegroundColor Yellow
$dockerConfigDir = "$env:USERPROFILE\.docker"
if (!(Test-Path $dockerConfigDir)) {
    New-Item -ItemType Directory -Path $dockerConfigDir -Force | Out-Null
}

$daemonConfig = @{
    "data-root" = "$dockerDataPath\docker"
    "exec-opts" = @("native.cgroupdriver=cgroupfs")
    "log-driver" = "json-file"
    "log-opts" = @{
        "max-size" = "10m"
        "max-file" = "3"
    }
    "storage-driver" = "overlay2"
} | ConvertTo-Json -Depth 10

$daemonConfig | Out-File -FilePath "$dockerConfigDir\daemon.json" -Encoding UTF8 -Force
Write-Host "  Daemon configured for D drive" -ForegroundColor Green

# Configure settings.json to disable WSL2
Write-Host "[Config] Disabling WSL2 backend..." -ForegroundColor Yellow
$settingsPath = "$env:APPDATA\Docker\settings.json"

# Wait for settings file to be created by installer
$waitCount = 0
while (!(Test-Path $settingsPath) -and $waitCount -lt 10) {
    Start-Sleep -Seconds 2
    $waitCount++
}

if (Test-Path $settingsPath) {
    $settings = Get-Content $settingsPath | ConvertFrom-Json
    $settings.wslEngineEnabled = $false
    $settings | ConvertTo-Json -Depth 10 | Out-File -FilePath $settingsPath -Encoding UTF8 -Force
    Write-Host "  WSL2 disabled in settings" -ForegroundColor Green
} else {
    Write-Host "  Warning: Settings file not found, will configure on first start" -ForegroundColor Yellow
}

# Create startup script for SEMDS
$startupScript = @'
# SEMDS Docker Post-Install Setup
Write-Host "Setting up SEMDS Docker environment..." -ForegroundColor Cyan

# Check Docker
$dockerInfo = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Docker is not running! Please start Docker Desktop first."
    exit 1
}

# Build SEMDS sandbox
cd d:\semds
Write-Host "Building SEMDS sandbox image..." -ForegroundColor Yellow
docker build -f docker/Dockerfile.sandbox -t semds-sandbox:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host "SEMDS sandbox built successfully!" -ForegroundColor Green
    docker run --rm semds-sandbox:latest python -c "print('SEMDS Sandbox is ready!')"
} else {
    Write-Error "Failed to build SEMDS sandbox"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "SEMDS Docker Environment Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
'@

$startupScript | Out-File -FilePath "$dockerDataPath\setup-semds.ps1" -Encoding UTF8 -Force

# ============================================================================
# COMPLETION
# ============================================================================
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "NUCLEAR RESET COMPLETE!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "CRITICAL NEXT STEPS:" -ForegroundColor Red
Write-Host ""
Write-Host "1. RESTART YOUR COMPUTER (MANDATORY)" -ForegroundColor Yellow
Write-Host "   This enables Hyper-V and completes installation" -ForegroundColor Gray
Write-Host ""
Write-Host "2. After restart, START DOCKER DESKTOP" -ForegroundColor Yellow
Write-Host "   - Wait for whale icon (may take 5-10 minutes first time)" -ForegroundColor Gray
Write-Host "   - If asked, choose 'Hyper-V' backend (NOT WSL2)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. VERIFY INSTALLATION:" -ForegroundColor Yellow
Write-Host "   Open PowerShell and run: docker --version" -ForegroundColor Gray
Write-Host ""
Write-Host "4. SETUP SEMDS:" -ForegroundColor Yellow
Write-Host "   Run: $dockerDataPath\setup-semds.ps1" -ForegroundColor Gray
Write-Host ""
Write-Host "Data Locations:" -ForegroundColor Cyan
Write-Host "   Program: C:\Program Files\Docker\ (~500MB)" -ForegroundColor Gray
Write-Host "   Data:    $dockerDataPath\ (images, containers, volumes)" -ForegroundColor Gray
Write-Host ""
Write-Host "If Docker still fails after restart:" -ForegroundColor Magenta
Write-Host "   1. Open 'Windows Security' -> 'App & Browser Control'" -ForegroundColor Gray
Write-Host "   2. Check if Docker is being blocked" -ForegroundColor Gray
Write-Host "   3. Add Docker to exclusions if needed" -ForegroundColor Gray
Write-Host ""

$restart = Read-Host "Restart computer now? (Y/N)"
if ($restart -eq "Y" -or $restart -eq "y") {
    Write-Host "Restarting in 5 seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    Restart-Computer -Force
}

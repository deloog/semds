# Install Docker Desktop 4.28.0 (Stable LTS Version)
# This version is more stable than latest 4.63.0

$ErrorActionPreference = "Stop"
$ProgressPreference = 'SilentlyContinue'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Desktop 4.28.0 Stable Install" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Admin check
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run as Administrator"
    exit 1
}

Write-Host "This will install Docker Desktop 4.28.0 (LTS stable version)" -ForegroundColor Yellow
Write-Host "Using Hyper-V backend (no WSL2 issues)" -ForegroundColor Yellow
Write-Host ""
$confirm = Read-Host "Continue? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    exit 0
}

# Step 1: Clean up any existing broken install
Write-Host "[1/5] Cleaning up existing Docker..." -ForegroundColor Yellow

# Kill processes
@("Docker Desktop", "com.docker.backend", "com.docker.service") | ForEach-Object {
    Get-Process -Name $_ -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}
wsl --shutdown 2>$null

# Unregister WSL
@("docker-desktop", "docker-desktop-data") | ForEach-Object {
    wsl --unregister $_ 2>$null
}

# Remove broken install
$pathsToRemove = @(
    "C:\Program Files\Docker",
    "$env:LOCALAPPDATA\Docker",
    "$env:APPDATA\Docker",
    "$env:USERPROFILE\.docker",
    "$env:PROGRAMDATA\DockerDesktop"
)

foreach ($path in $pathsToRemove) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Removed: $path" -ForegroundColor DarkGray
    }
}

# Remove registry keys
Remove-Item -Path "HKLM:\SOFTWARE\Docker Inc." -Recurse -ErrorAction SilentlyContinue
Remove-Item -Path "HKCU:\SOFTWARE\Docker Inc." -Recurse -ErrorAction SilentlyContinue

Write-Host "  Cleanup complete" -ForegroundColor Green

# Step 2: Enable Hyper-V
Write-Host "[2/5] Enabling Hyper-V..." -ForegroundColor Yellow

$features = @(
    "Microsoft-Hyper-V-All",
    "Microsoft-Hyper-V",
    "Containers-DisposableClientVM",
    "Containers"
)

foreach ($feature in $features) {
    dism /Online /Enable-Feature /FeatureName:$feature /All /NoRestart 2>&1 | Out-Null
    Write-Host "  Enabled: $feature" -ForegroundColor DarkGray
}

# Step 3: Download Docker 4.28.0 (Stable)
Write-Host "[3/5] Downloading Docker Desktop 4.28.0..." -ForegroundColor Yellow

$installerPath = "$env:TEMP\DockerDesktop-4.28.0.exe"
$downloadUrl = "https://desktop.docker.com/win/main/amd64/139021/Docker%20Desktop%20Installer.exe"

if (!(Test-Path $installerPath)) {
    try {
        Write-Host "  Downloading from Docker... (~500MB)" -ForegroundColor Gray
        Write-Host "  This may take a few minutes..." -ForegroundColor Gray
        
        Invoke-WebRequest -Uri $downloadUrl -OutFile $installerPath -UseBasicParsing
        
        Write-Host "  Download complete!" -ForegroundColor Green
    } catch {
        Write-Error "Download failed: $_"
        Write-Host ""
        Write-Host "Please manually download from:" -ForegroundColor Yellow
        Write-Host "https://docs.docker.com/desktop/release-notes/" -ForegroundColor Cyan
        Write-Host "Look for version 4.28.0" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host "  Using existing download" -ForegroundColor Green
}

# Step 4: Install with Hyper-V backend
Write-Host "[4/5] Installing Docker Desktop (Hyper-V backend)..." -ForegroundColor Yellow
Write-Host "  This will take 5-10 minutes. Please wait..." -ForegroundColor Magenta

# Create D drive directories first
$dockerDataPath = "D:\docker-data"
@("docker", "wsl") | ForEach-Object {
    $dir = "$dockerDataPath\$_"
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Run installer with Hyper-V explicitly (NO WSL2)
$process = Start-Process -FilePath $installerPath -ArgumentList "install", "--quiet", "--backend=hyper-v" -PassThru

# Show progress
$dots = 0
while (!$process.HasExited) {
    Write-Host "." -NoNewline -ForegroundColor Cyan
    Start-Sleep -Seconds 3
    $dots++
    if ($dots % 20 -eq 0) {
        Write-Host ""  # New line every minute
    }
}
Write-Host ""

if ($process.ExitCode -eq 0) {
    Write-Host "  Installation successful!" -ForegroundColor Green
} else {
    Write-Warning "Install exit code: $($process.ExitCode)"
    Write-Host "  This may still be OK - checking..." -ForegroundColor Yellow
}

# Step 5: Configure for D drive
Write-Host "[5/5] Configuring D drive data location..." -ForegroundColor Yellow

# Wait for settings file
$settingsPath = "$env:APPDATA\Docker\settings.json"
$waitCount = 0
while (!(Test-Path $settingsPath) -and $waitCount -lt 10) {
    Start-Sleep -Seconds 2
    $waitCount++
}

if (Test-Path $settingsPath) {
    # Disable WSL2
    $settings = Get-Content $settingsPath | ConvertFrom-Json
    $settings.wslEngineEnabled = $false
    $settings | ConvertTo-Json -Depth 10 | Out-File -FilePath $settingsPath -Encoding UTF8 -Force
    
    # Set data root
    $daemonConfig = @{
        "data-root" = "$dockerDataPath\docker"
        "storage-driver" = "overlay2"
    } | ConvertTo-Json
    
    $dockerConfigDir = "$env:USERPROFILE\.docker"
    if (!(Test-Path $dockerConfigDir)) {
        New-Item -ItemType Directory -Path $dockerConfigDir -Force | Out-Null
    }
    $daemonConfig | Out-File -FilePath "$dockerConfigDir\daemon.json" -Encoding UTF8 -Force
    
    Write-Host "  Configuration complete" -ForegroundColor Green
}

# Final check
$dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerExe) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS! Docker Desktop 4.28.0 installed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "RESTART REQUIRED!" -ForegroundColor Red
    Write-Host ""
    
    $restart = Read-Host "Restart computer now? (Y/N)"
    if ($restart -eq "Y" -or $restart -eq "y") {
        Restart-Computer -Force
    }
} else {
    Write-Error "Installation verification failed - Docker Desktop.exe not found"
    Write-Host ""
    Write-Host "Try manual install from:" -ForegroundColor Yellow
    Write-Host "https://docs.docker.com/desktop/release-notes/" -ForegroundColor Cyan
}

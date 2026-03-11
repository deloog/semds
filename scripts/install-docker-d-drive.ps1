# SEMS Docker Install Script - D Drive Data Configuration
# This installs Docker Desktop to C: (required), but moves all data to D:

param(
    [switch]$SkipDownload,
    [switch]$SkipWSLConfig
)

$ErrorActionPreference = "Stop"
$DockerDataPath = "D:\docker-data"
$WSLConfigPath = "$env:USERPROFILE\.wslconfig"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SEMDS Docker Install Script (D Drive)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin privileges
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run as Administrator (Right-click -> Run as administrator)"
    exit 1
}

# Step 1: Create D drive data directories
Write-Host "[1/6] Creating D drive data directories..." -ForegroundColor Yellow
$dirs = @(
    "$DockerDataPath\docker-desktop-data",
    "$DockerDataPath\docker-desktop",
    "$DockerDataPath\wsl",
    "$DockerDataPath\docker"
)
foreach ($dir in $dirs) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  Created: $dir" -ForegroundColor Gray
    }
}

# Step 2: Configure WSL2 to use D drive
if (!$SkipWSLConfig) {
    Write-Host "[2/6] Configuring WSL2 data location to D drive..." -ForegroundColor Yellow
    
    # Shutdown WSL
    Write-Host "  Stopping WSL..." -ForegroundColor Gray
    wsl --shutdown 2>$null
    
    # Create .wslconfig file
    $wslConfig = @"
[wsl2]
memory=8GB
processors=4
localhostForwarding=true
swap=$DockerDataPath\wsl\swap.vhdx
swapFile=$DockerDataPath\wsl\swap.vhdx
"@
    
    # Check if Docker WSL already exists
    $wslList = wsl --list --quiet 2>$null
    if ($wslList -match "docker-desktop") {
        Write-Host "  Found existing Docker WSL, migrating to D drive..." -ForegroundColor Gray
        
        # Export and migrate docker-desktop-data
        Write-Host "  Exporting docker-desktop-data..." -ForegroundColor Gray
        wsl --export docker-desktop-data "$DockerDataPath\docker-desktop-data.tar" 2>$null
        if ($LASTEXITCODE -eq 0) {
            wsl --unregister docker-desktop-data 2>$null
            wsl --import docker-desktop-data "$DockerDataPath\docker-desktop-data" "$DockerDataPath\docker-desktop-data.tar" 2>$null
            Remove-Item "$DockerDataPath\docker-desktop-data.tar" -Force -ErrorAction SilentlyContinue
        }
        
        # Export and migrate docker-desktop
        Write-Host "  Exporting docker-desktop..." -ForegroundColor Gray
        wsl --export docker-desktop "$DockerDataPath\docker-desktop.tar" 2>$null
        if ($LASTEXITCODE -eq 0) {
            wsl --unregister docker-desktop 2>$null
            wsl --import docker-desktop "$DockerDataPath\docker-desktop" "$DockerDataPath\docker-desktop.tar" 2>$null
            Remove-Item "$DockerDataPath\docker-desktop.tar" -Force -ErrorAction SilentlyContinue
        }
        
        Write-Host "  WSL data migrated to D drive" -ForegroundColor Green
    }
    
    # Write WSL config
    $wslConfig | Out-File -FilePath $WSLConfigPath -Encoding UTF8 -Force
    Write-Host "  WSL config written to: $WSLConfigPath" -ForegroundColor Green
}

# Step 3: Download Docker Desktop
$InstallerPath = "$env:TEMP\DockerDesktopInstaller.exe"
if (!$SkipDownload -or !(Test-Path $InstallerPath)) {
    Write-Host "[3/6] Downloading Docker Desktop..." -ForegroundColor Yellow
    $DockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    
    try {
        Invoke-WebRequest -Uri $DockerUrl -OutFile $InstallerPath -UseBasicParsing
        Write-Host "  Download complete: $InstallerPath" -ForegroundColor Green
    } catch {
        Write-Error "Download failed. Please download manually from: https://www.docker.com/products/docker-desktop"
        exit 1
    }
} else {
    Write-Host "[3/6] Using existing installer..." -ForegroundColor Yellow
}

# Step 4: Install Docker Desktop
Write-Host "[4/6] Installing Docker Desktop..." -ForegroundColor Yellow
Write-Host "  Note: Program files go to C: (~500MB), data goes to D:" -ForegroundColor Gray
Write-Host "  Installing, please wait..." -ForegroundColor Gray

$installArgs = "install", "--quiet", "--always-start-service"
$process = Start-Process -FilePath $InstallerPath -ArgumentList $installArgs -Wait -PassThru

if ($process.ExitCode -ne 0) {
    Write-Warning "Docker Desktop installation may have issues, exit code: $($process.ExitCode)"
} else {
    Write-Host "  Docker Desktop installation complete" -ForegroundColor Green
}

# Step 5: Configure Docker daemon.json (data root to D:)
Write-Host "[5/6] Configuring Docker data directory to D drive..." -ForegroundColor Yellow
$DockerConfigDir = "$env:USERPROFILE\.docker"
$DaemonConfigPath = "$DockerConfigDir\daemon.json"

if (!(Test-Path $DockerConfigDir)) {
    New-Item -ItemType Directory -Path $DockerConfigDir -Force | Out-Null
}

$daemonConfig = @{
    "data-root" = "$DockerDataPath\docker"
    "exec-opts" = @("native.cgroupdriver=cgroupfs")
    "log-driver" = "json-file"
    "log-opts" = @{
        "max-size" = "10m"
        "max-file" = "3"
    }
    "storage-driver" = "overlay2"
} | ConvertTo-Json -Depth 10

$daemonConfig | Out-File -FilePath $DaemonConfigPath -Encoding UTF8 -Force
Write-Host "  Docker config written to: $DaemonConfigPath" -ForegroundColor Green
Write-Host "  Data root: $DockerDataPath\docker" -ForegroundColor Gray

# Step 6: Create SEMDS startup script
Write-Host "[6/6] Creating SEMDS Docker configuration..." -ForegroundColor Yellow

$StartScriptContent = @'
# SEMDS Docker Setup Script
Write-Host "Setting up SEMDS Docker environment..."

# Check if Docker is running
$dockerInfo = docker info 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Please start Docker Desktop first" -ForegroundColor Red
    exit 1
}

# Build SEMDS sandbox image
Write-Host "Building SEMDS sandbox image..."
cd d:\semds
docker build -f docker/Dockerfile.sandbox -t semds-sandbox:latest .

# Verify
Write-Host "Verifying Docker environment..."
docker run --rm semds-sandbox:latest python -c "print('SEMDS Sandbox OK')"

Write-Host "SEMDS Docker environment ready!" -ForegroundColor Green
'@

$StartScriptPath = "$DockerDataPath\start-semds-docker.ps1"
$StartScriptContent | Out-File -FilePath $StartScriptPath -Encoding UTF8 -Force

Write-Host "  Startup script created: $StartScriptPath" -ForegroundColor Green

# Final message
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. RESTART YOUR COMPUTER (Required)" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Start Docker Desktop (first start may take 3-5 minutes)" -ForegroundColor White
Write-Host ""
Write-Host "3. Run SEMDS setup script:" -ForegroundColor White
Write-Host "   $StartScriptPath" -ForegroundColor Gray
Write-Host ""
Write-Host "Data Locations:" -ForegroundColor Cyan
Write-Host "   Docker data: $DockerDataPath\docker" -ForegroundColor Gray
Write-Host "   WSL data:    $DockerDataPath\docker-desktop*" -ForegroundColor Gray
Write-Host ""
Write-Host "C Drive Usage: ~500MB (program files only)" -ForegroundColor Green
Write-Host "D Drive Usage: Dynamic (images/containers/volumes)" -ForegroundColor Green
Write-Host ""
Write-Host "Note: After Windows updates Docker, you may need to re-run this script" -ForegroundColor Yellow

# Install Docker CE (Command Line Only) - No Desktop GUI
# This is the lightweight alternative to Docker Desktop

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker CE (Command Line) Install" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This installs Docker without the Desktop GUI" -ForegroundColor Yellow
Write-Host "Uses less resources and more reliable" -ForegroundColor Yellow
Write-Host ""

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run as Administrator"
    exit 1
}

# Enable required features
Write-Host "[1/4] Enabling required Windows features..." -ForegroundColor Yellow
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart -ErrorAction SilentlyContinue
dism /Online /Enable-Feature /FeatureName:Containers /All /NoRestart | Out-Null
Write-Host "      Done" -ForegroundColor Green

# Install Docker Provider
Write-Host "[2/4] Installing Docker Module..." -ForegroundColor Yellow
Install-Module -Name DockerMsftProvider -Repository PSGallery -Force -ErrorAction SilentlyContinue
Write-Host "      Done" -ForegroundColor Green

# Install Docker
Write-Host "[3/4] Installing Docker CE..." -ForegroundColor Yellow
Install-Package -Name docker -ProviderName DockerMsftProvider -Force -ErrorAction SilentlyContinue
Write-Host "      Done" -ForegroundColor Green

# Start Docker service
Write-Host "[4/4] Starting Docker service..." -ForegroundColor Yellow
Start-Service docker -ErrorAction SilentlyContinue
Set-Service docker -StartupType Automatic -ErrorAction SilentlyContinue
Write-Host "      Done" -ForegroundColor Green

# Configure D drive
Write-Host "Configuring D drive data..." -ForegroundColor Yellow
$daemonConfig = @{
    "data-root" = "D:\docker-data\docker"
    "exec-opts" = @("native.cgroupdriver=cgroupfs")
    "storage-driver" = "overlay2"
} | ConvertTo-Json

$dockerDir = "$env:ProgramData\docker\config"
New-Item -ItemType Directory -Path $dockerDir -Force | Out-Null
$daemonConfig | Out-File -FilePath "$dockerDir\daemon.json" -Encoding UTF8 -Force

# Restart to apply
Restart-Service docker -Force -ErrorAction SilentlyContinue

# Test
Write-Host "Testing Docker..." -ForegroundColor Yellow
$test = docker version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS! Docker CE is running!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "No GUI - use command line:" -ForegroundColor Cyan
    Write-Host "  docker run hello-world" -ForegroundColor White
    Write-Host "  docker build -t test ." -ForegroundColor White
    Write-Host ""
    Write-Host "Data location: D:\docker-data\" -ForegroundColor Gray
} else {
    Write-Host "Docker may need restart. Run after reboot: Start-Service docker" -ForegroundColor Yellow
}

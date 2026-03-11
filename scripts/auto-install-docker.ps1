# Auto-install Docker using existing installer
# One-click solution

$ErrorActionPreference = "Continue"
$ProgressPreference = 'SilentlyContinue'

Write-Host "========================================" -ForegroundColor Green
Write-Host "Docker Auto-Install (Local Installer)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

# Use existing installer
$installer = "$env:TEMP\DockerDesktopInstaller.exe"
if (!(Test-Path $installer)) {
    Write-Error "Installer not found at $installer"
    exit 1
}

Write-Host "Found installer: $installer" -ForegroundColor Gray
Write-Host "Starting silent installation..." -ForegroundColor Yellow
Write-Host "This will take 5-10 minutes. Do not close this window." -ForegroundColor Magenta
Write-Host ""

# Kill any running Docker
Get-Process | Where-Object {$_.Name -match "docker"} | Stop-Process -Force -ErrorAction SilentlyContinue
wsl --shutdown 2>$null

# Enable Hyper-V (required)
Write-Host "[1/3] Enabling Hyper-V..." -ForegroundColor Yellow
dism /Online /Enable-Feature /FeatureName:Microsoft-Hyper-V-All /All /NoRestart | Out-Null
dism /Online /Enable-Feature /FeatureName:Containers /All /NoRestart | Out-Null
Write-Host "      Done" -ForegroundColor Green

# Create D drive directories
Write-Host "[2/3] Preparing D drive..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "D:\docker-data\docker" -Force | Out-Null
Write-Host "      Done" -ForegroundColor Green

# Install Docker with progress
Write-Host "[3/3] Installing Docker Desktop..." -ForegroundColor Yellow
Write-Host "      Please wait..." -ForegroundColor Gray

$process = Start-Process -FilePath $installer -ArgumentList "install", "--quiet", "--always-start-service" -PassThru

# Show spinner while waiting
$spinner = @('|', '/', '-', '\')
$i = 0
while (!$process.HasExited) {
    Write-Host "`r      Installing... $($spinner[$i % 4])" -NoNewline -ForegroundColor Cyan
    Start-Sleep -Milliseconds 500
    $i++
}
Write-Host "`r                          " -NoNewline
Write-Host ""

if ($process.ExitCode -eq 0) {
    Write-Host "      Installation successful!" -ForegroundColor Green
} else {
    Write-Host "      Exit code: $($process.ExitCode) (may still be OK)" -ForegroundColor Yellow
}

# Configure D drive
$daemonJson = @"
{
    "data-root": "D:\\docker-data\\docker",
    "storage-driver": "overlay2"
}
"@

New-Item -ItemType Directory -Path "$env:USERPROFILE\.docker" -Force | Out-Null
$daemonJson | Out-File -FilePath "$env:USERPROFILE\.docker\daemon.json" -Encoding UTF8 -Force

# Check if installed
$dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerExe) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "SUCCESS! Docker Desktop Installed!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Location: $dockerExe" -ForegroundColor Gray
    Write-Host "Data: D:\docker-data\" -ForegroundColor Gray
    Write-Host ""
    Write-Host "NEXT STEPS:" -ForegroundColor Yellow
    Write-Host "1. RESTART COMPUTER (Required for Hyper-V)" -ForegroundColor Red
    Write-Host "2. After restart, run: & '$dockerExe'" -ForegroundColor White
    Write-Host "3. Wait for whale icon (3-5 minutes)" -ForegroundColor White
    Write-Host ""
    
    $restart = Read-Host "Restart now? (Y/N)"
    if ($restart -eq "Y" -or $restart -eq "y") {
        Restart-Computer -Force
    }
} else {
    Write-Host "Installation may have failed. Check 'Add or Remove Programs'" -ForegroundColor Red
}

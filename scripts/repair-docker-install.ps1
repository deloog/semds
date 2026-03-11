# Repair Docker Desktop Installation
# The install log shows it's installed but files may be corrupted

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Desktop Repair Tool" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Admin check
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run as Administrator"
    exit 1
}

# Step 1: Find the actual install location from registry
Write-Host "[1/4] Finding installation location..." -ForegroundColor Yellow
$regPaths = @(
    "HKLM:\SOFTWARE\Docker Inc.\Docker Desktop",
    "HKLM:\SOFTWARE\WOW6432Node\Docker Inc.\Docker Desktop"
)

$installPath = $null
foreach ($regPath in $regPaths) {
    if (Test-Path $regPath) {
        $props = Get-ItemProperty $regPath -ErrorAction SilentlyContinue
        if ($props.InstallPath) {
            $installPath = $props.InstallPath
            Write-Host "  Found in registry: $installPath" -ForegroundColor Green
            break
        }
    }
}

if (!$installPath) {
    $installPath = "C:\Program Files\Docker\Docker"
    Write-Host "  Using default: $installPath" -ForegroundColor Yellow
}

# Step 2: Check what's actually there
Write-Host "[2/4] Checking installation files..." -ForegroundColor Yellow
if (Test-Path $installPath) {
    Write-Host "  Install directory exists" -ForegroundColor Gray
    $files = Get-ChildItem $installPath -File -ErrorAction SilentlyContinue
    Write-Host "  Files found: $($files.Count)" -ForegroundColor Gray
    
    if ($files.Count -eq 0) {
        Write-Host "  WARNING: Directory is empty!" -ForegroundColor Red
        $needsReinstall = $true
    } else {
        $files | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor DarkGray }
    }
} else {
    Write-Host "  Directory does not exist!" -ForegroundColor Red
    $needsReinstall = $true
}

# Step 3: Check for Docker Desktop.exe specifically
$dockerExe = Join-Path $installPath "Docker Desktop.exe"
if (Test-Path $dockerExe) {
    Write-Host "  Docker Desktop.exe found!" -ForegroundColor Green
} else {
    Write-Host "  Docker Desktop.exe NOT found!" -ForegroundColor Red
    $needsReinstall = $true
    
    # Look for it elsewhere
    $possibleExes = Get-ChildItem "$installPath\*.exe" -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.Name -like "*Docker*"}
    if ($possibleExes) {
        Write-Host "  Found possible executables:" -ForegroundColor Yellow
        $possibleExes | ForEach-Object { Write-Host "    - $($_.FullName)" -ForegroundColor Gray }
    }
}

# Step 4: Fix or Reinstall
Write-Host "[3/4] Fixing installation..." -ForegroundColor Yellow

if ($needsReinstall) {
    Write-Host "  Installation is incomplete. Running repair..." -ForegroundColor Yellow
    
    # Find the installer
    $installer = "$env:TEMP\DockerDesktopInstaller.exe"
    $altInstaller = "$env:TEMP\DockerDesktopInstallers\1773101119107987300\Docker Desktop Installer.exe"
    
    $useInstaller = $null
    if (Test-Path $altInstaller) {
        $useInstaller = $altInstaller
    } elseif (Test-Path $installer) {
        $useInstaller = $installer
    }
    
    if ($useInstaller) {
        Write-Host "  Running: $useInstaller" -ForegroundColor Gray
        Write-Host "  Please wait... (this may take 5-10 minutes)" -ForegroundColor Magenta
        
        # Run repair install
        $process = Start-Process -FilePath $useInstaller -ArgumentList "install", "--quiet" -Wait -PassThru
        
        if ($process.ExitCode -eq 0) {
            Write-Host "  Repair completed!" -ForegroundColor Green
        } else {
            Write-Warning "Repair exit code: $($process.ExitCode)"
        }
    } else {
        Write-Error "Installer not found!"
        exit 1
    }
} else {
    Write-Host "  Installation appears intact" -ForegroundColor Green
}

# Step 5: Verify and create shortcuts
Write-Host "[4/4] Verifying and creating shortcuts..." -ForegroundColor Yellow

$dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
if (Test-Path $dockerExe) {
    Write-Host "  SUCCESS! Docker Desktop found" -ForegroundColor Green
    
    # Create a simple start script
    $startScript = @"
# Start Docker Desktop
Start-Process "$dockerExe"
Write-Host "Docker Desktop starting..." -ForegroundColor Green
Write-Host "Wait for whale icon in system tray" -ForegroundColor Yellow
"@
    
    $startScriptPath = "D:\docker-data\start-docker.ps1"
    $startScript | Out-File -FilePath $startScriptPath -Encoding UTF8 -Force
    Write-Host "  Start script created: $startScriptPath" -ForegroundColor Green
    
    # Start it
    Write-Host ""
    $startNow = Read-Host "Start Docker Desktop now? (Y/N)"
    if ($startNow -eq "Y" -or $startNow -eq "y") {
        Write-Host "Starting Docker Desktop..." -ForegroundColor Green
        Start-Process $dockerExe
        Write-Host ""
        Write-Host "Docker Desktop is starting!" -ForegroundColor Green
        Write-Host "Wait for whale icon in system tray (3-5 minutes)" -ForegroundColor Yellow
    }
} else {
    Write-Error "Docker Desktop.exe still not found after repair!"
    Write-Host ""
    Write-Host "Manual fix required:" -ForegroundColor Yellow
    Write-Host "1. Uninstall Docker from 'Add or Remove Programs'" -ForegroundColor White
    Write-Host "2. Delete C:\Program Files\Docker folder manually" -ForegroundColor White  
    Write-Host "3. Delete C:\ProgramData\DockerDesktop folder" -ForegroundColor White
    Write-Host "4. Reboot" -ForegroundColor White
    Write-Host "5. Download fresh installer from docker.com" -ForegroundColor White
    Write-Host "6. Install with Hyper-V backend" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Repair process complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

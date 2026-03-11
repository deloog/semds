# Switch to Hyper-V backend when WSL2 doesn't work
# Hyper-V uses more resources but is more stable

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Desktop Hyper-V Backend Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check admin privileges
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Please run as Administrator"
    exit 1
}

# Step 1: Enable Hyper-V
Write-Host "[1/3] Enabling Hyper-V..." -ForegroundColor Yellow

$hyperv = Get-WindowsOptionalFeature -FeatureName Microsoft-Hyper-V-All -Online -ErrorAction SilentlyContinue
if ($hyperv.State -ne "Enabled") {
    Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -NoRestart -All
    Write-Host "  Hyper-V enabled, restart required" -ForegroundColor Yellow
    $needRestart = $true
} else {
    Write-Host "  Hyper-V already enabled" -ForegroundColor Green
}

# Step 2: Configure Docker to use Hyper-V
Write-Host "[2/3] Configuring Docker to use Hyper-V..." -ForegroundColor Yellow

$dockerSettingsPath = "$env:APPDATA\Docker\settings.json"

if (Test-Path $dockerSettingsPath) {
    $settings = Get-Content $dockerSettingsPath | ConvertFrom-Json
    $settings.wslEngineEnabled = $false
    $settings | ConvertTo-Json -Depth 10 | Out-File -FilePath $dockerSettingsPath -Encoding UTF8
    Write-Host "  Docker settings updated" -ForegroundColor Green
} else {
    Write-Host "  Docker settings file not found, will configure on first start" -ForegroundColor Yellow
}

# Step 3: Disable WSL config
Write-Host "[3/3] Disabling WSL config..." -ForegroundColor Yellow

$wslConfigPath = "$env:USERPROFILE\.wslconfig"
if (Test-Path $wslConfigPath) {
    Rename-Item $wslConfigPath "$wslConfigPath.disabled" -Force
    Write-Host "  WSL config disabled" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Configuration Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

if ($needRestart) {
    Write-Host "RESTART REQUIRED!" -ForegroundColor Red
    Write-Host ""
    $restart = Read-Host "Restart now? (Y/N)"
    if ($restart -eq "Y" -or $restart -eq "y") {
        Restart-Computer -Force
    }
} else {
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Start Docker Desktop" -ForegroundColor White
    Write-Host "2. Go to Settings - General" -ForegroundColor White
    Write-Host "3. Ensure 'Use the WSL 2 based engine' is UNCHECKED" -ForegroundColor White
    Write-Host "4. Click Apply & Restart" -ForegroundColor White
}

Write-Host ""
Write-Host "Notes:" -ForegroundColor Yellow
Write-Host "- Hyper-V creates a real VM" -ForegroundColor Gray
Write-Host "- Higher memory usage (recommend 4GB+)" -ForegroundColor Gray
Write-Host "- Slower startup than WSL2" -ForegroundColor Gray
Write-Host "- But more stable, fewer pipe errors" -ForegroundColor Gray

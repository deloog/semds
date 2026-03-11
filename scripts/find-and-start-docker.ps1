# Find and start Docker Desktop

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Finding Docker Desktop..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Common locations to check
$possiblePaths = @(
    "C:\Program Files\Docker\Docker\Docker Desktop.exe",
    "C:\Program Files\Docker\Docker\frontend\Docker Desktop.exe",
    "$env:LOCALAPPDATA\Programs\Docker\Docker\Docker Desktop.exe",
    "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
    "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
)

$foundPath = $null
foreach ($path in $possiblePaths) {
    Write-Host "Checking: $path" -ForegroundColor Gray
    if (Test-Path $path) {
        $foundPath = $path
        Write-Host "  FOUND!" -ForegroundColor Green
        break
    }
}

if ($foundPath) {
    Write-Host ""
    Write-Host "Docker Desktop found at:" -ForegroundColor Green
    Write-Host $foundPath -ForegroundColor Yellow
    Write-Host ""
    
    $start = Read-Host "Start Docker Desktop now? (Y/N)"
    if ($start -eq "Y" -or $start -eq "y") {
        Write-Host "Starting Docker Desktop..." -ForegroundColor Green
        Start-Process $foundPath
        Write-Host ""
        Write-Host "Docker Desktop is starting!" -ForegroundColor Green
        Write-Host "Wait for the whale icon in system tray (3-5 minutes)" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Warning "Docker Desktop not found in standard locations."
    Write-Host ""
    Write-Host "Possible reasons:" -ForegroundColor Yellow
    Write-Host "  - Installation didn't complete" -ForegroundColor White
    Write-Host "  - Installed in a custom location" -ForegroundColor White
    Write-Host "  - Installation was cancelled" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "1. Run manual install: .\manual-install-docker.ps1" -ForegroundColor White
    Write-Host "2. Check 'Add or Remove Programs' in Windows Settings" -ForegroundColor White
    Write-Host "3. Download from https://www.docker.com/products/docker-desktop" -ForegroundColor White
}

@echo off
echo ========================================
echo Docker Desktop Install (Hyper-V Mode)
echo ========================================
echo.
echo This will:
echo   - Enable Hyper-V (requires restart)
echo   - Install Docker Desktop without WSL2
echo   - Configure data to D drive
echo.
pause

powershell -ExecutionPolicy Bypass -File "%~dp0install-docker-hyperv.ps1"

echo.
pause

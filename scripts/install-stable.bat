@echo off
echo ========================================
echo Docker Desktop 4.28.0 Stable Install
echo ========================================
echo.
echo This will:
echo   - Clean up broken Docker installation
echo   - Enable Hyper-V
echo   - Download Docker Desktop 4.28.0 (Stable)
echo   - Install with Hyper-V backend
echo   - Configure data to D drive
echo.
pause

powershell -ExecutionPolicy Bypass -File "%~dp0install-docker-stable.ps1"

echo.
pause

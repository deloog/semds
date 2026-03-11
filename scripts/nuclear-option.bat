@echo off
echo ========================================
echo DOCKER NUCLEAR RESET
echo Complete Fresh Install with Hyper-V
echo ========================================
echo.
echo This will:
echo   1. COMPLETELY remove Docker Desktop
echo   2. Clean all Docker data
echo   3. Enable Hyper-V (Windows feature)
echo   4. Install Docker with Hyper-V backend
echo   5. Configure data to D drive
echo.
echo *** THIS WILL DELETE ALL DOCKER DATA ***
echo *** Containers, images, volumes GONE ***
echo.
pause

powershell -ExecutionPolicy Bypass -File "%~dp0nuclear-option-docker.ps1"

echo.
pause

@echo off
chcp 65001 >nul
echo ========================================
echo SEMDS Docker Installer (D Drive Data)
echo ========================================
echo.
echo This will:
echo   - Install Docker Desktop to C: (program files ~500MB)
echo   - Configure all data storage to D: (images/containers/volumes)
echo   - Configure WSL2 to D: (virtual disk)
echo.
echo Press any key to continue, or close window to cancel...
pause >nul

echo.
echo Starting PowerShell installation script...
echo.

powershell -ExecutionPolicy Bypass -Command "& '%~dp0install-docker-d-drive.ps1'"

echo.
echo ========================================
echo Installation script completed
pause

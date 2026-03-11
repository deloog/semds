@echo off
chcp 65001 >nul
echo ========================================
echo Docker Desktop 错误修复工具
echo ========================================
echo.
echo 此工具将修复以下错误：
echo   - service exited with code 1
echo   - read/write on closed pipe
echo   - Docker Desktop 无法启动
echo.
pause

echo.
echo 正在启动修复脚本...
echo 需要管理员权限！
echo.

powershell -ExecutionPolicy Bypass -Command "& '%~dp0fix-docker-error.ps1'"

echo.
echo ========================================
echo 修复脚本执行完毕
echo ========================================
pause

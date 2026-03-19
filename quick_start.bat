@echo off
chcp 65001
echo ========================================
echo SEMDS Matrix Challenge - Quick Start
echo ========================================
echo.

REM Start Ollama in background
start /B "" "C:\Users\helen\AppData\Local\Programs\Ollama\ollama.exe" serve

REM Wait for startup
timeout /t 3 /nobreak >nul

echo [OK] Ollama started
echo.

REM Test connection
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Ollama API is ready
) else (
    echo [Warning] Ollama may still be starting...
)

echo.
echo ========================================
echo Starting Matrix Multiplication Challenge
echo ========================================
echo.

cd /d D:\semds
python start_matrix_challenge.py

echo.
echo Press any key to exit...
pause >nul

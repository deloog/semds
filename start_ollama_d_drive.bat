@echo off
chcp 65001
cls

echo ========================================
echo SEMDS Ollama Launcher (D Drive)
echo ========================================
echo.

REM Set model directory to D drive
set OLLAMA_MODELS=D:\ollama_models

REM Check if Ollama exists
if not exist "%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe" (
    echo [ERROR] Ollama not found!
    echo Please install from: https://ollama.com/download
    pause
    exit /b 1
)

echo [OK] Model directory: %OLLAMA_MODELS%
echo.

REM Check if model exists
if not exist "D:\ollama_models\manifests\*qwen*" (
    echo [INFO] Qwen model not found. Pulling...
    "%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe" pull qwen3.5:4b
    if errorlevel 1 (
        echo [ERROR] Failed to pull model
        pause
        exit /b 1
    )
)

echo [OK] Starting Ollama service...
echo [OK] API will be available at: http://localhost:11434
echo.
echo Press Ctrl+C to stop
echo.

REM Start Ollama with D drive models
"%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe" serve

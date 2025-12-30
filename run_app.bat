@echo off
setlocal

set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

if not exist .venv ( 
    echo ERROR: virtual environment .venv not found.
    pause
    exit /b 1
)

call .venv\Scripts\activate

if exist app.py (
    python app.py
) else (
    python main.py
)

if %errorlevel% neq 0 (
    echo Program exited with error %errorlevel%.
)

pause

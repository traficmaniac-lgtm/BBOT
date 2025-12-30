@echo off
setlocal

set PROJECT_DIR=%~dp0
cd /d %PROJECT_DIR%

if exist .git ( 
    echo Updating repository in %PROJECT_DIR%
    git pull
) else (
    echo ERROR: Directory is not a git repository.
    pause
    exit /b 1
)

echo Update complete.
pause

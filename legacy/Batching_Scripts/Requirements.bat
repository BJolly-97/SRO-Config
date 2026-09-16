@echo off

title Configurational Analysis v1.0

cd /d "%~dp0.."

echo Installing SRO-Config and required Python modules...
python3 -m pip install --quiet --no-warn-script-location -e .
if %errorlevel% neq 0 (
    echo Dependency install failed. Check Python installation.
    pause
    exit /b
)
echo All required modules installed.

echo.

cmd

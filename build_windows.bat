@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "VENV_PY=.venv\Scripts\python.exe"

if exist ".venv" if not exist "%VENV_PY%" (
    echo Existing .venv folder is incomplete. Recreating it...
    rmdir /s /q ".venv"
)

if not exist "%VENV_PY%" (
    echo Creating isolated Python environment...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        echo Python 3.12 was not found. Trying the default Python launcher...
        py -m venv .venv
    )
    if errorlevel 1 (
        echo Failed to create .venv. Install Python 3.12 from python.org, then run this again.
        pause
        exit /b 1
    )
)

echo Installing desktop build requirements...
"%VENV_PY%" -m pip install --upgrade pip
if errorlevel 1 goto build_failed

"%VENV_PY%" -m pip install -r requirements-desktop.txt
if errorlevel 1 goto build_failed

echo Building A321 Flight Planner.exe...
"%VENV_PY%" build.py
if errorlevel 1 goto build_failed

if exist "dist\A321 Flight Planner.exe" (
    echo.
    echo Build complete:
    echo %cd%\dist\A321 Flight Planner.exe
    pause
) else (
    echo.
    echo Build did not produce the EXE. Review the output above.
    pause
    exit /b 1
)

endlocal
exit /b 0

:build_failed
echo.
echo Build failed. Review the error above.
pause
exit /b 1

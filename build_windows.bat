@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv" (
    py -3.12 -m venv .venv 2>nul
    if errorlevel 1 (
        py -m venv .venv
    )
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements-desktop.txt
python build.py

if exist "dist\A321 Flight Planner.exe" (
    echo.
    echo Build complete:
    echo %cd%\dist\A321 Flight Planner.exe
) else (
    echo.
    echo Build did not produce the EXE. Review the output above.
    exit /b 1
)

endlocal

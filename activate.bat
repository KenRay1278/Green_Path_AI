@echo off
REM Activation and Startup Script for Windows
REM Jakarta Pathfinding AI

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║             Jakarta Pathfinding AI - Quick Start              ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

REM Check if conda is available
where conda >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Conda not found in PATH!
    echo.
    echo Please install Miniconda from:
    echo https://docs.conda.io/en/latest/miniconda.html
    echo.
    pause
    exit /b 1
)

echo ✅ Conda found!
echo.

REM Check if environment exists
conda env list | find "green_path" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ⚠️  Environment 'green_path' not found!
    echo.
    echo Creating environment...
    python setup_environment.py
    if %ERRORLEVEL% NEQ 0 (
        echo ❌ Failed to create environment
        pause
        exit /b 1
    )
)

echo.
echo ✅ Activating environment 'green_path'...
echo.

REM Check if data exists
if not exist "data\processed\jakarta_network_processed.pkl" (
    echo ⚠️  Network data not found!
    echo.
    echo Please run:
    echo   1. cd scripts
    echo   2. python network_extractor.py
    echo   3. python add_pollution_weights.py
    echo.
    set /p choice="Setup data now? (y/n): "
    if /i "%choice%"=="y" (
        cd scripts
        echo Running network extractor...
        call conda activate green_path
        python network_extractor.py
        echo Running pollution weights...
        python add_pollution_weights.py
        cd ..
    )
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo   Starting Flask Server...
echo ═══════════════════════════════════════════════════════════════
echo.

REM Activate and run server
cmd /k "conda activate green_path && python run_server.py"
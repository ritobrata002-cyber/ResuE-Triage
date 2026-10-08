@echo off
title RescuE-Triage Decision Support System Launcher
color 0B
cls

echo ===============================================================================
echo                RescuE-Triage: Emergency Dispatch Priority Router
echo         Dynamic Emergency Priority Index (DEPI) Decision-Support System
echo ===============================================================================
echo.
echo  Select Launch Mode:
echo    [1] Launch Modern Desktop GUI Application (Default)
echo    [2] Launch Web Command Center Dashboard (Localhost:8080)
echo    [3] Run Computational Algorithmic Benchmark (O(log N) vs O(N))
echo    [4] Run Automated Unit Test Suite
echo.
set /p choice="Enter choice (1-4, default 1): "

if "%choice%"=="2" (
    echo.
    echo Starting Web Command Center on http://127.0.0.1:8080 ...
    python main.py --web
) else if "%choice%"=="3" (
    echo.
    echo Running Algorithmic Benchmarks...
    python main.py --benchmark
    pause
) else if "%choice%"=="4" (
    echo.
    echo Running Automated Unit Tests...
    python main.py --test
    pause
) else (
    echo.
    echo Launching Desktop GUI Application...
    python main.py
)

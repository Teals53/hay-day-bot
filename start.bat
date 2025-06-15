@echo off
title HayDay Bot - Clean and Fast
echo ========================================
echo      HayDay Bot - Clean and Fast
echo ========================================
echo.

echo [INFO] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found
    echo Please run install.bat first
    echo.
    pause
    exit /b 1
)

python --version
echo.

echo [INFO] Checking core dependencies...

echo import sys > check_deps.py
echo try: >> check_deps.py
echo     import cv2, numpy, PIL, pyautogui, keyboard, mss, tkinter >> check_deps.py
echo     print('[INFO] All dependencies available!') >> check_deps.py
echo except ImportError as e: >> check_deps.py
echo     print('[ERROR] Missing dependency:', str(e)) >> check_deps.py
echo     print('Please run install.bat to install missing dependencies') >> check_deps.py
echo     sys.exit(1) >> check_deps.py

python check_deps.py
if errorlevel 1 (
    del check_deps.py 2>nul
    pause
    exit /b 1
)

del check_deps.py 2>nul

echo [INFO] Starting HayDay Bot...
echo ========================================
echo.
echo Quick Start:
echo 1. Make sure HayDay is running and visible
echo 2. Position your field clearly on screen  
echo 3. Press F4 to start, F5 to stop
echo 4. Monitor the clean GUI for real-time feedback
echo.

echo [STARTING] Launching Clean and Fast GUI...
python main.py

echo.
echo ========================================
echo     HayDay Bot - Session Complete
echo ========================================
echo.
echo Press any key to exit...
pause >nul 
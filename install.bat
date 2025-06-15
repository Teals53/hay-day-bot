@echo off
echo ========================================
echo   HayDay Bot - Installation Script
echo ========================================
echo.

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

python --version
echo Python found successfully!
echo.

echo [2/4] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: Could not upgrade pip, continuing anyway...
)
echo.

echo [3/4] Installing required dependencies...
echo Installing from requirements.txt...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)
echo.

echo [4/4] Testing installation...
echo Testing core dependencies...

echo import sys > test_deps.py
echo try: >> test_deps.py
echo     import cv2; print('✓ OpenCV:', cv2.__version__) >> test_deps.py
echo     import numpy; print('✓ NumPy:', numpy.__version__) >> test_deps.py
echo     import PIL; print('✓ Pillow:', PIL.__version__) >> test_deps.py
echo     import pyautogui; print('✓ PyAutoGUI:', pyautogui.__version__) >> test_deps.py
echo     import keyboard; print('✓ Keyboard: Available') >> test_deps.py
echo     import mss; print('✓ MSS: Available') >> test_deps.py
echo     import tkinter; print('✓ Tkinter: Available') >> test_deps.py
echo     print('All dependencies verified successfully!') >> test_deps.py
echo except ImportError as e: >> test_deps.py
echo     print('ERROR: Missing dependency -', str(e)) >> test_deps.py
echo     sys.exit(1) >> test_deps.py

python test_deps.py
if errorlevel 1 (
    echo.
    echo ERROR: Some dependencies failed to install properly
    echo Please check the error messages above and run install.bat again
    del test_deps.py 2>nul
    pause
    exit /b 1
)

del test_deps.py 2>nul

echo.
echo ========================================
echo   Installation completed successfully!
echo ========================================
echo.
echo All dependencies verified:
echo - OpenCV (Computer Vision)
echo - NumPy (Array Processing)  
echo - Pillow (Image Processing)
echo - PyAutoGUI (Automation)
echo - Keyboard (Hotkeys)
echo - MSS (Screen Capture)
echo - Tkinter (GUI Framework)
echo.
echo You can now run the bot using:
echo   - Double-click "start.bat"
echo   - Or run: python main.py
echo.
echo Press any key to exit...
pause >nul 
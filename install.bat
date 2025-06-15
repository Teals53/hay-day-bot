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
python -c "import cv2, numpy, PIL, pyautogui, keyboard, mss, tkinter; print('All dependencies installed successfully!')"
if errorlevel 1 (
    echo ERROR: Some dependencies failed to install properly
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installation completed successfully!
echo ========================================
echo.
echo You can now run the bot using:
echo   - Double-click "start.bat"
echo   - Or run: python main.py
echo.
echo Press any key to exit...
pause >nul 
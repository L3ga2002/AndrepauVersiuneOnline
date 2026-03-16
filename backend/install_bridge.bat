@echo off
echo ============================================
echo   ANDREPAU POS - Instalare Bridge Service
echo ============================================
echo.
echo Se verifica Python...
python --version 2>NUL
if %errorlevel% neq 0 (
    echo.
    echo EROARE: Python nu este instalat!
    echo Descarcati Python de pe: https://www.python.org/downloads/
    echo IMPORTANT: Bifati "Add Python to PATH" la instalare!
    echo.
    pause
    exit /b 1
)
echo Python gasit!
echo.
echo Se instaleaza dependentele...
pip install flask flask-cors requests
echo.
echo ============================================
echo   Instalare completa!
echo   Porniti bridge-ul cu: start_bridge.bat
echo ============================================
echo.
pause

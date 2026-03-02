@echo off
title ANDREPAU - Instalare Bridge Service
color 0A
echo.
echo ============================================================
echo   ANDREPAU POS - Instalare Bridge Service
echo   Casa de Marcat INCOTEX Succes M7
echo ============================================================
echo.

:: Verifica Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [EROARE] Python nu este instalat!
    echo.
    echo Descarcati Python de pe: https://www.python.org/downloads/
    echo IMPORTANT: Bifati "Add Python to PATH" la instalare!
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b
)

echo [OK] Python gasit:
python --version
echo.

:: Instaleaza dependente (incearca pip, apoi python -m pip)
echo Instalare dependente...
pip install flask flask-cors 2>nul
if %errorlevel% neq 0 (
    echo pip direct nu merge, incerc python -m pip...
    python -m pip install flask flask-cors
)
echo.

if %errorlevel% neq 0 (
    echo [EROARE] Nu s-au putut instala dependentele!
    pause
    exit /b
)

echo [OK] Dependente instalate cu succes!
echo.
echo ============================================================
echo   Instalare completa! 
echo.
echo   Pentru a porni serviciul, rulati:
echo     python fiscal_bridge.py
echo.
echo   Sau dublu-click pe: start_bridge.bat
echo ============================================================
echo.
pause

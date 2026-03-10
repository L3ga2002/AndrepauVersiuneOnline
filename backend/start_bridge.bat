@echo off
echo ============================================
echo   ANDREPAU POS - Bridge Service v3.0
echo   Casa de Marcat INCOTEX Succes M7
echo ============================================
echo.
echo Pornire bridge service...
echo Pagina test: http://localhost:5555/test
echo.
echo Asigurati-va ca SuccesDrv are "Start procesare" apasat!
echo.
python fiscal_bridge.py
if %errorlevel% neq 0 (
    echo.
    echo EROARE la pornire! Verificati ca Python este instalat.
    echo Rulati intai: install_bridge.bat
    pause
)

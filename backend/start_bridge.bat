@echo off
cd /d "%~dp0"
echo ============================================
echo   ANDREPAU POS - Bridge Service v3.1
echo   Casa de Marcat INCOTEX Succes M7
echo ============================================
echo.
echo Folder curent: %CD%
echo.
echo Pornire bridge cu conexiune la cloud (PWA)...
echo Pagina test locala: http://localhost:5555/test
echo.
echo Asigurati-va ca SuccesDrv are "Start procesare" apasat!
echo.
python "%~dp0fiscal_bridge.py" "https://andrepau-pos-1.preview.emergentagent.com"
if %errorlevel% neq 0 (
    echo.
    echo EROARE la pornire!
    pause
)

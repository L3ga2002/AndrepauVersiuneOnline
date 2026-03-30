@echo off
cd /d "%~dp0"
echo ============================================
echo   ANDREPAU - Actualizare Bridge Service
echo ============================================
echo.

set "TARGET=C:\kit sistem\ANDREPAU\SuccesDrv_8_3"

if not exist "%TARGET%" (
    echo EROARE: Folderul %TARGET% nu exista!
    echo Modificati calea TARGET in acest fisier.
    pause
    exit /b 1
)

echo Se copiaza fiscal_bridge.py in:
echo   %TARGET%
echo.

copy /Y "%~dp0fiscal_bridge.py" "%TARGET%\fiscal_bridge.py"
copy /Y "%~dp0start_bridge.bat" "%TARGET%\start_bridge.bat"
copy /Y "%~dp0install_bridge.bat" "%TARGET%\install_bridge.bat"

echo.
echo ============================================
echo   Fisiere copiate cu SUCCES!
echo   Se porneste bridge-ul...
echo ============================================
echo.

cd /d "%TARGET%"
python "%TARGET%\fiscal_bridge.py" "https://andrepau.com"

if %errorlevel% neq 0 (
    echo.
    echo EROARE la pornire!
    pause
)

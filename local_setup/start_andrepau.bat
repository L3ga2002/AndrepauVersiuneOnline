@echo off
chcp 65001 >nul
title ANDREPAU POS - Aplicatie Locala
color 0A

echo ================================================================
echo     ANDREPAU POS - Pornire Aplicatie Locala
echo     Materiale de Constructii
echo ================================================================
echo.

REM === Detecteaza calea proiectului ===
set "APP_DIR=%~dp0.."
cd /d "%APP_DIR%"
set "APP_DIR=%CD%"

REM === 1. Verifica si porneste MongoDB ===
echo [1/4] Verificare MongoDB...
sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    sc query MongoDB | find "RUNNING" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   MongoDB oprit. Se porneste...
        net start MongoDB
        timeout /t 3 /nobreak >nul
    )
    echo [OK] MongoDB ruleaza (Windows Service)
) else (
    REM Incearca mongod direct
    echo   MongoDB nu e serviciu Windows. Se porneste manual...
    
    REM Cauta mongod.exe
    set "MONGOD_PATH="
    if exist "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" set "MONGOD_PATH=C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe"
    if exist "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" set "MONGOD_PATH=C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe"
    if exist "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" set "MONGOD_PATH=C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
    
    if defined MONGOD_PATH (
        REM Creaza directorul de date
        if not exist "C:\data\db" mkdir "C:\data\db"
        start "MongoDB" /min "%MONGOD_PATH%" --dbpath "C:\data\db"
        timeout /t 3 /nobreak >nul
        echo [OK] MongoDB pornit manual
    ) else (
        echo [ATENTIE] MongoDB nu a fost gasit! Asigurati-va ca este instalat.
        echo   Descarcati de pe: https://www.mongodb.com/try/download/community
        echo.
        echo   Daca MongoDB este instalat intr-o alta locatie, porniti-l manual
        echo   inainte de a rula acest script.
        echo.
        pause
    )
)
echo.

REM === 2. Porneste Backend (FastAPI) ===
echo [2/4] Pornire Backend (FastAPI pe port 8001)...
cd /d "%APP_DIR%\backend"

REM Opreste instanta anterioara daca exista
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Backend" >nul 2>&1
timeout /t 1 /nobreak >nul

start "ANDREPAU-Backend" /min cmd /c "cd /d "%APP_DIR%\backend" && python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 /nobreak >nul
echo [OK] Backend pornit pe http://localhost:8001
echo.

REM === 3. Porneste Bridge Fiscal ===
echo [3/4] Pornire Bridge Fiscal (INCOTEX pe port 5555)...

REM Opreste instanta anterioara
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Bridge" >nul 2>&1
timeout /t 1 /nobreak >nul

start "ANDREPAU-Bridge" /min cmd /c "cd /d "%APP_DIR%\backend" && python fiscal_bridge.py http://localhost:8001"
timeout /t 2 /nobreak >nul
echo [OK] Bridge fiscal pornit pe http://localhost:5555
echo     Bridge conectat la backend local (http://localhost:8001)
echo.

REM === 4. Deschide Browser ===
echo [4/4] Deschidere browser...
timeout /t 2 /nobreak >nul
start http://localhost:8001

echo.
echo ================================================================
echo     ANDREPAU POS - APLICATIA RULEAZA!
echo ================================================================
echo.
echo   Aplicatie:     http://localhost:8001
echo   Bridge fiscal: http://localhost:5555/test
echo.
echo   Cont admin:    admin / admin123
echo   Cont casier:   casier / casier123
echo.
echo   NU INCHIDETI ACEASTA FEREASTRA!
echo   Pentru a opri, rulati: stop_andrepau.bat
echo   sau apasati CTRL+C
echo.
echo ================================================================
echo.

REM Tine fereastra deschisa
pause

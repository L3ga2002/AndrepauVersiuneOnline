@echo off
chcp 65001 >nul
title ANDREPAU POS
color 0A

REM === Detecteaza calea proiectului ===
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM === Verifica daca serviciile ruleaza deja ===
tasklist /fi "WINDOWTITLE eq ANDREPAU-Backend" 2>NUL | find "cmd.exe" >nul 2>&1
if %errorlevel% equ 0 (
    echo ANDREPAU POS ruleaza deja!
    start http://localhost:8001
    exit /b 0
)

echo.
echo   ╔══════════════════════════════════════╗
echo   ║       ANDREPAU POS - Pornire         ║
echo   ╚══════════════════════════════════════╝
echo.

REM === 1. MongoDB ===
echo   [■□□□] MongoDB...
sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    sc query MongoDB | find "RUNNING" >nul 2>&1
    if %errorlevel% neq 0 ( net start MongoDB >nul 2>&1 )
) else (
    set "MONGOD_PATH="
    if exist "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" set "MONGOD_PATH=C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe"
    if exist "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" set "MONGOD_PATH=C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe"
    if exist "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe" set "MONGOD_PATH=C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
    if defined MONGOD_PATH (
        if not exist "C:\data\db" mkdir "C:\data\db"
        start "MongoDB" /min "%MONGOD_PATH%" --dbpath "C:\data\db"
        timeout /t 3 /nobreak >nul
    )
)

REM === 2. Backend ===
echo   [■■□□] Backend...
cd /d "%APP_DIR%backend"
start "ANDREPAU-Backend" /min cmd /c "python -m uvicorn server:app --host 0.0.0.0 --port 8001"

REM === 3. Bridge Fiscal ===
echo   [■■■□] Bridge fiscal...
start "ANDREPAU-Bridge" /min cmd /c "python fiscal_bridge.py http://localhost:8001"

REM === 4. Asteptare + Deschide Browser ===
echo   [■■■■] Deschidere aplicatie...
timeout /t 4 /nobreak >nul
start http://localhost:8001

echo.
echo   ╔══════════════════════════════════════╗
echo   ║     ANDREPAU POS PORNIT CU SUCCES    ║
echo   ║                                      ║
echo   ║  Aplicatie:  http://localhost:8001    ║
echo   ║  Bridge:     http://localhost:5555    ║
echo   ║                                      ║
echo   ║  NU INCHIDETI ACEASTA FEREASTRA!     ║
echo   ╚══════════════════════════════════════╝
echo.

REM Tine fereastra deschisa si afiseaza ora
:loop
timeout /t 60 /nobreak >nul
echo   [%time:~0,5%] Aplicatia ruleaza...
goto loop

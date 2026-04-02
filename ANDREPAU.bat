@echo off
chcp 65001 >nul

REM === Verifica daca ruleaza deja ===
tasklist /fi "WINDOWTITLE eq ANDREPAU-Backend" 2>NUL | find "cmd.exe" >nul 2>&1
if %errorlevel% equ 0 (
    start chrome --app=http://localhost:8001 2>NUL || start msedge --app=http://localhost:8001 2>NUL || start http://localhost:8001
    exit /b 0
)

REM === Detecteaza calea proiectului ===
set "APP_DIR=%~dp0"
cd /d "%APP_DIR%"

REM === 1. MongoDB ===
sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    sc query MongoDB | find "RUNNING" >nul 2>&1
    if %errorlevel% neq 0 ( net start MongoDB >nul 2>&1 )
) else (
    if exist "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" (
        if not exist "C:\data\db" mkdir "C:\data\db"
        start "MongoDB" /min "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe" --dbpath "C:\data\db"
    )
    if exist "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" (
        if not exist "C:\data\db" mkdir "C:\data\db"
        start "MongoDB" /min "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe" --dbpath "C:\data\db"
    )
)

REM === 2. Backend (ASCUNS) ===
cd /d "%APP_DIR%backend"
start "ANDREPAU-Backend" /min cmd /c "python -m uvicorn server:app --host 0.0.0.0 --port 8001 2>nul"

REM === 3. Bridge Fiscal (ASCUNS) ===
start "ANDREPAU-Bridge" /min cmd /c "python fiscal_bridge.py http://localhost:8001 2>nul"

REM === 4. Asteapta si deschide ca APLICATIE (fara bara adresa) ===
timeout /t 4 /nobreak >nul

REM Incearca Chrome app mode, apoi Edge, apoi browser normal
start chrome --app=http://localhost:8001 2>NUL
if %errorlevel% neq 0 (
    start msedge --app=http://localhost:8001 2>NUL
    if %errorlevel% neq 0 (
        start http://localhost:8001
    )
)

REM === Ascunde si aceasta fereastra ===
exit

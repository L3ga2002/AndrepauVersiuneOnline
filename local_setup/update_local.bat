@echo off
chcp 65001 >nul
title ANDREPAU POS - Actualizare
color 0B

echo ================================================================
echo     ANDREPAU POS - Actualizare Aplicatie
echo ================================================================
echo.

REM === Detecteaza calea proiectului ===
set "APP_DIR=%~dp0.."
cd /d "%APP_DIR%"
set "APP_DIR=%CD%"

REM === Opreste serviciile ===
echo [1/5] Oprire servicii...
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Bridge" >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Servicii oprite.
echo.

REM === Git pull ===
echo [2/5] Descarcare actualizari din GitHub...
git pull origin main
if %errorlevel% neq 0 (
    echo [EROARE] Git pull a esuat! Verificati conexiunea la internet.
    pause
    exit /b 1
)
echo [OK] Cod actualizat.
echo.

REM === Backend deps ===
echo [3/5] Actualizare dependente backend...
cd /d "%APP_DIR%\backend"
pip install -r requirements.txt --quiet
echo [OK] Dependente backend actualizate.
echo.

REM === Frontend rebuild ===
echo [4/5] Reconstruire frontend...
cd /d "%APP_DIR%\frontend"
call yarn install --silent
call yarn build
echo [OK] Frontend reconstruit.
echo.

REM === Repornire ===
echo [5/5] Repornire servicii...
call "%~dp0start_andrepau.bat"

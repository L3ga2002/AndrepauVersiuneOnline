@echo off
chcp 65001 >nul
title ANDREPAU POS - Instalare Completa
color 0E

echo ================================================================
echo     ANDREPAU POS - Instalare Aplicatie Locala
echo     Materiale de Constructii - Sistem POS Offline
echo ================================================================
echo.

REM === Detecteaza calea proiectului ===
set "APP_DIR=%~dp0.."
cd /d "%APP_DIR%"
set "APP_DIR=%CD%"
echo [INFO] Director aplicatie: %APP_DIR%
echo.

REM === 1. Verifica Python ===
echo [1/6] Verificare Python...
python --version 2>NUL
if %errorlevel% neq 0 (
    echo.
    echo [EROARE] Python NU este instalat!
    echo.
    echo Descarcati Python de pe: https://www.python.org/downloads/
    echo.
    echo IMPORTANT: La instalare, bifati:
    echo   [x] Add Python to PATH
    echo   [x] Install for all users
    echo.
    echo Dupa instalare, rulati din nou acest script.
    echo.
    pause
    exit /b 1
)
echo [OK] Python gasit!
echo.

REM === 2. Verifica Node.js ===
echo [2/6] Verificare Node.js...
node --version 2>NUL
if %errorlevel% neq 0 (
    echo.
    echo [EROARE] Node.js NU este instalat!
    echo.
    echo Descarcati Node.js (LTS) de pe: https://nodejs.org/
    echo.
    echo Dupa instalare, rulati din nou acest script.
    echo.
    pause
    exit /b 1
)
echo [OK] Node.js gasit!
echo.

REM === 3. Verifica MongoDB ===
echo [3/6] Verificare MongoDB...
mongod --version 2>NUL
if %errorlevel% neq 0 (
    echo.
    echo [ATENTIE] MongoDB NU este instalat!
    echo.
    echo Descarcati MongoDB Community Server de pe:
    echo   https://www.mongodb.com/try/download/community
    echo.
    echo La instalare alegeti:
    echo   [x] Install MongoDB as a Service
    echo   [x] Run service as Network Service user
    echo.
    echo Dupa instalare, rulati din nou acest script.
    echo.
    pause
    exit /b 1
)
echo [OK] MongoDB gasit!
echo.

REM === 4. Verifica Git ===
echo [4/6] Verificare Git...
git --version 2>NUL
if %errorlevel% neq 0 (
    echo.
    echo [ATENTIE] Git NU este instalat!
    echo.
    echo Descarcati Git de pe: https://git-scm.com/download/win
    echo.
    echo Git este necesar pentru actualizari. Continuam fara el...
    echo.
)
echo [OK] Git gasit!
echo.

REM === 5. Instaleaza dependente backend ===
echo [5/6] Instalare dependente backend (Python)...
cd /d "%APP_DIR%\backend"
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [EROARE] Instalare dependente Python esuata!
    pause
    exit /b 1
)
echo [OK] Dependente backend instalate!
echo.

REM === 6. Instaleaza dependente frontend si construieste ===
echo [6/6] Instalare dependente frontend si construire...
cd /d "%APP_DIR%\frontend"

REM Instaleaza yarn daca nu exista
call yarn --version 2>NUL
if %errorlevel% neq 0 (
    echo   Instalez yarn...
    call npm install -g yarn
)

call yarn install --silent
if %errorlevel% neq 0 (
    echo [EROARE] Instalare dependente frontend esuata!
    pause
    exit /b 1
)

echo   Construire frontend (poate dura 1-2 minute)...
call yarn build
if %errorlevel% neq 0 (
    echo [EROARE] Construire frontend esuata!
    pause
    exit /b 1
)
echo [OK] Frontend construit cu succes!
echo.

REM === Configurare .env local ===
echo Configurare .env pentru modul local...
cd /d "%APP_DIR%\backend"
if not exist ".env" (
    echo MONGO_URL="mongodb://localhost:27017"> .env
    echo DB_NAME="andrepau">> .env
    echo CORS_ORIGINS="*">> .env
    echo [OK] Fisier .env creat!
) else (
    echo [OK] Fisier .env exista deja.
)
echo.

REM === Instaleaza bridge ===
echo Instalare dependente Bridge (Flask)...
pip install flask flask-cors --quiet
echo [OK] Bridge pregatit!
echo.

echo ================================================================
echo     INSTALARE COMPLETA!
echo ================================================================
echo.
echo   Pentru a porni aplicatia, dublu-click pe:
echo     start_andrepau.bat
echo.
echo   Aplicatia va fi disponibila la:
echo     http://localhost:8001
echo.
echo   Cont admin:  admin / admin123
echo   Cont casier: casier / casier123
echo.
echo ================================================================
pause

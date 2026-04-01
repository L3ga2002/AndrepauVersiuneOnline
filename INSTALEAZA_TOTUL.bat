@echo off
chcp 65001 >nul
title ANDREPAU POS - Instalare Completa Automata
color 0E

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║   ANDREPAU POS - INSTALARE AUTOMATA      ║
echo   ║   Urmeaza pasii de pe ecran              ║
echo   ╚══════════════════════════════════════════╝
echo.

REM === Creaza folder pentru downloaduri ===
set "DL_DIR=%USERPROFILE%\Desktop\ANDREPAU_Instalare"
if not exist "%DL_DIR%" mkdir "%DL_DIR%"

REM ===========================================================
REM  PASUL 1: Verificare si instalare Python
REM ===========================================================
echo ══════════════════════════════════════════
echo  PASUL 1 din 5: PYTHON
echo ══════════════════════════════════════════
python --version 2>NUL
if %errorlevel% equ 0 (
    echo   [OK] Python deja instalat!
    echo.
) else (
    echo   Se descarca Python...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%DL_DIR%\python_installer.exe'}"
    
    if exist "%DL_DIR%\python_installer.exe" (
        echo.
        echo   ╔══════════════════════════════════════════╗
        echo   ║  PYTHON - Se deschide installerul!       ║
        echo   ║                                          ║
        echo   ║  IMPORTANT: Bifeaza jos:                 ║
        echo   ║  [x] Add Python to PATH                  ║
        echo   ║                                          ║
        echo   ║  Apoi click: Install Now                 ║
        echo   ║  Asteapta sa termine → Close             ║
        echo   ╚══════════════════════════════════════════╝
        echo.
        start /wait "" "%DL_DIR%\python_installer.exe"
        echo   Apasa orice tasta DUPA ce ai terminat instalarea Python...
        pause >nul
    ) else (
        echo   [EROARE] Nu am putut descarca Python!
        echo   Descarcati manual de pe: https://www.python.org/downloads/
        pause
    )
)

REM ===========================================================
REM  PASUL 2: Verificare si instalare Node.js
REM ===========================================================
echo ══════════════════════════════════════════
echo  PASUL 2 din 5: NODE.JS
echo ══════════════════════════════════════════
node --version 2>NUL
if %errorlevel% equ 0 (
    echo   [OK] Node.js deja instalat!
    echo.
) else (
    echo   Se descarca Node.js...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://nodejs.org/dist/v20.18.0/node-v20.18.0-x64.msi' -OutFile '%DL_DIR%\nodejs_installer.msi'}"
    
    if exist "%DL_DIR%\nodejs_installer.msi" (
        echo.
        echo   ╔══════════════════════════════════════════╗
        echo   ║  NODE.JS - Se deschide installerul!      ║
        echo   ║                                          ║
        echo   ║  Click: Next → Next → Next → Install     ║
        echo   ║  Asteapta sa termine → Finish            ║
        echo   ╚══════════════════════════════════════════╝
        echo.
        start /wait msiexec /i "%DL_DIR%\nodejs_installer.msi"
        echo   Apasa orice tasta DUPA ce ai terminat instalarea Node.js...
        pause >nul
    ) else (
        echo   [EROARE] Nu am putut descarca Node.js!
        echo   Descarcati manual de pe: https://nodejs.org/
        pause
    )
)

REM ===========================================================
REM  PASUL 3: Verificare si instalare MongoDB
REM ===========================================================
echo ══════════════════════════════════════════
echo  PASUL 3 din 5: MONGODB
echo ══════════════════════════════════════════
sc query MongoDB >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] MongoDB deja instalat!
    echo.
) else (
    mongod --version 2>NUL
    if %errorlevel% equ 0 (
        echo   [OK] MongoDB deja instalat!
        echo.
    ) else (
        echo   Se descarca MongoDB...
        powershell -Command "& {Invoke-WebRequest -Uri 'https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.4-signed.msi' -OutFile '%DL_DIR%\mongodb_installer.msi'}"
        
        if exist "%DL_DIR%\mongodb_installer.msi" (
            echo.
            echo   ╔══════════════════════════════════════════╗
            echo   ║  MONGODB - Se deschide installerul!      ║
            echo   ║                                          ║
            echo   ║  Click: Next → Accept → "Complete"       ║
            echo   ║                                          ║
            echo   ║  IMPORTANT: Lasa bifat:                  ║
            echo   ║  [x] Install MongoDB as a Service        ║
            echo   ║                                          ║
            echo   ║  Next → Install → Finish                 ║
            echo   ╚══════════════════════════════════════════╝
            echo.
            start /wait msiexec /i "%DL_DIR%\mongodb_installer.msi"
            echo   Apasa orice tasta DUPA ce ai terminat instalarea MongoDB...
            pause >nul
        ) else (
            echo   [EROARE] Nu am putut descarca MongoDB!
            echo   Descarcati manual de pe: https://www.mongodb.com/try/download/community
            pause
        )
    )
)

REM ===========================================================
REM  PASUL 4: Verificare si instalare Git
REM ===========================================================
echo ══════════════════════════════════════════
echo  PASUL 4 din 5: GIT
echo ══════════════════════════════════════════
git --version 2>NUL
if %errorlevel% equ 0 (
    echo   [OK] Git deja instalat!
    echo.
) else (
    echo   Se descarca Git...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe' -OutFile '%DL_DIR%\git_installer.exe'}"
    
    if exist "%DL_DIR%\git_installer.exe" (
        echo.
        echo   ╔══════════════════════════════════════════╗
        echo   ║  GIT - Se deschide installerul!          ║
        echo   ║                                          ║
        echo   ║  Click: Next → Next → Next (tot default) ║
        echo   ║  → Install → Finish                      ║
        echo   ╚══════════════════════════════════════════╝
        echo.
        start /wait "" "%DL_DIR%\git_installer.exe"
        echo   Apasa orice tasta DUPA ce ai terminat instalarea Git...
        pause >nul
    ) else (
        echo   [EROARE] Nu am putut descarca Git!
        echo   Descarcati manual de pe: https://git-scm.com/download/win
        pause
    )
)

REM ===========================================================
REM  PASUL 5: Clonare si instalare ANDREPAU
REM ===========================================================
echo ══════════════════════════════════════════
echo  PASUL 5 din 5: INSTALARE ANDREPAU POS
echo ══════════════════════════════════════════
echo.

REM Refresheaza PATH-ul (pentru programele nou instalate)
set "PATH=%PATH%;C:\Python312;C:\Python312\Scripts;C:\Program Files\Git\bin;C:\Program Files\nodejs"

if exist "C:\ANDREPAU" (
    echo   [OK] Folderul C:\ANDREPAU exista deja!
    cd /d "C:\ANDREPAU"
    git pull origin main 2>NUL
    echo   Cod actualizat!
) else (
    echo   Se descarca aplicatia din GitHub...
    cd /d "C:\"
    git clone https://github.com/L3ga2002/AndrepauVersiuneOnline.git ANDREPAU
    if %errorlevel% neq 0 (
        echo   [EROARE] Nu am putut descarca de pe GitHub!
        echo   Verificati conexiunea la internet.
        pause
        exit /b 1
    )
)

echo.
echo   Instalare dependente backend (Python)...
cd /d "C:\ANDREPAU\backend"
pip install -r requirements.txt --quiet 2>NUL
python -m pip install -r requirements.txt --quiet 2>NUL

echo   Instalare yarn...
call npm install -g yarn 2>NUL

echo   Instalare dependente frontend...
cd /d "C:\ANDREPAU\frontend"
call yarn install --silent 2>NUL

echo   Construire frontend (1-2 minute)...
call yarn build 2>NUL

REM === Configurare .env local ===
cd /d "C:\ANDREPAU\backend"
if not exist ".env" (
    echo MONGO_URL="mongodb://localhost:27017"> .env
    echo DB_NAME="andrepau">> .env
    echo CORS_ORIGINS="*">> .env
    echo LOCAL_MODE="true">> .env
    echo SYNC_SECRET="andrepau-sync-2026">> .env
)

REM === Creaza shortcut pe Desktop ===
echo   Creare shortcut pe Desktop...
powershell -Command "& {$ws = New-Object -ComObject WScript.Shell; $sc = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\ANDREPAU POS.lnk'); $sc.TargetPath = 'C:\ANDREPAU\ANDREPAU.bat'; $sc.WorkingDirectory = 'C:\ANDREPAU'; $sc.Description = 'ANDREPAU POS - Materiale Constructii'; $sc.Save()}"

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║                                          ║
echo   ║     INSTALARE COMPLETA CU SUCCES!        ║
echo   ║                                          ║
echo   ║  Pe Desktop ai acum: "ANDREPAU POS"      ║
echo   ║  Dublu-click pe el si aplicatia porneste! ║
echo   ║                                          ║
echo   ║  Cont admin:  admin / admin123            ║
echo   ║  Cont casier: casier / casier123          ║
echo   ║                                          ║
echo   ╚══════════════════════════════════════════╝
echo.

REM === Curatenie ===
echo   Stergere fisiere de instalare...
rmdir /s /q "%DL_DIR%" 2>NUL

echo   Apasa orice tasta pentru a porni aplicatia prima data...
pause >nul

cd /d "C:\ANDREPAU"
call ANDREPAU.bat

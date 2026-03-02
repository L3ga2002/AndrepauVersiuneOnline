@echo off
title ANDREPAU - Bridge Service
color 0E
echo.
echo Pornire Bridge Service...
echo Deschideti in browser: http://localhost:5555/test
echo.
python "%~dp0fiscal_bridge.py"
if %errorlevel% neq 0 (
    echo.
    echo [EROARE] Bridge-ul s-a oprit cu eroare!
    echo Verificati ca Python si dependentele sunt instalate.
    echo Rulati install_bridge.bat mai intai.
    echo.
    pause
)

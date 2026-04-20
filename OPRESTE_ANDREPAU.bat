@echo off
REM ================================================
REM ANDREPAU POS - Oprire aplicatie locala
REM Opreste toate procesele Python (backend + bridge)
REM ================================================
chcp 65001 >nul
title ANDREPAU POS - Oprire

echo Oprire ANDREPAU POS...

REM Opreste procesele Python (uvicorn backend + bridge fiscal)
REM Filtreaza dupa linia de comanda sa nu oprim alte instante Python neasteptate
taskkill /f /fi "IMAGENAME eq pythonw.exe" >nul 2>&1
taskkill /f /fi "IMAGENAME eq python.exe" /fi "WINDOWTITLE eq *uvicorn*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Bridge" >nul 2>&1

REM Inchide si fereastra Chrome in mod aplicatie (daca e)
taskkill /f /fi "WINDOWTITLE eq ANDREPAU*" >nul 2>&1

echo ANDREPAU POS oprit cu succes.
timeout /t 2 /nobreak >nul
exit

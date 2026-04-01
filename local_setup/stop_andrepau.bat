@echo off
chcp 65001 >nul
title ANDREPAU POS - Oprire
color 0C

echo ================================================================
echo     ANDREPAU POS - Oprire Servicii
echo ================================================================
echo.

echo [1/2] Oprire Backend...
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Backend" >nul 2>&1
echo [OK] Backend oprit.
echo.

echo [2/2] Oprire Bridge Fiscal...
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Bridge" >nul 2>&1
echo [OK] Bridge oprit.
echo.

echo Nota: MongoDB ramane pornit (este serviciu Windows).
echo.
echo ================================================================
echo     Toate serviciile ANDREPAU au fost oprite.
echo ================================================================
echo.
pause

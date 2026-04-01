@echo off
chcp 65001 >nul
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Backend" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq ANDREPAU-Bridge" >nul 2>&1
echo ANDREPAU POS oprit.
timeout /t 2 /nobreak >nul

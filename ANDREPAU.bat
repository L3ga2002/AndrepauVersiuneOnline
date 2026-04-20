@echo off
REM ================================================
REM ANDREPAU POS - Launcher principal (offline/local)
REM Ruleaza VBS-ul care porneste totul ASCUNS
REM (fara ferestre CMD vizibile)
REM ================================================
cd /d "%~dp0"
start "" wscript.exe //nologo "ANDREPAU_START.vbs"
exit

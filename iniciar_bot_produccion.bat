@echo off
title BOT PRODUCCION - Live Trading
echo ============================================================
echo 💰 BOT DE PRODUCCION - LIVE TRADING
echo ============================================================
echo.
echo ⚠️  ⚠️  ⚠️  DINERO REAL ⚠️  ⚠️  ⚠️
echo.
echo Capital: $21,891.65 ARS
echo Simbolos: 26
echo.
pause
echo.
echo Iniciando bot de produccion...
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe run_bot.py --live --continuous

pause


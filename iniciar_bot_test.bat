@echo off
title BOT DE TEST - Paper Trading
echo ============================================================
echo 🧪 BOT DE TEST - PAPER TRADING
echo ============================================================
echo.
echo Iniciando bot de test...
echo.

cd /d "%~dp0test_bot"
..\venv\Scripts\python.exe run_bot.py --paper --continuous --interval 5

pause


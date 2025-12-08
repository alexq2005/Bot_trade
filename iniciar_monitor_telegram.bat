@echo off
title MONITOR TELEGRAM - Alertas Trading
echo ============================================================
echo 📱 MONITOR TELEGRAM - Alertas de Trading
echo ============================================================
echo.
echo Monitoreando:
echo   • Señales BUY/SELL
echo   • Errores criticos
echo   • Bot detenido
echo.
echo Alertas por Telegram: @Preoyect_bot
echo.
echo Iniciando monitor...
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe monitor_test_bot_telegram.py

pause


@echo off
title Monitor 14 Dias - Test Bot
cd /d "%~dp0"

echo ============================================================
echo MONITOR DE 14 DIAS - TEST BOT
echo ============================================================
echo.
echo Este script monitoreara el bot durante 14 dias
echo Generara reportes diarios y un reporte final
echo.
echo Configuracion:
echo   - Modo: Paper Trading
echo   - Estrategias: 13 avanzadas
echo   - Reportes: Diarios por Telegram
echo   - Duracion: 14 dias
echo.
echo ============================================================
echo.

REM Iniciar monitor en background
start "Monitor 14 Dias" cmd /k "..\venv\Scripts\python.exe monitor_14_dias.py"

echo.
echo Monitor iniciado en ventana separada
echo.
pause


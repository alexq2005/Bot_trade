@echo off
REM Script para iniciar el monitor de 14 dias de forma INDEPENDIENTE
REM Este script crea procesos que NO se detendrán al cerrar Cursor

title Monitor 14 Dias - INDEPENDIENTE
cd /d "%~dp0"

echo ============================================================
echo MONITOR DE 14 DIAS - MODO INDEPENDIENTE
echo ============================================================
echo.
echo Este monitor seguira corriendo aunque cierres Cursor
echo.
echo Configuracion:
echo   - Duracion: 14 dias
echo   - Reportes: Diarios por Telegram
echo   - Objetivo: Medir performance de estrategias
echo.
echo ============================================================
echo.

REM Iniciar en ventana separada completamente independiente
start "Monitor 14 Dias - INDEPENDIENTE" /MIN cmd /c "..\venv\Scripts\python.exe monitor_14_dias.py"

timeout /t 3 /nobreak >nul

echo.
echo Monitor iniciado en proceso INDEPENDIENTE
echo.
echo IMPORTANTE:
echo   - El monitor seguira corriendo aunque cierres Cursor
echo   - Generara reportes diarios automaticamente
echo   - Para detenerlo, usa: DETENER_TODO.bat
echo.
pause




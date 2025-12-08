@echo off
REM Script para iniciar el bot de forma INDEPENDIENTE de Cursor
REM Este script crea procesos que NO se detendrán al cerrar Cursor

title Bot Test - INDEPENDIENTE
cd /d "%~dp0"

echo ============================================================
echo BOT DE TEST - MODO INDEPENDIENTE
echo ============================================================
echo.
echo Este bot seguira corriendo aunque cierres Cursor
echo.
echo Configuracion:
echo   - Modo: Paper Trading
echo   - Estrategias: 13 avanzadas
echo   - Portfolio: Completo
echo.
echo ============================================================
echo.

REM Usar start con /B para iniciar en background pero independiente
REM O mejor: usar start sin /B para crear ventana separada completamente independiente
start "Bot Test - INDEPENDIENTE" /MIN cmd /c "..\venv\Scripts\python.exe run_bot.py --paper --continuous"

timeout /t 3 /nobreak >nul

echo.
echo Bot iniciado en proceso INDEPENDIENTE
echo.
echo IMPORTANTE:
echo   - El bot seguira corriendo aunque cierres Cursor
echo   - Para detenerlo, usa: DETENER_TODO.bat
echo   - O busca el proceso en el Administrador de Tareas
echo.
echo Verificando estado...
timeout /t 2 /nobreak >nul

if exist bot.pid (
    echo Bot PID guardado en: bot.pid
    type bot.pid
) else (
    echo Esperando que el bot inicie...
)

echo.
pause





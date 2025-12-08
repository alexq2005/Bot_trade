@echo off
REM Script para iniciar TODOS los componentes de forma INDEPENDIENTE
REM Estos procesos NO se detendrán al cerrar Cursor

title Iniciar Todo - INDEPENDIENTE
cd /d "%~dp0"

echo ============================================================
echo INICIANDO TODOS LOS COMPONENTES - MODO INDEPENDIENTE
echo ============================================================
echo.
echo Estos procesos seguiran corriendo aunque cierres Cursor
echo.
echo Componentes:
echo   1. Bot de Test (Paper Trading)
echo   2. Monitor de 14 Dias
echo   3. Dashboard (opcional)
echo.
echo ============================================================
echo.

REM Verificar que Python esté disponible
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python no encontrado en PATH
    echo Por favor, instala Python o activa el entorno virtual
    pause
    exit /b 1
)

REM 1. Iniciar Bot (proceso completamente independiente con ventana visible)
echo [1/3] Iniciando Bot de Test...
start "Bot Test - INDEPENDIENTE" cmd /k "python run_bot.py --paper --continuous"
timeout /t 3 /nobreak >nul

REM 2. Iniciar Monitor (proceso completamente independiente con ventana visible)
echo [2/3] Iniciando Monitor de 14 Dias...
start "Monitor 14 Dias - INDEPENDIENTE" cmd /k "python monitor_14_dias.py"
timeout /t 3 /nobreak >nul

REM 3. Preguntar por Dashboard
echo [3/3] Dashboard (opcional)...
set /p start_dashboard="¿Iniciar Dashboard? (S/N): "
if /i "%start_dashboard%"=="S" (
    echo Iniciando Dashboard...
    where streamlit >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        start "Dashboard Test - INDEPENDIENTE" cmd /k "streamlit run dashboard.py --server.port 8502"
    ) else (
        start "Dashboard Test - INDEPENDIENTE" cmd /k "python -m streamlit run dashboard.py --server.port 8502"
    )
) else (
    echo Dashboard omitido
)

echo.
echo ============================================================
echo TODOS LOS COMPONENTES INICIADOS
echo ============================================================
echo.
echo IMPORTANTE:
echo   - Todos los procesos son INDEPENDIENTES de Cursor
echo   - Seguiran corriendo aunque cierres Cursor
echo   - Para detener todo, usa: DETENER_TODO.bat
echo.
echo Verificando estado...
timeout /t 3 /nobreak >nul

if exist bot.pid (
    echo Bot: ACTIVO (PID: 
    type bot.pid
    echo )
) else (
    echo Bot: Iniciando...
)

echo.
echo Listo! Puedes cerrar Cursor sin problemas.
echo.
pause





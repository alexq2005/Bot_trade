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

REM Verificar si Python está disponible
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python no encontrado en PATH
    echo Por favor, instala Python o activa el entorno virtual
    pause
    exit /b 1
)

REM Iniciar monitor en ventana separada (independiente de Cursor)
start "Monitor 14 Dias - Test Bot" cmd /k "python monitor_14_dias.py"

echo.
echo ============================================================
echo Monitor iniciado en ventana separada
echo ============================================================
echo.
echo El monitoreo se ejecutara durante 14 dias
echo Puedes cerrar esta ventana sin afectar el monitoreo
echo.
echo Para ver el progreso, ejecuta: ver_progreso_14dias.py
echo Para detener el monitoreo, cierra la ventana del monitor
echo.
pause


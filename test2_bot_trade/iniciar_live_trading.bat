@echo off
REM ============================================================
REM INICIAR BOT EN MODO LIVE TRADING (ACTIVOS REALES)
REM ============================================================
REM ⚠️ ADVERTENCIA: Este modo opera con DINERO REAL
REM ============================================================

echo.
echo ============================================================
echo ⚠️  MODO LIVE TRADING - DINERO REAL ⚠️
echo ============================================================
echo.
echo ADVERTENCIAS IMPORTANTES:
echo   • El bot operará con DINERO REAL de tu cuenta IOL
echo   • Asegúrate de haber probado en modo PAPER primero
echo   • Verifica tu configuración de riesgo
echo   • Revisa límites de pérdida diaria
echo   • Ten capital suficiente para operar
echo.
echo ============================================================
echo.

REM Preguntar confirmación
set /p confirm="¿Estás seguro de iniciar en modo LIVE? (SI/NO): "
if /i not "%confirm%"=="SI" (
    echo.
    echo Operación cancelada.
    echo.
    pause
    exit /b
)

echo.
echo ============================================================
echo Iniciando bot en modo LIVE TRADING...
echo ============================================================
echo.

REM Cambiar al directorio del bot
cd /d "%~dp0"

REM Activar entorno virtual
call ..\venv\Scripts\activate.bat

REM Iniciar bot en modo LIVE
python run_bot.py --live --continuous

pause


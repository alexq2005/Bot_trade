@echo off
cls
echo ============================================================
echo ⚠️  BOT DE TEST EN MODO LIVE (DINERO REAL)
echo ============================================================
echo.
echo ⚠️  ⚠️  ⚠️  ADVERTENCIA CRITICA ⚠️  ⚠️  ⚠️
echo.
echo Este script ejecutara el Test Bot en MODO LIVE
echo.
echo Esto significa:
echo   • Operaciones con DINERO REAL
echo   • Usa tu cuenta real de IOL
echo   • Las operaciones afectan tu capital
echo.
echo ============================================================
echo.
echo Asegurate de:
echo   1. Haber probado en Paper Trading primero (24-48h)
echo   2. Sin errores en logs de paper trading
echo   3. Entender TODOS los cambios que hiciste
echo   4. Limites de riesgo configurados (testing_config.json)
echo   5. Bot de PRODUCCION detenido (evitar conflictos)
echo.
echo ============================================================
echo.
set /p confirmar1="¿Probaste en Paper Trading? (SI/NO): "

if /i not "%confirmar1%"=="SI" (
    echo.
    echo ❌ DEBES probar en Paper Trading primero
    echo    Ejecuta: ejecutar_bot_continuo_test.bat
    echo    Y selecciona modo Paper (opcion 1)
    pause
    exit /b
)

echo.
set /p confirmar2="¿El bot de PRODUCCION esta detenido? (SI/NO): "

if /i not "%confirmar2%"=="SI" (
    echo.
    echo ⚠️  ADVERTENCIA: Puede haber conflictos
    echo    Recomendacion: Detener bot de produccion primero
    echo.
    set /p continuar="¿Continuar de todas formas? (SI/NO): "
    if /i not "%continuar%"=="SI" (
        echo ❌ Cancelado
        pause
        exit /b
    )
)

echo.
echo ============================================================
echo CONFIGURACION DE LIVE TESTING
echo ============================================================
echo.
echo ¿Cuantos simbolos quieres monitorear?
echo   1. Solo 2-3 simbolos (RECOMENDADO para testing)
echo   2. Todos los simbolos del portafolio
echo.
set /p simbolos_opcion="Selecciona (1 o 2): "

echo.
echo ============================================================
echo ⚠️  CONFIRMACION FINAL
echo ============================================================
echo.
echo Estas a punto de ejecutar Test Bot en MODO LIVE con:
if "%simbolos_opcion%"=="2" (
    echo   • Todos los simbolos del portafolio
) else (
    echo   • 2-3 simbolos de prueba
)
echo   • Dinero REAL de tu cuenta IOL
echo   • Intervalo de 60 minutos
echo.

set /p final="Escribe 'EJECUTAR LIVE' para continuar: "

if not "%final%"=="EJECUTAR LIVE" (
    echo.
    echo ❌ Cancelado por seguridad
    pause
    exit /b
)

echo.
echo ============================================================
echo 🚀 INICIANDO TEST BOT EN MODO LIVE
echo ============================================================
echo.
echo 💰 USANDO DINERO REAL
echo ⏱️  Intervalo: 60 minutos
echo 📊 Monitorea los logs activamente
echo.
echo Presiona Ctrl+C para detener en cualquier momento
echo.
echo ============================================================
echo.

cd %~dp0

if "%simbolos_opcion%"=="2" (
    ..\venv\Scripts\python.exe run_bot.py --live --continuous --interval 60
) else (
    ..\venv\Scripts\python.exe run_bot.py --live --continuous --interval 60 --symbols AAPL,MSFT,GOOGL
)

pause


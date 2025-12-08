@echo off
echo ============================================================
echo 🔄 EJECUTANDO BOT DE TEST EN MODO CONTINUO
echo ============================================================
echo.
echo SELECCIONA MODO:
echo   1. PAPER TRADING (Simulacion - Recomendado)
echo   2. LIVE TRADING (Dinero REAL - Solo para validacion final)
echo.
set /p modo="Selecciona modo (1 o 2): "

if "%modo%"=="2" (
    echo.
    echo ============================================================
    echo ⚠️  ⚠️  ⚠️  ADVERTENCIA ⚠️  ⚠️  ⚠️
    echo ============================================================
    echo.
    echo Modo LIVE seleccionado - SE USARA DINERO REAL
    echo.
    set /p confirmar="Confirma que quieres operar con dinero REAL (SI/NO): "
    
    if /i not "%confirmar%"=="SI" (
        echo.
        echo ❌ Cancelado por seguridad
        pause
        exit /b
    )
    
    echo.
    echo ✅ Confirmado - Iniciando en LIVE
    echo ⏱️  Intervalo: 5 minutos
    echo 💰 Se usara capital REAL de IOL
    echo.
    cd %~dp0
    ..\venv\Scripts\python.exe run_bot.py --live --continuous --interval 5
) else (
    echo.
    echo ✅ Iniciando en PAPER TRADING
    echo ⏱️  Intervalo: 5 minutos
    echo 💰 Capital simulado
    echo.
    cd %~dp0
    ..\venv\Scripts\python.exe run_bot.py --paper --continuous --interval 5
)

pause


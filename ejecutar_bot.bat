@echo off
REM Script para ejecutar el Bot de Trading
REM Windows Batch Script

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo.
    echo ========================================
    echo   Iniciando Bot de Trading
    echo ========================================
    echo.
    echo Selecciona el modo:
    echo 1. Paper Trading (Simulacion)
    echo 2. Live Trading (Dinero Real)
    echo.
    set /p modo="Modo (1 o 2): "
    
    if "%modo%"=="1" (
        echo.
        echo Iniciando en modo PAPER TRADING...
        echo Presiona Ctrl+C para detener
        echo.
        python run_bot.py --paper --continuous
    ) else if "%modo%"=="2" (
        echo.
        echo ========================================
        echo   ADVERTENCIA: MODO LIVE TRADING
        echo ========================================
        echo.
        echo Esto ejecutara ordenes con DINERO REAL
        echo.
        set /p confirmar="¿Estas seguro? (escribe SI para confirmar): "
        
        if /i "%confirmar%"=="SI" (
            echo.
            echo Iniciando en modo LIVE...
            echo Presiona Ctrl+C para detener
            echo.
            python run_bot.py --live --continuous
        ) else (
            echo Cancelado.
            pause
        )
    ) else (
        echo Opcion invalida
        pause
    )
) else (
    echo ERROR: No se encuentra el entorno virtual
    pause
)


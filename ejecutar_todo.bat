@echo off
REM Script para ejecutar todos los componentes principales
REM Windows Batch Script

echo ========================================
echo   IOL Quantum AI - Ejecutar Todo
echo ========================================
echo.

cd /d "%~dp0"

REM Verificar que estamos en el directorio correcto
if not exist "dashboard.py" (
    echo ERROR: No se encuentra dashboard.py
    echo Asegurate de ejecutar este script desde el directorio financial_ai
    pause
    exit /b 1
)

REM Activar venv
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo ERROR: No se encuentra el entorno virtual
    echo Ejecuta primero: python -m venv venv
    pause
    exit /b 1
)

echo.
echo ========================================
echo   1. DIAGNOSTICO INICIAL
echo ========================================
echo.
python scripts\diagnostico_completo.py
echo.
pause

echo.
echo ========================================
echo   2. CONFIGURACION
echo ========================================
echo.
python scripts\gestionar_config.py show
echo.
pause

echo.
echo ========================================
echo   3. INICIANDO DASHBOARD
echo ========================================
echo.
echo Dashboard se abrira en: http://localhost:8501
echo Presiona Ctrl+C para detener
echo.
start "Dashboard" cmd /k "python -m streamlit run dashboard.py"
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   4. INICIANDO BOT (PAPER TRADING)
echo ========================================
echo.
echo El bot se ejecutara en modo PAPER TRADING
echo Presiona Ctrl+C para detener
echo.
start "Trading Bot" cmd /k "python run_bot.py --paper --continuous"

echo.
echo ========================================
echo   SISTEMA INICIADO
echo ========================================
echo.
echo Dashboard: http://localhost:8501
echo Bot: Ejecutandose en modo Paper Trading
echo.
echo Para detener todo, cierra las ventanas o presiona Ctrl+C
echo.
pause


@echo off
REM Script para ejecutar solo el Dashboard
REM Windows Batch Script

cd /d "%~dp0"

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo.
    echo ========================================
    echo   Iniciando Dashboard
    echo ========================================
    echo.
    echo Abriendo en: http://localhost:8501
    echo Presiona Ctrl+C para detener
    echo.
    python -m streamlit run dashboard.py
) else (
    echo ERROR: No se encuentra el entorno virtual
    pause
)


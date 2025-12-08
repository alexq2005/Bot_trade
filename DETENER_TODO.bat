@echo off
cls
echo ============================================================
echo 🛑 DETENER TODOS LOS COMPONENTES
echo ============================================================
echo.
echo Este script detendra TODOS los procesos del sistema:
echo   • Bots de trading
echo   • Dashboards
echo   • Monitores
echo   • Controllers
echo.
echo ⚠️  Esto detendra TODOS los procesos Python
echo.
pause
echo.
echo Deteniendo procesos...
echo.

REM Detener todos los procesos Python
taskkill /F /IM python.exe 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Procesos Python detenidos
) else (
    echo ℹ️  No habia procesos Python corriendo
)

timeout /t 1 /nobreak >nul

REM Detener Streamlit
taskkill /F /IM streamlit.exe 2>nul
if %ERRORLEVEL% EQU 0 (
    echo ✅ Streamlit detenido
) else (
    echo ℹ️  Streamlit no estaba corriendo
)

timeout /t 1 /nobreak >nul

REM Limpiar archivos PID
cd /d "%~dp0"
if exist "bot.pid" (
    del /F /Q "bot.pid" 2>nul
    echo ✅ Archivo bot.pid eliminado
)

if exist "test_bot\bot.pid" (
    del /F /Q "test_bot\bot.pid" 2>nul
    echo ✅ Archivo test_bot\bot.pid eliminado
)

echo.
echo ============================================================
echo ✅ TODOS LOS COMPONENTES DETENIDOS
echo ============================================================
echo.
pause


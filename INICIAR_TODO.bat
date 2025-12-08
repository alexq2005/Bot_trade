@echo off
cls
echo ============================================================
echo 🚀 SISTEMA IOL QUANTUM AI - INICIO COMPLETO
echo ============================================================
echo.
echo Este script iniciara TODOS los componentes del sistema:
echo.
echo 1. 🧪 Bot de Test (Paper Trading)
echo 2. 💰 Bot de Produccion (Live Trading)
echo 3. 🌐 Dashboard Test (Puerto 8502)
echo 4. 🌐 Dashboard Produccion (Puerto 8501)
echo 5. 📱 Monitor Telegram (Alertas)
echo 6. 🛠️ Cursor Controller (Desarrollo)
echo.
echo Cada componente se abrira en su propia ventana con nombre.
echo.
echo ============================================================
echo.
pause
echo.
echo Iniciando componentes...
echo.

cd /d "%~dp0"

echo [1/6] Iniciando Bot de Test...
start "BOT TEST" cmd /k "iniciar_bot_test.bat"
timeout /t 3 /nobreak >nul

echo [2/6] Iniciando Bot de Produccion...
start "BOT PRODUCCION" cmd /k "iniciar_bot_produccion.bat"
timeout /t 3 /nobreak >nul

echo [3/6] Iniciando Dashboard Test...
start "DASHBOARD TEST" cmd /k "iniciar_dashboard_test.bat"
timeout /t 3 /nobreak >nul

echo [4/6] Iniciando Dashboard Produccion...
start "DASHBOARD PROD" cmd /k "iniciar_dashboard_prod.bat"
timeout /t 3 /nobreak >nul

echo [5/6] Iniciando Monitor Telegram...
start "MONITOR TELEGRAM" cmd /k "iniciar_monitor_telegram.bat"
timeout /t 3 /nobreak >nul

echo [6/6] Iniciando Cursor Controller...
start "CURSOR CONTROLLER" cmd /k "iniciar_cursor_controller.bat"
timeout /t 2 /nobreak >nul

echo.
echo ============================================================
echo ✅ TODOS LOS COMPONENTES INICIADOS
echo ============================================================
echo.
echo Ventanas abiertas:
echo   • BOT TEST
echo   • BOT PRODUCCION
echo   • DASHBOARD TEST
echo   • DASHBOARD PROD
echo   • MONITOR TELEGRAM
echo   • CURSOR CONTROLLER
echo.
echo 💡 Cada ventana tiene su nombre en la barra de titulo
echo.
echo URLs:
echo   Dashboard Test: http://localhost:8502
echo   Dashboard Prod: http://localhost:8501
echo.
echo Telegram: @Preoyect_bot
echo   • Comandos trading: /estado, /portafolio, /restart
echo   • Comandos desarrollo: /dev_status, /dev_logs, /dev_help
echo.
echo ============================================================
echo.
pause


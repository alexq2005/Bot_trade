@echo off
echo ============================================================
echo 🔄 REINICIO LIMPIO DEL BOT
echo ============================================================
echo.

echo 🛑 Paso 1: Deteniendo TODAS las instancias de Python...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 3 /nobreak >nul

echo ✅ Procesos detenidos
echo.

echo 🧹 Paso 2: Limpiando archivos temporales...
if exist bot.pid del /F bot.pid
if exist stop_flag.txt del /F stop_flag.txt
if exist restart_flag.txt del /F restart_flag.txt
echo ✅ Archivos limpiados
echo.

echo ⏳ Paso 3: Esperando 35 segundos para liberar Telegram polling...
echo    (Telegram necesita tiempo para detectar que el polling se detuvo)
timeout /t 35 /nobreak

echo.
echo 🚀 Paso 4: Iniciando bot en modo PAPER TRADING...
echo.
start "IOL Trading Bot" .\venv\Scripts\python.exe run_bot.py --paper --continuous

timeout /t 8 /nobreak >nul

echo.
echo ============================================================
echo 📋 VERIFICACIÓN
echo ============================================================

if exist bot.pid (
    set /p pid=<bot.pid
    echo ✅ Bot iniciado correctamente ^(PID: %pid%^)
    echo.
    echo 📱 PRUEBA EN TELEGRAM:
    echo    1. Abre Telegram y busca: @Preoyect_bot
    echo    2. Envía: /help
    echo    3. El bot debería responder en 1-2 segundos
) else (
    echo ❌ Bot no inició correctamente
    echo    Revisa los logs en la carpeta logs/
)

echo.
echo ============================================================
pause


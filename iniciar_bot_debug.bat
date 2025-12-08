@echo off
echo ============================================================
echo 🚀 INICIANDO BOT CON DEBUG COMPLETO
echo ============================================================
echo.

echo 🛑 Deteniendo instancias previas...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 3 /nobreak >nul

echo 🧹 Limpiando...
if exist bot.pid del /F bot.pid
if exist stop_flag.txt del /F stop_flag.txt
if exist restart_flag.txt del /F restart_flag.txt

echo ⏳ Esperando 35 segundos para liberar Telegram...
timeout /t 35 /nobreak

cls
echo ============================================================
echo 🚀 BOT INICIANDO
echo ============================================================
echo.
echo 📱 INSTRUCCIONES:
echo    1. Espera a ver el mensaje "Polling de Telegram iniciado"
echo    2. Luego envía /help a @Preoyect_bot en Telegram
echo    3. Observa esta ventana - deberías ver:
echo       "📨 Mensaje recibido..."
echo       "⚙️ Ejecutando comando: /help"
echo       "✅ Comando /help ejecutado exitosamente"
echo.
echo ============================================================
echo.

.\venv\Scripts\python.exe run_bot.py --paper --continuous

pause


@echo off
echo ============================================================
echo 🛠️ CURSOR TELEGRAM CONTROLLER
echo ============================================================
echo.
echo Este script permite controlar el desarrollo desde Telegram
echo.
echo Comandos disponibles:
echo   /dev_status - Estado del sistema
echo   /dev_logs - Ver logs
echo   /dev_restart_test - Reiniciar bot de test
echo   /dev_backup - Crear backup
echo   /dev_exec [cmd] - Ejecutar comando
echo   /dev_help - Ayuda completa
echo.
echo ============================================================
echo.
echo 🚀 Iniciando controller...
echo.

.\venv\Scripts\python.exe test_bot\features\cursor_telegram_controller.py

pause


@echo off
title CURSOR CONTROLLER - Comandos Desarrollo
echo ============================================================
echo 🛠️ CURSOR TELEGRAM CONTROLLER
echo ============================================================
echo.
echo Control de desarrollo via Telegram
echo.
echo Comandos disponibles:
echo   /dev_status - Estado del sistema
echo   /dev_logs - Ver logs
echo   /dev_restart_test - Reiniciar test bot
echo   /dev_backup - Crear backup
echo   /dev_exec [cmd] - Ejecutar comando
echo   /dev_help - Ayuda completa
echo.
echo Bot: @Preoyect_bot
echo.
echo Iniciando controller...
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe test_bot\features\cursor_telegram_controller.py

pause


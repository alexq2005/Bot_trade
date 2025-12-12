@echo off
REM Script para ejecutar el bot en modo LIVE sin problemas de PowerShell
cd /d "%~dp0"

REM Activar entorno virtual y ejecutar bot
call ..\..\.venv\Scripts\activate.bat
python iniciar_bot_con_logs.py --live --continuous --interval 60

pause


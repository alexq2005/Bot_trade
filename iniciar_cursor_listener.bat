@echo off
title CURSOR TASK LISTENER - Telegram
echo ============================================================
echo 🎯 CURSOR TASK LISTENER
echo ============================================================
echo.
echo Sistema de cola de tareas para Cursor
echo.
echo Tu envias: /dev_task [solicitud]
echo Cursor procesa y responde
echo.
echo Escuchando Telegram...
echo.

cd /d "%~dp0"
.\venv\Scripts\python.exe cursor_task_listener.py

pause


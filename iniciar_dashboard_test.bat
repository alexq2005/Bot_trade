@echo off
title DASHBOARD TEST - Puerto 8502
echo ============================================================
echo 🌐 DASHBOARD DE TEST - Puerto 8502
echo ============================================================
echo.
echo URL: http://localhost:8502
echo.
echo Iniciando dashboard...
echo.

cd /d "%~dp0test_bot"
..\venv\Scripts\streamlit run dashboard.py --server.port 8502

pause


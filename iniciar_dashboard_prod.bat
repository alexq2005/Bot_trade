@echo off
title DASHBOARD PRODUCCION - Puerto 8501
echo ============================================================
echo 🚀 DASHBOARD DE PRODUCCION - Puerto 8501
echo ============================================================
echo.
echo URL: http://localhost:8501
echo.
echo Iniciando dashboard...
echo.

cd /d "%~dp0"
.\venv\Scripts\streamlit run dashboard.py --server.port 8501

pause


@echo off
echo ============================================================
echo 🌐 EJECUTANDO DASHBOARD DE TEST
echo ============================================================
echo.
echo 🔗 Puerto: 8502 (Producción usa 8501)
echo 📊 URL: http://localhost:8502
echo ⚠️  Dashboard de TESTING - No afecta producción
echo.
echo ============================================================
echo.

cd %~dp0
..\venv\Scripts\python.exe -m streamlit run dashboard.py --server.port 8502

pause


@echo off
echo ============================================================
echo 🧪 EJECUTANDO TEST BOT
echo ============================================================
echo.
echo ⚠️  MODO: PAPER TRADING (No usa dinero real)
echo 📊 Símbolos: AAPL, MSFT, GOOGL
echo 💰 Capital: $10,000 ARS (simulado)
echo.
echo ============================================================
echo.

cd %~dp0
..\venv\Scripts\python.exe test_trading_bot.py

pause


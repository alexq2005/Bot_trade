═══════════════════════════════════════════════════════════════
  INSTALACIÓN RÁPIDA - IOL Quantum AI Trading Bot
═══════════════════════════════════════════════════════════════

📋 REQUISITOS:
  • Python 3.9 o superior
  • Cuenta de IOL activa
  • Telegram (opcional)

🚀 INSTALACIÓN EN 5 PASOS:

1. INSTALAR PYTHON
   Descargar desde: https://www.python.org/downloads/
   ⚠️ Marcar "Add Python to PATH" al instalar

2. INSTALAR DEPENDENCIAS
   Abrir terminal en la carpeta del proyecto y ejecutar:
   
   python -m venv venv
   venv\Scripts\activate          (Windows)
   source venv/bin/activate       (Linux/Mac)
   
   pip install -r requirements.txt

3. CONFIGURAR CREDENCIALES
   Crear archivo .env en la raíz del proyecto con:
   
   IOL_USERNAME=tu_email@ejemplo.com
   IOL_PASSWORD=tu_contraseña
   TELEGRAM_BOT_TOKEN=tu_token (opcional)
   TELEGRAM_CHAT_ID=tu_chat_id (opcional)

4. PROBAR CONEXIÓN
   python -c "from src.connectors.iol_client import IOLClient; iol = IOLClient(); print('✅ Conectado')"

5. EJECUTAR BOT
   
   Modo Simulación (Paper Trading):
   python run_bot.py --continuous
   
   Modo Real (Live Trading):
   python run_bot.py --live --continuous
   
   Dashboard:
   streamlit run dashboard.py

📚 DOCUMENTACIÓN COMPLETA:
   Ver archivo: GUIA_INSTALACION.md

⚠️ IMPORTANTE:
   • NUNCA compartas tu archivo .env
   • Empieza con Paper Trading antes de usar dinero real
   • Revisa la configuración en professional_config.json

✅ VERIFICAR INSTALACIÓN:
   python verificar_operaciones_hoy.py

═══════════════════════════════════════════════════════════════


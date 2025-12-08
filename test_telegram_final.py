"""
Test final de Telegram usando el código actualizado
"""
import os
import sys
from pathlib import Path

# Cargar .env
from dotenv import load_dotenv
load_dotenv()

# Agregar al path
sys.path.append(str(Path(__file__).parent))

from src.services.telegram_bot import TelegramAlertBot

print("=" * 70)
print("🧪 PRUEBA FINAL DE TELEGRAM")
print("=" * 70)
print()

# Inicializar bot
print("1. Inicializando bot...")
bot = TelegramAlertBot()

if not bot.bot:
    print("❌ Bot no inicializado. Verifica las credenciales en .env")
    sys.exit(1)

print("✅ Bot inicializado")
print()

# Enviar mensaje de prueba
print("2. Enviando mensaje de prueba...")
success = bot.send_alert("""
🚀 *PRUEBA DE TELEGRAM*

✅ Bot de Trading configurado correctamente

*Estado:* Operativo
*Versión:* python-telegram-bot 22.5

Si recibes este mensaje, la configuración es correcta! 🎉
""")

if success:
    print("✅ Mensaje enviado exitosamente!")
    print()
    print("=" * 70)
    print("🎉 ¡TELEGRAM FUNCIONA CORRECTAMENTE!")
    print("=" * 70)
    print()
    print("✅ Revisa tu Telegram para ver el mensaje")
else:
    print("❌ No se pudo enviar el mensaje")
    print("   Verifica las credenciales y que hayas enviado un mensaje a tu bot primero")

print()

# Probar señal de trading
print("3. Probando señal de trading...")
success2 = bot.send_trading_signal(
    symbol="AAPL",
    signal="BUY",
    price=150.25,
    confidence=0.85,
    data={
        "AI Score": "85%",
        "Technical": "Bullish",
        "Sentiment": "Positive"
    }
)

if success2:
    print("✅ Señal de trading enviada exitosamente!")
else:
    print("❌ No se pudo enviar la señal")

print()
print("=" * 70)
print("✅ Prueba completada")
print("=" * 70)


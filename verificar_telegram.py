"""
Script para verificar y solucionar problemas de Telegram
"""
import os
import sys
import asyncio
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    print("❌ python-telegram-bot no está instalado")
    print("   Instala con: pip install python-telegram-bot")
    sys.exit(1)

print("=" * 70)
print("🔍 VERIFICACIÓN Y SOLUCIÓN DE TELEGRAM")
print("=" * 70)
print()

# Verificar credenciales
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not bot_token:
    print("❌ TELEGRAM_BOT_TOKEN no encontrado en .env")
    sys.exit(1)

if not chat_id:
    print("❌ TELEGRAM_CHAT_ID no encontrado en .env")
    sys.exit(1)

print(f"✅ Token configurado: {bot_token[:15]}...")
print(f"✅ Chat ID configurado: {chat_id}")
print()

# Probar conexión
print("1. Probando conexión con Telegram...")
try:
    async def test_connection():
        bot = Bot(token=bot_token)
        
        # Obtener información del bot
        bot_info = await bot.get_me()
        print(f"   ✅ Bot conectado: @{bot_info.username} ({bot_info.first_name})")
        
        # Intentar enviar mensaje
        print()
        print("2. Intentando enviar mensaje de prueba...")
        try:
            await bot.send_message(
                chat_id=chat_id,
                text="🧪 *Prueba de Telegram*\n\n✅ Si recibes este mensaje, todo funciona correctamente!"
            )
            print("   ✅ Mensaje enviado exitosamente!")
            print()
            print("=" * 70)
            print("🎉 ¡TELEGRAM FUNCIONA CORRECTAMENTE!")
            print("=" * 70)
            print()
            print("✅ Revisa tu Telegram para ver el mensaje")
            return True
        except TelegramError as e:
            error_msg = str(e)
            print(f"   ❌ Error: {error_msg}")
            print()
            
            if "blocked" in error_msg.lower() or "forbidden" in error_msg.lower():
                print("=" * 70)
                print("🔴 PROBLEMA: Bot bloqueado o no iniciado")
                print("=" * 70)
                print()
                print("📝 SOLUCIÓN:")
                print()
                print("1. Abre Telegram en tu teléfono/computadora")
                print("2. Busca tu bot (nombre: " + bot_info.first_name + ")")
                print(f"   O busca: @{bot_info.username}")
                print()
                print("3. Abre la conversación con el bot")
                print("4. Envía cualquier mensaje al bot (ej: /start o Hola)")
                print()
                print("5. Vuelve a ejecutar este script:")
                print("   python verificar_telegram.py")
                print()
                print("💡 IMPORTANTE: Debes enviar un mensaje al bot primero")
                print("   antes de que pueda enviarte mensajes.")
            elif "chat not found" in error_msg.lower():
                print("=" * 70)
                print("🔴 PROBLEMA: Chat ID incorrecto")
                print("=" * 70)
                print()
                print("📝 SOLUCIÓN:")
                print()
                print("1. Busca @userinfobot en Telegram")
                print("2. Envía /start")
                print("3. Copia tu Chat ID")
                print("4. Actualiza TELEGRAM_CHAT_ID en el archivo .env")
            else:
                print("=" * 70)
                print("🔴 ERROR DESCONOCIDO")
                print("=" * 70)
                print(f"   Mensaje: {error_msg}")
                print()
                print("💡 Verifica:")
                print("   - Token correcto")
                print("   - Chat ID correcto")
                print("   - Has enviado un mensaje al bot primero")
            
            return False
    
    result = asyncio.run(test_connection())
    sys.exit(0 if result else 1)
    
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


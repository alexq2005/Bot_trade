"""
Prueba directa: simula recibir un comando /help y procesarlo
"""
import sys
import os
from pathlib import Path

# Cargar .env
from dotenv import load_dotenv
load_dotenv()

# Agregar src al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

print("="*70)
print("🧪 PRUEBA DIRECTA DEL SISTEMA DE COMANDOS DE TELEGRAM")
print("="*70)
print()

try:
    from src.services.telegram_command_handler import TelegramCommandHandler
    
    print("1️⃣ Creando TelegramCommandHandler...")
    handler = TelegramCommandHandler()
    
    print(f"   Token: {'✅' if handler.bot_token else '❌'}")
    print(f"   Chat ID: {'✅' if handler.chat_id else '❌'}")
    print(f"   Comandos registrados: {len(handler.all_commands)}")
    print()
    
    # Mostrar comandos disponibles
    print("📋 Comandos registrados:")
    for cmd in sorted(handler.all_commands.keys())[:15]:
        print(f"   • {cmd}")
    if len(handler.all_commands) > 15:
        print(f"   ... y {len(handler.all_commands) - 15} más")
    print()
    
    # 2. Simular un mensaje /help
    print("2️⃣ Simulando mensaje /help...")
    fake_update = {
        'update_id': 999999,
        'message': {
            'message_id': 123,
            'from': {
                'id': int(handler.chat_id) if handler.chat_id else 123456,
                'first_name': 'Test User',
                'username': 'testuser'
            },
            'chat': {
                'id': int(handler.chat_id) if handler.chat_id else 123456,
                'type': 'private'
            },
            'date': 1234567890,
            'text': '/help'
        }
    }
    
    print("   Procesando mensaje simulado...")
    handler._process_message(fake_update)
    
    print()
    print("="*70)
    print("✅ PRUEBA COMPLETADA")
    print("="*70)
    print()
    print("💡 ANÁLISIS:")
    print("   Si viste 'Comando /help ejecutado exitosamente' arriba:")
    print("   → El sistema de comandos FUNCIONA correctamente")
    print("   → El problema está en el POLLING (recepción de mensajes)")
    print()
    print("   Si viste un error:")
    print("   → Hay un problema en el procesamiento de comandos")
    print("   → Revisa el error arriba para más detalles")

except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()


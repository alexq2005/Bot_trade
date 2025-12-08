"""
Script para actualizar el menú de comandos de Telegram en BotFather
Ejecuta este script para registrar todos los comandos disponibles en el menú de Telegram
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

def actualizar_comandos_telegram():
    """Actualiza el menú de comandos de Telegram usando la API de BotFather"""
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ Error: TELEGRAM_BOT_TOKEN no configurado en .env")
        return False
    
    # Definir comandos para el menú de Telegram
    # NOTA: Telegram solo permite comandos en inglés en el menú, pero el bot acepta alias en español
    commands = [
        {
            "command": "start",
            "description": "Iniciar el bot y ver información de bienvenida"
        },
        {
            "command": "help",
            "description": "Ver todos los comandos disponibles"
        },
        {
            "command": "status",
            "description": "Ver estado actual del bot"
        },
        {
            "command": "start_live",
            "description": "🚀 Iniciar bot en modo LIVE trading"
        },
        {
            "command": "portfolio",
            "description": "Ver tu portafolio actual"
        },
        {
            "command": "balance",
            "description": "Ver saldo disponible en IOL"
        },
        {
            "command": "update_balance",
            "description": "🔄 Actualizar saldo desde IOL"
        },
        {
            "command": "analyze",
            "description": "Ejecutar análisis manual del mercado"
        },
        {
            "command": "config",
            "description": "Ver configuración actual del bot"
        },
        {
            "command": "set_risk",
            "description": "⚙️ Cambiar riesgo por operación (ej: 0.03)"
        },
        {
            "command": "set_interval",
            "description": "⚙️ Cambiar intervalo de análisis en minutos"
        },
        {
            "command": "toggle_sentiment",
            "description": "⚙️ Activar/desactivar análisis de sentimiento"
        },
        {
            "command": "toggle_news",
            "description": "⚙️ Activar/desactivar obtención de noticias"
        },
        {
            "command": "toggle_autoconfig",
            "description": "⚙️ Activar/desactivar autoconfiguración"
        },
        {
            "command": "set_mode",
            "description": "⚙️ Cambiar modo (manual/automatic)"
        },
        {
            "command": "set_buy_threshold",
            "description": "⚙️ Cambiar umbral de compra (ej: 25)"
        },
        {
            "command": "set_sell_threshold",
            "description": "⚙️ Cambiar umbral de venta (ej: -25)"
        },
        {
            "command": "scores",
            "description": "📊 Ver scores recientes de análisis"
        },
        {
            "command": "restart",
            "description": "🔄 Reiniciar ciclo de análisis inmediatamente"
        },
        {
            "command": "restart_full",
            "description": "🔄 Solicitar reinicio completo del bot"
        }
    ]
    
    # URL de la API de Telegram
    url = f"https://api.telegram.org/bot{bot_token}/setMyCommands"
    
    try:
        response = requests.post(url, json={"commands": commands}, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        
        if result.get("ok"):
            print("✅ Comandos de Telegram actualizados exitosamente!")
            print(f"\n📋 Comandos registrados ({len(commands)}):")
            for cmd in commands:
                print(f"   • /{cmd['command']} - {cmd['description']}")
            print("\n💡 Ahora puedes ver estos comandos en el menú de Telegram")
            print("   (Escribe '/' en el chat con tu bot para ver el menú)")
            return True
        else:
            print(f"❌ Error: {result.get('description', 'Error desconocido')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando con Telegram API: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 Actualizando comandos de Telegram...")
    print("=" * 60)
    print()
    
    success = actualizar_comandos_telegram()
    
    print()
    print("=" * 60)
    if success:
        print("✅ Proceso completado exitosamente")
    else:
        print("❌ Proceso completado con errores")
    print("=" * 60)


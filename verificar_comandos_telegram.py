"""
Script para verificar y diagnosticar los comandos de Telegram
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

def verificar_comandos():
    """Verifica los comandos registrados en Telegram"""
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE COMANDOS DE TELEGRAM")
    print("=" * 60)
    print()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ Error: TELEGRAM_BOT_TOKEN no configurado en .env")
        return False
    
    # 1. Verificar que el bot existe
    print("1️⃣ Verificando bot...")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        result = response.json()
        
        if result.get('ok'):
            bot_info = result.get('result', {})
            print(f"   ✅ Bot: @{bot_info.get('username', 'N/A')}")
        else:
            print(f"   ❌ Error: {result.get('description', 'Error desconocido')}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print()
    
    # 2. Obtener comandos actuales
    print("2️⃣ Comandos registrados actualmente:")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMyCommands"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        result = response.json()
        
        if result.get('ok'):
            commands = result.get('result', [])
            if commands:
                print(f"   ✅ {len(commands)} comandos encontrados:")
                for cmd in commands:
                    print(f"      • /{cmd.get('command')} - {cmd.get('description', 'Sin descripción')}")
            else:
                print("   ⚠️  No hay comandos registrados")
        else:
            print(f"   ❌ Error: {result.get('description', 'Error desconocido')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print()
    
    # 3. Registrar comandos nuevamente
    print("3️⃣ Registrando comandos...")
    commands = [
        {"command": "start", "description": "Iniciar el bot"},
        {"command": "help", "description": "Ver todos los comandos"},
        {"command": "status", "description": "Ver estado del bot"},
        {"command": "portfolio", "description": "Ver portafolio"},
        {"command": "balance", "description": "Ver saldo en IOL"},
        {"command": "update_balance", "description": "Actualizar saldo desde IOL"},
        {"command": "analyze", "description": "Ejecutar análisis manual"},
        {"command": "config", "description": "Ver configuración"},
        {"command": "set_risk", "description": "Cambiar riesgo (ej: 0.03)"},
        {"command": "set_interval", "description": "Cambiar intervalo (minutos)"},
        {"command": "toggle_sentiment", "description": "Activar/desactivar sentimiento"},
        {"command": "toggle_news", "description": "Activar/desactivar noticias"},
        {"command": "toggle_autoconfig", "description": "Activar/desactivar autoconfig"},
        {"command": "set_mode", "description": "Cambiar modo (manual/automatic)"},
        {"command": "set_buy_threshold", "description": "Cambiar umbral de compra (ej: 25)"},
        {"command": "set_sell_threshold", "description": "Cambiar umbral de venta (ej: -25)"},
        {"command": "scores", "description": "Ver scores recientes de análisis"},
        {"command": "restart", "description": "Reiniciar análisis"},
        {"command": "restart_full", "description": "Reinicio completo"}
    ]
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/setMyCommands"
        response = requests.post(url, json={"commands": commands}, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if result.get("ok"):
            print(f"   ✅ {len(commands)} comandos registrados exitosamente")
            print()
            print("   📋 Comandos registrados:")
            for cmd in commands:
                print(f"      • /{cmd['command']}")
        else:
            print(f"   ❌ Error: {result.get('description', 'Error desconocido')}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print()
    
    # 4. Verificar nuevamente
    print("4️⃣ Verificando comandos después del registro...")
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMyCommands"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        result = response.json()
        
        if result.get('ok'):
            commands_after = result.get('result', [])
            print(f"   ✅ {len(commands_after)} comandos confirmados")
        else:
            print(f"   ⚠️  No se pudieron verificar los comandos")
    except Exception as e:
        print(f"   ⚠️  Error verificando: {e}")
    
    print()
    print("=" * 60)
    print("✅ Verificación completada")
    print("=" * 60)
    print()
    print("💡 INSTRUCCIONES:")
    print("   1. Cierra y vuelve a abrir Telegram")
    print("   2. Abre el chat con tu bot")
    print("   3. Escribe '/' (barra diagonal) para ver el menú")
    print("   4. O escribe directamente un comando como /help")
    print()
    print("⚠️  Si aún no aparecen:")
    print("   • Espera unos segundos y vuelve a intentar")
    print("   • Reinicia Telegram completamente")
    print("   • Verifica que estés en el chat correcto con tu bot")
    
    return True

if __name__ == "__main__":
    verificar_comandos()


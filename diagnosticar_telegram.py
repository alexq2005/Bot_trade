"""
Script de diagnóstico para problemas con Telegram
"""
import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno
env_path = ".env"
if os.path.exists(env_path):
    load_dotenv(env_path)
    print("✅ Archivo .env cargado")
else:
    print("❌ No se encontró archivo .env")
    sys.exit(1)

# Verificar token
token = os.getenv('TELEGRAM_BOT_TOKEN', '')
if token:
    print(f"✅ Token configurado: {token[:10]}...{token[-5:]}")
else:
    print("❌ TELEGRAM_BOT_TOKEN no configurado")
    sys.exit(1)

# Verificar Chat ID
chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
if chat_id:
    print(f"✅ Chat ID configurado: {chat_id}")
else:
    print("⚠️  TELEGRAM_CHAT_ID no configurado (el bot aceptará cualquier chat)")

# Verificar conectividad con Telegram
print("\n🔍 Verificando conectividad con Telegram API...")
try:
    import requests
    
    # Test 1: getMe
    print("\nTest 1: getMe (información del bot)")
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        bot_info = result.get('result', {})
        print(f"✅ Bot conectado exitosamente:")
        print(f"   • Nombre: {bot_info.get('first_name', 'N/A')}")
        print(f"   • Username: @{bot_info.get('username', 'N/A')}")
        print(f"   • ID: {bot_info.get('id', 'N/A')}")
    else:
        print(f"❌ Error: {result.get('description', 'Unknown')}")
        sys.exit(1)
    
    # Test 2: getUpdates
    print("\nTest 2: getUpdates (últimos mensajes)")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"limit": 5, "timeout": 1}
    response = requests.get(url, params=params, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        updates = result.get('result', [])
        print(f"✅ {len(updates)} mensajes recientes:")
        
        if not updates:
            print("   ℹ️  No hay mensajes recientes")
            print("   💡 Envía /help a tu bot ahora para probar")
        else:
            for update in updates[-3:]:  # Mostrar últimos 3
                message = update.get('message', {})
                chat = message.get('chat', {})
                text = message.get('text', '')
                from_user = message.get('from', {})
                
                print(f"\n   📨 Mensaje:")
                print(f"      De: {from_user.get('first_name', 'N/A')} (@{from_user.get('username', 'N/A')})")
                print(f"      Chat ID: {chat.get('id', 'N/A')}")
                print(f"      Texto: {text[:50]}")
                
                # Verificar autorización
                if chat_id and str(chat.get('id')) != str(chat_id):
                    print(f"      ⚠️  CHAT NO AUTORIZADO (esperado: {chat_id})")
                else:
                    print(f"      ✅ Chat autorizado")
    else:
        print(f"❌ Error: {result.get('description', 'Unknown')}")
    
    # Test 3: Verificar conflictos de polling
    print("\nTest 3: Verificar conflictos de polling")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": -1, "timeout": 1}
    response = requests.get(url, params=params, timeout=5)
    
    if response.status_code == 409:
        print("⚠️  Error 409: Hay múltiples instancias del bot haciendo polling")
        print("   💡 Solución:")
        print("      1. Detén todas las instancias del bot")
        print("      2. Espera 30 segundos")
        print("      3. Inicia solo UNA instancia")
    elif response.status_code == 200:
        print("✅ No hay conflictos de polling")
    else:
        print(f"⚠️  Status code inesperado: {response.status_code}")

except requests.exceptions.RequestException as e:
    print(f"❌ Error de conexión: {e}")
    sys.exit(1)
except ImportError:
    print("❌ Librería 'requests' no disponible")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error inesperado: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("📋 RESUMEN")
print("="*60)
print("✅ Token: Configurado y válido")
print(f"{'✅' if chat_id else '⚠️ '} Chat ID: {'Configurado' if chat_id else 'No configurado'}")
print("✅ Conectividad: OK")
print("\n💡 SIGUIENTE PASO:")
print("   1. Envía /help a tu bot desde Telegram")
print("   2. Si no responde, revisa:")
print("      • Que el Chat ID en .env coincida con tu chat")
print("      • Que no haya múltiples instancias del bot corriendo")
print("      • Los logs del bot en logs/*.log")


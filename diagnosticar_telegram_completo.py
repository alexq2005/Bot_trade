"""
Diagnóstico Completo del Sistema de Telegram
Verifica bot, dashboard watchdog y configuración
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Cargar .env
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    print("✅ Archivo .env cargado\n")
else:
    print("❌ No se encontró archivo .env\n")
    sys.exit(1)

print("="*70)
print("📱 DIAGNÓSTICO COMPLETO DEL SISTEMA DE TELEGRAM")
print("="*70)
print()

# 1. Verificar credenciales
print("1️⃣ CREDENCIALES")
print("-" * 70)
token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if token:
    print(f"✅ Token configurado: {token[:15]}...{token[-5:]}")
else:
    print("❌ TELEGRAM_BOT_TOKEN no configurado")
    sys.exit(1)

if chat_id:
    print(f"✅ Chat ID configurado: {chat_id}")
else:
    print("⚠️  TELEGRAM_CHAT_ID no configurado")

print()

# 2. Verificar estado del bot
print("2️⃣ ESTADO DEL BOT DE TRADING")
print("-" * 70)
pid_file = Path("bot.pid")
bot_running = False
bot_pid = None

if pid_file.exists():
    try:
        with open(pid_file, 'r') as f:
            bot_pid = int(f.read().strip())
        
        # Verificar si el proceso existe
        try:
            import psutil
            if psutil.pid_exists(bot_pid):
                process = psutil.Process(bot_pid)
                if process.is_running():
                    cmdline = ' '.join(process.cmdline())
                    if 'run_bot.py' in cmdline or 'trading_bot.py' in cmdline:
                        bot_running = True
                        print(f"✅ Bot ACTIVO (PID: {bot_pid})")
                        print(f"   Comando: {cmdline[:80]}...")
                    else:
                        print(f"⚠️  Proceso {bot_pid} existe pero no es el bot")
                        bot_running = False
                else:
                    print(f"❌ Proceso {bot_pid} no está corriendo")
                    bot_running = False
            else:
                print(f"❌ Proceso {bot_pid} no existe")
                bot_running = False
        except ImportError:
            # Sin psutil, usar método alternativo
            try:
                os.kill(bot_pid, 0)
                bot_running = True
                print(f"✅ Bot probablemente ACTIVO (PID: {bot_pid})")
                print("   ⚠️  Instala psutil para verificación más precisa")
            except (OSError, ProcessLookupError):
                print(f"❌ Proceso {bot_pid} no existe")
                bot_running = False
    except Exception as e:
        print(f"❌ Error leyendo bot.pid: {e}")
        bot_running = False
else:
    print("❌ Bot NO está corriendo (no hay bot.pid)")
    bot_running = False

print()

# 3. Verificar conectividad con Telegram
print("3️⃣ CONECTIVIDAD CON TELEGRAM API")
print("-" * 70)
try:
    import requests
    
    # Test getMe
    url = f"https://api.telegram.org/bot{token}/getMe"
    response = requests.get(url, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        bot_info = result.get('result', {})
        print(f"✅ Conexión exitosa con Telegram API")
        print(f"   • Nombre del bot: {bot_info.get('first_name', 'N/A')}")
        print(f"   • Username: @{bot_info.get('username', 'N/A')}")
        print(f"   • ID del bot: {bot_info.get('id', 'N/A')}")
    else:
        print(f"❌ Error: {result.get('description', 'Unknown')}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    sys.exit(1)

print()

# 4. Verificar conflictos de polling
print("4️⃣ VERIFICACIÓN DE CONFLICTOS DE POLLING")
print("-" * 70)
try:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"offset": -1, "timeout": 1}
    response = requests.get(url, params=params, timeout=5)
    
    if response.status_code == 409:
        print("⚠️  CONFLICTO DETECTADO (Error 409)")
        print("   • Hay múltiples instancias haciendo polling")
        print()
        print("   Posibles causas:")
        if bot_running:
            print("   ✓ El bot está corriendo (esto es normal)")
        else:
            print("   ❌ El bot NO está corriendo pero hay conflicto")
            print("      → Puede haber otro dashboard abierto")
            print("      → Puede haber otro script haciendo polling")
        
        print()
        print("   💡 Solución:")
        print("      1. Cierra todos los dashboards (Streamlit)")
        print("      2. Detén el bot si está corriendo")
        print("      3. Espera 30 segundos")
        print("      4. Reinicia solo UNA instancia")
    elif response.status_code == 200:
        print("✅ NO hay conflictos de polling")
        result = response.json()
        if result.get('ok'):
            updates_count = len(result.get('result', []))
            print(f"   • {updates_count} mensajes pendientes")
    else:
        print(f"⚠️  Status code inesperado: {response.status_code}")
except Exception as e:
    print(f"❌ Error verificando conflictos: {e}")

print()

# 5. Verificar últimos mensajes
print("5️⃣ ÚLTIMOS MENSAJES RECIBIDOS")
print("-" * 70)
try:
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"limit": 5, "timeout": 1}
    response = requests.get(url, params=params, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        updates = result.get('result', [])
        if updates:
            print(f"📨 Se encontraron {len(updates)} mensajes recientes:\n")
            for update in updates[-3:]:  # Últimos 3
                message = update.get('message', {})
                text = message.get('text', '')
                from_user = message.get('from', {})
                chat = message.get('chat', {})
                msg_chat_id = str(chat.get('id', ''))
                date = message.get('date', 0)
                
                # Convertir timestamp a fecha
                msg_date = datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S') if date else 'N/A'
                
                print(f"   📨 De: {from_user.get('first_name', 'N/A')} (@{from_user.get('username', 'N/A')})")
                print(f"      Chat ID: {msg_chat_id}")
                print(f"      Mensaje: {text[:50]}")
                print(f"      Fecha: {msg_date}")
                
                # Verificar autorización
                if chat_id and msg_chat_id != str(chat_id):
                    print(f"      ⚠️  CHAT NO AUTORIZADO (esperado: {chat_id})")
                else:
                    print(f"      ✅ Chat autorizado")
                print()
        else:
            print("ℹ️  No hay mensajes recientes")
    else:
        print(f"❌ Error: {result.get('description', 'Unknown')}")
except Exception as e:
    print(f"❌ Error obteniendo mensajes: {e}")

print()

# 6. Resumen y recomendaciones
print("="*70)
print("📋 RESUMEN Y RECOMENDACIONES")
print("="*70)
print()

if token and chat_id:
    print("✅ Configuración: CORRECTA")
else:
    print("❌ Configuración: INCOMPLETA")

if bot_running:
    print("✅ Bot de Trading: ACTIVO")
    print("   → El bot manejará todos los comandos de Telegram")
    print("   → El watchdog del dashboard se pausará automáticamente")
else:
    print("❌ Bot de Trading: INACTIVO")
    print("   → El watchdog del dashboard escuchará comandos")
    print("   → Solo comandos básicos disponibles:")
    print("      • /start_live - Iniciar bot remotamente")
    print("      • /status - Ver estado")
    print("      • /help - Ver ayuda")

print()
print("💡 PRÓXIMOS PASOS:")
if not bot_running:
    print("   1. Inicia el bot para activar todos los comandos")
    print("   2. O usa /start_live desde Telegram para iniciar remotamente")
else:
    print("   1. Envía /help a @Preoyect_bot en Telegram")
    print("   2. El bot responderá con la lista completa de comandos")
    print("   3. Si no responde, revisa los logs del bot")

print()
print("📄 Documentación completa: TELEGRAM_SETUP.md")
print("="*70)


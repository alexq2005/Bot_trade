"""
Verifica si el thread de polling de Telegram está realmente activo
"""
import os
import sys
import threading
from pathlib import Path

print("="*70)
print("🔍 VERIFICACIÓN DE POLLING ACTIVO")
print("="*70)
print()

# 1. Verificar bot.pid
pid_file = Path("bot.pid")
if not pid_file.exists():
    print("❌ Bot no está corriendo (no hay bot.pid)")
    exit(1)

with open(pid_file, 'r') as f:
    pid = int(f.read().strip())

print(f"✅ Bot corriendo (PID: {pid})")
print()

# 2. Verificar threads activos
print("📊 Threads activos en el proceso:")
try:
    import psutil
    process = psutil.Process(pid)
    threads = process.threads()
    print(f"   Total de threads: {len(threads)}")
    print()
    
    # El thread de polling debería estar entre ellos
    print("💡 Si el bot tiene más de 2-3 threads, el polling probablemente está activo")
    print(f"   (Thread principal + Thread de polling + Otros threads del bot)")
    
except ImportError:
    print("   ⚠️  psutil no disponible - no se puede verificar threads")
except Exception as e:
    print(f"   ❌ Error: {e}")

print()

# 3. Simular envío de mensaje directamente desde Python
print("🧪 PRUEBA DIRECTA DE ENVÍO:")
print("-" * 70)

from dotenv import load_dotenv
load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if token and chat_id:
    try:
        import requests
        from datetime import datetime
        
        # Enviar mensaje de prueba CON TIMESTAMP para verificar recepción
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"""🔔 *PING DEL BOT*

⏰ Timestamp: `{timestamp}`

📝 *Responde con:* `/help`

💡 Si el bot responde, el sistema funciona.
Si NO responde en 5 segundos, hay un problema con el polling.""",
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Mensaje PING enviado a las {timestamp}")
            print(f"   📱 Revisa Telegram y responde con /help")
            print()
            print("⏳ Esperando 8 segundos...")
            import time
            time.sleep(8)
            
            # Verificar si el bot procesó el mensaje
            print()
            print("🔍 Verificando si el bot recibió tu respuesta...")
            
            # Obtener actualizaciones (sin consumirlas)
            url_updates = f"https://api.telegram.org/bot{token}/getUpdates"
            response = requests.get(url_updates, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                updates = result.get('result', [])
                print(f"   📊 Mensajes en cola: {len(updates)}")
                
                if updates:
                    print(f"   ⚠️  HAY {len(updates)} MENSAJE(S) SIN PROCESAR")
                    print(f"   → El bot NO está recibiendo mensajes")
                    print(f"   → El polling NO está funcionando correctamente")
                    print()
                    
                    for update in updates[-3:]:
                        msg = update.get('message', {})
                        text = msg.get('text', '')
                        print(f"      • Mensaje pendiente: {text}")
                else:
                    print(f"   ✅ No hay mensajes pendientes")
                    print(f"   → O el bot los procesó (BUENO)")
                    print(f"   → O no enviaste el mensaje aún")
        else:
            print(f"❌ Error enviando PING: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ Token o Chat ID no configurados")

print()
print("="*70)


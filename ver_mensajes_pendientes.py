"""
Ver mensajes pendientes de Telegram sin procesarlos
"""
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not token:
    print("❌ Token no configurado")
    exit(1)

try:
    import requests
    
    print("="*70)
    print("📨 MENSAJES PENDIENTES EN TELEGRAM")
    print("="*70)
    print()
    
    # Obtener mensajes sin marcarlos como leídos
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"limit": 20}  # Sin offset para no marcar como leídos
    response = requests.get(url, params=params, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        updates = result.get('result', [])
        print(f"📊 Total de mensajes en cola: {len(updates)}")
        print()
        
        if updates:
            print("📋 MENSAJES:")
            print("-" * 70)
            for update in updates:
                message = update.get('message', {})
                text = message.get('text', '')
                from_user = message.get('from', {})
                msg_chat = message.get('chat', {})
                msg_chat_id = msg_chat.get('id', '')
                date = message.get('date', 0)
                update_id = update.get('update_id', 0)
                
                msg_time = datetime.fromtimestamp(date).strftime('%Y-%m-%d %H:%M:%S') if date else 'N/A'
                
                print(f"Update ID: {update_id}")
                print(f"  De: {from_user.get('first_name', 'N/A')} (@{from_user.get('username', 'N/A')})")
                print(f"  Chat ID: {msg_chat_id}")
                print(f"  Mensaje: {text}")
                print(f"  Fecha: {msg_time}")
                
                # Verificar autorización
                if chat_id and str(msg_chat_id) != str(chat_id):
                    print(f"  ⚠️  CHAT NO AUTORIZADO (esperado: {chat_id})")
                else:
                    print(f"  ✅ Chat autorizado")
                
                # Detectar comandos
                if text.startswith('/'):
                    print(f"  🎯 COMANDO DETECTADO: {text}")
                
                print()
            
            # Verificar si el bot está procesando mensajes
            print("="*70)
            print("🔍 ANÁLISIS")
            print("="*70)
            
            help_commands = [u for u in updates if '/help' in u.get('message', {}).get('text', '').lower()]
            if help_commands:
                print(f"⚠️  HAY {len(help_commands)} COMANDO(S) /help SIN PROCESAR")
                print("   → El bot NO está procesando los mensajes")
                print("   → El polling puede no estar funcionando correctamente")
            else:
                print("ℹ️  No hay comandos /help pendientes")
            
            print()
            print("💡 POSIBLES CAUSAS:")
            print("   1. El polling del bot no se inició correctamente")
            print("   2. El _polling_loop() tiene un error y no procesa mensajes")
            print("   3. El offset está mal configurado y no lee mensajes nuevos")
            
        else:
            print("✅ No hay mensajes pendientes")
            print("   💡 Envía /help al bot AHORA y vuelve a ejecutar este script")
    else:
        print(f"❌ Error: {result.get('description', 'Unknown')}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()


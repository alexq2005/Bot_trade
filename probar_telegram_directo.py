"""
Prueba directa de Telegram - Envía mensaje de prueba al bot
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not token or not chat_id:
    print("❌ Token o Chat ID no configurados")
    sys.exit(1)

print("="*70)
print("📱 PRUEBA DIRECTA DE TELEGRAM")
print("="*70)
print(f"Token: {token[:15]}...{token[-5:]}")
print(f"Chat ID: {chat_id}")
print()

try:
    import requests
    
    # 1. Enviar mensaje de prueba AL usuario
    print("1️⃣ Enviando mensaje de prueba a tu chat...")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": """🧪 *MENSAJE DE PRUEBA DEL BOT*

✅ Si recibes este mensaje, significa que:
• El bot puede ENVIAR mensajes
• Tu Chat ID es correcto

📝 *Ahora prueba:*
• Envía `/help` a este bot
• El bot debería responder con la lista de comandos

💡 *Si el bot NO responde a `/help`:*
• Puede haber un problema con el polling (recepción de mensajes)
• Revisa que solo haya UNA instancia del bot corriendo

⏰ Enviado: """ + str(os.popen('echo %time%').read().strip() if sys.platform == 'win32' else os.popen('date "+%H:%M:%S"').read().strip()),
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        print("✅ Mensaje ENVIADO exitosamente")
        print("   📱 Revisa tu Telegram - deberías ver el mensaje")
    else:
        print(f"❌ Error: {result.get('description', 'Unknown')}")
        sys.exit(1)
    
    print()
    
    # 2. Verificar si hay mensajes recibidos (para ver si el usuario envió algo)
    print("2️⃣ Verificando mensajes recibidos del usuario...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    params = {"limit": 10}
    response = requests.get(url, params=params, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        updates = result.get('result', [])
        print(f"📨 Total de mensajes en cola: {len(updates)}")
        
        if updates:
            print("\n📋 Últimos mensajes:")
            for update in updates[-5:]:  # Últimos 5
                message = update.get('message', {})
                text = message.get('text', '')
                from_user = message.get('from', {})
                date = message.get('date', 0)
                
                from datetime import datetime
                msg_time = datetime.fromtimestamp(date).strftime('%H:%M:%S')
                
                print(f"   • [{msg_time}] {from_user.get('first_name', 'N/A')}: {text}")
                
                # Verificar si es comando /help
                if '/help' in text.lower():
                    print(f"      ⚠️  COMANDO /help DETECTADO pero no procesado por el bot!")
        else:
            print("ℹ️  No hay mensajes en cola")
            print("   💡 Envía /help al bot AHORA y vuelve a ejecutar este script")
    
    print()
    
    # 3. Verificar estado de polling
    print("3️⃣ Verificando conflictos de polling...")
    test_params = {"offset": -1, "timeout": 1}
    response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", 
                          params=test_params, timeout=5)
    
    if response.status_code == 409:
        print("⚠️  Error 409: HAY CONFLICTO DE POLLING")
        print("   • Hay múltiples instancias haciendo polling")
        print("   • Esto puede impedir que el bot reciba mensajes")
        print()
        print("   💡 Solución:")
        print("      1. Detén TODAS las instancias del bot")
        print("      2. Cierra todos los dashboards de Streamlit")
        print("      3. Espera 30-60 segundos")
        print("      4. Inicia solo UNA instancia del bot")
    else:
        print("✅ NO hay conflicto de polling")
        print("   • El bot debería poder recibir mensajes")
        print("   • Si no responde, puede ser un problema de código")
    
    print()
    print("="*70)
    print("📋 RESUMEN")
    print("="*70)
    print("✅ El bot PUEDE enviar mensajes")
    print("❓ ¿El bot puede RECIBIR mensajes?")
    print()
    print("💡 PRUEBA:")
    print("   1. Revisa tu Telegram - deberías haber recibido el mensaje de prueba")
    print("   2. Responde con: /help")
    print("   3. Si el bot NO responde:")
    print("      → Hay un problema con el polling del bot")
    print("      → Verifica que solo haya UNA instancia corriendo")
    print("      → Revisa el código de start_polling() en trading_bot.py")
    print("="*70)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


"""
Test simple de Telegram - Verificar que funciona la comunicación
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

print("="*70)
print("🧪 TEST SIMPLE DE TELEGRAM")
print("="*70)
print()
print(f"Token: {TOKEN[:20]}...")
print(f"Chat ID: {CHAT_ID}")
print()

# Test 1: Enviar mensaje
print("📤 Enviando mensaje de prueba...")
url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": "🧪 TEST - Cursor Controller funcionando correctamente"
}

try:
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code == 200:
        print("✅ Mensaje enviado correctamente")
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ Error: {e}")

print()

# Test 2: Obtener updates
print("📥 Obteniendo mensajes pendientes...")
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
params = {"offset": -1, "limit": 5}

try:
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        data = response.json()
        updates = data.get('result', [])
        print(f"✅ Recibidos {len(updates)} mensajes")
        
        if updates:
            print()
            print("📋 Últimos mensajes:")
            for update in updates[-5:]:
                msg = update.get('message', {})
                text = msg.get('text', '')
                date = msg.get('date', 0)
                print(f"  • {text} (timestamp: {date})")
    else:
        print(f"❌ Error: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("="*70)
print("✅ Test completado")
print("="*70)


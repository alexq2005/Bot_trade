"""
Resetea el offset de Telegram para que el bot pueda recibir mensajes nuevos
"""
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TELEGRAM_BOT_TOKEN')
if not token:
    print("❌ Token no configurado")
    exit(1)

try:
    import requests
    
    print("="*70)
    print("🔄 RESETEO DE OFFSET DE TELEGRAM")
    print("="*70)
    print()
    
    # 1. Obtener todos los mensajes pendientes
    print("1️⃣ Obteniendo mensajes actuales...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    response = requests.get(url, timeout=10)
    result = response.json()
    
    if result.get('ok'):
        updates = result.get('result', [])
        print(f"   📊 Mensajes en cola: {len(updates)}")
        
        if updates:
            max_id = max(u.get('update_id', 0) for u in updates)
            print(f"   📍 Último update_id: {max_id}")
            
            # 2. Marcar todos como leídos (avanzar offset más allá del último)
            print()
            print("2️⃣ Marcando mensajes como leídos...")
            params = {"offset": max_id + 1}
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get('ok'):
                print("   ✅ Offset actualizado")
                print(f"   📍 Nuevo offset: {max_id + 1}")
            else:
                print(f"   ❌ Error: {result.get('description', 'Unknown')}")
        else:
            print("   ✅ No hay mensajes pendientes - offset ya está actualizado")
    else:
        print(f"❌ Error: {result.get('description', 'Unknown')}")
        exit(1)
    
    print()
    print("="*70)
    print("✅ OFFSET RESETEADO")
    print("="*70)
    print()
    print("💡 SIGUIENTE PASO:")
    print("   1. El bot ahora solo procesará mensajes NUEVOS")
    print("   2. Envía /help al bot en Telegram AHORA")
    print("   3. El bot debería responder inmediatamente")
    print()
    print("⚠️  IMPORTANTE:")
    print("   • Los mensajes ANTERIORES fueron descartados")
    print("   • Solo mensajes enviados DESPUÉS de este reset serán procesados")
    print("="*70)

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()


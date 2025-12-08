"""
Script para detener todas las instancias de polling de Telegram
"""
import os
import sys
import time
from pathlib import Path

def reset_telegram_offset():
    """Resetea el offset de Telegram para resolver conflictos"""
    try:
        import requests
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        if not bot_token:
            print("❌ TELEGRAM_BOT_TOKEN no configurado")
            return False
        
        # Resetear offset usando getUpdates con offset=-1
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        params = {"offset": -1, "timeout": 1}
        
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                print("✅ Offset de Telegram reseteado")
                return True
            else:
                print(f"⚠️  Respuesta inesperada: {response.status_code}")
                return False
        except Exception as e:
            print(f"⚠️  Error reseteando offset: {e}")
            return False
    except ImportError:
        print("❌ requests no disponible")
        return False


def check_running_instances():
    """Verifica si hay múltiples instancias del bot corriendo"""
    try:
        import psutil
        
        bot_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmdline_str = ' '.join(cmdline)
                    # Buscar procesos relacionados con el bot
                    if 'run_bot.py' in cmdline_str or 'trading_bot.py' in cmdline_str:
                        bot_processes.append({
                            'pid': proc.info['pid'],
                            'cmdline': cmdline_str
                        })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return bot_processes
    except ImportError:
        print("⚠️  psutil no disponible, no se pueden verificar procesos")
        return []


def main():
    print("=" * 70)
    print("🔧 RESOLVER CONFLICTO DE TELEGRAM POLLING")
    print("=" * 70)
    print()
    
    # 1. Verificar procesos corriendo
    print("1️⃣ Verificando procesos del bot...")
    processes = check_running_instances()
    
    if processes:
        print(f"   ⚠️  Se encontraron {len(processes)} proceso(s) del bot:")
        for proc in processes:
            print(f"      • PID {proc['pid']}: {proc['cmdline'][:80]}...")
        print()
        print("   💡 Recomendación: Detén todas las instancias excepto una")
        print()
    else:
        print("   ✅ No se encontraron procesos del bot corriendo")
        print()
    
    # 2. Resetear offset de Telegram
    print("2️⃣ Reseteando offset de Telegram...")
    if reset_telegram_offset():
        print("   ✅ Offset reseteado exitosamente")
    else:
        print("   ⚠️  No se pudo resetear el offset")
    print()
    
    # 3. Instrucciones
    print("=" * 70)
    print("📋 INSTRUCCIONES PARA RESOLVER EL CONFLICTO")
    print("=" * 70)
    print()
    print("1. Detén TODAS las instancias del bot:")
    print("   • Desde el dashboard: Botón 'Detener Bot'")
    print("   • Desde terminal: taskkill /F /PID [PID_NUMBER]")
    print("   • O reinicia tu computadora")
    print()
    print("2. Verifica que no haya procesos corriendo:")
    print("   • Windows: tasklist | findstr python")
    print("   • Linux/Mac: ps aux | grep run_bot")
    print()
    print("3. Inicia SOLO UNA instancia del bot:")
    print("   • python run_bot.py --live --continuous")
    print("   • O desde el dashboard")
    print()
    print("4. NO ejecutes telegram_bot_launcher.py si el bot principal")
    print("   ya está corriendo (ambos hacen polling)")
    print()
    print("=" * 70)
    print("💡 El error 409 ocurre cuando múltiples instancias intentan")
    print("   hacer polling a Telegram simultáneamente.")
    print("=" * 70)


if __name__ == "__main__":
    main()


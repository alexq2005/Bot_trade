"""
Script para detener todos los procesos del bot y limpiar archivos de control
"""

import os
import sys
from pathlib import Path
import time

def detener_todo():
    """Detiene todos los procesos del bot y limpia archivos"""
    
    print("=" * 60)
    print("🛑 DETENIENDO BOT Y MONITOREO CONTINUO")
    print("=" * 60)
    print()
    
    # 1. Crear stop_flag para detener el bot si está corriendo
    print("📋 Creando señal de detención...")
    stop_flag = Path("stop_flag.txt")
    try:
        stop_flag.write_text("STOP", encoding='utf-8')
        print("   ✅ stop_flag.txt creado")
    except Exception as e:
        print(f"   ⚠️  Error creando stop_flag: {e}")
    
    # 2. Limpiar bot.pid
    print("\n📋 Limpiando archivos de control...")
    pid_file = Path("bot.pid")
    if pid_file.exists():
        try:
            # Verificar si el proceso existe antes de eliminar
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                try:
                    os.kill(pid, 0)  # Verificar existencia
                    print(f"   ⚠️  Proceso con PID {pid} aún existe")
                    print(f"   💡 El proceso debería detenerse al cerrar la ventana")
                except (OSError, ProcessLookupError):
                    print(f"   ✅ Proceso con PID {pid} ya no existe")
            except:
                pass
            
            # Eliminar bot.pid
            pid_file.unlink()
            print("   ✅ bot.pid eliminado")
        except Exception as e:
            print(f"   ⚠️  Error eliminando bot.pid: {e}")
    else:
        print("   ℹ️  bot.pid no existe")
    
    # 3. Esperar un momento para que los procesos se detengan
    print("\n⏳ Esperando 3 segundos para que los procesos se detengan...")
    time.sleep(3)
    
    # 4. Verificar procesos restantes
    print("\n🔍 Verificando procesos restantes...")
    try:
        import psutil
        procesos_bot = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'run_bot' in cmdline or 'trading_bot' in cmdline or 'test2_bot_trade' in cmdline:
                    procesos_bot.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if procesos_bot:
            print(f"   ⚠️  Aún hay {len(procesos_bot)} proceso(s) activo(s):")
            for proc in procesos_bot:
                print(f"      PID: {proc['pid']}, Nombre: {proc['name']}")
            print("   💡 Puedes terminarlos manualmente o cerrar las ventanas")
        else:
            print("   ✅ No hay procesos del bot activos")
    except ImportError:
        print("   ℹ️  psutil no disponible, no se pueden verificar procesos")
        print("   💡 Verifica manualmente si hay procesos activos")
    
    # 5. Limpiar stop_flag después de un momento
    print("\n📋 Limpiando stop_flag...")
    if stop_flag.exists():
        try:
            stop_flag.unlink()
            print("   ✅ stop_flag.txt eliminado")
        except:
            pass
    
    print()
    print("=" * 60)
    print("✅ PROCESO DE DETENCIÓN COMPLETADO")
    print("=" * 60)
    print()
    print("💡 Recomendaciones:")
    print("   • Verifica que todas las ventanas estén cerradas")
    print("   • Si hay procesos activos, ciérralos manualmente")
    print("   • Puedes verificar con: python verificar_conflictos.py")
    print()
    print("🚀 Para reiniciar el bot:")
    print("   • python run_bot.py --paper --continuous")
    print("   • O desde Telegram: /iniciar_bot paper")

if __name__ == "__main__":
    detener_todo()


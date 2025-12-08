"""
Script para detener todas las instancias del bot que puedan estar causando conflicto 409
"""
import os
import sys
from pathlib import Path

def get_bot_pids():
    """Obtiene los PIDs de procesos relacionados con el bot"""
    bot_pids = []
    
    # Leer PID del archivo bot.pid si existe
    pid_file = Path("bot.pid")
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            bot_pids.append(pid)
            print(f"✅ PID encontrado en bot.pid: {pid}")
        except:
            pass
    
    # Buscar procesos de Python que ejecutan run_bot.py o trading_bot.py
    try:
        import psutil
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline:
                    cmdline_str = ' '.join(cmdline)
                    # Buscar procesos relacionados con el bot
                    if any(keyword in cmdline_str for keyword in ['run_bot.py', 'trading_bot.py', 'telegram_bot_launcher.py']):
                        pid = proc.info['pid']
                        if pid not in bot_pids:
                            bot_pids.append(pid)
                            print(f"✅ Proceso encontrado: PID {pid}")
                            print(f"   Comando: {cmdline_str[:100]}...")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except ImportError:
        print("⚠️  psutil no disponible, solo se verificará bot.pid")
    
    return bot_pids


def stop_process(pid):
    """Detiene un proceso por PID"""
    try:
        import psutil
        proc = psutil.Process(pid)
        proc.terminate()
        print(f"   ✅ Proceso {pid} terminado")
        return True
    except ImportError:
        # Usar taskkill en Windows
        import subprocess
        try:
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                         capture_output=True, check=True)
            print(f"   ✅ Proceso {pid} terminado (taskkill)")
            return True
        except:
            print(f"   ❌ No se pudo terminar proceso {pid}")
            return False
    except psutil.NoSuchProcess:
        print(f"   ⚠️  Proceso {pid} ya no existe")
        return True
    except Exception as e:
        print(f"   ❌ Error terminando proceso {pid}: {e}")
        return False


def main():
    print("=" * 70)
    print("🛑 DETENER TODAS LAS INSTANCIAS DEL BOT")
    print("=" * 70)
    print()
    
    # Obtener PIDs
    print("🔍 Buscando instancias del bot...")
    bot_pids = get_bot_pids()
    
    if not bot_pids:
        print("✅ No se encontraron instancias del bot corriendo")
        print()
        print("💡 Si aún ves el error 409, puede ser:")
        print("   • Otra aplicación usando el mismo bot de Telegram")
        print("   • Bot corriendo en otra computadora/servidor")
        print("   • Proceso zombie que no aparece en la lista")
        return
    
    print()
    print(f"📋 Se encontraron {len(bot_pids)} instancia(s) del bot:")
    for pid in bot_pids:
        print(f"   • PID: {pid}")
    print()
    
    # Preguntar confirmación
    print("⚠️  ADVERTENCIA: Esto detendrá TODAS las instancias del bot")
    respuesta = input("¿Deseas continuar? (s/n): ").lower().strip()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Operación cancelada")
        return
    
    print()
    print("🛑 Deteniendo procesos...")
    
    # Detener cada proceso
    stopped = 0
    for pid in bot_pids:
        print(f"   Deteniendo PID {pid}...")
        if stop_process(pid):
            stopped += 1
    
    print()
    print(f"✅ {stopped}/{len(bot_pids)} proceso(s) detenido(s)")
    
    # Eliminar archivo PID
    pid_file = Path("bot.pid")
    if pid_file.exists():
        try:
            pid_file.unlink()
            print("✅ Archivo bot.pid eliminado")
        except:
            print("⚠️  No se pudo eliminar bot.pid")
    
    print()
    print("=" * 70)
    print("✅ Todas las instancias han sido detenidas")
    print()
    print("💡 Ahora puedes iniciar el bot nuevamente:")
    print("   python run_bot.py --live --continuous")
    print("=" * 70)


if __name__ == "__main__":
    main()


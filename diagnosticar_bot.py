"""
Script de diagnóstico para entender por qué se detuvo el bot
"""
import os
import sys
from pathlib import Path
from datetime import datetime

print("="*60)
print("🔍 DIAGNÓSTICO DEL BOT")
print("="*60)
print()

# 1. Verificar archivo PID
pid_file = Path("bot.pid")
if pid_file.exists():
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        print(f"✅ Archivo PID encontrado: {pid}")
        
        # Verificar si el proceso sigue corriendo
        try:
            import psutil
            try:
                process = psutil.Process(pid)
                if process.is_running():
                    print(f"✅ Proceso {pid} está corriendo")
                    print(f"   Nombre: {process.name()}")
                    print(f"   Estado: {process.status()}")
                else:
                    print(f"❌ Proceso {pid} NO está corriendo (pero el PID existe)")
            except psutil.NoSuchProcess:
                print(f"❌ Proceso {pid} NO existe (PID huérfano)")
        except ImportError:
            # Sin psutil, usar os.kill
            try:
                os.kill(pid, 0)
                print(f"✅ Proceso {pid} parece estar corriendo")
            except OSError:
                print(f"❌ Proceso {pid} NO está corriendo")
    except Exception as e:
        print(f"⚠️  Error leyendo PID: {e}")
else:
    print("❌ No hay archivo bot.pid - El bot no está corriendo")

print()

# 2. Verificar restart_flag
restart_flag = Path("restart_flag.txt")
if restart_flag.exists():
    print("⚠️  Archivo restart_flag.txt encontrado")
    print("   Este archivo causa que el bot se detenga")
    try:
        content = restart_flag.read_text()
        print(f"   Contenido: {content}")
    except:
        pass
    print("   💡 Elimínalo si quieres que el bot continúe")
else:
    print("✅ No hay restart_flag.txt")

print()

# 3. Verificar logs
log_file = Path("bot.log")
if log_file.exists():
    print(f"✅ Archivo bot.log encontrado")
    try:
        # Leer últimas 20 líneas
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            last_lines = lines[-20:] if len(lines) > 20 else lines
            print("   Últimas líneas del log:")
            print("   " + "-"*56)
            for line in last_lines:
                print(f"   {line.rstrip()}")
            print("   " + "-"*56)
    except Exception as e:
        print(f"   ⚠️  Error leyendo log: {e}")
else:
    print("❌ No hay archivo bot.log")

print()

# 4. Verificar operaciones recientes
ops_file = Path("data/operations_log.json")
if ops_file.exists():
    try:
        import json
        with open(ops_file, 'r', encoding='utf-8') as f:
            operations = json.load(f)
        if operations:
            last_op = operations[-1]
            last_time = datetime.fromisoformat(last_op.get('timestamp', ''))
            time_diff = datetime.now() - last_time
            print(f"✅ Última operación registrada:")
            print(f"   Tipo: {last_op.get('type', 'N/A')}")
            print(f"   Hace: {time_diff}")
            print(f"   Timestamp: {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("⚠️  No hay operaciones registradas")
    except Exception as e:
        print(f"⚠️  Error leyendo operaciones: {e}")
else:
    print("⚠️  No hay archivo operations_log.json")

print()

# 5. Verificar procesos de Python corriendo
print("🔍 Procesos de Python relacionados:")
try:
    import psutil
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if 'run_bot.py' in cmdline or 'trading_bot.py' in cmdline:
                    python_processes.append(proc.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if python_processes:
        for proc in python_processes:
            print(f"   PID: {proc['pid']}")
            print(f"   CMD: {' '.join(proc['cmdline'][:3])}...")
            print()
    else:
        print("   ❌ No se encontraron procesos del bot corriendo")
except ImportError:
    print("   ⚠️  psutil no disponible - no se pueden listar procesos")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print()

# 6. Resumen y recomendaciones
print("="*60)
print("📋 RESUMEN Y RECOMENDACIONES")
print("="*60)
print()

if not pid_file.exists():
    print("❌ El bot NO está corriendo")
    print()
    print("💡 Posibles causas:")
    print("   1. El bot fue detenido manualmente (Ctrl+C)")
    print("   2. Hubo un error crítico que cerró el proceso")
    print("   3. La ventana de consola fue cerrada")
    print("   4. El sistema reinició o apagó")
    print()
    print("✅ Solución:")
    print("   - Inicia el bot nuevamente desde el dashboard")
    print("   - O ejecuta: python run_bot.py --live --continuous")
elif restart_flag.exists():
    print("⚠️  El bot se detuvo por restart_flag.txt")
    print()
    print("✅ Solución:")
    print("   - Elimina restart_flag.txt si quieres que continúe")
    print("   - O reinicia el bot manualmente")
else:
    print("✅ El bot debería estar corriendo")
    print("   Si no lo está, verifica los logs para más detalles")

print()
print("="*60)


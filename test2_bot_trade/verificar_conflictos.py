"""
Script para verificar conflictos del bot
Verifica si hay múltiples instancias corriendo
"""

import os
import sys
from pathlib import Path

def verificar_conflictos():
    """Verifica conflictos del bot"""
    
    print("=" * 60)
    print("🔍 VERIFICACIÓN DE CONFLICTOS DEL BOT")
    print("=" * 60)
    print()
    
    # Verificar archivo PID
    print("📋 Archivos de Control:")
    pid_file = Path("bot.pid")
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid_content = f.read().strip()
                if pid_content:
                    pid_value = int(pid_content)
                    print(f"   ✅ bot.pid existe (PID: {pid_value})")
                    
                    # Verificar si el proceso existe
                    try:
                        os.kill(pid_value, 0)  # Signal 0 solo verifica existencia
                        print(f"   ✅ Proceso activo (PID: {pid_value})")
                    except (OSError, ProcessLookupError):
                        print(f"   ⚠️  Proceso NO existe (PID obsoleto)")
                        print(f"   💡 Considera eliminar bot.pid")
                else:
                    print("   ⚠️  bot.pid existe pero está vacío")
        except Exception as e:
            print(f"   ⚠️  Error leyendo bot.pid: {e}")
    else:
        print("   ❌ bot.pid no existe")
    
    # Verificar stop_flag
    stop_flag = Path("stop_flag.txt")
    if stop_flag.exists():
        print("   ⚠️  stop_flag.txt existe (bot está siendo detenido)")
    else:
        print("   ✅ stop_flag.txt no existe")
    
    print()
    
    # Verificar procesos Python (simplificado - solo verificar PID)
    print("🐍 Verificación de Procesos:")
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid_value = int(f.read().strip())
                try:
                    os.kill(pid_value, 0)
                    print(f"   ✅ Proceso con PID {pid_value} está activo")
                    print(f"   ✅ Solo una instancia detectada (basado en bot.pid)")
                except (OSError, ProcessLookupError):
                    print(f"   ⚠️  Proceso con PID {pid_value} NO existe")
                    print(f"   💡 El archivo bot.pid está obsoleto")
        except:
            pass
    else:
        print("   ✅ No hay bot.pid - no hay instancias corriendo")
    
    print()
    
    # Verificar errores 409 en logs
    print("📄 Verificando logs de Telegram (errores 409):")
    log_dir = Path("logs")
    if log_dir.exists():
        log_files = sorted(log_dir.glob("trading_bot_*.log"), reverse=True)
        if log_files:
            log_file = log_files[0]
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    contenido = f.read()
                    conflictos = []
                    for line in contenido.split('\n'):
                        if '409' in line or 'Conflict' in line.lower() or 'conflicto' in line.lower():
                            conflictos.append(line.strip())
                    
                    if conflictos:
                        print(f"   ⚠️  Se encontraron {len(conflictos)} error(es) 409 en los logs:")
                        for conflicto in conflictos[-5:]:  # Últimos 5
                            print(f"      {conflicto[:80]}...")
                        print("   💡 Esto indica conflicto de Telegram Polling")
                    else:
                        print("   ✅ No se encontraron errores 409 en los logs recientes")
            except Exception as e:
                print(f"   ⚠️  Error leyendo logs: {e}")
        else:
            print("   ℹ️  No se encontraron archivos de log")
    else:
        print("   ℹ️  No se encontró el directorio de logs")
    
    print()
    print("=" * 60)
    print("💡 RECOMENDACIONES")
    print("=" * 60)
    print()
    print("✅ Si solo hay UNA instancia:")
    print("   • Puedes continuar normalmente")
    print("   • El bot maneja conflictos automáticamente")
    print()
    print("⚠️  Si hay MÚLTIPLES instancias:")
    print("   1. Detén todas: /detener_bot (desde Telegram)")
    print("   2. O crea stop_flag.txt")
    print("   3. Espera a que se detengan")
    print("   4. Inicia solo UNA instancia")
    print()
    print("📄 Ver documentación: CONFLICTOS_MONITOREO_CONTINUO.md")

if __name__ == "__main__":
    verificar_conflictos()


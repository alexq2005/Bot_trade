"""
Script para reiniciar el bot por completo
Detiene cualquier instancia corriendo y luego inicia una nueva
"""
import os
import sys
import time
import subprocess
from pathlib import Path

def check_bot_running():
    """Verifica si el bot está corriendo"""
    pid_file = Path("bot.pid")
    if not pid_file.exists():
        return False, None
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Verificar si el proceso existe
        try:
            import psutil
            if psutil.pid_exists(pid):
                return True, pid
        except ImportError:
            # Si psutil no está disponible, intentar con tasklist (Windows)
            if sys.platform == 'win32':
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True
                )
                if str(pid) in result.stdout:
                    return True, pid
        
        # PID no existe, limpiar archivo
        pid_file.unlink()
        return False, None
    except Exception:
        return False, None

def stop_bot():
    """Detiene el bot si está corriendo"""
    print("="*70)
    print("🛑 DETENIENDO BOT")
    print("="*70)
    
    is_running, pid = check_bot_running()
    
    if not is_running:
        print("\n✅ El bot NO está corriendo")
        return True
    
    print(f"\n🔄 Bot corriendo con PID: {pid}")
    print("   Deteniendo...")
    
    try:
        import psutil
        process = psutil.Process(pid)
        process.terminate()
        
        # Esperar hasta 5 segundos
        try:
            process.wait(timeout=5)
            print("   ✅ Bot detenido correctamente")
        except psutil.TimeoutExpired:
            print("   ⚠️  Forzando cierre...")
            process.kill()
            print("   ✅ Bot forzado a cerrar")
    except ImportError:
        # Usar taskkill en Windows
        if sys.platform == 'win32':
            try:
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                             capture_output=True, check=False)
                print("   ✅ Bot detenido")
            except Exception as e:
                print(f"   ⚠️  Error deteniendo bot: {e}")
                return False
        else:
            # Linux/Mac
            try:
                os.kill(pid, 15)  # SIGTERM
                time.sleep(2)
                os.kill(pid, 9)   # SIGKILL si aún está vivo
                print("   ✅ Bot detenido")
            except Exception as e:
                print(f"   ⚠️  Error deteniendo bot: {e}")
                return False
    
    # Limpiar archivo PID
    pid_file = Path("bot.pid")
    if pid_file.exists():
        pid_file.unlink()
    
    # Esperar un momento
    time.sleep(2)
    
    return True

def start_bot(live_mode=False, continuous=True):
    """Inicia el bot"""
    print("\n" + "="*70)
    print("🚀 INICIANDO BOT")
    print("="*70)
    
    mode_text = "💰 LIVE TRADING" if live_mode else "🧪 PAPER TRADING"
    print(f"\n📊 Modo: {mode_text}")
    print(f"🔄 Modo continuo: {'Sí' if continuous else 'No'}")
    
    # Verificar que run_bot.py existe
    run_bot_script = Path("run_bot.py")
    if not run_bot_script.exists():
        print("\n❌ Error: No se encontró run_bot.py")
        return False
    
    # Construir comando
    python_cmd = sys.executable
    cmd = [python_cmd, str(run_bot_script)]
    
    if live_mode:
        cmd.append("--live")
    
    if continuous:
        cmd.append("--continuous")
    
    print(f"\n🔄 Ejecutando: {' '.join(cmd)}")
    
    try:
        if sys.platform == 'win32':
            # En Windows, abrir en nueva ventana de consola
            CREATE_NEW_CONSOLE = 0x00000010
            subprocess.Popen(
                cmd,
                creationflags=CREATE_NEW_CONSOLE,
                cwd=Path.cwd()
            )
            print("\n✅ Bot iniciado en nueva ventana de consola")
            print("   💡 Revisa la ventana para ver los logs")
        else:
            # Linux/Mac - ejecutar en background
            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path.cwd()
            )
            print("\n✅ Bot iniciado en background")
            print("   💡 Revisa los logs en logs/trading_bot_*.log")
        
        # Esperar un momento para que se cree el PID
        time.sleep(3)
        
        # Verificar que se inició
        is_running, pid = check_bot_running()
        if is_running:
            print(f"   ✅ Bot corriendo con PID: {pid}")
        else:
            print("   ⚠️  El bot puede estar iniciando...")
            print("   💡 Espera unos segundos y verifica con: python verificar_operaciones_hoy.py")
        
        return True
    except Exception as e:
        print(f"\n❌ Error iniciando bot: {e}")
        return False

def main():
    """Función principal"""
    print("="*70)
    print("🔄 REINICIO COMPLETO DEL BOT")
    print("="*70)
    
    # Preguntar modo
    print("\n📊 Selecciona el modo:")
    print("   1. 🧪 Paper Trading (simulación)")
    print("   2. 💰 Live Trading (dinero real)")
    
    try:
        choice = input("\n   Opción (1 o 2): ").strip()
        live_mode = (choice == "2")
    except KeyboardInterrupt:
        print("\n\n❌ Cancelado por el usuario")
        return
    
    # Detener bot si está corriendo
    if not stop_bot():
        print("\n⚠️  No se pudo detener el bot completamente")
        print("   💡 Intenta detenerlo manualmente antes de continuar")
        return
    
    # Esperar un momento
    print("\n⏳ Esperando 3 segundos antes de reiniciar...")
    time.sleep(3)
    
    # Iniciar bot
    if start_bot(live_mode=live_mode, continuous=True):
        print("\n" + "="*70)
        print("✅ REINICIO COMPLETO EXITOSO")
        print("="*70)
        print("\n💡 El bot está corriendo con los cambios aplicados")
        print("   • Corrección de calculate_position_size")
        print("   • Actualización inmediata de saldo al iniciar")
        print("\n📊 Para verificar el estado:")
        print("   python verificar_operaciones_hoy.py")
    else:
        print("\n❌ Error al iniciar el bot")
        print("   💡 Revisa los logs para más información")

if __name__ == "__main__":
    main()


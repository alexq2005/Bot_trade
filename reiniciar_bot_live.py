"""
Script para reiniciar el bot en modo LIVE automáticamente
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
        
        try:
            import psutil
            if psutil.pid_exists(pid):
                return True, pid
        except ImportError:
            if sys.platform == 'win32':
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True
                )
                if str(pid) in result.stdout:
                    return True, pid
        
        pid_file.unlink()
        return False, None
    except Exception:
        return False, None

def stop_bot():
    """Detiene el bot si está corriendo"""
    print("🛑 Deteniendo bot...")
    
    is_running, pid = check_bot_running()
    
    if not is_running:
        print("✅ Bot no está corriendo")
        return True
    
    print(f"   PID: {pid}")
    
    try:
        import psutil
        process = psutil.Process(pid)
        process.terminate()
        try:
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            process.kill()
    except ImportError:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                         capture_output=True, check=False)
        else:
            os.kill(pid, 15)
            time.sleep(2)
            os.kill(pid, 9)
    
    pid_file = Path("bot.pid")
    if pid_file.exists():
        pid_file.unlink()
    
    time.sleep(2)
    return True

def start_bot_live():
    """Inicia el bot en modo LIVE"""
    print("\n🚀 Iniciando bot en modo LIVE TRADING...")
    
    run_bot_script = Path("run_bot.py")
    if not run_bot_script.exists():
        print("❌ Error: No se encontró run_bot.py")
        return False
    
    python_cmd = sys.executable
    cmd = [python_cmd, str(run_bot_script), "--live", "--continuous"]
    
    try:
        if sys.platform == 'win32':
            CREATE_NEW_CONSOLE = 0x00000010
            subprocess.Popen(
                cmd,
                creationflags=CREATE_NEW_CONSOLE,
                cwd=Path.cwd()
            )
            print("✅ Bot iniciado en nueva ventana")
        else:
            subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=Path.cwd()
            )
            print("✅ Bot iniciado en background")
        
        time.sleep(3)
        
        is_running, pid = check_bot_running()
        if is_running:
            print(f"✅ Bot corriendo con PID: {pid}")
        else:
            print("⚠️  Esperando que el bot inicie...")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("="*70)
    print("🔄 REINICIO COMPLETO DEL BOT - MODO LIVE")
    print("="*70)
    
    # Detener
    if not stop_bot():
        print("⚠️  No se pudo detener el bot")
        return
    
    time.sleep(2)
    
    # Iniciar
    if start_bot_live():
        print("\n" + "="*70)
        print("✅ REINICIO EXITOSO")
        print("="*70)
        print("\n💡 Cambios aplicados:")
        print("   • Corrección de calculate_position_size")
        print("   • Actualización inmediata de saldo")
        print("\n📊 Verifica el estado con:")
        print("   python verificar_operaciones_hoy.py")
    else:
        print("\n❌ Error al iniciar el bot")

if __name__ == "__main__":
    main()


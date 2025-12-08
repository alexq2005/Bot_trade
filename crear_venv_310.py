"""
Script para crear un nuevo entorno virtual con Python 3.10.9
"""
import subprocess
import sys
import os
import shutil
from pathlib import Path

def print_header(text):
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()

def check_python310():
    """Verifica si Python 3.10 está disponible"""
    print_header("🔍 BUSCANDO PYTHON 3.10.9")
    
    # Intentar diferentes comandos
    commands = [
        ["python3.10", "--version"],
        ["py", "-3.10", "--version"],
        ["python", "--version"],
    ]
    
    python_cmd = None
    version = None
    
    for cmd in commands:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                if "3.10" in output:
                    python_cmd = cmd[0] if len(cmd) == 2 else "python"
                    version = output
                    break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    if python_cmd and version:
        print(f"✅ Encontrado: {version}")
        print(f"   Comando: {python_cmd}")
        return python_cmd
    else:
        print("❌ Python 3.10.9 no encontrado")
        print()
        print("💡 Instrucciones:")
        print("   1. Descarga Python 3.10.9 desde:")
        print("      https://www.python.org/downloads/release/python-3109/")
        print("   2. Instálalo marcando 'Add Python to PATH'")
        print("   3. Reinicia PowerShell")
        print("   4. Ejecuta este script nuevamente")
        return None

def backup_venv():
    """Hace backup del entorno virtual actual"""
    print_header("💾 BACKUP DE ENTORNO VIRTUAL")
    
    venv_path = Path("venv")
    if venv_path.exists():
        backup_path = Path("venv_backup")
        if backup_path.exists():
            print(f"⚠️  Ya existe un backup: {backup_path}")
            response = input("¿Eliminar backup anterior? (s/n): ").lower()
            if response == 's':
                shutil.rmtree(backup_path)
            else:
                print("❌ No se puede continuar sin eliminar el backup")
                return False
        
        print(f"📦 Creando backup de {venv_path}...")
        try:
            shutil.copytree(venv_path, backup_path)
            print(f"✅ Backup creado: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Error creando backup: {e}")
            return False
    else:
        print("ℹ️  No hay entorno virtual para hacer backup")
        return True

def remove_old_venv():
    """Elimina el entorno virtual antiguo"""
    print_header("🗑️  ELIMINANDO ENTORNO VIRTUAL ANTERIOR")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print(f"⚠️  Se eliminará: {venv_path}")
        response = input("¿Continuar? (s/n): ").lower()
        if response != 's':
            print("❌ Operación cancelada")
            return False
        
        try:
            shutil.rmtree(venv_path)
            print("✅ Entorno virtual eliminado")
            return True
        except Exception as e:
            print(f"❌ Error eliminando: {e}")
            return False
    else:
        print("ℹ️  No hay entorno virtual para eliminar")
        return True

def create_new_venv(python_cmd):
    """Crea un nuevo entorno virtual"""
    print_header("🆕 CREANDO NUEVO ENTORNO VIRTUAL")
    
    print(f"Ejecutando: {python_cmd} -m venv venv")
    try:
        result = subprocess.run(
            [python_cmd, "-m", "venv", "venv"],
            check=True,
            timeout=60
        )
        print("✅ Entorno virtual creado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creando entorno virtual: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def install_dependencies():
    """Instala las dependencias"""
    print_header("📦 INSTALANDO DEPENDENCIAS")
    
    if sys.platform == "win32":
        pip_cmd = Path("venv") / "Scripts" / "pip.exe"
    else:
        pip_cmd = Path("venv") / "bin" / "pip"
    
    if not pip_cmd.exists():
        print(f"❌ No se encontró pip en: {pip_cmd}")
        return False
    
    commands = [
        [str(pip_cmd), "install", "--upgrade", "pip"],
        [str(pip_cmd), "install", "-r", "requirements.txt"],
    ]
    
    for cmd in commands:
        print(f"Ejecutando: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                check=True,
                timeout=300
            )
            print("✅ Completado")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True

def verify_installation():
    """Verifica la instalación"""
    print_header("✅ VERIFICANDO INSTALACIÓN")
    
    if sys.platform == "win32":
        python_cmd = Path("venv") / "Scripts" / "python.exe"
    else:
        python_cmd = Path("venv") / "bin" / "python"
    
    if not python_cmd.exists():
        print(f"❌ No se encontró Python en: {python_cmd}")
        return False
    
    # Verificar versión
    try:
        result = subprocess.run(
            [str(python_cmd), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"✅ Versión: {result.stdout.strip()}")
    except Exception as e:
        print(f"⚠️  No se pudo verificar versión: {e}")
    
    # Verificar TensorFlow
    try:
        result = subprocess.run(
            [str(python_cmd), "-c", "import tensorflow as tf; print(f'TensorFlow {tf.__version__}')"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  No se pudo verificar TensorFlow: {e}")
        return False

def main():
    print()
    print("=" * 70)
    print("  🔄 CREACIÓN DE ENTORNO VIRTUAL CON PYTHON 3.10.9")
    print("=" * 70)
    print()
    
    # Paso 1: Verificar Python 3.10
    python_cmd = check_python310()
    if not python_cmd:
        return
    
    print()
    
    # Paso 2: Backup
    if not backup_venv():
        return
    
    print()
    
    # Paso 3: Eliminar venv antiguo
    if not remove_old_venv():
        return
    
    print()
    
    # Paso 4: Crear nuevo venv
    if not create_new_venv(python_cmd):
        return
    
    print()
    
    # Paso 5: Instalar dependencias
    if not install_dependencies():
        print()
        print("⚠️  Hubo errores instalando dependencias")
        print("   Puedes instalarlas manualmente:")
        print("   .\\venv\\Scripts\\Activate.ps1")
        print("   pip install -r requirements.txt")
        return
    
    print()
    
    # Paso 6: Verificar
    if verify_installation():
        print()
        print("=" * 70)
        print("  ✅ MIGRACIÓN COMPLETADA")
        print("=" * 70)
        print()
        print("Para activar el entorno virtual:")
        print("  .\\venv\\Scripts\\Activate.ps1")
        print()
        print("Para verificar:")
        print("  python --version")
        print("  python -c \"import tensorflow; print('OK')\"")

if __name__ == "__main__":
    main()


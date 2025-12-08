"""
Script para recrear el entorno virtual con Python 3.10.9
"""
import subprocess
import sys
import shutil
from pathlib import Path

def print_header(text):
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()

def find_python310():
    """Busca Python 3.10.9 en el sistema"""
    print_header("🔍 BUSCANDO PYTHON 3.10.9")
    
    # Intentar diferentes comandos y obtener la ruta completa
    test_commands = [
        ["py", "-3.10", "--version"],
        ["python3.10", "--version"],
        ["C:\\Python310\\python.exe", "--version"],
        ["C:\\Program Files\\Python310\\python.exe", "--version"],
        ["C:\\Users\\Lexus\\AppData\\Local\\Programs\\Python\\Python310\\python.exe", "--version"],
    ]
    
    python_cmd = None
    python_path = None
    version = None
    
    for cmd in test_commands:
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
                    version = output
                    # Si es 'py -3.10', obtener la ruta completa
                    if cmd[0] == "py":
                        try:
                            # Obtener la ruta completa usando py -3.10 -c "import sys; print(sys.executable)"
                            path_result = subprocess.run(
                                ["py", "-3.10", "-c", "import sys; print(sys.executable)"],
                                capture_output=True,
                                text=True,
                                timeout=5
                            )
                            if path_result.returncode == 0:
                                python_path = path_result.stdout.strip()
                                python_cmd = python_path
                            else:
                                python_cmd = "py -3.10"
                        except:
                            python_cmd = "py -3.10"
                    else:
                        python_cmd = cmd[0]
                        python_path = cmd[0]
                    
                    print(f"✅ Encontrado: {version}")
                    print(f"   Comando: {python_cmd}")
                    if python_path:
                        print(f"   Ruta: {python_path}")
                    return python_cmd
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    
    print("❌ Python 3.10.9 no encontrado")
    print()
    print("💡 Instrucciones:")
    print("   1. Descarga Python 3.10.9 desde:")
    print("      https://www.python.org/downloads/release/python-3109/")
    print("   2. Instálalo marcando 'Add Python to PATH'")
    print("   3. Reinicia PowerShell")
    print("   4. Ejecuta este script nuevamente")
    return None

def backup_and_remove_venv():
    """Hace backup y elimina el venv actual"""
    print_header("💾 BACKUP Y ELIMINACIÓN DE VENV ACTUAL")
    
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    
    if not venv_path.exists():
        print("ℹ️  No hay venv para eliminar")
        return True
    
    backup_path = project_root / "venv_backup"
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
    except Exception as e:
        print(f"⚠️  Error creando backup: {e}")
        print("   Continuando de todas formas...")
    
    print(f"🗑️  Eliminando venv actual...")
    try:
        shutil.rmtree(venv_path)
        print("✅ Venv eliminado")
        return True
    except Exception as e:
        print(f"❌ Error eliminando venv: {e}")
        return False

def create_new_venv(python_cmd):
    """Crea un nuevo venv con Python 3.10.9"""
    print_header("🆕 CREANDO NUEVO VENV CON PYTHON 3.10.9")
    
    project_root = Path(__file__).parent
    
    # Si el comando tiene espacios (como "py -3.10"), dividirlo
    if " " in python_cmd:
        cmd_parts = python_cmd.split()
    else:
        cmd_parts = [python_cmd]
    
    cmd_parts.extend(["-m", "venv", "venv"])
    
    print(f"Ejecutando: {' '.join(cmd_parts)}")
    try:
        result = subprocess.run(
            cmd_parts,
            cwd=project_root,
            check=True,
            timeout=60
        )
        print("✅ Entorno virtual creado correctamente")
        
        # Verificar que el venv creado tenga Python 3.10
        venv_python = project_root / "venv" / "Scripts" / "python.exe"
        if venv_python.exists():
            try:
                result = subprocess.run(
                    [str(venv_python), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                version = result.stdout.strip()
                print(f"✅ Versión del venv: {version}")
                if "3.10" not in version:
                    print(f"⚠️  ADVERTENCIA: El venv no tiene Python 3.10.x")
                    print(f"   Versión encontrada: {version}")
                    return False
            except Exception as e:
                print(f"⚠️  No se pudo verificar versión del venv: {e}")
        
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
    
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    venv_pip = project_root / "venv" / "Scripts" / "pip.exe"
    
    if not venv_python.exists():
        print(f"❌ No se encontró Python en: {venv_python}")
        return False
    
    # Verificar versión
    try:
        result = subprocess.run(
            [str(venv_python), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"✅ Versión: {result.stdout.strip()}")
    except Exception as e:
        print(f"⚠️  No se pudo verificar versión: {e}")
    
    commands = [
        [str(venv_pip), "install", "--upgrade", "pip", "setuptools", "wheel"],
        [str(venv_pip), "install", "-r", str(project_root / "requirements.txt")],
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n[{i}/{len(commands)}] Ejecutando: {' '.join(cmd)}")
        print("-" * 70)
        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                check=False,
                timeout=600
            )
            if result.returncode == 0:
                print(f"✅ Completado")
            else:
                print(f"⚠️  Código de salida: {result.returncode}")
        except subprocess.TimeoutExpired:
            print("⚠️  Tiempo de espera agotado")
        except Exception as e:
            print(f"⚠️  Error: {e}")
    
    return True

def verify_installation():
    """Verifica la instalación"""
    print_header("✅ VERIFICANDO INSTALACIÓN")
    
    project_root = Path(__file__).parent
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    
    # Verificar versión
    try:
        result = subprocess.run(
            [str(venv_python), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = result.stdout.strip()
        print(f"✅ Python: {version}")
        
        if "3.10" not in version:
            print(f"⚠️  ADVERTENCIA: La versión no es 3.10.x")
            print(f"   Versión encontrada: {version}")
    except Exception as e:
        print(f"⚠️  No se pudo verificar versión: {e}")
    
    # Verificar numpy
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import numpy; print(f'NumPy {numpy.__version__}')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            print(f"❌ Error: {result.stderr}")
    except Exception as e:
        print(f"⚠️  No se pudo verificar NumPy: {e}")
    
    # Verificar TensorFlow
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import tensorflow as tf; print(f'TensorFlow {tf.__version__}')"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
            return True
        else:
            print(f"⚠️  TensorFlow no instalado o error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"⚠️  No se pudo verificar TensorFlow: {e}")
        return False

def main():
    print()
    print("=" * 70)
    print("  🔄 RECREACIÓN DE ENTORNO VIRTUAL CON PYTHON 3.10.9")
    print("=" * 70)
    print()
    
    # Paso 1: Buscar Python 3.10
    python_cmd = find_python310()
    if not python_cmd:
        return
    
    print()
    
    # Paso 2: Backup y eliminar venv
    if not backup_and_remove_venv():
        return
    
    print()
    
    # Paso 3: Crear nuevo venv
    if not create_new_venv(python_cmd):
        return
    
    print()
    
    # Paso 4: Instalar dependencias
    print("⚠️  IMPORTANTE: Esto puede tardar varios minutos")
    response = input("¿Continuar con la instalación? (s/n): ").lower()
    if response != 's':
        print("❌ Operación cancelada")
        return
    
    if not install_dependencies():
        print()
        print("⚠️  Hubo errores durante la instalación")
        print("   Puedes intentar manualmente:")
        print("   .\\venv\\Scripts\\pip.exe install -r requirements.txt")
        return
    
    print()
    
    # Paso 5: Verificar
    if verify_installation():
        print()
        print("=" * 70)
        print("  ✅ RECREACIÓN COMPLETADA")
        print("=" * 70)
        print()
        print("Para usar el entorno virtual:")
        print("  cd financial_ai")
        print("  .\\venv\\Scripts\\python.exe run_bot.py --live --continuous")
        print()
        print("Para verificar:")
        print("  .\\venv\\Scripts\\python.exe --version")
        print("  .\\venv\\Scripts\\python.exe -c \"import tensorflow; print('OK')\"")

if __name__ == "__main__":
    main()



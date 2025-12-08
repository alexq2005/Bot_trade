"""
Script directo para crear venv con Python 3.10.9 (sin confirmaciones)
"""
import subprocess
import shutil
from pathlib import Path

def main():
    print("=" * 70)
    print("  🔄 CREANDO VENV CON PYTHON 3.10.9")
    print("=" * 70)
    print()
    
    project_root = Path(__file__).parent
    
    # Buscar Python 3.10.9
    python_paths = [
        r"C:\Users\Lexus\AppData\Local\Programs\Python\Python310\python.exe",
        r"C:\Python310\python.exe",
        r"C:\Program Files\Python310\python.exe",
    ]
    
    python_exe = None
    for path in python_paths:
        if Path(path).exists():
            try:
                result = subprocess.run(
                    [path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "3.10" in result.stdout:
                    python_exe = path
                    print(f"✅ Python 3.10.9 encontrado: {path}")
                    break
            except:
                continue
    
    if not python_exe:
        # Intentar con py launcher
        try:
            result = subprocess.run(
                ["py", "-3.10", "-c", "import sys; print(sys.executable)"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                python_exe = result.stdout.strip()
                print(f"✅ Python 3.10.9 encontrado: {python_exe}")
        except:
            pass
    
    if not python_exe:
        print("❌ Python 3.10.9 no encontrado")
        print("   Instala Python 3.10.9 desde:")
        print("   https://www.python.org/downloads/release/python-3109/")
        return
    
    # Eliminar venv existente
    venv_path = project_root / "venv"
    if venv_path.exists():
        print(f"\n🗑️  Eliminando venv existente...")
        try:
            shutil.rmtree(venv_path)
            print("✅ Venv eliminado")
        except Exception as e:
            print(f"⚠️  Error eliminando venv: {e}")
            return
    
    # Crear nuevo venv
    print(f"\n🆕 Creando nuevo venv...")
    try:
        result = subprocess.run(
            [python_exe, "-m", "venv", "venv"],
            cwd=project_root,
            check=True,
            timeout=60
        )
        print("✅ Venv creado")
    except Exception as e:
        print(f"❌ Error creando venv: {e}")
        return
    
    # Verificar versión del venv
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
                print(f"❌ ERROR: El venv no tiene Python 3.10.x")
                print(f"   Versión encontrada: {version}")
                return
        except Exception as e:
            print(f"⚠️  No se pudo verificar versión: {e}")
    
    # Instalar dependencias
    print(f"\n📦 Instalando dependencias (esto puede tardar varios minutos)...")
    venv_pip = project_root / "venv" / "Scripts" / "pip.exe"
    
    commands = [
        [str(venv_pip), "install", "--upgrade", "pip", "setuptools", "wheel"],
        [str(venv_pip), "install", "-r", str(project_root / "requirements.txt")],
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n[{i}/{len(commands)}] {' '.join(cmd)}")
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
                if i == 1:
                    # Si falla el upgrade de pip, intentar con python -m pip
                    print("   Intentando con python -m pip...")
                    alt_cmd = [str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"]
                    result2 = subprocess.run(alt_cmd, cwd=project_root, check=False, timeout=600)
                    if result2.returncode == 0:
                        print("✅ Completado con método alternativo")
        except subprocess.TimeoutExpired:
            print("⚠️  Tiempo de espera agotado")
        except Exception as e:
            print(f"⚠️  Error: {e}")
    
    # Verificar instalación
    print(f"\n✅ VERIFICANDO INSTALACIÓN")
    print("-" * 70)
    
    try:
        result = subprocess.run(
            [str(venv_python), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"✅ Python: {result.stdout.strip()}")
    except:
        pass
    
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import numpy; print(f'NumPy {numpy.__version__}')"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
    except:
        print("⚠️  NumPy no verificado")
    
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import tensorflow as tf; print(f'TensorFlow {tf.__version__}')"],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            print(f"⚠️  TensorFlow: {result.stderr[:200]}")
    except:
        print("⚠️  TensorFlow no verificado")
    
    print()
    print("=" * 70)
    print("  ✅ PROCESO COMPLETADO")
    print("=" * 70)
    print()
    print("Para ejecutar el bot:")
    print("  .\\venv\\Scripts\\python.exe run_bot.py --live --continuous")
    print()

if __name__ == "__main__":
    main()


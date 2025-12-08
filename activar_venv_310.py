"""
Script para activar el entorno virtual con Python 3.10.9 y reinstalar dependencias
"""
import subprocess
import sys
from pathlib import Path

def print_header(text):
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()

def check_venv_python():
    """Verifica la versión de Python en el venv"""
    print_header("🔍 VERIFICANDO PYTHON EN VENV")
    
    if sys.platform == "win32":
        python_path = Path("venv") / "Scripts" / "python.exe"
    else:
        python_path = Path("venv") / "bin" / "python"
    
    if not python_path.exists():
        print(f"❌ No se encontró Python en: {python_path}")
        return None
    
    try:
        result = subprocess.run(
            [str(python_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        version = result.stdout.strip()
        print(f"✅ {version}")
        
        # Verificar que sea 3.10
        if "3.10" in version:
            print("✅ Python 3.10.x detectado - COMPATIBLE con TensorFlow")
            return python_path
        else:
            print(f"⚠️  Versión {version} - Puede no ser compatible")
            return python_path
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def install_dependencies(python_path):
    """Instala las dependencias usando el Python del venv"""
    print_header("📦 INSTALANDO DEPENDENCIAS")
    
    if sys.platform == "win32":
        pip_path = Path("venv") / "Scripts" / "pip.exe"
    else:
        pip_path = Path("venv") / "bin" / "pip"
    
    commands = [
        [str(pip_path), "install", "--upgrade", "pip", "setuptools", "wheel"],
        [str(pip_path), "install", "-r", "requirements.txt"],
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n[{i}/{len(commands)}] Ejecutando: {' '.join(cmd)}")
        print("-" * 70)
        try:
            result = subprocess.run(
                cmd,
                check=False,
                timeout=600  # 10 minutos
            )
            if result.returncode == 0:
                print(f"✅ Completado")
            else:
                print(f"⚠️  Código de salida: {result.returncode}")
                print("   Continuando de todas formas...")
        except subprocess.TimeoutExpired:
            print("⚠️  Tiempo de espera agotado")
        except Exception as e:
            print(f"⚠️  Error: {e}")
    
    return True

def verify_tensorflow(python_path):
    """Verifica que TensorFlow esté instalado"""
    print_header("✅ VERIFICANDO TENSORFLOW")
    
    try:
        result = subprocess.run(
            [str(python_path), "-c", "import tensorflow as tf; print(f'TensorFlow {tf.__version__}')"],
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
        print(f"⚠️  Error: {e}")
        return False

def main():
    print()
    print("=" * 70)
    print("  🔄 ACTIVACIÓN Y CONFIGURACIÓN DE VENV CON PYTHON 3.10.9")
    print("=" * 70)
    print()
    
    # Verificar Python en venv
    python_path = check_venv_python()
    if not python_path:
        print()
        print("❌ No se puede continuar sin Python en el venv")
        print("   Ejecuta: python crear_venv_310.py")
        return
    
    print()
    
    # Instalar dependencias
    print("⚠️  IMPORTANTE: Esto puede tardar varios minutos")
    response = input("¿Continuar con la instalación? (s/n): ").lower()
    if response != 's':
        print("❌ Operación cancelada")
        return
    
    if not install_dependencies(python_path):
        print()
        print("⚠️  Hubo errores durante la instalación")
        print("   Puedes intentar manualmente:")
        print("   .\\venv\\Scripts\\Activate.ps1")
        print("   pip install -r requirements.txt")
        return
    
    print()
    
    # Verificar TensorFlow
    if verify_tensorflow(python_path):
        print()
        print("=" * 70)
        print("  ✅ INSTALACIÓN COMPLETADA")
        print("=" * 70)
        print()
        print("Para usar el entorno virtual:")
        print("  .\\venv\\Scripts\\Activate.ps1")
        print()
        print("Para verificar:")
        print("  python --version")
        print("  python -c \"import tensorflow; print('OK')\"")
    else:
        print()
        print("⚠️  TensorFlow no se instaló correctamente")
        print("   Intenta manualmente:")
        print("   .\\venv\\Scripts\\Activate.ps1")
        print("   pip install tensorflow")

if __name__ == "__main__":
    main()


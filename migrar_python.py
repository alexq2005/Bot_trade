"""
Script automatizado para migrar a Python 3.10.9
"""
import sys
import subprocess
import os
import shutil
from pathlib import Path

def print_header(text):
    print("=" * 70)
    print(f"  {text}")
    print("=" * 70)
    print()

def check_python_version():
    """Verifica la versión actual de Python"""
    print_header("🐍 VERIFICACIÓN DE VERSIÓN DE PYTHON")
    
    version = sys.version_info
    print(f"Versión actual: Python {version.major}.{version.minor}.{version.micro}")
    print(f"Ruta del ejecutable: {sys.executable}")
    print()
    
    if version.major == 3 and version.minor == 10:
        print("✅ Python 3.10 - COMPATIBLE con TensorFlow")
        return True
    elif version.major == 3 and version.minor == 14:
        print("❌ Python 3.14 - NO COMPATIBLE con TensorFlow")
        print("   ⚠️  TensorFlow requiere Python 3.7-3.11")
        print("   💡 Necesitas cambiar a Python 3.10.9")
        return False
    elif version.major == 3 and 7 <= version.minor <= 11:
        print(f"✅ Python 3.{version.minor} - COMPATIBLE con TensorFlow")
        return True
    else:
        print(f"⚠️  Python {version.major}.{version.minor} - Verificar compatibilidad")
        return False

def check_venv():
    """Verifica si existe un entorno virtual"""
    print_header("🔍 VERIFICACIÓN DE ENTORNO VIRTUAL")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("✅ Entorno virtual encontrado: venv/")
        
        # Verificar Python en venv
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            python_path = venv_path / "bin" / "python"
        
        if python_path.exists():
            try:
                result = subprocess.run(
                    [str(python_path), "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                print(f"   Versión en venv: {result.stdout.strip()}")
            except Exception as e:
                print(f"   ⚠️  No se pudo verificar: {e}")
        
        return True
    else:
        print("❌ No se encontró entorno virtual")
        return False

def check_tensorflow():
    """Verifica si TensorFlow está instalado"""
    print_header("🔍 VERIFICACIÓN DE TENSORFLOW")
    
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow {tf.__version__} instalado")
        return True
    except ImportError:
        print("❌ TensorFlow NO está instalado")
        return False
    except Exception as e:
        print(f"⚠️  Error al verificar TensorFlow: {e}")
        return False

def get_instructions():
    """Muestra instrucciones de migración"""
    print_header("📋 INSTRUCCIONES DE MIGRACIÓN")
    
    print("Para migrar a Python 3.10.9, sigue estos pasos:")
    print()
    print("1. DESCARGAR PYTHON 3.10.9:")
    print("   https://www.python.org/downloads/release/python-3109/")
    print("   • Descarga: Windows installer (64-bit)")
    print("   • ✅ Marca 'Add Python to PATH'")
    print()
    print("2. CREAR NUEVO ENTORNO VIRTUAL:")
    print("   python -m venv venv")
    print()
    print("3. ACTIVAR ENTORNO:")
    print("   .\\venv\\Scripts\\Activate.ps1")
    print()
    print("4. INSTALAR DEPENDENCIAS:")
    print("   pip install -r requirements.txt")
    print()
    print("5. VERIFICAR:")
    print("   python -c \"import tensorflow; print('OK')\"")
    print()
    print("📖 Ver GUIA_MIGRACION_PYTHON.md para más detalles")

def main():
    print()
    print("=" * 70)
    print("  🔄 DIAGNÓSTICO DE MIGRACIÓN A PYTHON 3.10.9")
    print("=" * 70)
    print()
    
    # Verificar versión
    is_compatible = check_python_version()
    print()
    
    # Verificar entorno virtual
    has_venv = check_venv()
    print()
    
    # Verificar TensorFlow
    has_tensorflow = check_tensorflow()
    print()
    
    # Resumen
    print_header("📊 RESUMEN")
    
    status = []
    status.append(("Python 3.10.x", is_compatible))
    status.append(("Entorno Virtual", has_venv))
    status.append(("TensorFlow", has_tensorflow))
    
    for name, ok in status:
        icon = "✅" if ok else "❌"
        print(f"{icon} {name}")
    
    print()
    
    if all(ok for _, ok in status):
        print("✅ Todo está correcto. No necesitas migrar.")
    else:
        print("⚠️  Se requiere migración a Python 3.10.9")
        print()
        get_instructions()

if __name__ == "__main__":
    main()


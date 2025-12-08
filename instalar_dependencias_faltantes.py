"""
Script para instalar dependencias faltantes detectadas en el testeo
"""
import subprocess
import sys

def instalar_paquete(paquete):
    """Instala un paquete usando pip"""
    try:
        print(f"📦 Instalando {paquete}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])
        print(f"✅ {paquete} instalado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando {paquete}: {e}")
        return False

def main():
    print("=" * 70)
    print("📦 INSTALACIÓN DE DEPENDENCIAS FALTANTES")
    print("=" * 70)
    print()
    
    dependencias_faltantes = [
        "tensorflow",
        "scikit-learn"
    ]
    
    print("🔍 Dependencias a instalar:")
    for dep in dependencias_faltantes:
        print(f"   • {dep}")
    print()
    
    respuesta = input("¿Deseas instalar estas dependencias? (s/n): ").lower().strip()
    
    if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
        print("❌ Instalación cancelada")
        return
    
    print()
    print("🚀 Iniciando instalación...")
    print()
    
    exitosos = 0
    for dep in dependencias_faltantes:
        if instalar_paquete(dep):
            exitosos += 1
        print()
    
    print("=" * 70)
    print(f"✅ {exitosos}/{len(dependencias_faltantes)} dependencias instaladas")
    print("=" * 70)
    print()
    print("💡 Ejecuta 'python testeo_completo.py' nuevamente para verificar")

if __name__ == "__main__":
    main()


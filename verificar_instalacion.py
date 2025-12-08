"""
Script para verificar que la instalación esté completa y correcta
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Verifica la versión de Python"""
    print("🐍 Verificando Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Se requiere 3.9+")
        return False

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    print("\n📦 Verificando dependencias...")
    
    required_packages = [
        'tensorflow',
        'pandas',
        'numpy',
        'requests',
        'streamlit',
        'yfinance',
        'scikit-learn',
        'plotly',
        'python-dotenv'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - NO instalado")
            missing.append(package)
    
    if missing:
        print(f"\n   ⚠️  Faltan {len(missing)} paquetes")
        print(f"   💡 Ejecuta: pip install -r requirements.txt")
        return False
    
    return True

def check_env_file():
    """Verifica que el archivo .env exista y tenga las variables necesarias"""
    print("\n🔐 Verificando archivo .env...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("   ❌ Archivo .env NO encontrado")
        print("   💡 Crea el archivo .env con tus credenciales")
        return False
    
    print("   ✅ Archivo .env encontrado")
    
    # Verificar variables
    required_vars = ['IOL_USERNAME', 'IOL_PASSWORD']
    optional_vars = ['TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    missing_required = []
    for var in required_vars:
        if var not in content:
            missing_required.append(var)
        else:
            print(f"   ✅ {var} configurado")
    
    if missing_required:
        print(f"   ❌ Faltan variables requeridas: {', '.join(missing_required)}")
        return False
    
    # Verificar opcionales
    for var in optional_vars:
        if var in content:
            print(f"   ✅ {var} configurado (opcional)")
        else:
            print(f"   ⚠️  {var} no configurado (opcional)")
    
    return True

def check_iol_connection():
    """Verifica conexión a IOL"""
    print("\n🔌 Verificando conexión a IOL...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from src.connectors.iol_client import IOLClient
        iol = IOLClient()
        balance = iol.get_available_balance()
        print(f"   ✅ Conectado a IOL")
        print(f"   💰 Saldo disponible: ${balance:,.2f} ARS")
        return True
    except Exception as e:
        print(f"   ❌ Error conectando a IOL: {e}")
        print("   💡 Verifica tus credenciales en .env")
        return False

def check_config_files():
    """Verifica archivos de configuración"""
    print("\n⚙️  Verificando archivos de configuración...")
    
    config_files = {
        'professional_config.json': 'Configuración del bot',
        'my_portfolio.json': 'Portafolio de símbolos'
    }
    
    all_ok = True
    for file, desc in config_files.items():
        if Path(file).exists():
            print(f"   ✅ {file} ({desc})")
        else:
            print(f"   ⚠️  {file} no encontrado ({desc})")
            all_ok = False
    
    return all_ok

def check_directories():
    """Verifica que los directorios necesarios existan"""
    print("\n📁 Verificando directorios...")
    
    directories = ['data', 'logs', 'src']
    
    all_ok = True
    for dir_name in directories:
        if Path(dir_name).exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ⚠️  {dir_name}/ no encontrado")
            all_ok = False
    
    return all_ok

def main():
    """Función principal"""
    print("="*70)
    print("🔍 VERIFICACIÓN DE INSTALACIÓN")
    print("="*70)
    
    checks = [
        ("Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Archivo .env", check_env_file),
        ("Archivos de configuración", check_config_files),
        ("Directorios", check_directories),
        ("Conexión IOL", check_iol_connection),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n   ❌ Error en verificación de {name}: {e}")
            results.append((name, False))
    
    # Resumen
    print("\n" + "="*70)
    print("📋 RESUMEN")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"   {status} {name}")
    
    print(f"\n📊 Resultado: {passed}/{total} verificaciones pasadas")
    
    if passed == total:
        print("\n🎉 ¡Instalación completa y correcta!")
        print("   💡 Puedes ejecutar el bot con: python run_bot.py --continuous")
    else:
        print("\n⚠️  Instalación incompleta")
        print("   💡 Revisa los errores arriba y corrige los problemas")
        print("   💡 Consulta GUIA_INSTALACION.md para más ayuda")

if __name__ == "__main__":
    main()


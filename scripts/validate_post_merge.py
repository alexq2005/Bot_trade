#!/usr/bin/env python3
"""
Script de Validación Rápida Post-Merge
Ejecutar después de aplicar los cambios de Jules
"""
import sys
import os
import importlib

def test_critical_imports():
    """Verifica que los módulos críticos se importen sin errores"""
    print("🔍 TEST 1: Importaciones Críticas")
    critical_modules = [
        "src.connectors.iol_client",
        "src.services.price_service",
        "src.services.trading_form_service",
        "src.services.portfolio_persistence",
    ]
    
    sys.path.insert(0, os.path.abspath("."))
    
    for module in critical_modules:
        try:
            importlib.import_module(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            return False
    return True

def test_env_vars():
    """Verifica variables de entorno críticas"""
    print("\n🔍 TEST 2: Variables de Entorno")
    from dotenv import load_dotenv
    load_dotenv()
    
    required = ["IOL_USER", "IOL_PASSWORD"]
    for var in required:
        if os.getenv(var):
            print(f"  ✅ {var} configurado")
        else:
            print(f"  ⚠️ {var} faltante (esperado si usas .env)")
    return True

def test_file_structure():
    """Verifica que archivos críticos existan"""
    print("\n🔍 TEST 3: Estructura de Archivos")
    critical_files = [
        "test2_bot_trade/dashboard.py",
        "test2_bot_trade/src/dashboard/views/terminal_manual_simplified.py",
        "test2_bot_trade/trading_bot.py",
        "requirements.txt",
    ]
    
    for file in critical_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} NO EXISTE")
            return False
    return True

def main():
    print("🚀 VALIDACIÓN POST-MERGE DE CAMBIOS DE JULES\n")
    
    tests = [
        test_file_structure(),
        test_env_vars(),
        test_critical_imports(),
    ]
    
    if all(tests):
        print("\n✅ VALIDACIÓN EXITOSA - Sistema parece estable")
        print("Siguiente paso: Ejecutar 'streamlit run test2_bot_trade/dashboard.py'")
        return 0
    else:
        print("\n❌ VALIDACIÓN FALLÓ - Revisar errores arriba")
        return 1

if __name__ == "__main__":
    sys.exit(main())

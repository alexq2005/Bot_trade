"""
Script de Diagnóstico Completo del Sistema
Verifica todos los componentes y genera un reporte
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Agregar directorio raíz al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.services.health_monitor import check_system_health
from src.core.config_manager import get_config_manager, validate_config
from src.core.circuit_breaker import get_iol_circuit_breaker, get_telegram_circuit_breaker
from src.core.enhanced_cache import get_quote_cache, get_prediction_cache
from src.core.logger import get_logger

logger = get_logger("diagnostico")


def print_section(title: str):
    """Imprime un título de sección"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def check_health():
    """Verifica la salud del sistema"""
    print_section("🏥 SALUD DEL SISTEMA")
    
    try:
        health = check_system_health()
        
        status_icons = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }
        
        icon = status_icons.get(health.overall_status, "❓")
        print(f"\nEstado General: {icon} {health.overall_status.upper()}")
        print(f"Timestamp: {health.timestamp}")
        
        print("\nComponentes:")
        for component in health.components:
            icon = status_icons.get(component.status, "❓")
            print(f"  {icon} {component.component}: {component.status}")
            print(f"     {component.message}")
            if component.response_time_ms:
                print(f"     Tiempo de respuesta: {component.response_time_ms:.2f} ms")
        
        print("\nMétricas:")
        for key, value in health.metrics.items():
            print(f"  {key}: {value}")
        
        print("\nRecomendaciones:")
        for rec in health.recommendations:
            print(f"  {rec}")
        
        return health.overall_status == "healthy"
    except Exception as e:
        print(f"❌ Error verificando salud: {e}")
        return False


def check_configuration():
    """Verifica la configuración"""
    print_section("⚙️ CONFIGURACIÓN")
    
    try:
        manager = get_config_manager()
        config = manager.get_config()
        
        print(f"Entorno: {config.environment}")
        print(f"Símbolos: {len(config.trading.symbols)} configurados")
        print(f"Capital: ${config.trading.initial_capital:,.2f}")
        print(f"Riesgo por trade: {config.trading.risk_per_trade}%")
        
        # Validar
        is_valid = validate_config()
        return is_valid
    except Exception as e:
        print(f"❌ Error verificando configuración: {e}")
        return False


def check_circuit_breakers():
    """Verifica circuit breakers"""
    print_section("🔌 CIRCUIT BREAKERS")
    
    try:
        iol_cb = get_iol_circuit_breaker()
        telegram_cb = get_telegram_circuit_breaker()
        
        iol_stats = iol_cb.get_stats()
        telegram_stats = telegram_cb.get_stats()
        
        print("IOL Circuit Breaker:")
        print(f"  Estado: {iol_stats['state']}")
        print(f"  Llamadas totales: {iol_stats['total_calls']}")
        print(f"  Fallos: {iol_stats['total_failures']}")
        print(f"  Éxitos: {iol_stats['total_successes']}")
        
        print("\nTelegram Circuit Breaker:")
        print(f"  Estado: {telegram_stats['state']}")
        print(f"  Llamadas totales: {telegram_stats['total_calls']}")
        print(f"  Fallos: {telegram_stats['total_failures']}")
        print(f"  Éxitos: {telegram_stats['total_successes']}")
        
        all_healthy = iol_stats['state'] != 'open' and telegram_stats['state'] != 'open'
        return all_healthy
    except Exception as e:
        print(f"❌ Error verificando circuit breakers: {e}")
        return False


def check_cache():
    """Verifica el estado del caché"""
    print_section("💾 CACHÉ")
    
    try:
        quote_cache = get_quote_cache()
        prediction_cache = get_prediction_cache()
        
        quote_stats = quote_cache.get_stats()
        prediction_stats = prediction_cache.get_stats()
        
        print("Caché de Cotizaciones:")
        print(f"  Entradas en memoria: {quote_stats['memory_entries']}")
        print(f"  Entradas persistentes: {quote_stats['persistent_entries']}")
        
        print("\nCaché de Predicciones:")
        print(f"  Entradas en memoria: {prediction_stats['memory_entries']}")
        print(f"  Entradas persistentes: {prediction_stats['persistent_entries']}")
        
        return True
    except Exception as e:
        print(f"❌ Error verificando caché: {e}")
        return False


def check_files():
    """Verifica archivos importantes"""
    print_section("📁 ARCHIVOS")
    
    important_files = [
        "trading_bot.py",
        "dashboard.py",
        "run_bot.py",
        ".env",
        "professional_config.json",
        "trades.json",
        "trading_bot.db",
    ]
    
    all_exist = True
    for file_path in important_files:
        path = Path(file_path)
        exists = path.exists()
        icon = "✅" if exists else "❌"
        size = f"({path.stat().st_size / 1024:.1f} KB)" if exists else ""
        print(f"  {icon} {file_path} {size}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_dependencies():
    """Verifica dependencias importantes"""
    print_section("📦 DEPENDENCIAS")
    
    required_packages = [
        "pandas",
        "numpy",
        "tensorflow",
        "streamlit",
        "plotly",
        "requests",
        "yfinance",
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (no instalado)")
            all_installed = False
    
    return all_installed


def generate_report():
    """Genera un reporte completo"""
    print("\n" + "="*70)
    print("  🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    results['health'] = check_health()
    results['config'] = check_configuration()
    results['circuit_breakers'] = check_circuit_breakers()
    results['cache'] = check_cache()
    results['files'] = check_files()
    results['dependencies'] = check_dependencies()
    
    # Resumen final
    print_section("📊 RESUMEN")
    
    total_checks = len(results)
    passed_checks = sum(1 for v in results.values() if v)
    
    print(f"Checks realizados: {total_checks}")
    print(f"Checks exitosos: {passed_checks}")
    print(f"Checks fallidos: {total_checks - passed_checks}")
    
    for check_name, passed in results.items():
        icon = "✅" if passed else "❌"
        print(f"  {icon} {check_name.replace('_', ' ').title()}")
    
    overall_status = "✅ SALUDABLE" if all(results.values()) else "⚠️ REQUIERE ATENCIÓN"
    print(f"\nEstado General: {overall_status}")
    
    return results


if __name__ == "__main__":
    try:
        results = generate_report()
        
        # Exit code basado en resultados
        if all(results.values()):
            sys.exit(0)
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Diagnóstico interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Error fatal en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


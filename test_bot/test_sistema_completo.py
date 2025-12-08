"""
Test del Sistema Completo
Importa y prueba Bot Live + Dashboard de forma segura

Estado: 🧪 TESTING
Versión: 0.1

Descripción:
    Prueba el sistema completo (bot + dashboard) en modo testing
    sin afectar el bot de producción que está corriendo.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import time

# Configurar paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Suprimir warnings
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("="*70)
print("🧪 TEST SISTEMA COMPLETO - Bot Live + Dashboard")
print("="*70)
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
print()

# Verificar que el bot de producción está corriendo
print("🔍 Verificando estado del bot de producción...")
pid_file = PROJECT_ROOT / "bot.pid"

if pid_file.exists():
    with open(pid_file, 'r') as f:
        prod_pid = f.read().strip()
    print(f"   ✅ Bot de PRODUCCIÓN está corriendo (PID: {prod_pid})")
    print(f"   💡 El test se ejecutará de forma INDEPENDIENTE")
    print()
else:
    print(f"   ℹ️  Bot de producción no está corriendo")
    print()

# Cargar configuración
print("1️⃣ Cargando módulos del sistema...")
print()

# Importar TradingBot
try:
    print("   📦 Importando trading_bot.py...")
    from trading_bot import TradingBot
    print("   ✅ TradingBot importado")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Importar componentes del Dashboard
try:
    print("   📦 Importando componentes de dashboard.py...")
    
    # No importamos todo el dashboard (causaría conflicto con Streamlit)
    # Solo importamos las funciones/clases específicas que necesitamos
    
    # Importar servicios del dashboard
    from src.services.prediction_service import PredictionService
    from src.services.technical_analysis import TechnicalAnalysisService
    from src.services.portfolio_optimizer import PortfolioOptimizer
    from src.services.adaptive_risk_manager import AdaptiveRiskManager
    from src.connectors.iol_client import IOLClient
    from src.services.portfolio_persistence import load_portfolio
    
    print("   ✅ Componentes de dashboard importados")
except Exception as e:
    print(f"   ⚠️  Error importando dashboard components: {e}")
    print(f"   💡 Continuando con funcionalidad básica")

print()

# Crear instancias de servicios (modo testing)
print("2️⃣ Inicializando servicios en modo TESTING...")
print()

services = {}

try:
    print("   🔮 Inicializando PredictionService...")
    services['predictor'] = PredictionService()
    print("   ✅ PredictionService listo")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

try:
    print("   📊 Inicializando TechnicalAnalysisService...")
    services['technical'] = TechnicalAnalysisService(iol_client=None)
    print("   ✅ TechnicalAnalysisService listo")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

try:
    print("   💼 Inicializando PortfolioOptimizer...")
    services['optimizer'] = PortfolioOptimizer()
    print("   ✅ PortfolioOptimizer listo")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

try:
    print("   🛡️  Inicializando AdaptiveRiskManager...")
    services['risk_manager'] = AdaptiveRiskManager(initial_capital=10000.0)
    print("   ✅ AdaptiveRiskManager listo")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print()
print(f"✅ {len(services)} servicios inicializados")
print()

# Crear Test Bot con servicios del dashboard
print("3️⃣ Creando Test Bot con integración completa...")
print()

try:
    test_bot = TradingBot(
        symbols=['AAPL', 'MSFT', 'GOOGL'],  # Símbolos de prueba
        initial_capital=10000.0,
        paper_trading=True  # SIEMPRE paper en testing
    )
    print("   ✅ Test Bot inicializado con éxito")
    print()
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Cargar portafolio de producción (solo lectura)
print("4️⃣ Cargando datos de producción (solo lectura)...")
print()

try:
    portfolio = load_portfolio()
    if portfolio:
        print(f"   ✅ Portafolio cargado: {len(portfolio)} activos")
        total_value = sum(p.get('total_val', 0) for p in portfolio)
        print(f"   💰 Valor total portafolio: ${total_value:,.2f}")
    else:
        print(f"   ℹ️  Portafolio vacío")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

print()

# Menú de testing
print("="*70)
print("🎮 MENÚ DE TESTING DEL SISTEMA COMPLETO")
print("="*70)
print()
print("1. 🔍 Ejecutar ciclo de análisis único (3 símbolos)")
print("2. 📊 Analizar símbolo específico con todos los servicios")
print("3. 💼 Ver portafolio de producción (solo lectura)")
print("4. 🧪 Probar servicios del dashboard")
print("5. 🤖 Ejecutar predicción con IA")
print("6. 📈 Ejecutar análisis técnico completo")
print("7. 🛡️  Probar gestión de riesgo")
print("8. 🔄 Modo continuo (intervalo 5 min)")
print("9. ❌ Salir")
print()

def test_prediccion_ia():
    """Prueba el servicio de predicción"""
    print("="*70)
    print("🤖 TEST DE PREDICCIÓN CON IA")
    print("="*70)
    print()
    
    symbol = input("📊 Símbolo a predecir (ej: AAPL): ").strip().upper() or "AAPL"
    
    try:
        print(f"\n🔮 Ejecutando predicción para {symbol}...")
        predictor = services.get('predictor')
        
        if not predictor:
            print("❌ PredictionService no disponible")
            return
        
        resultado = predictor.generate_signal(symbol, threshold=2.0)
        
        print("\n✅ PREDICCIÓN COMPLETADA")
        print("-"*70)
        print(f"Símbolo: {symbol}")
        print(f"Precio Actual: ${resultado.get('current_price', 0):.2f}")
        print(f"Precio Predicho: ${resultado.get('predicted_price', 0):.2f}")
        print(f"Cambio Esperado: {resultado.get('change_pct', 0):+.2f}%")
        print(f"Señal: {resultado.get('signal', 'N/A')}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_analisis_tecnico():
    """Prueba el análisis técnico"""
    print("="*70)
    print("📈 TEST DE ANÁLISIS TÉCNICO")
    print("="*70)
    print()
    
    symbol = input("📊 Símbolo a analizar (ej: AAPL): ").strip().upper() or "AAPL"
    
    try:
        print(f"\n📊 Ejecutando análisis técnico para {symbol}...")
        tech_service = services.get('technical')
        
        if not tech_service:
            print("❌ TechnicalAnalysisService no disponible")
            return
        
        analisis = tech_service.get_full_analysis(symbol)
        
        print("\n✅ ANÁLISIS TÉCNICO COMPLETADO")
        print("-"*70)
        
        # Momentum
        momentum = analisis.get('momentum', {})
        print("\n📊 Momentum:")
        print(f"  RSI: {momentum.get('rsi', 'N/A')}")
        print(f"  MACD: {momentum.get('macd', 'N/A')}")
        print(f"  Signal: {momentum.get('macd_signal', 'N/A')}")
        
        # Trend
        trend = analisis.get('trend', {})
        print("\n📈 Tendencia:")
        print(f"  Precio Actual: ${trend.get('current_price', 0):.2f}")
        print(f"  SMA 20: ${trend.get('sma_20', 0):.2f}")
        print(f"  EMA 12: ${trend.get('ema_12', 0):.2f}")
        
        # Volatility
        volatility = analisis.get('volatility', {})
        print("\n📊 Volatilidad:")
        print(f"  ATR: {volatility.get('atr', 'N/A')}")
        print(f"  Bollinger Superior: {volatility.get('bb_upper', 'N/A')}")
        print(f"  Bollinger Inferior: {volatility.get('bb_lower', 'N/A')}")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def test_gestion_riesgo():
    """Prueba la gestión de riesgo"""
    print("="*70)
    print("🛡️  TEST DE GESTIÓN DE RIESGO")
    print("="*70)
    print()
    
    risk_manager = services.get('risk_manager')
    
    if not risk_manager:
        print("❌ RiskManager no disponible")
        return
    
    print(f"Capital Total: ${risk_manager.capital:,.2f}")
    print(f"Capital Disponible: ${risk_manager.available_capital:,.2f}")
    print()
    
    # Simular cálculo de posición
    symbol = input("📊 Símbolo para calcular posición (ej: AAPL): ").strip().upper() or "AAPL"
    price = float(input("💵 Precio actual (ej: 150): ").strip() or "150")
    
    try:
        position = risk_manager.calculate_position_size(
            symbol=symbol,
            current_price=price,
            stop_loss_price=price * 0.95  # 5% de stop loss
        )
        
        print("\n✅ CÁLCULO DE POSICIÓN")
        print("-"*70)
        print(f"Símbolo: {symbol}")
        print(f"Precio: ${price:.2f}")
        print(f"Cantidad calculada: {position.get('quantity', 0)} acciones")
        print(f"Capital a usar: ${position.get('capital_to_use', 0):,.2f}")
        print(f"% del capital: {position.get('position_pct', 0):.2f}%")
        print(f"Riesgo por operación: ${position.get('risk_amount', 0):,.2f}")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def ver_portafolio_produccion():
    """Ver portafolio de producción (solo lectura)"""
    print("="*70)
    print("💼 PORTAFOLIO DE PRODUCCIÓN (Solo Lectura)")
    print("="*70)
    print()
    
    try:
        portfolio = load_portfolio()
        
        if not portfolio:
            print("ℹ️  Portafolio vacío")
            return
        
        total_value = sum(p.get('total_val', 0) for p in portfolio)
        
        print(f"📊 Total activos: {len(portfolio)}")
        print(f"💰 Valor total: ${total_value:,.2f}")
        print()
        print("📋 Activos:")
        print("-"*70)
        
        for i, asset in enumerate(portfolio[:10], 1):  # Primeros 10
            symbol = asset.get('symbol', 'N/A')
            qty = asset.get('quantity', 0)
            price = asset.get('avg_price', 0)
            value = asset.get('total_val', 0)
            
            print(f"{i:2}. {symbol:8} | Qty: {qty:6.0f} | ${price:8.2f} | Total: ${value:10,.2f}")
        
        if len(portfolio) > 10:
            print(f"    ... y {len(portfolio) - 10} más")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_servicios_dashboard():
    """Prueba todos los servicios del dashboard"""
    print("="*70)
    print("🧪 TEST DE SERVICIOS DEL DASHBOARD")
    print("="*70)
    print()
    
    print(f"📊 Servicios disponibles: {len(services)}")
    print()
    
    for name, service in services.items():
        if service:
            print(f"  ✅ {name}: {service.__class__.__name__}")
        else:
            print(f"  ❌ {name}: No disponible")
    
    print()

# Menú principal
def menu():
    """Menú interactivo"""
    while True:
        try:
            opcion = input("Selecciona opción (1-9): ").strip()
            print()
            
            if opcion == '1':
                # Ejecutar ciclo único
                print("🔍 Ejecutando ciclo de análisis...")
                try:
                    resultados = test_bot.run_analysis_cycle()
                    print(f"✅ Ciclo completado: {len(resultados)} símbolos analizados")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
            elif opcion == '2':
                # Analizar símbolo específico
                symbol = input("📊 Símbolo: ").strip().upper()
                if symbol:
                    try:
                        resultado = test_bot.analyze_symbol(symbol)
                        print(f"✅ {symbol} analizado: {resultado.get('final_signal', 'N/A')}")
                    except Exception as e:
                        print(f"❌ Error: {e}")
                        
            elif opcion == '3':
                ver_portafolio_produccion()
                
            elif opcion == '4':
                test_servicios_dashboard()
                
            elif opcion == '5':
                test_prediccion_ia()
                
            elif opcion == '6':
                test_analisis_tecnico()
                
            elif opcion == '7':
                test_gestion_riesgo()
                
            elif opcion == '8':
                print("🔄 Iniciando modo continuo (5 min por ciclo)...")
                print("⚠️  Presiona Ctrl+C para detener")
                print()
                try:
                    test_bot.run_continuous(interval_minutes=5)
                except KeyboardInterrupt:
                    print("\n🛑 Modo continuo detenido")
                break
                
            elif opcion == '9':
                print("👋 Saliendo...")
                break
                
            else:
                print("❌ Opción inválida")
            
            print()
            print("-"*70)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# Ejecutar
if __name__ == "__main__":
    print("="*70)
    print("✅ SISTEMA DE TESTING LISTO")
    print("="*70)
    print()
    print("📦 Componentes cargados:")
    print(f"  ✅ TradingBot (de trading_bot.py)")
    print(f"  ✅ Servicios del Dashboard ({len(services)} servicios)")
    print(f"  ✅ Test Bot configurado (Paper Trading)")
    print()
    print("💡 El bot de PRODUCCIÓN sigue funcionando independientemente")
    print()
    
    try:
        menu()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print()
        print("="*70)
        print("🏁 TEST FINALIZADO")
        print("="*70)
        print()


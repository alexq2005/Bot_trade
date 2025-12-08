"""
Test Trading Bot - Versión de Prueba Independiente
Estado: 🧪 TESTING
Versión: 0.1

Descripción:
    Bot de trading de prueba que funciona de forma completamente
    independiente del bot de producción. Usa configuración de testing
    y modo paper trading obligatorio.

Propósito:
    Probar nuevas funcionalidades sin afectar el bot en producción.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import time

# Configurar paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

# Suprimir warnings
import warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("="*70)
print("🧪 TEST TRADING BOT - Versión de Prueba")
print("="*70)
print(f"📅 Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"📁 Directorio: {Path.cwd()}")
print("="*70)
print()

# Preguntar modo de operación
print("⚠️  SELECCIONA MODO DE OPERACIÓN:")
print()
print("1. 🧪 PAPER TRADING - Simulación (recomendado para testing)")
print("2. 💰 LIVE TRADING - Dinero REAL (para validación final)")
print()

modo_input = input("Selecciona modo (1 o 2): ").strip()
paper_trading_mode = modo_input != '2'

if paper_trading_mode:
    print()
    print("✅ MODO SELECCIONADO: PAPER TRADING (Simulación)")
    print("   💡 No se usará dinero real")
else:
    print()
    print("⚠️  MODO SELECCIONADO: LIVE TRADING")
    print("   ⚠️  ⚠️  ⚠️  SE USARÁ DINERO REAL ⚠️  ⚠️  ⚠️")
    print()
    confirmacion = input("¿CONFIRMAS que quieres usar DINERO REAL? (escribe 'SI'): ").strip().upper()
    if confirmacion != 'SI':
        print("❌ Operación cancelada - Cambiando a Paper Trading")
        paper_trading_mode = True
    else:
        print("✅ Confirmado - Modo LIVE activado")
        print("   💰 Se operará con dinero real")

print("="*70)
print()

# Cargar configuración de testing
print("1️⃣ Cargando configuración de testing...")
try:
    import json
    config_file = PROJECT_ROOT / "test_bot" / "configs" / "testing_config.json"
    
    if not config_file.exists():
        print(f"❌ No se encontró: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r', encoding='utf-8') as f:
        test_config = json.load(f)
    
    print(f"   ✅ Config cargada desde: testing_config.json")
    print(f"   📊 Environment: {test_config.get('environment', 'N/A')}")
    print(f"   🧪 Paper Trading: {test_config.get('paper_trading', True)}")
    print(f"   ⏱️  Intervalo: {test_config.get('analysis_interval_minutes', 5)} min")
    print()
except Exception as e:
    print(f"❌ Error cargando config: {e}")
    sys.exit(1)

# Cargar variables de entorno
print("2️⃣ Cargando variables de entorno...")
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    
    if env_path.exists():
        load_dotenv(env_path)
        print("   ✅ Variables de .env cargadas")
    else:
        print("   ⚠️  Archivo .env no encontrado")
    print()
except Exception as e:
    print(f"   ⚠️  Error: {e}")
    print()

# Importar TradingBot
print("3️⃣ Importando TradingBot...")
try:
    from trading_bot import TradingBot
    print("   ✅ TradingBot importado correctamente")
    print()
except ImportError as e:
    print(f"   ❌ Error importando TradingBot: {e}")
    sys.exit(1)

# Configurar símbolos de prueba
print("4️⃣ Configurando símbolos...")
if paper_trading_mode:
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']  # Solo 3 para testing rápido
    capital_inicial = 10000.0
    print(f"   📊 Símbolos de prueba: {', '.join(test_symbols)}")
    print(f"   💰 Capital inicial: $10,000 ARS (simulado)")
else:
    # En LIVE, usar símbolos del portafolio o permitir selección
    print("   📊 Opciones de símbolos:")
    print("   1. Usar portafolio completo (26 símbolos)")
    print("   2. Usar símbolos de prueba (AAPL, MSFT, GOOGL)")
    print("   3. Especificar símbolos manualmente")
    
    simbolos_opcion = input("   Selecciona (1-3): ").strip()
    
    if simbolos_opcion == '1':
        from src.services.portfolio_persistence import load_portfolio
        portfolio = load_portfolio()
        test_symbols = [p['symbol'] for p in portfolio] if portfolio else ['AAPL', 'MSFT']
        print(f"   ✅ Usando {len(test_symbols)} símbolos del portafolio")
    elif simbolos_opcion == '3':
        simbolos_input = input("   Ingresa símbolos (separados por coma): ").strip()
        test_symbols = [s.strip().upper() for s in simbolos_input.split(',') if s.strip()]
        print(f"   ✅ Usando {len(test_symbols)} símbolos personalizados")
    else:
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        print(f"   ✅ Usando símbolos de prueba: {', '.join(test_symbols)}")
    
    capital_inicial = None  # Se obtendrá de IOL
    print(f"   💰 Capital: Se obtendrá de IOL (saldo real)")

print()

# Crear instancia del bot de prueba
print("5️⃣ Creando instancia del Test Bot...")

# Advertencia final si es LIVE
if not paper_trading_mode:
    print()
    print("="*70)
    print("⚠️  ⚠️  ⚠️  ÚLTIMA ADVERTENCIA ⚠️  ⚠️  ⚠️")
    print("="*70)
    print("Estás a punto de iniciar el Test Bot en MODO LIVE")
    print("Esto significa que:")
    print("  • Se ejecutarán operaciones con DINERO REAL")
    print("  • Se usará tu cuenta de IOL")
    print("  • Las operaciones afectarán tu capital real")
    print()
    print("💡 Asegúrate de:")
    print("  • Haber probado TODO en Paper Trading primero")
    print("  • Entender completamente los cambios que hiciste")
    print("  • Tener límites de riesgo configurados correctamente")
    print("="*70)
    print()
    ultima_confirmacion = input("Escribe 'EJECUTAR LIVE' para continuar: ").strip()
    if ultima_confirmacion != 'EJECUTAR LIVE':
        print("❌ Cancelado - Saliendo por seguridad")
        sys.exit(0)
    print()

try:
    test_bot = TradingBot(
        symbols=test_symbols,
        initial_capital=capital_inicial,
        paper_trading=paper_trading_mode
    )
    modo_texto = "PAPER TRADING" if paper_trading_mode else "LIVE TRADING"
    print(f"   ✅ Test Bot inicializado en modo: {modo_texto}")
    
    if not paper_trading_mode:
        print(f"   💰 Capital real: ${test_bot.capital:,.2f}")
        print(f"   ⚠️  OPERANDO CON DINERO REAL")
    
    print()
except Exception as e:
    print(f"   ❌ Error creando bot: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Menú de opciones
print("="*70)
print("🎮 OPCIONES DE TESTING")
print("="*70)
print()
print("1. 🔍 Ejecutar un ciclo de análisis único")
print("2. 🔄 Ejecutar modo continuo (5 min por ciclo)")
print("3. 📊 Analizar un símbolo específico")
print("4. ⚙️  Ver configuración del test bot")
print("5. 🧪 Probar features nuevas (si están disponibles)")
print("6. ❌ Salir")
print()

def ejecutar_ciclo_unico():
    """Ejecuta un solo ciclo de análisis"""
    print("="*70)
    print("🔍 EJECUTANDO CICLO DE ANÁLISIS ÚNICO")
    print("="*70)
    print()
    
    try:
        resultados = test_bot.run_analysis_cycle()
        print()
        print("="*70)
        print("✅ CICLO COMPLETADO")
        print("="*70)
        print(f"📊 Símbolos analizados: {len(resultados)}")
        
        for resultado in resultados:
            if resultado:
                symbol = resultado.get('symbol', 'N/A')
                signal = resultado.get('final_signal', 'N/A')
                score = resultado.get('score', 0)
                print(f"  • {symbol}: {signal} (Score: {score})")
        
        print()
    except Exception as e:
        print(f"❌ Error en ciclo: {e}")
        import traceback
        traceback.print_exc()

def ejecutar_modo_continuo():
    """Ejecuta el bot en modo continuo (testing)"""
    print("="*70)
    print("🔄 MODO CONTINUO DE TESTING")
    print("="*70)
    print("⏱️  Intervalo: 5 minutos")
    print("⚠️  Presiona Ctrl+C para detener")
    print("="*70)
    print()
    
    try:
        # Usar intervalo corto de testing (5 min)
        test_bot.run_continuous(interval_minutes=5)
    except KeyboardInterrupt:
        print("\n\n🛑 Test Bot detenido por usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def analizar_simbolo_especifico():
    """Analiza un símbolo específico"""
    print()
    symbol = input("📊 Ingresa el símbolo a analizar (ej: AAPL): ").strip().upper()
    
    if not symbol:
        print("❌ Símbolo vacío")
        return
    
    print()
    print("="*70)
    print(f"📊 ANALIZANDO {symbol}")
    print("="*70)
    print()
    
    try:
        resultado = test_bot.analyze_symbol(symbol)
        
        if resultado:
            print()
            print("✅ ANÁLISIS COMPLETADO")
            print("-"*70)
            print(f"Símbolo: {resultado.get('symbol', 'N/A')}")
            print(f"Señal Final: {resultado.get('final_signal', 'N/A')}")
            print(f"Score: {resultado.get('score', 0)}")
            print(f"Confianza: {resultado.get('confidence', 'N/A')}")
            print(f"Precio Actual: ${resultado.get('current_price', 0):.2f}")
            
            if resultado.get('buy_factors'):
                print("\n✅ Factores de Compra:")
                for factor in resultado['buy_factors']:
                    print(f"  • {factor}")
            
            if resultado.get('sell_factors'):
                print("\n❌ Factores de Venta:")
                for factor in resultado['sell_factors']:
                    print(f"  • {factor}")
            print()
    except Exception as e:
        print(f"❌ Error analizando {symbol}: {e}")
        import traceback
        traceback.print_exc()

def ver_configuracion():
    """Muestra la configuración del test bot"""
    print("="*70)
    print("⚙️  CONFIGURACIÓN DEL TEST BOT")
    print("="*70)
    print()
    print(f"Modo: {'PAPER TRADING' if test_bot.paper_trading else 'LIVE'}")
    print(f"Capital: ${test_bot.capital:,.2f}")
    print(f"Símbolos: {', '.join(test_bot.symbols)}")
    print()
    print("Configuración de testing:")
    for key, value in test_config.items():
        if key != 'feature_configs':
            print(f"  • {key}: {value}")
    print()

def probar_features_nuevas():
    """Prueba features nuevas si están disponibles"""
    print("="*70)
    print("🧪 PROBANDO FEATURES NUEVAS")
    print("="*70)
    print()
    
    features_config = test_config.get('features', {})
    
    print("📋 Features configuradas:")
    for feature_name, enabled in features_config.items():
        status = "✅ ACTIVA" if enabled else "⏸️ Inactiva"
        print(f"  • {feature_name}: {status}")
    
    print()
    
    # Verificar si hay features activas
    features_activas = [f for f, enabled in features_config.items() if enabled]
    
    if not features_activas:
        print("ℹ️  No hay features activas para probar")
        print("💡 Activa features en test_bot/configs/testing_config.json")
    else:
        print(f"🚀 Features activas: {', '.join(features_activas)}")
        # Aquí se ejecutarían las features cuando estén implementadas
    
    print()

# Menú interactivo
def menu():
    """Menú principal del test bot"""
    while True:
        try:
            opcion = input("Selecciona opción (1-6): ").strip()
            print()
            
            if opcion == '1':
                ejecutar_ciclo_unico()
            elif opcion == '2':
                ejecutar_modo_continuo()
                break  # Salir después del modo continuo
            elif opcion == '3':
                analizar_simbolo_especifico()
            elif opcion == '4':
                ver_configuracion()
            elif opcion == '5':
                probar_features_nuevas()
            elif opcion == '6':
                print("👋 Saliendo del Test Bot...")
                break
            else:
                print("❌ Opción inválida. Elige 1-6")
            
            print()
            print("-"*70)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Test Bot interrumpido")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

# Ejecutar menú
if __name__ == "__main__":
    try:
        menu()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print()
        print("="*70)
        print("🏁 Test Bot Finalizado")
        print("="*70)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("💡 El bot de producción sigue funcionando normalmente")
        print()


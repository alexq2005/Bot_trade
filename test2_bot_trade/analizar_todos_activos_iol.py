"""
Script para analizar TODOS los activos disponibles en IOL
"""
import sys
import json
from pathlib import Path
from trading_bot import TradingBot
from src.connectors.iol_client import IOLClient
from src.services.iol_universe_loader import IOLUniverseLoader

def configurar_universo_completo():
    """Configura el bot para analizar todos los activos de IOL"""
    print("="*70)
    print("🌍 CONFIGURANDO ANÁLISIS DE TODOS LOS ACTIVOS DE IOL")
    print("="*70)
    
    # Cargar o crear configuración
    config_file = Path("professional_config.json")
    config = {}
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {}
    
    # Configurar modo universo completo
    if 'monitoring' not in config:
        config['monitoring'] = {}
    
    config['monitoring']['use_full_universe'] = True
    config['monitoring']['max_symbols'] = 500  # Máximo de símbolos a analizar
    config['monitoring']['universe_categories'] = [
        'acciones',    # Acciones argentinas
        'cedears',     # CEDEARs (acciones USA)
        'bonos',       # Bonos
        'obligaciones' # Obligaciones negociables
    ]
    
    # Guardar configuración
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("✅ Configuración actualizada:")
    print(f"   • Modo: Universo Completo")
    print(f"   • Máximo de símbolos: {config['monitoring']['max_symbols']}")
    print(f"   • Categorías: {', '.join(config['monitoring']['universe_categories'])}")
    print()

def verificar_activos_disponibles():
    """Verifica cuántos activos están disponibles en IOL"""
    print("="*70)
    print("🔍 VERIFICANDO ACTIVOS DISPONIBLES EN IOL")
    print("="*70)
    
    try:
        iol = IOLClient()
        loader = IOLUniverseLoader(iol)
        
        # Obtener todos los instrumentos
        categories = ['acciones', 'cedears', 'bonos', 'obligaciones']
        all_instruments = loader.get_all_instruments(categories=categories)
        
        total = sum(len(symbols) for symbols in all_instruments.values())
        
        print(f"\n📊 RESUMEN DE ACTIVOS DISPONIBLES:")
        print(f"   • Acciones: {len(all_instruments.get('acciones', []))}")
        print(f"   • CEDEARs: {len(all_instruments.get('cedears', []))}")
        print(f"   • Bonos: {len(all_instruments.get('bonos', []))}")
        print(f"   • Obligaciones: {len(all_instruments.get('obligaciones', []))}")
        print(f"\n   📈 TOTAL: {total} instrumentos disponibles")
        print()
        
        return total
        
    except Exception as e:
        print(f"❌ Error verificando activos: {e}")
        return 0

def ejecutar_analisis_completo():
    """Ejecuta el análisis de todos los activos"""
    print("="*70)
    print("🚀 INICIANDO ANÁLISIS COMPLETO DE ACTIVOS IOL")
    print("="*70)
    print("\n⚠️  ADVERTENCIA: Este análisis puede tomar mucho tiempo")
    print("⚠️  Se analizarán cientos de activos")
    print("⚠️  El bot operará en modo LIVE TRADING\n")
    
    # Confirmación
    respuesta = input("¿Continuar con el análisis completo? (escribe 'SI' para confirmar): ")
    if respuesta.upper() != 'SI':
        print("❌ Análisis cancelado")
        return
    
    try:
        # Crear bot en modo LIVE con universo completo
        # Los símbolos se cargarán automáticamente desde la configuración
        print("\n🤖 Inicializando bot con universo completo...")
        bot = TradingBot(
            symbols=None,  # None para que use la configuración
            initial_capital=None,  # Se obtiene de IOL
            paper_trading=False  # MODO LIVE
        )
        
        print(f"\n✅ Bot inicializado")
        print(f"   • Símbolos a analizar: {len(bot.symbols)}")
        print(f"   • Capital: ${bot.capital:,.2f} ARS")
        print(f"   • Modo: LIVE TRADING")
        
        # Ejecutar análisis
        print("\n" + "="*70)
        print("🔄 EJECUTANDO ANÁLISIS COMPLETO")
        print("="*70)
        print("\n⏳ Esto puede tomar varios minutos...\n")
        
        resultados = bot.run_analysis_cycle()
        
        # Resumen de resultados
        print("\n" + "="*70)
        print("📊 RESUMEN DEL ANÁLISIS")
        print("="*70)
        
        if resultados:
            # Contar señales
            buy_signals = [r for r in resultados if r.get('final_signal') == 'BUY']
            sell_signals = [r for r in resultados if r.get('final_signal') == 'SELL']
            hold_signals = [r for r in resultados if r.get('final_signal') == 'HOLD']
            
            print(f"\n📈 Total analizado: {len(resultados)} activos")
            print(f"   🟢 Señales BUY: {len(buy_signals)}")
            print(f"   🔴 Señales SELL: {len(sell_signals)}")
            print(f"   ⏸️  Señales HOLD: {len(hold_signals)}")
            
            if buy_signals:
                print(f"\n🎯 Oportunidades de COMPRA detectadas:")
                for signal in buy_signals[:10]:  # Mostrar primeros 10
                    symbol = signal.get('symbol', 'N/A')
                    score = signal.get('score', 0)
                    price = signal.get('current_price', 0)
                    print(f"   • {symbol}: Score {score:.2f} | Precio: ${price:,.2f}")
                if len(buy_signals) > 10:
                    print(f"   ... y {len(buy_signals) - 10} más")
            
            if sell_signals:
                print(f"\n🔴 Señales de VENTA detectadas:")
                for signal in sell_signals[:10]:
                    symbol = signal.get('symbol', 'N/A')
                    score = signal.get('score', 0)
                    print(f"   • {symbol}: Score {score:.2f}")
        else:
            print("\n⚠️  No se generaron resultados")
        
        print("\n" + "="*70)
        print("✅ ANÁLISIS COMPLETADO")
        print("="*70)
        print("\n💡 Revisa los logs y trades.json para ver detalles")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌍 ANÁLISIS COMPLETO DE ACTIVOS IOL")
    print("="*70)
    print("\nEste script analizará TODOS los activos disponibles en IOL")
    print("y ejecutará operaciones reales si encuentra señales BUY")
    print("\n⚠️  ADVERTENCIA: Se usará DINERO REAL")
    print("="*70 + "\n")
    
    # Paso 1: Configurar universo completo
    configurar_universo_completo()
    
    # Paso 2: Verificar activos disponibles
    total_activos = verificar_activos_disponibles()
    
    if total_activos == 0:
        print("⚠️  No se pudieron cargar activos. Abortando...")
        sys.exit(1)
    
    # Paso 3: Ejecutar análisis
    ejecutar_analisis_completo()


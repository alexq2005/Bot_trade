"""
Script para cargar datos históricos de los símbolos del universo completo
"""
import json
from pathlib import Path
from scripts.ingest_data import ingest_symbol

def cargar_datos_historicos():
    """Carga datos históricos para todos los símbolos configurados"""
    
    print("="*70)
    print("📥 CARGANDO DATOS HISTÓRICOS")
    print("="*70)
    print()
    
    # Cargar configuración
    config_file = Path("professional_config.json")
    if not config_file.exists():
        print("❌ No se encontró professional_config.json")
        return
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    monitoring = config.get('monitoring', {})
    use_full_universe = monitoring.get('use_full_universe', False)
    max_symbols = monitoring.get('max_symbols', 200)
    categories = monitoring.get('universe_categories', ['acciones', 'cedears', 'bonos'])
    
    print(f"📋 Configuración:")
    print(f"   • Universo completo: {'✅' if use_full_universe else '❌'}")
    print(f"   • Máximo símbolos: {max_symbols}")
    print(f"   • Categorías: {', '.join(categories)}")
    print()
    
    # Obtener símbolos
    symbols = []
    
    if use_full_universe:
        print("🌍 Cargando símbolos del universo completo...")
        try:
            from src.connectors.iol_client import IOLClient
            from src.services.iol_universe_loader import IOLUniverseLoader
            
            iol = IOLClient()
            loader = IOLUniverseLoader(iol)
            
            # Intentar cargar universo completo
            try:
                universe_symbols = loader.get_tradeable_universe(max_symbols=max_symbols)
                if universe_symbols:
                    symbols = universe_symbols
                    print(f"✅ Cargados {len(symbols)} símbolos del universo")
            except Exception as e:
                print(f"⚠️  Error con get_tradeable_universe: {e}")
                # Fallback: cargar por categorías
                all_instruments = loader.get_all_instruments(categories=categories)
                for cat_symbols in all_instruments.values():
                    symbols.extend(cat_symbols)
                symbols = list(set(symbols))[:max_symbols]
                print(f"✅ Cargados {len(symbols)} símbolos por categorías")
        except Exception as e:
            print(f"❌ Error cargando universo: {e}")
            print("   Usando símbolos conocidos como fallback...")
            # Fallback con símbolos conocidos
            if 'acciones' in categories:
                symbols.extend(['GGAL', 'YPFD', 'PAMP', 'BMA', 'ALUA', 'LOMA'])
            if 'cedears' in categories:
                symbols.extend(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'])
            if 'bonos' in categories:
                symbols.extend(['GD30', 'GD35', 'AL30', 'AL35'])
    else:
        print("💼 Cargando símbolos del portafolio...")
        try:
            from src.services.portfolio_persistence import load_portfolio
            portfolio = load_portfolio()
            if portfolio:
                symbols = [p.get('symbol', '').strip() for p in portfolio if p.get('symbol')]
                print(f"✅ Cargados {len(symbols)} símbolos del portafolio")
            else:
                print("⚠️  Portafolio vacío")
        except Exception as e:
            print(f"❌ Error cargando portafolio: {e}")
    
    if not symbols:
        print("❌ No se pudieron cargar símbolos")
        return
    
    print()
    print(f"📊 Total de símbolos a procesar: {len(symbols)}")
    print(f"📋 Primeros 10: {', '.join(symbols[:10])}")
    print()
    print("="*70)
    print("🚀 INICIANDO CARGA DE DATOS HISTÓRICOS")
    print("="*70)
    print()
    
    # Cargar datos históricos (1 año) para cada símbolo
    exitosos = 0
    fallidos = 0
    
    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Procesando {symbol}...")
        try:
            ingest_symbol(symbol, period="1y")
            exitosos += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            fallidos += 1
    
    print()
    print("="*70)
    print("✅ CARGA COMPLETADA")
    print("="*70)
    print(f"   • Exitosos: {exitosos}")
    print(f"   • Fallidos: {fallidos}")
    print(f"   • Total: {len(symbols)}")
    print()
    print("💡 Ahora puedes reiniciar el bot desde el dashboard")
    print("="*70)

if __name__ == "__main__":
    cargar_datos_historicos()


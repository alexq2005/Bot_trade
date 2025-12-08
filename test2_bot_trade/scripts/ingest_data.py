"""
Script to ingest historical market data from Yahoo Finance into the database.
"""
import sys
import os
import argparse
from datetime import datetime, timedelta
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connectors.yahoo_client import YahooFinanceClient
from src.connectors.byma_client import BYMAClient
from src.connectors.multi_source_client import MultiSourceDataClient
from src.core.database import SessionLocal, init_db
from src.models.market_data import MarketData

def ingest_symbol(symbol: str, period: str = "1y", days: int = None, use_multi_source: bool = True):
    """
    Ingest historical data for a given symbol.
    
    Args:
        symbol: Símbolo a descargar
        period: Período en formato Yahoo Finance ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
        days: Número de días de historia (sobrescribe period si se especifica)
        use_multi_source: Si True, intenta múltiples fuentes (Yahoo, BYMA, etc.)
    """
    print(f"📥 Descargando datos para {symbol}...")
    
    # Initialize database
    init_db()
    
    # Convertir days a period si se especifica
    if days is not None:
        if days >= 3650:
            period = "10y"
        elif days >= 1825:
            period = "5y"
        elif days >= 730:
            period = "2y"
        elif days >= 365:
            period = "1y"
        elif days >= 180:
            period = "6mo"
        elif days >= 90:
            period = "3mo"
        elif days >= 30:
            period = "1mo"
        elif days >= 5:
            period = "5d"
        else:
            period = "1d"
        print(f"   Período calculado: {period} ({days} días)")
    
    history = None
    
    # Intentar múltiples fuentes si está habilitado
    if use_multi_source:
        try:
            multi_client = MultiSourceDataClient()
            result = multi_client.get_history(symbol, period=period, interval="1d")
            history = result.get('data', None)
            source = result.get('source', 'Unknown')
            if history is not None and not history.empty:
                print(f"   ✅ Datos obtenidos desde {source}")
        except Exception as e:
            print(f"   ⚠️  Error con multi-source: {e}")
    
    # Fallback a Yahoo Finance
    if history is None or history.empty:
        try:
            client = YahooFinanceClient()
            history = client.get_history(symbol, period=period)
            if not history.empty:
                print(f"   ✅ Datos obtenidos desde Yahoo Finance")
        except Exception as e:
            print(f"   ⚠️  Error con Yahoo Finance: {e}")
    
    # Fallback a BYMA para símbolos argentinos
    if (history is None or history.empty) and ('.BA' in symbol or symbol in ['GGAL', 'YPFD', 'PAMP', 'LOMA', 'CEPU', 'EDN', 'NU']):
        try:
            byma_client = BYMAClient()
            history = byma_client.get_history(symbol, period=period, interval="1d")
            if not history.empty:
                print(f"   ✅ Datos obtenidos desde BYMA/Yahoo")
        except Exception as e:
            print(f"   ⚠️  Error con BYMA: {e}")
    
    if history is None or history.empty:
        print(f"⚠️  No data found for {symbol} from any source")
        return
    
    print(f"   📊 Datos obtenidos: {len(history)} registros")
    
    # Store in database
    db = SessionLocal()
    try:
        count = 0
        updated = 0
        for index, row in history.iterrows():
            # Check if record already exists
            existing = db.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.timestamp == index
            ).first()
            
            if existing:
                # Update existing record solo si hay cambios significativos
                needs_update = (
                    abs(existing.close - row['Close']) > 0.01 or
                    abs(existing.volume - row['Volume']) > 0.01
                )
                if needs_update:
                    existing.open = row['Open']
                    existing.high = row['High']
                    existing.low = row['Low']
                    existing.close = row['Close']
                    existing.volume = row['Volume']
                    updated += 1
            else:
                # Create new record
                market_data = MarketData(
                    symbol=symbol,
                    timestamp=index,
                    open=row['Open'],
                    high=row['High'],
                    low=row['Low'],
                    close=row['Close'],
                    volume=row['Volume'],
                    source='yahoo'
                )
                db.add(market_data)
                count += 1
        
        db.commit()
        if count > 0:
            print(f"✓ Ingested {count} new records for {symbol}")
        if updated > 0:
            print(f"✓ Updated {updated} existing records for {symbol}")
        if count == 0 and updated == 0:
            print(f"ℹ️  No new or updated records for {symbol} (todos los datos ya existen)")
        
        # Show summary
        total = db.query(MarketData).filter(MarketData.symbol == symbol).count()
        print(f"  Total records in DB for {symbol}: {total}")
        
        # Si hay muy pocos registros y se solicitó 1 año, advertir
        if total < 30 and period in ['1y', '2y', '5y']:
            print(f"  ⚠️  Solo {total} registros disponibles. Puede haber un problema con la fuente de datos.")
        
    except Exception as e:
        print(f"Error ingesting {symbol}: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """
    Main ingestion script.
    Descarga datos de símbolos del portafolio IOL o lista personalizada.
    Soporta activos de cualquier mercado global.
    """
    parser = argparse.ArgumentParser(description='Descargar datos históricos de mercado')
    parser.add_argument('--symbols', type=str, help='Lista de símbolos separados por coma (ej: AAPL,TSLA,GGAL)')
    parser.add_argument('--period', type=str, default='1y', 
                       choices=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'],
                       help='Período de datos (default: 1y)')
    parser.add_argument('--days', type=int, help='Número de días de historia (sobrescribe --period)')
    parser.add_argument('--single-source', action='store_true', 
                       help='Usar solo Yahoo Finance (no intentar múltiples fuentes)')
    
    args = parser.parse_args()
    
    # Try to get symbols from IOL portfolio first
    symbols = []
    
    # 1. Try Local Portfolio (my_portfolio.json)
    try:
        import json
        import os
        if os.path.exists('my_portfolio.json'):
            with open('my_portfolio.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                portfolio = data.get('portfolio', [])
                local_symbols = [p['symbol'] for p in portfolio if 'symbol' in p]
                if local_symbols:
                    symbols = local_symbols
                    print(f"Usando {len(symbols)} simbolos de tu portafolio LOCAL (my_portfolio.json):")
                    for sym in symbols:
                        print(f"   * {sym}")
    except Exception as e:
        print(f"Error leyendo portafolio local: {e}")

    # 2. If no local portfolio, try IOL API
    if not symbols:
        try:
            from src.connectors.iol_client import IOLClient
            client = IOLClient()
            portfolio = client.get_portfolio()
            
            if portfolio and 'activos' in portfolio:
                # Extract symbols from portfolio
                portfolio_symbols = [asset['titulo']['simbolo'] for asset in portfolio['activos']]
                if portfolio_symbols:
                    symbols = portfolio_symbols
                    print(f"Usando {len(symbols)} simbolos de tu portafolio IOL:")
                    for sym in symbols:
                        print(f"   * {sym}")
        except Exception as e:
            print(f"No se pudo obtener portafolio de IOL: {e}")
    
    # If no portfolio symbols, check command line arguments
    if not symbols and args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
        print(f"Usando simbolos personalizados: {', '.join(symbols)}")
    
    # If still no symbols, use diverse global defaults
    if not symbols:
        symbols = [
            # Argentina
            "GGAL.BA", "YPFD.BA", "PAMP.BA",
            # USA
            "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA",
            # ETFs Globales
            "SPY",   # S&P 500
            "QQQ",   # Nasdaq
            "EEM",   # Emerging Markets
            "VTI",   # Total US Market
        ]
        print(f"Usando simbolos por defecto (mercados globales):")
        for sym in symbols:
            print(f"   * {sym}")
    
    # Determinar período
    period = args.period
    days = args.days
    use_multi_source = not args.single_source
    
    if days:
        period_str = f"{days} días"
    else:
        period_str = period
    
    print(f"\n{'='*60}")
    print(f"📊 INICIANDO DESCARGA DE DATOS")
    print(f"{'='*60}")
    print(f"📅 Período: {period_str}")
    print(f"📈 Símbolos: {len(symbols)}")
    print(f"🌐 Fuentes múltiples: {'Sí' if use_multi_source else 'No (solo Yahoo)'}")
    print(f"{'='*60}\n")
    
    success_count = 0
    failed_symbols = []
    
    for symbol in symbols:
        try:
            ingest_symbol(symbol, period=period, days=days, use_multi_source=use_multi_source)
            success_count += 1
            print()  # Línea en blanco entre símbolos
        except Exception as e:
            print(f"❌ Error con {symbol}: {e}\n")
            failed_symbols.append(symbol)
    
    print(f"\n{'='*60}")
    print(f"✅ DESCARGA COMPLETA")
    print(f"{'='*60}")
    print(f"✅ Exitosos: {success_count}/{len(symbols)}")
    if failed_symbols:
        print(f"❌ Fallidos: {len(failed_symbols)}")
        print(f"   Símbolos: {', '.join(failed_symbols)}")
    print(f"{'='*60}\n")
    
    return success_count > 0

if __name__ == "__main__":
    main()

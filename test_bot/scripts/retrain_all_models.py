"""
Script to retrain all models using the new multivariate architecture.
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.continuous_learning import ContinuousLearning
from src.core.database import SessionLocal
from src.models.market_data import MarketData

def main():
    print("🚀 Starting Bulk Retraining for Multivariate LSTM Upgrade...")
    
    # 1. Try to load symbols from local portfolio first
    symbols = []
    try:
        from src.services.portfolio_persistence import load_portfolio
        portfolio = load_portfolio()
        if portfolio:
            portfolio_symbols = [p.get('symbol') for p in portfolio if p.get('symbol')]
            if portfolio_symbols:
                symbols = portfolio_symbols
                print(f"📂 Cargados {len(symbols)} símbolos del portafolio local:")
                for sym in symbols[:10]:  # Mostrar primeros 10
                    print(f"   * {sym}")
                if len(symbols) > 10:
                    print(f"   ... y {len(symbols) - 10} más")
    except Exception as e:
        print(f"⚠️  No se pudo cargar portafolio local: {e}")
    
    # 2. If no portfolio symbols, get from database
    if not symbols:
        db = SessionLocal()
        try:
            symbols = [s[0] for s in db.query(MarketData.symbol).distinct().all()]
            print(f"📊 Cargados {len(symbols)} símbolos de la base de datos: {', '.join(symbols[:10])}")
            if len(symbols) > 10:
                print(f"   ... y {len(symbols) - 10} más")
        finally:
            db.close()
    
    if not symbols:
        print("❌ No se encontraron símbolos para entrenar. Asegúrate de tener:")
        print("   1. Un archivo my_portfolio.json con tu portafolio, o")
        print("   2. Datos en la base de datos (ejecuta scripts/ingest_data.py primero)")
        return
    
    cl = ContinuousLearning()
    
    # 2. Force retrain for each symbol
    for symbol in symbols:
        print(f"\n🔄 Processing {symbol}...")
        try:
            # We can use retrain_model directly
            result = cl.retrain_model(symbol, epochs=30)
            if result.get('success'):
                print(f"✅ Success! Loss: {result['training_loss']:.4f}")
            else:
                print(f"❌ Failed: {result.get('error')}")
        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")

    print("\n✨ All models updated to new architecture!")

if __name__ == "__main__":
    main()


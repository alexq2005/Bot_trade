"""
Script para recolectar datos históricos de símbolos que fallaron en el entrenamiento.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.console_utils import setup_windows_console, safe_print
from src.connectors.yahoo_client import YahooFinanceClient
from src.connectors.byma_client import BYMAClient
from src.connectors.multi_source_client import MultiSourceDataClient
from src.core.database import SessionLocal, init_db
from src.models.market_data import MarketData

setup_windows_console()

def main():
    """
    Recolecta datos para los símbolos que fallaron en el entrenamiento.
    """
    # Símbolos sin datos históricos identificados en el análisis
    missing_symbols = [
        'BA37D', 'BPOC7', 'BYMA', 'COME', 'ECOG', 'GD35', 'METR', 
        'PAMP', 'T15D5', 'TGNO4', 'TGSU2', 'TRAN', 'TTM26', 'TX26', 'YPFD'
    ]
    
    safe_print("=" * 70)
    safe_print("📊 RECOLECCIÓN DE DATOS FALTANTES")
    safe_print("=" * 70)
    safe_print(f"\n📋 Símbolos a procesar: {len(missing_symbols)}")
    safe_print(f"   {', '.join(missing_symbols)}\n")
    
    # Configurar período (por defecto 2 años para tener más datos)
    period = "2y"  # 2 años de datos históricos
    days = None   # O usar days=730 para 2 años
    
    safe_print(f"📅 Período configurado: {period} (2 años)")
    safe_print(f"🌐 Usando múltiples fuentes: Sí\n")
    safe_print("=" * 70 + "\n")
    
    # Importar función de ingest_data
    from scripts.ingest_data import ingest_symbol
    
    success_count = 0
    failed_symbols = []
    
    for symbol in missing_symbols:
        try:
            safe_print(f"\n{'─'*70}")
            ingest_symbol(symbol, period=period, days=days, use_multi_source=True)
            success_count += 1
        except Exception as e:
            safe_print(f"❌ Error con {symbol}: {e}")
            failed_symbols.append(symbol)
    
    safe_print(f"\n{'='*70}")
    safe_print("✅ RECOLECCIÓN COMPLETA")
    safe_print(f"{'='*70}")
    safe_print(f"✅ Exitosos: {success_count}/{len(missing_symbols)}")
    if failed_symbols:
        safe_print(f"❌ Fallidos: {len(failed_symbols)}")
        safe_print(f"   Símbolos: {', '.join(failed_symbols)}")
        safe_print(f"\n💡 Estos símbolos pueden no estar disponibles en las fuentes consultadas")
        safe_print(f"   o pueden requerir un formato diferente (ej: PAMP.BA, YPFD.BA)")
    safe_print(f"{'='*70}\n")
    
    return success_count > 0

if __name__ == "__main__":
    main()


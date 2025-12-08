"""
Test script for technical analysis.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.technical_analysis import TechnicalAnalysisService

def main():
    service = TechnicalAnalysisService()
    
    symbols = ['AAPL', 'GGAL.BA']
    
    print("=== Technical Analysis ===\n")
    for symbol in symbols:
        try:
            analysis = service.get_full_analysis(symbol)
            print(f"{symbol}:")
            print(f"  Price: ${analysis['trend']['current_price']:.2f}")
            print(f"  RSI: {analysis['momentum']['rsi']:.2f}" if analysis['momentum']['rsi'] else "  RSI: N/A")
            print(f"  ATR: {analysis['volatility']['atr']:.2f}" if analysis['volatility']['atr'] else "  ATR: N/A")
            print(f"  Signal: {analysis['signal']}")
            print()
        except Exception as e:
            print(f"{symbol}: Error - {e}\n")

if __name__ == "__main__":
    main()

"""
Test script for prediction service.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.prediction_service import PredictionService

def main():
    service = PredictionService()
    
    symbols = ['AAPL']
    
    print("=== Trading Signals ===\n")
    for symbol in symbols:
        try:
            signal = service.generate_signal(symbol, threshold=2.0)
            print(f"{symbol}:")
            print(f"  Current: ${signal['current_price']:.2f}")
            print(f"  Predicted: ${signal['predicted_price']:.2f}")
            print(f"  Change: {signal['change_pct']:.2f}%")
            print(f"  Signal: {signal['signal']} (Confidence: {signal['confidence']:.2f})")
            print()
        except Exception as e:
            print(f"{symbol}: Error - {e}\n")

if __name__ == "__main__":
    main()

"""
Verify all trained models and generate predictions report.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.prediction_service import PredictionService

def main():
    service = PredictionService()
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'SPY', 'GGAL.BA']
    
    print("="*70)
    print("🤖 AI PREDICTIONS REPORT - ALL MODELS")
    print("="*70)
    print()
    
    results = []
    
    for symbol in symbols:
        try:
            prediction = service.generate_signal(symbol, threshold=2.0)
            results.append(prediction)
            
            print(f"📊 {symbol}")
            print(f"   Current Price:    ${prediction['current_price']:.2f}")
            print(f"   Predicted Price:  ${prediction['predicted_price']:.2f}")
            print(f"   Expected Change:  {prediction['change_pct']:+.2f}%")
            print(f"   Signal:           {prediction['signal']}")
            print(f"   Confidence:       {prediction['confidence']:.2f}x")
            print()
            
        except Exception as e:
            print(f"❌ {symbol}: Error - {e}")
            print()
    
    # Summary
    print("="*70)
    print("📈 SUMMARY")
    print("="*70)
    
    buy_signals = [r for r in results if r['signal'] == 'BUY']
    sell_signals = [r for r in results if r['signal'] == 'SELL']
    hold_signals = [r for r in results if r['signal'] == 'HOLD']
    
    print(f"Total Models: {len(results)}")
    print(f"🟢 BUY Signals:  {len(buy_signals)}")
    print(f"🔴 SELL Signals: {len(sell_signals)}")
    print(f"🟡 HOLD Signals: {len(hold_signals)}")
    print()
    
    if buy_signals:
        print("🟢 BUY Opportunities:")
        for signal in buy_signals:
            print(f"   {signal['symbol']}: {signal['change_pct']:+.2f}% (Confidence: {signal['confidence']:.2f}x)")
    
    if sell_signals:
        print("\n🔴 SELL Recommendations:")
        for signal in sell_signals:
            print(f"   {signal['symbol']}: {signal['change_pct']:+.2f}% (Confidence: {signal['confidence']:.2f}x)")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()

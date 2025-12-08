"""
Test backtesting engine.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.backtester import Backtester

def main():
    backtester = Backtester(initial_capital=10000)
    
    print("=== Backtesting Simple MA Strategy ===\n")
    print("Symbol: AAPL")
    print("Strategy: MA Crossover (20/50)")
    print("Initial Capital: $10,000\n")
    
    results = backtester.run_simple_ma_strategy('AAPL', short_window=20, long_window=50)
    
    if 'error' not in results:
        print(f"Final Portfolio Value: ${results['final_value']:.2f}")
        print(f"Total Return: {results['total_return']:.2f}%")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Win Rate: {results['win_rate']:.2f}%")
    else:
        print(f"Error: {results['error']}")

if __name__ == "__main__":
    main()

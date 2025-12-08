"""
Test script for portfolio optimization.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.portfolio_optimizer import PortfolioOptimizer

def main():
    optimizer = PortfolioOptimizer()
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'SPY']
    
    print("=== Portfolio Optimization ===\n")
    
    # Get returns data
    returns_df = optimizer.get_returns_data(symbols, days=252)
    print(f"Analyzing {len(returns_df.columns)} assets with {len(returns_df)} days of data\n")
    
    # Max Sharpe Ratio
    print("1. Maximum Sharpe Ratio Portfolio (Markowitz):")
    sharpe_result = optimizer.optimize_sharpe_ratio(returns_df)
    if sharpe_result['success']:
        print(f"   Expected Return: {sharpe_result['metrics']['return']*100:.2f}%")
        print(f"   Volatility: {sharpe_result['metrics']['volatility']*100:.2f}%")
        print(f"   Sharpe Ratio: {sharpe_result['metrics']['sharpe_ratio']:.2f}")
        print("   Weights:")
        for symbol, weight in sharpe_result['weights'].items():
            print(f"     {symbol}: {weight*100:.2f}%")
    print()
    
    # Min Variance
    print("2. Minimum Variance Portfolio:")
    minvar_result = optimizer.optimize_min_variance(returns_df)
    if minvar_result['success']:
        print(f"   Expected Return: {minvar_result['metrics']['return']*100:.2f}%")
        print(f"   Volatility: {minvar_result['metrics']['volatility']*100:.2f}%")
        print(f"   Sharpe Ratio: {minvar_result['metrics']['sharpe_ratio']:.2f}")
        print("   Weights:")
        for symbol, weight in minvar_result['weights'].items():
            print(f"     {symbol}: {weight*100:.2f}%")
    print()
    
    # Risk Parity
    print("3. Risk Parity Portfolio:")
    rp_result = optimizer.risk_parity_weights(returns_df)
    if rp_result['success']:
        print(f"   Expected Return: {rp_result['metrics']['return']*100:.2f}%")
        print(f"   Volatility: {rp_result['metrics']['volatility']*100:.2f}%")
        print(f"   Sharpe Ratio: {rp_result['metrics']['sharpe_ratio']:.2f}")
        print("   Weights:")
        for symbol, weight in rp_result['weights'].items():
            print(f"     {symbol}: {weight*100:.2f}%")

if __name__ == "__main__":
    main()

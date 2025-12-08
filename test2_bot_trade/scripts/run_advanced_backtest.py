"""
Script para ejecutar backtesting avanzado
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from datetime import datetime, timedelta
from src.services.advanced_backtester import (
    AdvancedBacktester,
    create_ma_crossover_strategy,
    create_rsi_strategy,
    create_macd_strategy
)
from src.core.logger import get_logger

logger = get_logger("backtest_script")

def main():
    print("📊 Sistema Avanzado de Backtesting")
    print("="*70)
    
    # Configuración
    symbol = input("Símbolo a probar (ej: AAPL): ").strip() or "AAPL"
    days = int(input("Días de datos históricos (default 252): ").strip() or "252")
    
    # Calcular fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Crear backtester
    backtester = AdvancedBacktester(initial_capital=10000.0, commission=0.001)
    
    # Crear estrategias
    strategies = [
        create_ma_crossover_strategy(20, 50),
        create_rsi_strategy(30, 70),
        create_macd_strategy(),
    ]
    
    print(f"\n🔄 Ejecutando backtesting para {symbol}...")
    print(f"   Período: {start_date.date()} a {end_date.date()}")
    print(f"   Estrategias: {len(strategies)}\n")
    
    # Comparar estrategias
    comparison = backtester.compare_strategies(symbol, strategies, start_date, end_date)
    
    # Mostrar resultados
    print("\n" + "="*70)
    print("📊 RESULTADOS DEL BACKTESTING")
    print("="*70)
    
    for strategy_name, result in comparison['results'].items():
        if 'error' in result:
            print(f"\n❌ {strategy_name}: {result['error']}")
            continue
        
        metrics = result.get('metrics', {})
        print(f"\n📈 {strategy_name}:")
        print(f"   Retorno Total: {result['total_return']:.2f}%")
        print(f"   Capital Final: ${result['final_capital']:,.2f}")
        print(f"   Total Trades: {metrics.get('total_trades', 0)}")
        print(f"   Win Rate: {metrics.get('win_rate', 0):.1f}%")
        print(f"   Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"   Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
        print(f"   Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
        print(f"   Profit Factor: {metrics.get('profit_factor', 0):.2f}")
    
    # Mejor estrategia
    if comparison.get('best_strategy'):
        print(f"\n🏆 Mejor Estrategia: {comparison['best_strategy']}")
        best_metrics = comparison['comparison_metrics']
        print(f"   Sharpe Ratio: {best_metrics.get('best_sharpe', 0):.2f}")
        print(f"   Retorno: {best_metrics.get('best_return', 0):.2f}%")
        print(f"   Win Rate: {best_metrics.get('best_win_rate', 0):.1f}%")
    
    # Guardar resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"backtest_comparison_{symbol}_{timestamp}.json"
    backtester.save_results(comparison, filename)
    print(f"\n💾 Resultados guardados en: data/backtest_results/{filename}")

if __name__ == "__main__":
    main()


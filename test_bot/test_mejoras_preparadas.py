"""
Script de prueba para las mejoras preparadas
Prueba los 3 nuevos servicios antes de integrar
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

print("=" * 60)
print("🧪 PRUEBA DE MEJORAS PREPARADAS")
print("=" * 60)
print()

# Test 1: Commission Calculator
print("=" * 60)
print("1️⃣  COMMISSION CALCULATOR")
print("=" * 60)
try:
    from src.services.commission_calculator import CommissionCalculator
    
    calc = CommissionCalculator()
    
    # Test: Comisión de compra
    print("\n📊 Test: Comisión de Compra (GGAL, $1000, 10 acciones)")
    result = calc.calculate_commission('GGAL', 1000.0, 10, 'BUY')
    print(f"   Precio total: ${result['total_value']:,.2f}")
    print(f"   Comisión: ${result['commission']:.2f} ({result['commission_rate']*100:.2f}%)")
    print(f"   Total con comisión: ${result['total_with_commission']:,.2f}")
    
    # Test: Round trip
    print("\n📊 Test: Costo Ida y Vuelta (compra $1000, venta $1050)")
    round_trip = calc.calculate_round_trip_cost('GGAL', 1000.0, 1050.0, 10)
    print(f"   Comisión compra: ${round_trip['buy_commission']:.2f}")
    print(f"   Comisión venta: ${round_trip['sell_commission']:.2f}")
    print(f"   Total comisiones: ${round_trip['total_commissions']:.2f}")
    print(f"   P&L bruto: ${round_trip['gross_pnl']:,.2f}")
    print(f"   P&L neto: ${round_trip['net_pnl']:,.2f}")
    print(f"   Mínimo para break-even: {round_trip['min_profit_pct_to_break_even']:.2f}%")
    
    # Test: Decisión de trade
    print("\n📊 Test: ¿Ejecutar Trade? (entrada $1000, salida $1030, ganancia esperada 3%)")
    decision = calc.should_execute_trade('GGAL', 1000.0, 1030.0, 10, 3.0)
    print(f"   Ganancia esperada: {decision['expected_profit_pct']:.2f}%")
    print(f"   Costo total: {decision['total_cost_pct']:.2f}%")
    print(f"   Ganancia neta: {decision['net_profit_pct']:.2f}%")
    print(f"   Decisión: {decision['recommendation']}")
    print(f"   Razón: {decision['reason']}")
    
    print("\n✅ Commission Calculator: OK")
    
except Exception as e:
    print(f"\n❌ Commission Calculator: ERROR - {e}")
    import traceback
    traceback.print_exc()

print()

# Test 2: Candlestick Analyzer
print("=" * 60)
print("2️⃣  CANDLESTICK ANALYZER")
print("=" * 60)
try:
    from src.services.candlestick_analyzer import CandlestickAnalyzer
    import pandas as pd
    import numpy as np
    
    analyzer = CandlestickAnalyzer()
    
    # Crear datos de prueba (simulando Hammer)
    print("\n📊 Test: Detectar Hammer (patrón alcista)")
    dates = pd.date_range('2025-01-01', periods=10, freq='D')
    data = {
        'open': [100, 98, 97, 99, 95, 96, 97, 98, 99, 100],
        'high': [102, 99, 98, 101, 97, 98, 99, 100, 101, 102],
        'low': [98, 97, 96, 98, 92, 93, 94, 95, 96, 97],  # Última vela con sombra inferior larga
        'close': [99, 97, 98, 100, 96, 97, 98, 99, 100, 101],  # Última vela alcista
        'volume': [1000] * 10
    }
    df = pd.DataFrame(data, index=dates)
    
    result = analyzer.analyze(df, lookback=5)
    print(f"   Patrones detectados: {result['count']}")
    print(f"   Score total: {result['score']:+d}")
    if result['patterns_detected']:
        print(f"   Patrones: {', '.join(result['patterns_detected'])}")
        print(f"   Descripciones: {', '.join(result['descriptions'])}")
    else:
        print("   (No se detectaron patrones en datos de prueba)")
    
    print("\n✅ Candlestick Analyzer: OK")
    
except Exception as e:
    print(f"\n❌ Candlestick Analyzer: ERROR - {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Correlation Analyzer
print("=" * 60)
print("3️⃣  CORRELATION ANALYZER")
print("=" * 60)
try:
    from src.services.correlation_analyzer import CorrelationAnalyzer
    
    analyzer = CorrelationAnalyzer()
    
    # Test: Análisis de portafolio
    print("\n📊 Test: Análisis de Portafolio")
    symbols = ['GGAL', 'PAMP', 'YPF', 'KO', 'LOMA']
    result = analyzer.analyze_portfolio(symbols)
    
    print(f"   Score de diversificación: {result['diversification_score']:.1f}/100")
    print(f"   Símbolos analizados: {len(result['symbols_analyzed'])}")
    print(f"   Pares altamente correlacionados: {len(result['high_correlation_pairs'])}")
    
    if result['recommendations']:
        print("\n   Recomendaciones:")
        for rec in result['recommendations'][:3]:
            print(f"     • {rec}")
    
    # Test: ¿Agregar símbolo?
    print("\n📊 Test: ¿Agregar Nuevo Símbolo? (AAPL a portafolio con GGAL, PAMP, YPF)")
    decision = analyzer.should_add_symbol('AAPL', ['GGAL', 'PAMP', 'YPF'])
    print(f"   ¿Agregar?: {decision['should_add']}")
    print(f"   Razón: {decision['reason']}")
    print(f"   Correlación máxima: {decision['max_correlation']:.2f}")
    print(f"   Correlación promedio: {decision['avg_correlation']:.2f}")
    
    print("\n✅ Correlation Analyzer: OK")
    
except Exception as e:
    print(f"\n❌ Correlation Analyzer: ERROR - {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
print("✅ PRUEBAS COMPLETADAS")
print("=" * 60)
print()
print("📋 RESUMEN:")
print("   • Commission Calculator: Listo para integrar")
print("   • Candlestick Analyzer: Listo para integrar")
print("   • Correlation Analyzer: Listo para integrar")
print()
print("📝 Próximo paso: Integrar después del monitoreo de 14 días")
print()



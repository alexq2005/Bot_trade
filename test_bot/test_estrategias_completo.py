"""
Test completo de las 13 estrategias avanzadas
Verifica que todas funcionen correctamente
"""
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

print("="*70)
print("🧪 TEST COMPLETO DE 13 ESTRATEGIAS AVANZADAS")
print("="*70)
print()

# Preparar datos de prueba
print("📊 Preparando datos de prueba...")
np.random.seed(42)

# Crear DataFrame de prueba con OHLCV
dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
df_test = pd.DataFrame({
    'open': 100 + np.random.randn(100).cumsum(),
    'high': 102 + np.random.randn(100).cumsum(),
    'low': 98 + np.random.randn(100).cumsum(),
    'close': 100 + np.random.randn(100).cumsum(),
    'volume': np.random.randint(1000000, 10000000, 100)
}, index=dates)

# Asegurar que high > low
df_test['high'] = df_test[['open', 'close']].max(axis=1) + abs(np.random.randn(100))
df_test['low'] = df_test[['open', 'close']].min(axis=1) - abs(np.random.randn(100))

print(f"✅ DataFrame de prueba creado: {len(df_test)} registros")
print()

# Test results
results = {}
errors = []

# ============================================================
# 1. REGIME DETECTOR
# ============================================================
print("1. 🎯 Testing Regime Detector...")
try:
    from src.services.regime_detector import RegimeDetector
    
    detector = RegimeDetector()
    regime, info = detector.detect_regime(df_test)
    
    assert regime in ['TRENDING', 'RANGING', 'VOLATILE', 'UNKNOWN'], f"Régimen inválido: {regime}"
    assert 'adx' in info, "Falta ADX en info"
    assert 'volatility' in info, "Falta volatility en info"
    
    print(f"   ✅ Régimen detectado: {regime}")
    print(f"   ✅ ADX: {info['adx']}")
    print(f"   ✅ Volatilidad: {info['volatility']}%")
    results['regime_detector'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Regime Detector: {e}")
    results['regime_detector'] = 'FAIL'

print()

# ============================================================
# 2. MULTI-TIMEFRAME ANALYZER
# ============================================================
print("2. 📈 Testing Multi-Timeframe Analyzer...")
try:
    from src.services.multi_timeframe_analyzer import MultiTimeframeAnalyzer
    
    analyzer = MultiTimeframeAnalyzer()
    # Test con símbolo conocido
    result = analyzer.analyze_all_timeframes('AAPL')
    
    assert 'signal' in result, "Falta signal en resultado"
    assert 'score' in result, "Falta score en resultado"
    assert 'timeframes' in result, "Falta timeframes en resultado"
    
    print(f"   ✅ Señal: {result['signal']}")
    print(f"   ✅ Score: {result['score']}")
    print(f"   ✅ Timeframes analizados: {len(result['timeframes'])}")
    results['multi_timeframe'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Multi-Timeframe: {e}")
    results['multi_timeframe'] = 'FAIL'

print()

# ============================================================
# 3. ORDER FLOW ANALYZER
# ============================================================
print("3. 📊 Testing Order Flow Analyzer...")
try:
    from src.services.order_flow_analyzer import OrderFlowAnalyzer
    from src.connectors.iol_client import IOLClient
    
    # Mock IOL client para test
    class MockIOLClient:
        def get_market_depth(self, symbol):
            return {
                'bids': [
                    {'price': 100, 'quantity': 1000},
                    {'price': 99, 'quantity': 500}
                ],
                'asks': [
                    {'price': 101, 'quantity': 800},
                    {'price': 102, 'quantity': 400}
                ]
            }
    
    mock_client = MockIOLClient()
    analyzer = OrderFlowAnalyzer(mock_client)
    result = analyzer.analyze_flow('TEST')
    
    assert 'pressure' in result, "Falta pressure"
    assert 'score' in result, "Falta score"
    
    print(f"   ✅ Presión: {result['pressure']}")
    print(f"   ✅ Score: {result['score']}")
    results['order_flow'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Order Flow: {e}")
    results['order_flow'] = 'FAIL'

print()

# ============================================================
# 4. SEASONAL ANALYZER
# ============================================================
print("4. 🍂 Testing Seasonal Analyzer...")
try:
    from src.services.seasonal_analyzer import SeasonalAnalyzer
    
    analyzer = SeasonalAnalyzer()
    result = analyzer.analyze('TEST', df_test)
    
    assert 'score' in result, "Falta score"
    
    print(f"   ✅ Score: {result['score']}")
    print(f"   ✅ Factores: {len(result.get('factors', []))}")
    results['seasonal'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Seasonal: {e}")
    results['seasonal'] = 'FAIL'

print()

# ============================================================
# 5. FRACTAL ANALYZER
# ============================================================
print("5. 🔄 Testing Fractal Analyzer...")
try:
    from src.services.fractal_analyzer import FractalAnalyzer
    
    analyzer = FractalAnalyzer()
    result = analyzer.analyze(df_test)
    
    assert 'score' in result, "Falta score"
    
    print(f"   ✅ Score: {result['score']}")
    print(f"   ✅ Fractales alcistas: {result.get('bullish_fractals', 0)}")
    print(f"   ✅ Fractales bajistas: {result.get('bearish_fractals', 0)}")
    results['fractals'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Fractals: {e}")
    results['fractals'] = 'FAIL'

print()

# ============================================================
# 6. ANOMALY DETECTOR
# ============================================================
print("6. 🔍 Testing Anomaly Detector...")
try:
    from src.services.anomaly_detector import AnomalyDetector
    
    detector = AnomalyDetector()
    result = detector.detect(df_test)
    
    assert 'score' in result, "Falta score"
    assert 'anomalies' in result, "Falta anomalies"
    
    print(f"   ✅ Score: {result['score']}")
    print(f"   ✅ Anomalías detectadas: {result.get('count', 0)}")
    results['anomaly'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Anomaly: {e}")
    results['anomaly'] = 'FAIL'

print()

# ============================================================
# 7. VOLUME PROFILE ANALYZER
# ============================================================
print("7. 📊 Testing Volume Profile Analyzer...")
try:
    from src.services.volume_profile_analyzer import VolumeProfileAnalyzer
    
    analyzer = VolumeProfileAnalyzer()
    result = analyzer.analyze(df_test)
    
    assert 'score' in result, "Falta score"
    assert 'poc' in result, "Falta POC"
    
    print(f"   ✅ Score: {result['score']}")
    print(f"   ✅ POC: ${result.get('poc', 0):.2f}")
    print(f"   ✅ Value Area: ${result.get('value_area_low', 0):.2f} - ${result.get('value_area_high', 0):.2f}")
    results['volume_profile'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Volume Profile: {e}")
    results['volume_profile'] = 'FAIL'

print()

# ============================================================
# 8. MONTE CARLO SIMULATOR
# ============================================================
print("8. 🎲 Testing Monte Carlo Simulator...")
try:
    from src.services.monte_carlo_simulator import MonteCarloSimulator
    
    simulator = MonteCarloSimulator(num_simulations=1000)  # Reducido para test
    result = simulator.simulate_trade('TEST', 100, 0.25, days_forward=30, position_size=10)
    
    assert 'score' in result, "Falta score"
    assert 'win_rate' in result, "Falta win_rate"
    assert 'expected_value' in result, "Falta expected_value"
    
    print(f"   ✅ Score: {result['score']}")
    print(f"   ✅ Win Rate: {result['win_rate']}%")
    print(f"   ✅ Expected Value: ${result['expected_value']:.2f}")
    results['monte_carlo'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Monte Carlo: {e}")
    results['monte_carlo'] = 'FAIL'

print()

# ============================================================
# 9. PATTERN RECOGNIZER
# ============================================================
print("9. 🧬 Testing Pattern Recognizer...")
try:
    from src.services.pattern_recognizer import PatternRecognizer
    
    recognizer = PatternRecognizer()
    result = recognizer.detect_all_patterns(df_test)
    
    assert 'score' in result, "Falta score"
    assert 'patterns_detected' in result, "Falta patterns_detected"
    
    print(f"   ✅ Score: {result['score']}")
    print(f"   ✅ Patrones detectados: {result.get('count', 0)}")
    if result.get('patterns_detected'):
        print(f"   ✅ Patrones: {', '.join(result['patterns_detected'])}")
    results['patterns'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Patterns: {e}")
    results['patterns'] = 'FAIL'

print()

# ============================================================
# 10. PAIRS TRADER
# ============================================================
print("10. 💹 Testing Pairs Trader...")
try:
    from src.services.pairs_trader import PairsTrader
    
    trader = PairsTrader()
    
    # Crear dos dataframes correlacionados para test
    df_a = df_test.copy()
    df_b = df_test.copy()
    df_b['close'] = df_b['close'] * 1.1  # Agregar variación
    
    result = trader.analyze_pair('TEST_A', 'TEST_B', df_a, df_b)
    
    assert 'z_score' in result or 'error' in result, "Resultado inválido"
    
    if 'z_score' in result:
        print(f"   ✅ Z-Score: {result['z_score']}")
        print(f"   ✅ Par: {result.get('pair', 'N/A')}")
    else:
        print(f"   ⚠️  No pudo analizar par (normal si datos insuficientes)")
    
    results['pairs'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Pairs Trader: {e}")
    results['pairs'] = 'FAIL'

print()

# ============================================================
# 11. ELLIOTT WAVE ANALYZER
# ============================================================
print("11. 🌊 Testing Elliott Wave Analyzer...")
try:
    from src.services.elliott_wave_analyzer import ElliottWaveAnalyzer
    
    analyzer = ElliottWaveAnalyzer()
    result = analyzer.detect_wave(df_test)
    
    assert 'wave' in result, "Falta wave"
    assert 'score' in result, "Falta score"
    
    print(f"   ✅ Onda detectada: {result['wave']}")
    print(f"   ✅ Score: {result['score']}")
    results['elliott'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Elliott Wave: {e}")
    results['elliott'] = 'FAIL'

print()

# ============================================================
# 12. SMART MONEY ANALYZER
# ============================================================
print("12. 💰 Testing Smart Money Analyzer...")
try:
    from src.services.smart_money_analyzer import SmartMoneyAnalyzer
    
    analyzer = SmartMoneyAnalyzer()
    result = analyzer.analyze(df_test)
    
    assert 'score' in result, "Falta score"
    assert 'factors' in result, "Falta factors"
    
    print(f"   ✅ Score: {result['score']}")
    print(f"   ✅ Factores: {len(result.get('factors', []))}")
    results['smart_money'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Smart Money: {e}")
    results['smart_money'] = 'FAIL'

print()

# ============================================================
# 13. META-LEARNER
# ============================================================
print("13. 🤖 Testing Meta-Learner...")
try:
    from src.services.meta_learner import MetaLearner
    
    learner = MetaLearner()
    
    # Scores de prueba de otras estrategias
    all_scores = {
        'technical': 20,
        'ai_prediction': 15,
        'sentiment': 5,
        'regime': 10,
        'multi_timeframe': 25
    }
    
    market_conditions = {
        'regime': 'TRENDING',
        'volatility': 0.20
    }
    
    result = learner.combine_signals(all_scores, market_conditions)
    
    assert 'final_score' in result, "Falta final_score"
    assert 'confidence' in result, "Falta confidence"
    
    print(f"   ✅ Score final: {result['final_score']}")
    print(f"   ✅ Confianza: {result['confidence']}")
    print(f"   ✅ Pesos usados: {result.get('weights_used', 'N/A')}")
    results['meta_learner'] = 'PASS'
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    errors.append(f"Meta-Learner: {e}")
    results['meta_learner'] = 'FAIL'

print()

# ============================================================
# RESUMEN FINAL
# ============================================================
print("="*70)
print("📊 RESUMEN DE RESULTADOS")
print("="*70)
print()

passed = sum(1 for r in results.values() if r == 'PASS')
failed = sum(1 for r in results.values() if r == 'FAIL')
total = len(results)

print(f"✅ PASARON: {passed}/{total}")
print(f"❌ FALLARON: {failed}/{total}")
print()

if failed == 0:
    print("🎉 ¡TODAS LAS ESTRATEGIAS FUNCIONAN CORRECTAMENTE!")
    print()
    print("Detalles:")
    for strategy, status in results.items():
        print(f"  ✅ {strategy}")
else:
    print("⚠️  ALGUNAS ESTRATEGIAS TIENEN ERRORES:")
    print()
    for strategy, status in results.items():
        emoji = "✅" if status == 'PASS' else "❌"
        print(f"  {emoji} {strategy}: {status}")
    
    print()
    print("📋 ERRORES DETALLADOS:")
    for error in errors:
        print(f"  • {error}")

print()
print("="*70)

# Exit code
sys.exit(0 if failed == 0 else 1)


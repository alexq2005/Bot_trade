"""
Script para verificar si las estrategias avanzadas se están ejecutando
Busca en los logs y archivos del bot
"""
import json
import os
from pathlib import Path
from datetime import datetime

print("="*70)
print("🔍 VERIFICACIÓN DE ESTRATEGIAS AVANZADAS")
print("="*70)
print()

# 1. Verificar que el bot está corriendo
pid_file = Path("bot.pid")
if pid_file.exists():
    with open(pid_file, 'r') as f:
        pid = f.read().strip()
    print(f"✅ Bot ejecutándose (PID: {pid})")
else:
    print("❌ Bot NO está ejecutándose")
    exit(1)

print()

# 2. Verificar archivos de estrategias
print("📁 Verificando archivos de estrategias:")
print("-" * 70)

strategies_dir = Path("src/services")
strategy_files = [
    "regime_detector.py",
    "multi_timeframe_analyzer.py",
    "order_flow_analyzer.py",
    "seasonal_analyzer.py",
    "fractal_analyzer.py",
    "anomaly_detector.py",
    "volume_profile_analyzer.py",
    "monte_carlo_simulator.py",
    "pattern_recognizer.py",
    "pairs_trader.py",
    "elliott_wave_analyzer.py",
    "smart_money_analyzer.py",
    "meta_learner.py"
]

found = 0
for sf in strategy_files:
    file_path = strategies_dir / sf
    if file_path.exists():
        print(f"  ✅ {sf}")
        found += 1
    else:
        print(f"  ❌ {sf} NO ENCONTRADO")

print()
print(f"Total: {found}/{len(strategy_files)} estrategias encontradas")
print()

# 3. Buscar en el código del bot si están importadas
print("🔍 Verificando imports en trading_bot.py:")
print("-" * 70)

bot_file = Path("trading_bot.py")
if bot_file.exists():
    with open(bot_file, 'r', encoding='utf-8') as f:
        bot_content = f.read()
    
    imports_found = []
    for strategy in ["RegimeDetector", "MultiTimeframeAnalyzer", "OrderFlowAnalyzer",
                     "SeasonalAnalyzer", "FractalAnalyzer", "AnomalyDetector",
                     "VolumeProfileAnalyzer", "MonteCarloSimulator", "PatternRecognizer",
                     "PairsTrader", "ElliottWaveAnalyzer", "SmartMoneyAnalyzer", "MetaLearner"]:
        if strategy in bot_content:
            imports_found.append(strategy)
            print(f"  ✅ {strategy}")
        else:
            print(f"  ❌ {strategy} NO importado")
    
    print()
    print(f"Total: {len(imports_found)}/13 estrategias importadas")
    
    # Buscar la línea de inicialización
    if "advanced_strategies_enabled" in bot_content:
        print("  ✅ Flag 'advanced_strategies_enabled' encontrado")
    else:
        print("  ❌ Flag 'advanced_strategies_enabled' NO encontrado")
    
    print()

# 4. Verificar configuración
print("⚙️  Verificando configuración:")
print("-" * 70)

config_file = Path("professional_config.json")
if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    monitoring = config.get('monitoring', {})
    only_iol = monitoring.get('only_iol_portfolio', False)
    
    print(f"  Portfolio Mode: {'SOLO_IOL' if only_iol else 'COMPLETO'}")
    print(f"  Buy Threshold: {config.get('buy_threshold', 25)}")
    print(f"  Sell Threshold: {config.get('sell_threshold', -25)}")
    print()

# 5. Buscar evidencia de ejecución en logs recientes
print("📊 Buscando evidencia de ejecución:")
print("-" * 70)

# Buscar archivo de análisis más reciente
operations_file = Path("data/operations_log.json")
if operations_file.exists():
    try:
        with open(operations_file, 'r', encoding='utf-8') as f:
            operations = json.load(f)
        
        # Buscar análisis recientes (última hora)
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=1)
        recent_analyses = [
            op for op in operations 
            if op['type'] == 'ANALYSIS' and datetime.fromisoformat(op['timestamp']) >= cutoff
        ]
        
        if recent_analyses:
            print(f"  ✅ {len(recent_analyses)} análisis en la última hora")
            
            # Mostrar el más reciente
            latest = max(recent_analyses, key=lambda x: x['timestamp'])
            data = latest.get('data', {})
            print(f"\n  Último análisis:")
            print(f"    Símbolo: {data.get('symbol', 'N/A')}")
            print(f"    Score: {data.get('score', 0)}")
            print(f"    Señal: {data.get('final_signal', 'N/A')}")
            print(f"    Timestamp: {latest['timestamp'][:19]}")
        else:
            print("  ⚠️  No hay análisis recientes en la última hora")
            print("     El bot puede estar en proceso de inicialización")
    except:
        print("  ⚠️  Error leyendo operations_log.json")
else:
    print("  ⚠️  operations_log.json no existe aún")

print()

# 6. Recomendaciones
print("💡 RECOMENDACIONES:")
print("-" * 70)
print("  1. El bot está analizando símbolos (ver logs)")
print("  2. Los mensajes de estrategias avanzadas se muestran en CONSOLA")
print("  3. Para verlos:")
print("     - Ejecuta el bot en primer plano (sin background)")
print("     - O busca la ventana de consola que se abrió")
print()
print("  4. Para ejecutar en primer plano:")
print("     cd test_bot")
print("     python run_bot.py --paper --continuous")
print()

print("="*70)
print("✅ VERIFICACIÓN COMPLETADA")
print("="*70)


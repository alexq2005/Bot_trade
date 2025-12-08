"""
Script de diagnóstico para entender por qué no se ejecutan órdenes de compra
"""
import os
import sys
from pathlib import Path
from datetime import datetime, time

# Agregar el directorio al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

print("="*60)
print("🔍 DIAGNÓSTICO: ¿Por qué no se ejecutan órdenes?")
print("="*60)
print()

# 1. Verificar horarios de trading
print("1️⃣ VERIFICAR HORARIOS DE TRADING")
print("-"*60)
now = datetime.now()
current_time = now.time()
trading_start = time(11, 0)  # 11:00
trading_end = time(17, 0)     # 17:00

print(f"   Hora actual: {current_time.strftime('%H:%M:%S')}")
print(f"   Horario IOL: {trading_start.strftime('%H:%M')} - {trading_end.strftime('%H:%M')}")

if current_time < trading_start:
    print(f"   ❌ ANTES del horario de trading")
    print(f"   ⏰ Espera hasta las {trading_start.strftime('%H:%M')}")
elif current_time > trading_end:
    print(f"   ❌ DESPUÉS del horario de trading")
    print(f"   ⏰ El mercado cerró a las {trading_end.strftime('%H:%M')}")
else:
    print(f"   ✅ Dentro del horario de trading")
    
    # Verificar primeros/últimos minutos
    avoid_first = 15  # Primeros 15 minutos
    avoid_last = 15   # Últimos 15 minutos
    
    minutes_since_open = (current_time.hour - trading_start.hour) * 60 + (current_time.minute - trading_start.minute)
    minutes_to_close = (trading_end.hour - current_time.hour) * 60 + (trading_end.minute - current_time.minute)
    
    if minutes_since_open < avoid_first:
        print(f"   ⚠️  Primeros {avoid_first} minutos - Alta volatilidad")
        print(f"   ⏰ Espera {avoid_first - minutes_since_open} minutos más")
    elif minutes_to_close < avoid_last:
        print(f"   ⚠️  Últimos {avoid_last} minutos - Cierre de mercado")
        print(f"   ⏰ Solo quedan {minutes_to_close} minutos")
    else:
        print(f"   ✅ Horario válido para operar")

print()

# 2. Verificar Risk Manager
print("2️⃣ VERIFICAR RISK MANAGER")
print("-"*60)
try:
    from src.services.adaptive_risk_manager import AdaptiveRiskManager
    from src.connectors.iol_client import IOLClient
    
    iol_client = IOLClient()
    available_balance = iol_client.get_available_balance()
    
    risk_manager = AdaptiveRiskManager(initial_capital=available_balance)
    risk_manager.current_capital = available_balance
    
    can_trade, reason = risk_manager.can_trade()
    
    print(f"   Capital disponible: ${available_balance:,.2f}")
    print(f"   ¿Puede operar? {can_trade}")
    print(f"   Razón: {reason}")
    
    # Mostrar estadísticas del risk manager
    print(f"\n   📊 Estadísticas:")
    print(f"      • Operaciones diarias: {risk_manager.daily_trades_count}/{risk_manager.max_daily_trades}")
    print(f"      • P&L diario: ${risk_manager.daily_pnl:,.2f}")
    print(f"      • Pérdidas consecutivas: {risk_manager.consecutive_losses}/{risk_manager.max_consecutive_losses}")
    print(f"      • Capital actual: ${risk_manager.current_capital:,.2f}")
    print(f"      • Capital inicial: ${risk_manager.initial_capital:,.2f}")
    
except Exception as e:
    print(f"   ❌ Error verificando Risk Manager: {e}")

print()

# 3. Verificar filtros profesionales
print("3️⃣ VERIFICAR FILTROS PROFESIONALES")
print("-"*60)
try:
    from src.services.professional_trader import ProfessionalTrader
    
    trader = ProfessionalTrader()
    
    # Verificar filtros de tiempo
    can_trade_time, time_reason = trader.check_time_filters()
    print(f"   Filtros de Tiempo:")
    print(f"      ¿Puede operar? {can_trade_time}")
    print(f"      Razón: {time_reason}")
    
    # Verificar configuración
    config = trader.config
    time_config = config.get("time_management", {})
    print(f"\n   ⚙️  Configuración:")
    print(f"      • Horario inicio: {time_config.get('trading_hours_start', '11:00')}")
    print(f"      • Horario fin: {time_config.get('trading_hours_end', '17:00')}")
    print(f"      • Evitar primeros minutos: {time_config.get('avoid_first_minutes', 15)}")
    print(f"      • Evitar últimos minutos: {time_config.get('avoid_last_minutes', 15)}")
    
except Exception as e:
    print(f"   ❌ Error verificando filtros: {e}")

print()

# 4. Verificar operaciones recientes
print("4️⃣ VERIFICAR OPERACIONES RECIENTES")
print("-"*60)
ops_file = Path("data/operations_log.json")
if ops_file.exists():
    try:
        import json
        with open(ops_file, 'r', encoding='utf-8') as f:
            operations = json.load(f)
        
        # Filtrar análisis recientes con señales BUY
        recent_buy_signals = []
        for op in operations[-50:]:  # Últimas 50 operaciones
            if op.get('type') == 'ANALYSIS':
                data = op.get('data', {})
                signal = data.get('final_signal', 'HOLD')
                if signal == 'BUY':
                    recent_buy_signals.append({
                        'symbol': data.get('symbol', 'N/A'),
                        'timestamp': op.get('timestamp', ''),
                        'score': data.get('score', 0),
                        'filter_reason': data.get('filter_reason', 'N/A')
                    })
        
        if recent_buy_signals:
            print(f"   ✅ Se encontraron {len(recent_buy_signals)} señales BUY recientes:")
            for sig in recent_buy_signals[-5:]:  # Últimas 5
                print(f"      • {sig['symbol']}: Score {sig['score']:.1f}")
                if sig['filter_reason'] != 'N/A':
                    print(f"        ⚠️  Bloqueado: {sig['filter_reason']}")
        else:
            print(f"   ⚠️  No hay señales BUY recientes")
            print(f"   💡 El bot puede estar generando solo señales HOLD o SELL")
    except Exception as e:
        print(f"   ❌ Error leyendo operaciones: {e}")
else:
    print(f"   ⚠️  No hay archivo operations_log.json")

print()

# 5. Verificar trades ejecutados
print("5️⃣ VERIFICAR TRADES EJECUTADOS")
print("-"*60)
trades_file = Path("trades.json")
if trades_file.exists():
    try:
        import json
        with open(trades_file, 'r', encoding='utf-8') as f:
            trades = json.load(f)
        
        buy_trades = [t for t in trades if t.get('signal') == 'BUY']
        live_trades = [t for t in trades if t.get('mode') == 'LIVE']
        
        print(f"   Total trades: {len(trades)}")
        print(f"   Compras: {len(buy_trades)}")
        print(f"   Trades LIVE: {len(live_trades)}")
        
        if live_trades:
            print(f"\n   📋 Últimos trades LIVE:")
            for trade in live_trades[-5:]:
                timestamp = trade.get('timestamp', '')
                try:
                    trade_time = datetime.fromisoformat(timestamp)
                    time_str = trade_time.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    time_str = timestamp
                print(f"      • {trade.get('symbol', 'N/A')}: {trade.get('signal', 'N/A')} - {time_str}")
        else:
            print(f"   ⚠️  No hay trades LIVE ejecutados")
            print(f"   💡 Todas las operaciones pueden estar en modo PAPER")
    except Exception as e:
        print(f"   ❌ Error leyendo trades: {e}")
else:
    print(f"   ⚠️  No hay archivo trades.json")

print()

# 6. Resumen y recomendaciones
print("="*60)
print("📋 RESUMEN Y RECOMENDACIONES")
print("="*60)
print()

issues = []

# Verificar horarios
if current_time < trading_start or current_time > trading_end:
    issues.append("❌ Fuera del horario de trading IOL (11:00-17:00)")
elif minutes_since_open < 15 or minutes_to_close < 15:
    issues.append("⚠️  En los primeros/últimos 15 minutos (alta volatilidad)")

# Verificar risk manager
try:
    if not can_trade:
        issues.append(f"❌ Risk Manager bloquea operaciones: {reason}")
except:
    pass

# Verificar filtros de tiempo
try:
    if not can_trade_time:
        issues.append(f"❌ Filtros de tiempo bloquean: {time_reason}")
except:
    pass

if issues:
    print("🚨 PROBLEMAS DETECTADOS:")
    for issue in issues:
        print(f"   {issue}")
    print()
    print("✅ SOLUCIONES:")
    print("   1. Verifica que estés dentro del horario 11:00-17:00")
    print("   2. Espera a que pasen los primeros 15 minutos")
    print("   3. Revisa la configuración del Risk Manager")
    print("   4. Verifica que no hayas alcanzado límites diarios")
    print("   5. Revisa los logs del bot para más detalles")
else:
    print("✅ No se detectaron problemas obvios")
    print()
    print("💡 Posibles causas:")
    print("   1. El bot no está generando señales BUY (solo HOLD)")
    print("   2. Los scores no alcanzan el umbral mínimo")
    print("   3. Los filtros de entrada profesionales están bloqueando")
    print("   4. El position_size calculado es 0")
    print()
    print("🔍 Para más detalles:")
    print("   - Revisa operations_log.json para ver las señales generadas")
    print("   - Verifica el score mínimo requerido en el código")
    print("   - Revisa los filtros de entrada en professional_config.json")

print()
print("="*60)


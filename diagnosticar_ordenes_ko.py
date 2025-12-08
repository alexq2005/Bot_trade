"""
Diagnóstico de Órdenes de KO - Por qué no se ejecutaron en IOL
"""
import json
from pathlib import Path
from datetime import datetime

print("="*70)
print("🔍 DIAGNÓSTICO DE ÓRDENES KO")
print("="*70)
print()

# 1. Leer trades.json
trades_file = Path("trades.json")
if not trades_file.exists():
    print("❌ No existe trades.json")
    exit(1)

with open(trades_file, 'r') as f:
    all_trades = json.load(f)

# Filtrar KO de hoy
ko_today = [t for t in all_trades if t.get('symbol') == 'KO' and '2025-12-02' in t.get('timestamp', '')]

print(f"📊 Operaciones de KO hoy: {len(ko_today)}")
print()

for i, trade in enumerate(ko_today, 1):
    print(f"Operación #{i}:")
    print(f"  ⏰ Timestamp: {trade.get('timestamp')}")
    print(f"  📈 Signal: {trade.get('signal')}")
    print(f"  📦 Quantity: {trade.get('quantity')}")
    print(f"  💵 Price: ${trade.get('price'):.2f}")
    print(f"  ✅ Status: {trade.get('status')}")
    print(f"  💰 Mode: {trade.get('mode')}")
    print(f"  🔢 Order ID: {trade.get('order_id')}")
    
    if 'error' in trade:
        print(f"  ❌ Error: {trade.get('error')}")
    
    print()

print("="*70)
print("🔍 ANÁLISIS")
print("="*70)
print()

# Verificar si todas tienen order_id N/A
all_na = all(t.get('order_id') == 'N/A' for t in ko_today)

if all_na:
    print("❌ PROBLEMA: Todas las operaciones tienen order_id = 'N/A'")
    print()
    print("Esto significa:")
    print("  • El bot generó señales BUY")
    print("  • Intentó ejecutar en IOL")
    print("  • IOL NO devolvió 'numeroOperacion'")
    print("  • Las órdenes NO se ejecutaron realmente")
    print()
    print("🔍 Posibles causas:")
    print("  1. Saldo insuficiente en IOL")
    print("  2. El bot está realmente en PAPER aunque diga LIVE")
    print("  3. Error en iol_client.place_order()")
    print("  4. IOL rechazó las órdenes silenciosamente")
    print()
    print("✅ Solución:")
    print("  Revisar los logs del bot en el momento de estas operaciones")
    print("  Buscar mensajes de:")
    print("    • '💸 [LIVE TRADING] Sending order'")
    print("    • '📊 Verificando saldo'")
    print("    • '❌ Saldo insuficiente'")
    print("    • '✅ Orden ejecutada'")
else:
    print("✅ Algunas órdenes tienen ID válido")

print()
print("="*70)
print("💡 PRÓXIMOS PASOS")
print("="*70)
print()
print("1. Verificar que el bot esté en modo LIVE:")
print("   grep 'Mode:.*LIVE' logs/trading_bot_20251202.log")
print()
print("2. Buscar logs de ejecución de KO:")
print("   grep -A 10 'Analyzing KO' logs/trading_bot_20251202.log")
print()
print("3. Verificar saldo en IOL:")
print("   python -c \"from src.connectors.iol_client import IOLClient; c = IOLClient(); print(c.get_available_balance())\"")
print()
print("="*70)


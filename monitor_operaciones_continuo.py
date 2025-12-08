"""
Monitor Continuo de Operaciones del Bot
Muestra en tiempo real cuando el bot ejecuta operaciones
"""
import time
from pathlib import Path
from datetime import datetime
import json

print("="*70)
print("📊 MONITOR CONTINUO DE OPERACIONES")
print("="*70)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("🔍 Monitoreando:")
print("  • Señales BUY/SELL generadas")
print("  • Ejecuciones en IOL")
print("  • Cambios en trades.json")
print("  • Errores de ejecución")
print()
print("⏳ Presiona Ctrl+C para detener")
print("="*70)
print()

# Estado inicial
last_trade_count = 0
last_check_time = datetime.now()
check_count = 0

try:
    # Contar trades iniciales
    if Path("trades.json").exists():
        with open("trades.json", 'r') as f:
            trades = json.load(f)
            last_trade_count = len(trades)
    
    print(f"📋 Trades iniciales: {last_trade_count}")
    print()
    
    while True:
        check_count += 1
        current_time = datetime.now()
        
        # Cada 10 checks mostrar que está vivo
        if check_count % 10 == 1:
            print(f"[{current_time.strftime('%H:%M:%S')}] Monitoreando... (check #{check_count})")
        
        # 1. Verificar nuevos trades
        if Path("trades.json").exists():
            try:
                with open("trades.json", 'r') as f:
                    trades = json.load(f)
                    current_count = len(trades)
                
                if current_count > last_trade_count:
                    # ¡Nuevo trade!
                    new_trades = trades[last_trade_count:]
                    
                    for trade in new_trades:
                        print()
                        print("="*70)
                        print("🚨 NUEVA OPERACIÓN DETECTADA!")
                        print("="*70)
                        print()
                        print(f"⏰ Timestamp: {trade.get('timestamp')}")
                        print(f"📈 Símbolo: {trade.get('symbol')}")
                        print(f"🎯 Señal: {trade.get('signal')}")
                        print(f"📦 Cantidad: {trade.get('quantity')}")
                        print(f"💵 Precio: ${trade.get('price'):.2f}")
                        print(f"🛡️  Stop Loss: ${trade.get('stop_loss'):.2f}")
                        print(f"🎯 Take Profit: ${trade.get('take_profit'):.2f}")
                        print(f"✅ Status: {trade.get('status')}")
                        print(f"💰 Modo: {trade.get('mode')}")
                        print(f"🔢 Order ID: {trade.get('order_id')}")
                        
                        if 'error' in trade:
                            print(f"❌ Error: {trade.get('error')}")
                        
                        print()
                        
                        # Análisis del resultado
                        if trade.get('order_id') and trade.get('order_id') not in ['N/A', 'MISSING', 'UNKNOWN']:
                            print("✅ ¡ORDEN EJECUTADA EXITOSAMENTE EN IOL!")
                            print(f"   Order ID real: {trade.get('order_id')}")
                            print(f"   💰 Tu saldo en IOL debería haber cambiado")
                        elif trade.get('status') == 'FAILED':
                            print("❌ Orden FALLÓ - No se ejecutó")
                            print(f"   Razón: {trade.get('error', 'Desconocida')}")
                        else:
                            print("⚠️  Orden marcada como FILLED pero sin order ID")
                            print("   🐛 Posible bug - revisar logs")
                        
                        print("="*70)
                        print()
                    
                    last_trade_count = current_count
            except Exception as e:
                if check_count % 10 == 1:
                    print(f"⚠️  Error leyendo trades.json: {e}")
        
        # 2. Verificar terminal para señales
        terminal_file = Path("c:/Users/Lexus/.cursor/projects/c-Users-Lexus-gemini-antigravity-scratch/terminals/31.txt")
        if terminal_file.exists():
            try:
                with open(terminal_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent = ''.join(lines[-50:])
                
                # Buscar mensajes clave de ejecución
                if '💸 [LIVE TRADING] Sending order' in recent and check_count % 5 == 0:
                    print()
                    print("🚀 Bot está intentando ejecutar una orden...")
                    print("   Revisando detalles en próximo check...")
                    
                if '✅ Orden ejecutada en IOL' in recent:
                    print()
                    print("✅ ¡CONFIRMACIÓN DE EJECUCIÓN EN IOL DETECTADA!")
                    print("   Revisa trades.json para detalles")
                    
                if '❌ Saldo insuficiente' in recent:
                    print()
                    print("❌ Orden bloqueada por saldo insuficiente")
                    print("   El bot no tiene capital suficiente")
                    
            except:
                pass
        
        # Pausa antes del próximo check
        time.sleep(5)  # Check cada 5 segundos

except KeyboardInterrupt:
    print()
    print()
    print("="*70)
    print("🛑 Monitor detenido por usuario")
    print("="*70)
    print(f"Checks realizados: {check_count}")
    print(f"Nuevos trades detectados: {last_trade_count}")
    print()

except Exception as e:
    print()
    print(f"❌ Error en monitor: {e}")
    import traceback
    traceback.print_exc()

finally:
    print()
    print("🏁 Monitor finalizado")
    print()


"""
Script para verificar si el bot realizó operaciones
"""
import json
from pathlib import Path
from datetime import datetime

def main():
    print("="*70)
    print("🔍 VERIFICACIÓN DE OPERACIONES DEL BOT")
    print("="*70)
    
    # Verificar trades.json
    trades_file = Path("trades.json")
    if trades_file.exists():
        with open(trades_file, 'r', encoding='utf-8') as f:
            trades = json.load(f)
        
        print(f"\n📊 TRADES ENCONTRADOS: {len(trades)}")
        
        # Filtrar por tipo
        buy_trades = [t for t in trades if t.get('signal') == 'BUY' or t.get('action') == 'BUY']
        sell_trades = [t for t in trades if t.get('signal') == 'SELL' or t.get('action') == 'SELL']
        
        # Filtrar por modo
        paper_trades = [t for t in trades if t.get('mode') == 'PAPER']
        live_trades = [t for t in trades if t.get('mode') == 'LIVE']
        
        # Filtrar por estado
        filled_trades = [t for t in trades if t.get('status') in ['FILLED', 'executed', 'EXECUTED']]
        pending_trades = [t for t in trades if t.get('status') == 'PENDING']
        failed_trades = [t for t in trades if t.get('status') == 'FAILED']
        
        print(f"\n📈 Compras (BUY): {len(buy_trades)}")
        print(f"📉 Ventas (SELL): {len(sell_trades)}")
        print(f"\n🧪 Paper Trading: {len(paper_trades)}")
        print(f"💰 Live Trading: {len(live_trades)}")
        print(f"\n✅ Ejecutados (FILLED/executed): {len(filled_trades)}")
        print(f"⏳ Pendientes (PENDING): {len(pending_trades)}")
        print(f"❌ Fallidos (FAILED): {len(failed_trades)}")
        
        # Mostrar últimos 5 trades
        if trades:
            print(f"\n📋 ÚLTIMOS 5 TRADES:")
            for i, trade in enumerate(trades[-5:], 1):
                symbol = trade.get('symbol', 'N/A')
                action = trade.get('signal') or trade.get('action', 'N/A')
                quantity = trade.get('quantity', 0)
                price = trade.get('price', 0)
                status = trade.get('status', 'N/A')
                mode = trade.get('mode', 'N/A')
                timestamp = trade.get('timestamp', '')
                
                # Formatear timestamp
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
                
                print(f"\n   {i}. {symbol} | {action} | {quantity} @ ${price:.2f}")
                print(f"      Estado: {status} | Modo: {mode}")
                print(f"      Fecha: {timestamp}")
    else:
        print("\n⚠️  No se encontró trades.json")
        print("   → El bot aún no ha realizado operaciones")
    
    # Verificar operations_log.json
    ops_file = Path("data/operations_log.json")
    if ops_file.exists():
        with open(ops_file, 'r', encoding='utf-8') as f:
            operations = json.load(f)
        
        # Filtrar solo operaciones de trading (no análisis)
        trade_ops = [op for op in operations if op.get('type') in ['TRADE', 'BUY', 'SELL']]
        analysis_ops = [op for op in operations if op.get('type') == 'ANALYSIS']
        
        print(f"\n\n📝 OPERACIONES EN LOG:")
        print(f"   • Total operaciones: {len(operations)}")
        print(f"   • Trades: {len(trade_ops)}")
        print(f"   • Análisis: {len(analysis_ops)}")
        
        if trade_ops:
            print(f"\n   📋 Últimas operaciones de trading:")
            for op in trade_ops[-3:]:
                data = op.get('data', {})
                symbol = data.get('symbol', 'N/A')
                action = op.get('type', 'N/A')
                timestamp = op.get('timestamp', 'N/A')
                print(f"      • {symbol} | {action} | {timestamp}")
    else:
        print("\n⚠️  No se encontró data/operations_log.json")
    
    # Resumen
    print("\n" + "="*70)
    print("📋 RESUMEN")
    print("="*70)
    
    if trades_file.exists() and len(trades) > 0:
        live_executed = [t for t in trades if t.get('mode') == 'LIVE' and t.get('status') in ['FILLED', 'executed', 'EXECUTED']]
        paper_executed = [t for t in trades if t.get('mode') == 'PAPER' and t.get('status') in ['FILLED', 'executed', 'EXECUTED']]
        
        if live_executed:
            print(f"\n✅ El bot SÍ realizó operaciones en modo LIVE:")
            print(f"   • {len(live_executed)} operaciones ejecutadas")
        elif paper_executed:
            print(f"\n🧪 El bot realizó operaciones en modo PAPER (simulación):")
            print(f"   • {len(paper_executed)} operaciones simuladas")
        else:
            print(f"\n⏸️  El bot no ha ejecutado operaciones aún")
            if pending_trades:
                print(f"   • {len(pending_trades)} operaciones pendientes")
            if failed_trades:
                print(f"   • {len(failed_trades)} operaciones fallidas")
    else:
        print("\n⏸️  El bot no ha realizado operaciones aún")
        print("   → Verifica que el bot esté corriendo")
        print("   → Verifica que los umbrales de compra/venta sean adecuados")
        print("   → Verifica que el Risk Manager no esté bloqueando operaciones")

if __name__ == "__main__":
    main()


"""
Verificar el saldo de IOL y compararlo con las operaciones realizadas
"""
import json
from pathlib import Path
from datetime import datetime
from src.connectors.iol_client import IOLClient

def main():
    print("="*70)
    print("💰 VERIFICACIÓN DE SALDO Y OPERACIONES")
    print("="*70)
    
    # Conectar a IOL y obtener saldo actual
    try:
        print("\n🔄 Conectando a IOL...")
        iol = IOLClient()
        current_balance = iol.get_available_balance()
        print(f"\n💵 SALDO ACTUAL EN IOL: ${current_balance:,.2f} ARS")
    except Exception as e:
        print(f"\n❌ Error obteniendo saldo de IOL: {e}")
        return
    
    # Cargar trades
    trades_file = Path("trades.json")
    if not trades_file.exists():
        print("\n⚠️  No se encontró trades.json")
        return
    
    with open(trades_file, 'r', encoding='utf-8') as f:
        trades = json.load(f)
    
    # Filtrar operaciones LIVE ejecutadas recientes (últimas 7 días)
    now = datetime.now()
    live_executed = []
    
    for trade in trades:
        if trade.get('mode') == 'LIVE' and trade.get('status') in ['FILLED', 'executed', 'EXECUTED']:
            try:
                timestamp_str = trade.get('timestamp', '')
                if timestamp_str:
                    trade_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    days_ago = (now - trade_date.replace(tzinfo=None)).days
                    if days_ago <= 7:  # Últimos 7 días
                        live_executed.append((trade, days_ago))
            except:
                pass
    
    print(f"\n📊 OPERACIONES LIVE EJECUTADAS (últimos 7 días): {len(live_executed)}")
    
    if live_executed:
        total_cost = 0
        print("\n📋 Detalle de operaciones:")
        for trade, days_ago in live_executed:
            symbol = trade.get('symbol', 'N/A')
            action = trade.get('signal') or trade.get('action', 'N/A')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            total = trade.get('total', quantity * price)
            timestamp = trade.get('timestamp', '')
            
            # Formatear timestamp
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            print(f"\n   • {symbol} | {action} | {quantity} @ ${price:.2f}")
            print(f"     Total: ${total:,.2f} ARS | Hace {days_ago} días")
            
            if action == 'BUY':
                total_cost += total
            elif action == 'SELL':
                total_cost -= total
        
        print(f"\n💰 IMPACTO EN SALDO:")
        print(f"   • Costo total de compras: ${total_cost:,.2f} ARS")
        print(f"   • Si estas operaciones se ejecutaron, el saldo debería haber cambiado")
    else:
        print("\n⚠️  No hay operaciones LIVE ejecutadas en los últimos 7 días")
    
    # Verificar órdenes pendientes
    pending_trades = [
        t for t in trades 
        if t.get('status') == 'PENDING' and t.get('mode') == 'LIVE'
    ]
    
    if pending_trades:
        print(f"\n⏳ ÓRDENES PENDIENTES: {len(pending_trades)}")
        pending_cost = 0
        for trade in pending_trades:
            symbol = trade.get('symbol', 'N/A')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            total = trade.get('total', quantity * price)
            order_id = trade.get('operation_id')
            timestamp = trade.get('timestamp', '')
            
            # Formatear timestamp
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    pass
            
            print(f"\n   • {symbol} | {quantity} @ ${price:.2f} | Total: ${total:,.2f}")
            print(f"     Order ID: {order_id} | Fecha: {timestamp}")
            pending_cost += total
        
        print(f"\n💰 Saldo bloqueado en órdenes pendientes: ${pending_cost:,.2f} ARS")
        print(f"   • Este saldo puede estar reservado pero no descontado aún")
    
    # Verificar historial de IOL
    try:
        print("\n🔄 Consultando historial de operaciones en IOL...")
        # Obtener operaciones recientes de IOL
        # Nota: Esto depende de si IOLClient tiene un método para obtener historial
        print("   💡 Revisa manualmente en IOL si las órdenes se ejecutaron")
    except Exception as e:
        print(f"   ⚠️  Error consultando historial: {e}")
    
    # Resumen y recomendaciones
    print("\n" + "="*70)
    print("📋 RESUMEN Y RECOMENDACIONES")
    print("="*70)
    
    print("\n💡 Posibles razones por las que el saldo no cambió:")
    print("   1. Las órdenes pendientes no se ejecutaron aún")
    print("   2. Las órdenes fueron canceladas")
    print("   3. El bot no está actualizando el saldo correctamente")
    print("   4. Las operaciones fueron hace tiempo y ya se reflejaron")
    
    print("\n🔧 Acciones recomendadas:")
    print("   1. Revisa tu cuenta de IOL para ver el estado de las órdenes")
    print("   2. Ejecuta /update_balance en Telegram para forzar actualización")
    print("   3. Verifica que el bot esté corriendo y actualizando cada hora")
    print("   4. Revisa los logs del bot para ver si hay errores")
    
    print(f"\n💰 Saldo actual reportado: ${current_balance:,.2f} ARS")
    print("   • Compara este valor con el que ves en tu cuenta de IOL")

if __name__ == "__main__":
    main()


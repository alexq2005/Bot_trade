"""
Verificar el estado de las órdenes pendientes en IOL
"""
import json
from pathlib import Path
from src.connectors.iol_client import IOLClient

def main():
    print("="*70)
    print("🔍 VERIFICACIÓN DE ÓRDENES PENDIENTES")
    print("="*70)
    
    # Cargar trades
    trades_file = Path("trades.json")
    if not trades_file.exists():
        print("\n⚠️  No se encontró trades.json")
        return
    
    with open(trades_file, 'r', encoding='utf-8') as f:
        trades = json.load(f)
    
    # Filtrar órdenes pendientes en LIVE
    pending_trades = [
        t for t in trades 
        if t.get('status') == 'PENDING' and t.get('mode') == 'LIVE'
    ]
    
    if not pending_trades:
        print("\n✅ No hay órdenes pendientes")
        return
    
    print(f"\n📋 ÓRDENES PENDIENTES: {len(pending_trades)}")
    
    # Conectar a IOL
    try:
        iol = IOLClient()
        print("\n🔄 Consultando estado en IOL...\n")
        
        for trade in pending_trades:
            order_id = trade.get('operation_id')
            symbol = trade.get('symbol')
            quantity = trade.get('quantity')
            price = trade.get('price')
            timestamp = trade.get('timestamp', '')
            
            print(f"📊 {symbol}")
            print(f"   • Order ID: {order_id}")
            print(f"   • Cantidad: {quantity}")
            print(f"   • Precio: ${price:.2f}")
            print(f"   • Fecha: {timestamp}")
            
            if order_id:
                try:
                    # Intentar obtener el estado de la orden desde IOL
                    # Nota: IOL puede tener un método para consultar órdenes
                    print(f"   • Estado en IOL: Consultando...")
                    # Aquí podrías agregar lógica para consultar el estado real
                    print(f"   💡 Revisa manualmente en IOL el estado de la orden {order_id}")
                except Exception as e:
                    print(f"   ⚠️  Error consultando orden: {e}")
            print()
        
        print("💡 Recomendación:")
        print("   • Revisa el estado de estas órdenes en tu cuenta de IOL")
        print("   • Si están ejecutadas, el bot las actualizará en el próximo ciclo")
        print("   • Si están canceladas, puedes eliminarlas manualmente del archivo trades.json")
        
    except Exception as e:
        print(f"\n❌ Error conectando a IOL: {e}")
        print("\n📋 Órdenes pendientes encontradas:")
        for trade in pending_trades:
            print(f"   • {trade.get('symbol')} - Order ID: {trade.get('operation_id')}")

if __name__ == "__main__":
    main()


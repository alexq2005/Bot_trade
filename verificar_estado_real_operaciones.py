"""
Verificar el estado real de las operaciones en IOL comparando con trades.json
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.connectors.iol_client import IOLClient

def main():
    print("="*70)
    print("🔍 VERIFICACIÓN DEL ESTADO REAL DE OPERACIONES EN IOL")
    print("="*70)
    
    # Conectar a IOL
    try:
        print("\n🔄 Conectando a IOL...")
        iol = IOLClient()
        current_balance = iol.get_available_balance()
        print(f"✅ Conectado a IOL")
        print(f"💰 Saldo actual: ${current_balance:,.2f} ARS\n")
    except Exception as e:
        print(f"❌ Error conectando a IOL: {e}")
        return
    
    # Obtener historial de operaciones de IOL (últimos 7 días)
    operations = []  # Inicializar antes del try
    try:
        print("📋 Consultando historial de operaciones en IOL (últimos 7 días)...")
        fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        fecha_desde = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        history = iol.get_operation_history(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)
        
        if history and 'operaciones' in history:
            operations = history['operaciones']
            print(f"✅ Encontradas {len(operations)} operaciones en IOL\n")
            
            # Mostrar operaciones recientes
            if operations:
                print("📊 OPERACIONES EN IOL (últimos 7 días):")
                for op in operations[:10]:  # Mostrar últimas 10
                    numero_operacion = op.get('numeroOperacion', 'N/A')
                    simbolo = op.get('simbolo', 'N/A')
                    cantidad = op.get('cantidad', 0)
                    precio = op.get('precio', 0)
                    fecha = op.get('fecha', 'N/A')
                    tipo = op.get('tipoOperacion', 'N/A')
                    estado = op.get('estado', 'N/A')
                    
                    print(f"\n   • {simbolo} | {tipo} | {cantidad} @ ${precio:.2f}")
                    print(f"     Operación #{numero_operacion} | Estado: {estado} | Fecha: {fecha}")
        else:
            print("⚠️  No se encontraron operaciones en el historial de IOL")
            print("   (Puede que no haya operaciones en los últimos 7 días)")
            operations = []
    except Exception as e:
        print(f"⚠️  Error obteniendo historial: {e}")
        operations = []
    
    # Comparar con trades.json
    print("\n" + "="*70)
    print("📊 COMPARACIÓN CON TRADES.JSON")
    print("="*70)
    
    trades_file = Path("trades.json")
    if not trades_file.exists():
        print("\n⚠️  No se encontró trades.json")
        return
    
    with open(trades_file, 'r', encoding='utf-8') as f:
        trades = json.load(f)
    
    # Filtrar operaciones LIVE
    live_trades = [t for t in trades if t.get('mode') == 'LIVE']
    
    print(f"\n📋 Trades en archivo: {len(live_trades)} operaciones LIVE")
    
    # Buscar coincidencias
    if operations:
        print("\n🔍 Buscando coincidencias entre trades.json e IOL...")
        
        for trade in live_trades:
            symbol = trade.get('symbol', '').replace('.BA', '')
            order_id = trade.get('order_id') or trade.get('operation_id')
            status = trade.get('status', '')
            timestamp = trade.get('timestamp', '')
            
            # Buscar en historial de IOL
            found = False
            for op in operations:
                op_symbol = op.get('simbolo', '').replace('.BA', '')
                op_num = op.get('numeroOperacion')
                
                if op_symbol == symbol and op_num == order_id:
                    found = True
                    op_status = op.get('estado', 'N/A')
                    print(f"\n   ✅ {symbol} - Order #{order_id}")
                    print(f"      En trades.json: {status}")
                    print(f"      En IOL: {op_status}")
                    if status != op_status:
                        print(f"      ⚠️  DISCREPANCIA: El estado no coincide")
                    break
            
            if not found and order_id:
                print(f"\n   ⚠️  {symbol} - Order #{order_id}")
                print(f"      En trades.json: {status}")
                print(f"      En IOL: NO ENCONTRADA")
                print(f"      💡 La orden puede haber sido cancelada o no existe")
    
    # Verificar operación específica de GGAL.BA
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN ESPECÍFICA: GGAL.BA")
    print("="*70)
    
    ggal_trades = [t for t in live_trades if 'GGAL' in t.get('symbol', '')]
    
    if ggal_trades:
        print(f"\n📋 Trades de GGAL.BA en archivo: {len(ggal_trades)}")
        
        for trade in ggal_trades:
            symbol = trade.get('symbol', 'N/A')
            order_id = trade.get('order_id') or trade.get('operation_id')
            status = trade.get('status', 'N/A')
            quantity = trade.get('quantity', 0)
            price = trade.get('price', 0)
            timestamp = trade.get('timestamp', 'N/A')
            
            print(f"\n   • {symbol} | {quantity} @ ${price:.2f}")
            print(f"     Order ID: {order_id} | Estado: {status}")
            print(f"     Fecha: {timestamp}")
            
            # Buscar en IOL
            if operations:
                found_in_iol = False
                for op in operations:
                    if op.get('numeroOperacion') == order_id:
                        found_in_iol = True
                        op_status = op.get('estado', 'N/A')
                        print(f"     ✅ Encontrada en IOL - Estado: {op_status}")
                        if status == 'FILLED' and op_status != 'FILLED':
                            print(f"     ⚠️  DISCREPANCIA: trades.json dice FILLED pero IOL dice {op_status}")
                        break
                
                if not found_in_iol:
                    print(f"     ⚠️  NO encontrada en historial de IOL")
                    print(f"     💡 Posibles razones:")
                    print(f"        - La orden fue cancelada")
                    print(f"        - La orden no se ejecutó realmente")
                    print(f"        - La orden es muy antigua (más de 7 días)")
    
    # Resumen y recomendaciones
    print("\n" + "="*70)
    print("📋 RESUMEN Y RECOMENDACIONES")
    print("="*70)
    
    print("\n💡 Si el saldo no cambió:")
    print("   1. Verifica en tu cuenta de IOL si la orden de GGAL.BA realmente se ejecutó")
    print("   2. Si la orden está cancelada, el saldo no debería cambiar")
    print("   3. Si la orden está pendiente, el saldo puede estar reservado pero no descontado")
    print("   4. Ejecuta /update_balance en Telegram para forzar actualización")
    
    print(f"\n💰 Saldo actual en IOL: ${current_balance:,.2f} ARS")
    print("   • Compara este valor con el que ves en tu cuenta web de IOL")

if __name__ == "__main__":
    main()


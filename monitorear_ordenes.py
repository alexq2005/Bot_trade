"""
Script para monitorear la ejecución de órdenes en tiempo real
Especialmente útil en modo LIVE TRADING
"""
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class OrderMonitor:
    """Monitor de ejecución de órdenes"""
    
    def __init__(self, trades_file: str = "trades.json", log_file: str = "data/operations_log.json"):
        self.trades_file = Path(trades_file)
        self.log_file = Path(log_file)
        self.last_trade_count = 0
        self.last_log_count = 0
        self.monitored_trades = []
        self.monitored_logs = []
        
    def load_trades(self) -> List[Dict]:
        """Carga trades desde trades.json"""
        if not self.trades_file.exists():
            return []
        
        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error cargando trades: {e}")
            return []
    
    def load_logs(self) -> List[Dict]:
        """Carga logs desde operations_log.json"""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error cargando logs: {e}")
            return []
    
    def get_new_trades(self) -> List[Dict]:
        """Retorna solo los trades nuevos"""
        trades = self.load_trades()
        if len(trades) > self.last_trade_count:
            new_trades = trades[self.last_trade_count:]
            self.last_trade_count = len(trades)
            return new_trades
        return []
    
    def get_new_logs(self) -> List[Dict]:
        """Retorna solo los logs nuevos relacionados con órdenes"""
        logs = self.load_logs()
        if len(logs) > self.last_log_count:
            new_logs = logs[self.last_log_count:]
            self.last_log_count = len(logs)
            
            # Filtrar solo logs relacionados con órdenes
            order_logs = [
                log for log in new_logs 
                if log.get('type') in ['TRADE', 'ORDER', 'EXECUTION'] or
                   'order' in log.get('type', '').lower() or
                   'trade' in log.get('type', '').lower()
            ]
            return order_logs
        return []
    
    def format_trade(self, trade: Dict) -> str:
        """Formatea un trade para mostrar"""
        symbol = trade.get('symbol', 'N/A')
        signal = trade.get('signal', 'N/A')
        price = trade.get('price', 0)
        quantity = trade.get('quantity', 0)
        status = trade.get('status', 'UNKNOWN')
        mode = trade.get('mode', 'UNKNOWN')
        timestamp = trade.get('timestamp', 'N/A')
        
        # Formatear timestamp
        if timestamp != 'N/A':
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # Emoji según status
        status_emoji = {
            'FILLED': '✅',
            'PENDING': '⏳',
            'FAILED': '❌',
            'CANCELLED': '🚫',
            'PARTIAL': '⚠️'
        }.get(status, '❓')
        
        # Emoji según modo
        mode_emoji = '💰' if mode == 'LIVE' else '🧪'
        
        result = f"""
{'='*70}
{status_emoji} {mode_emoji} NUEVA ORDEN EJECUTADA
{'='*70}
📊 Símbolo: {symbol}
📈 Señal: {signal}
💰 Precio: ${price:,.2f}
📦 Cantidad: {quantity}
📋 Estado: {status}
🕐 Timestamp: {timestamp}
"""
        
        # Agregar información adicional si está disponible
        if 'order_id' in trade:
            result += f"🆔 Order ID: {trade['order_id']}\n"
        
        if 'pnl' in trade and trade['pnl'] is not None:
            pnl = trade['pnl']
            pnl_pct = trade.get('pnl_pct', 0)
            pnl_emoji = '🟢' if pnl >= 0 else '🔴'
            result += f"{pnl_emoji} P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)\n"
        
        if 'error' in trade:
            result += f"❌ Error: {trade['error']}\n"
        
        if 'buy_price' in trade:
            result += f"📥 Precio de compra: ${trade['buy_price']:,.2f}\n"
        
        result += "="*70
        
        return result
    
    def format_log(self, log: Dict) -> str:
        """Formatea un log para mostrar"""
        log_type = log.get('type', 'UNKNOWN')
        timestamp = log.get('timestamp', 'N/A')
        data = log.get('data', {})
        
        # Formatear timestamp
        if timestamp != 'N/A':
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        result = f"""
{'='*70}
📝 LOG: {log_type}
{'='*70}
🕐 Timestamp: {timestamp}
"""
        
        # Agregar información del log según el tipo
        if 'symbol' in data:
            result += f"📊 Símbolo: {data['symbol']}\n"
        
        if 'message' in data:
            result += f"💬 Mensaje: {data['message']}\n"
        
        if 'status' in data:
            result += f"📋 Estado: {data['status']}\n"
        
        result += "="*70
        
        return result
    
    def monitor(self, interval: float = 2.0):
        """Monitorea ejecuciones de órdenes en tiempo real"""
        print("="*70)
        print("🔍 MONITOR DE EJECUCIÓN DE ÓRDENES")
        print("="*70)
        print(f"📁 Archivo de trades: {self.trades_file}")
        print(f"📁 Archivo de logs: {self.log_file}")
        print(f"⏱️  Intervalo de verificación: {interval} segundos")
        print("="*70)
        print("\n💡 Esperando nuevas órdenes...")
        print("   Presiona Ctrl+C para detener\n")
        
        # Inicializar contadores
        self.last_trade_count = len(self.load_trades())
        self.last_log_count = len(self.load_logs())
        
        try:
            while True:
                # Verificar nuevos trades
                new_trades = self.get_new_trades()
                for trade in new_trades:
                    print(self.format_trade(trade))
                    self.monitored_trades.append(trade)
                
                # Verificar nuevos logs relacionados con órdenes
                new_logs = self.get_new_logs()
                for log in new_logs:
                    # Solo mostrar logs importantes
                    if log.get('type') in ['TRADE', 'ORDER', 'EXECUTION']:
                        print(self.format_log(log))
                        self.monitored_logs.append(log)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n" + "="*70)
            print("🛑 Monitor detenido por el usuario")
            print("="*70)
            print(f"\n📊 Resumen:")
            print(f"   • Trades monitoreados: {len(self.monitored_trades)}")
            print(f"   • Logs monitoreados: {len(self.monitored_logs)}")
            print("="*70)
    
    def show_summary(self):
        """Muestra un resumen de todas las órdenes"""
        trades = self.load_trades()
        
        if not trades:
            print("⚠️  No hay trades registrados aún")
            return
        
        print("="*70)
        print("📊 RESUMEN DE ÓRDENES")
        print("="*70)
        
        # Filtrar solo trades LIVE
        live_trades = [t for t in trades if t.get('mode') == 'LIVE']
        
        if not live_trades:
            print("⚠️  No hay trades en modo LIVE")
            return
        
        print(f"\n💰 Total de órdenes LIVE: {len(live_trades)}")
        
        # Estadísticas
        filled = [t for t in live_trades if t.get('status') == 'FILLED']
        failed = [t for t in live_trades if t.get('status') == 'FAILED']
        pending = [t for t in live_trades if t.get('status') == 'PENDING']
        
        print(f"   ✅ Ejecutadas: {len(filled)}")
        print(f"   ❌ Fallidas: {len(failed)}")
        print(f"   ⏳ Pendientes: {len(pending)}")
        
        # P&L total
        total_pnl = sum(t.get('pnl', 0) for t in live_trades if t.get('pnl') is not None)
        if total_pnl != 0:
            pnl_emoji = '🟢' if total_pnl >= 0 else '🔴'
            print(f"\n{pnl_emoji} P&L Total: ${total_pnl:,.2f}")
        
        # Últimas 5 órdenes
        print(f"\n📋 Últimas 5 órdenes:")
        print("-"*70)
        for trade in live_trades[-5:]:
            symbol = trade.get('symbol', 'N/A')
            signal = trade.get('signal', 'N/A')
            status = trade.get('status', 'N/A')
            price = trade.get('price', 0)
            quantity = trade.get('quantity', 0)
            pnl = trade.get('pnl', None)
            
            status_emoji = '✅' if status == 'FILLED' else '❌' if status == 'FAILED' else '⏳'
            pnl_str = f" | P&L: ${pnl:,.2f}" if pnl is not None else ""
            
            print(f"{status_emoji} {symbol} {signal} | ${price:,.2f} x {quantity} | {status}{pnl_str}")
        
        print("="*70)

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de ejecución de órdenes')
    parser.add_argument('--interval', type=float, default=2.0, 
                       help='Intervalo de verificación en segundos (default: 2.0)')
    parser.add_argument('--summary', action='store_true',
                       help='Mostrar resumen y salir')
    args = parser.parse_args()
    
    monitor = OrderMonitor()
    
    if args.summary:
        monitor.show_summary()
    else:
        monitor.monitor(interval=args.interval)

if __name__ == "__main__":
    main()


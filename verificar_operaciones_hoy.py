"""
Verificar si el bot realizó operaciones HOY (30 de noviembre de 2025)
"""
import json
from pathlib import Path
from datetime import datetime

def main():
    print("="*70)
    print("🔍 VERIFICACIÓN DE OPERACIONES DE HOY")
    print("="*70)
    
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"\n📅 Fecha de hoy: {today}")
    
    # Verificar trades.json
    trades_file = Path("trades.json")
    today_trades = []
    
    if trades_file.exists():
        with open(trades_file, 'r', encoding='utf-8') as f:
            trades = json.load(f)
        
        # Filtrar trades de hoy
        for trade in trades:
            timestamp = trade.get('timestamp', '')
            if timestamp and timestamp.startswith(today):
                today_trades.append(trade)
        
        print(f"\n📊 TRADES DE HOY: {len(today_trades)}")
        
        if today_trades:
            print("\n📋 Detalle de trades de hoy:")
            for trade in today_trades:
                symbol = trade.get('symbol', 'N/A')
                action = trade.get('signal') or trade.get('action', 'N/A')
                quantity = trade.get('quantity', 0)
                price = trade.get('price', 0)
                status = trade.get('status', 'N/A')
                mode = trade.get('mode', 'N/A')
                timestamp = trade.get('timestamp', '')
                
                # Extraer hora
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hora = dt.strftime('%H:%M:%S')
                except:
                    hora = timestamp
                
                print(f"\n   • {symbol} | {action} | {quantity} @ ${price:.2f}")
                print(f"     Estado: {status} | Modo: {mode} | Hora: {hora}")
        else:
            print("\n⚠️  No hay trades registrados para hoy")
            print("   → El bot NO ha realizado operaciones hoy")
    
    # Verificar operations_log.json
    ops_file = Path("data/operations_log.json")
    today_operations = []
    today_analyses = []
    
    if ops_file.exists():
        with open(ops_file, 'r', encoding='utf-8') as f:
            operations = json.load(f)
        
        # Filtrar operaciones de hoy
        for op in operations:
            timestamp = op.get('timestamp', '')
            if timestamp and timestamp.startswith(today):
                today_operations.append(op)
                if op.get('type') == 'ANALYSIS':
                    today_analyses.append(op)
        
        print(f"\n📝 OPERACIONES EN LOG DE HOY: {len(today_operations)}")
        print(f"   • Análisis: {len(today_analyses)}")
        print(f"   • Trades: {len([o for o in today_operations if o.get('type') in ['TRADE', 'BUY', 'SELL']])}")
        
        if today_analyses:
            print(f"\n📊 Últimos análisis de hoy:")
            for op in today_analyses[-5:]:
                data = op.get('data', {})
                symbol = data.get('symbol', 'N/A')
                signal = data.get('final_signal', 'N/A')
                score = data.get('score', 0)
                timestamp = op.get('timestamp', '')
                
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    hora = dt.strftime('%H:%M:%S')
                except:
                    hora = timestamp
                
                print(f"   • {symbol} | {signal} | Score: {score} | {hora}")
    
    # Verificar si el bot está corriendo
    print("\n" + "="*70)
    print("🤖 ESTADO DEL BOT")
    print("="*70)
    
    pid_file = Path("bot.pid")
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Intentar usar psutil si está disponible
            try:
                import psutil
                if psutil.pid_exists(pid):
                    try:
                        process = psutil.Process(pid)
                        print(f"\n✅ Bot está corriendo (PID: {pid})")
                        print(f"   • Iniciado: {datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
                    except Exception as e:
                        print(f"\n⚠️  Bot PID existe pero no se puede acceder al proceso: {e}")
                else:
                    print(f"\n❌ Bot NO está corriendo (PID {pid} no existe)")
            except ImportError:
                # psutil no está instalado, usar método alternativo
                import subprocess
                import sys
                if sys.platform == 'win32':
                    # Windows: usar tasklist
                    result = subprocess.run(
                        ['tasklist', '/FI', f'PID eq {pid}'],
                        capture_output=True,
                        text=True
                    )
                    if str(pid) in result.stdout:
                        print(f"\n✅ Bot está corriendo (PID: {pid})")
                        print(f"   • Verificado con tasklist")
                    else:
                        print(f"\n❌ Bot NO está corriendo (PID {pid} no existe)")
                else:
                    # Linux/Mac: usar kill -0
                    import os
                    try:
                        os.kill(pid, 0)  # No mata, solo verifica
                        print(f"\n✅ Bot está corriendo (PID: {pid})")
                    except OSError:
                        print(f"\n❌ Bot NO está corriendo (PID {pid} no existe)")
        except Exception as e:
            print(f"\n⚠️  Error verificando PID: {e}")
    else:
        print("\n❌ Bot NO está corriendo (no se encontró bot.pid)")
    
    # Resumen
    print("\n" + "="*70)
    print("📋 RESUMEN")
    print("="*70)
    
    if today_trades:
        live_today = [t for t in today_trades if t.get('mode') == 'LIVE']
        paper_today = [t for t in today_trades if t.get('mode') == 'PAPER']
        
        if live_today:
            executed_today = [t for t in live_today if t.get('status') in ['FILLED', 'executed', 'EXECUTED']]
            print(f"\n✅ El bot SÍ operó HOY:")
            print(f"   • Operaciones LIVE: {len(live_today)}")
            print(f"   • Ejecutadas: {len(executed_today)}")
            if paper_today:
                print(f"   • Simuladas (Paper): {len(paper_today)}")
        elif paper_today:
            print(f"\n🧪 El bot operó HOY en modo Paper Trading:")
            print(f"   • Operaciones simuladas: {len(paper_today)}")
        else:
            print(f"\n⏸️  El bot NO operó HOY en modo LIVE")
    else:
        print(f"\n⏸️  El bot NO realizó operaciones HOY")
        print(f"   • Últimas operaciones fueron días anteriores")
        print(f"   • Verifica que el bot esté corriendo")
        print(f"   • Verifica que los umbrales permitan operar")
        print(f"   • Verifica que el Risk Manager no esté bloqueando")
    
    if today_analyses:
        print(f"\n📊 El bot SÍ realizó análisis HOY:")
        print(f"   • {len(today_analyses)} análisis completados")
        print(f"   → El bot está activo y analizando mercado")
    else:
        print(f"\n⚠️  El bot NO realizó análisis HOY")
        print(f"   → Puede que el bot no esté corriendo")
        print(f"   → O que no haya completado ningún ciclo de análisis")

if __name__ == "__main__":
    main()


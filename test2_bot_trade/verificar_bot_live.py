"""
Script para verificar el estado del bot en modo LIVE
"""
import json
import os
from pathlib import Path
from datetime import datetime

def verificar_estado_bot():
    """Verifica el estado completo del bot"""
    
    print("="*70)
    print("🔍 VERIFICACIÓN DEL BOT EN MODO LIVE")
    print("="*70)
    print()
    
    # 1. Verificar archivo PID
    pid_file = Path("bot.pid")
    if pid_file.exists():
        with open(pid_file, 'r') as f:
            pid = f.read().strip()
        print(f"✅ Bot corriendo (PID: {pid})")
        
        # Verificar si el proceso existe
        try:
            import psutil
            if psutil.pid_exists(int(pid)):
                process = psutil.Process(int(pid))
                print(f"   • Proceso activo desde: {datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   • Uso de CPU: {process.cpu_percent(interval=0.1):.1f}%")
                print(f"   • Uso de RAM: {process.memory_info().rss / 1024 / 1024:.1f} MB")
            else:
                print(f"   ⚠️  Proceso no encontrado (puede haber terminado)")
        except ImportError:
            print(f"   ℹ️  psutil no disponible, no se puede verificar el proceso")
        except Exception as e:
            print(f"   ⚠️  Error verificando proceso: {e}")
    else:
        print("❌ Bot NO está corriendo (no hay archivo bot.pid)")
    
    print()
    
    # 2. Verificar configuración
    config_file = Path("professional_config.json")
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("📋 CONFIGURACIÓN:")
        monitoring = config.get('monitoring', {})
        use_full_universe = monitoring.get('use_full_universe', False)
        max_symbols = monitoring.get('max_symbols', 200)
        categories = monitoring.get('universe_categories', [])
        
        print(f"   • Modo Universo Completo: {'✅ ACTIVO' if use_full_universe else '❌ INACTIVO'}")
        if use_full_universe:
            print(f"   • Máximo de símbolos: {max_symbols}")
            print(f"   • Categorías: {', '.join(categories)}")
        
        # Verificar modo desde múltiples fuentes
        paper_trading = config.get('paper_trading', True)
        # También verificar si hay una clave directa
        if 'paper_trading' not in config:
            # Intentar inferir desde otras configuraciones
            paper_trading = True  # Default seguro
        
        modo_texto = '🧪 PAPER TRADING' if paper_trading else '💰 LIVE TRADING'
        print(f"   • Modo configurado: {modo_texto}")
        print(f"   • Nota: El modo real se determina al iniciar el bot con --live o --paper")
        print(f"   • Intervalo de análisis: {config.get('analysis_interval_minutes', 60)} minutos")
    else:
        print("⚠️  No se encontró professional_config.json")
    
    print()
    
    # 3. Verificar símbolos cargados
    print("📊 SÍMBOLOS:")
    # Intentar leer desde el log o verificar en la base de datos
    try:
        from src.core.database import SessionLocal, init_db
        from src.models.market_data import MarketData
        
        init_db()
        db = SessionLocal()
        try:
            symbols = db.query(MarketData.symbol).distinct().all()
            symbols_list = [s[0] for s in symbols]
            
            if symbols_list:
                print(f"   • Símbolos en base de datos: {len(symbols_list)}")
                print(f"   • Primeros 10: {', '.join(symbols_list[:10])}")
                
                # Verificar cantidad de registros por símbolo
                print()
                print("   📈 Registros por símbolo:")
                for symbol in symbols_list[:5]:
                    count = db.query(MarketData).filter(MarketData.symbol == symbol).count()
                    status = "✅" if count >= 30 else "⚠️" if count >= 10 else "❌"
                    print(f"      {status} {symbol}: {count} registros")
            else:
                print("   ⚠️  No hay símbolos en la base de datos")
        finally:
            db.close()
    except Exception as e:
        print(f"   ⚠️  Error verificando símbolos: {e}")
    
    print()
    
    # 4. Verificar trades recientes
    trades_file = Path("data/trades.json")
    if trades_file.exists():
        try:
            with open(trades_file, 'r', encoding='utf-8') as f:
                trades = json.load(f)
            
            if trades:
                live_trades = [t for t in trades if t.get('mode') == 'LIVE']
                print(f"💰 TRADES:")
                print(f"   • Total de trades: {len(trades)}")
                print(f"   • Trades LIVE: {len(live_trades)}")
                
                if live_trades:
                    print(f"   • Último trade LIVE: {live_trades[-1].get('timestamp', 'N/A')}")
            else:
                print("💰 TRADES: No hay trades registrados")
        except Exception as e:
            print(f"   ⚠️  Error leyendo trades: {e}")
    else:
        print("💰 TRADES: No hay archivo de trades")
    
    print()
    
    # 5. Verificar conexión IOL
    print("🔌 CONEXIÓN IOL:")
    try:
        from src.connectors.iol_client import IOLClient
        iol = IOLClient()
        saldo = iol.get_available_balance()
        print(f"   ✅ Conectado a IOL")
        print(f"   • Saldo disponible: ${saldo:,.2f} ARS")
    except Exception as e:
        print(f"   ❌ Error conectando a IOL: {e}")
    
    print()
    print("="*70)
    print("✅ Verificación completada")
    print("="*70)

if __name__ == "__main__":
    verificar_estado_bot()


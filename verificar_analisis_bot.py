"""
Script para verificar si el bot está analizando activamente
"""
import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

def verificar_analisis():
    """Verifica si el bot está analizando activamente"""
    print("\n" + "="*70)
    print("🔍 VERIFICACIÓN DE ANÁLISIS DEL BOT")
    print("="*70)
    
    # 1. Verificar si el bot está corriendo
    print("\n1️⃣ ESTADO DEL PROCESO DEL BOT")
    print("-" * 70)
    pid_file = Path("bot.pid")
    bot_running = False
    
    # Intentar importar psutil primero
    try:
        import psutil
        psutil_available = True
    except ImportError:
        psutil_available = False
    
    if pid_file.exists():
        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            if psutil_available:
                try:
                    process = psutil.Process(pid)
                    if process.is_running():
                        bot_running = True
                        print(f"✅ Bot corriendo (PID: {pid})")
                        print(f"   Iniciado: {datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"   CPU: {process.cpu_percent(interval=0.1):.1f}%")
                        print(f"   Memoria: {process.memory_info().rss / 1024 / 1024:.1f} MB")
                    else:
                        print(f"❌ Proceso {pid} no está corriendo")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    print(f"⚠️  Proceso {pid} no existe o no se puede acceder")
            else:
                print(f"⚠️  psutil no disponible - No se puede verificar el proceso {pid}")
                print(f"   PID encontrado: {pid}")
        except Exception as e:
            print(f"⚠️  Error leyendo PID: {e}")
    else:
        print("❌ Archivo bot.pid no encontrado - Bot no está corriendo")
    
    # 2. Verificar logs recientes
    print("\n2️⃣ ACTIVIDAD EN LOGS")
    print("-" * 70)
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("trading_bot_*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)
            mod_time = datetime.fromtimestamp(latest_log.stat().st_mtime)
            time_diff = datetime.now() - mod_time
            
            print(f"📄 Último log: {latest_log.name}")
            print(f"   Modificado: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Hace: {time_diff}")
            
            # Leer últimas líneas del log
            try:
                with open(latest_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_lines = lines[-20:] if len(lines) > 20 else lines
                    
                    print(f"\n   📝 Últimas líneas del log:")
                    for line in last_lines[-5:]:
                        if line.strip():
                            print(f"      {line.strip()[:100]}")
                    
                    # Buscar indicadores de análisis
                    analysis_indicators = [
                        "Starting Analysis Cycle",
                        "Analyzing",
                        "AI Prediction",
                        "Technical Analysis",
                        "Sentiment Analysis"
                    ]
                    
                    found_indicators = []
                    for line in last_lines:
                        for indicator in analysis_indicators:
                            if indicator in line:
                                found_indicators.append(indicator)
                                break
                    
                    if found_indicators:
                        print(f"\n   ✅ Indicadores de análisis encontrados:")
                        for indicator in set(found_indicators):
                            print(f"      • {indicator}")
                    else:
                        print(f"\n   ⚠️  No se encontraron indicadores recientes de análisis")
                        
            except Exception as e:
                print(f"   ⚠️  Error leyendo log: {e}")
        else:
            print("❌ No se encontraron archivos de log")
    else:
        print("❌ Directorio de logs no existe")
    
    # 3. Verificar operations_log.json
    print("\n3️⃣ OPERACIONES REGISTRADAS")
    print("-" * 70)
    operations_file = Path("data/operations_log.json")
    if operations_file.exists():
        try:
            with open(operations_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
            
            if operations:
                print(f"✅ Total de operaciones: {len(operations)}")
                
                # Operaciones recientes (últimas 24 horas)
                cutoff = datetime.now() - timedelta(hours=24)
                recent_ops = []
                for op in operations:
                    try:
                        op_time = datetime.fromisoformat(op.get('timestamp', ''))
                        if op_time >= cutoff:
                            recent_ops.append(op)
                    except:
                        pass
                
                if recent_ops:
                    print(f"   📊 Operaciones en las últimas 24h: {len(recent_ops)}")
                    print(f"\n   📋 Últimas 3 operaciones:")
                    for op in recent_ops[-3:]:
                        symbol = op.get('symbol', 'N/A')
                        op_type = op.get('type', 'N/A')
                        timestamp = op.get('timestamp', 'N/A')
                        print(f"      • {symbol} - {op_type} - {timestamp}")
                else:
                    print(f"   ⚠️  No hay operaciones en las últimas 24 horas")
                
                # Última operación
                last_op = operations[-1]
                last_time = datetime.fromisoformat(last_op.get('timestamp', ''))
                time_diff = datetime.now() - last_time
                print(f"\n   🕐 Última operación: hace {time_diff}")
            else:
                print("⚠️  Archivo existe pero está vacío")
        except Exception as e:
            print(f"⚠️  Error leyendo operaciones: {e}")
    else:
        print("❌ Archivo operations_log.json no existe")
    
    # 4. Verificar trades.json
    print("\n4️⃣ TRADES EJECUTADOS")
    print("-" * 70)
    trades_file = Path("trades.json")
    if trades_file.exists():
        try:
            with open(trades_file, 'r', encoding='utf-8') as f:
                trades = json.load(f)
            
            if trades:
                print(f"✅ Total de trades: {len(trades)}")
                
                # Trades recientes
                cutoff = datetime.now() - timedelta(hours=24)
                recent_trades = []
                for trade in trades:
                    try:
                        trade_time = datetime.fromisoformat(trade.get('timestamp', ''))
                        if trade_time >= cutoff:
                            recent_trades.append(trade)
                    except:
                        pass
                
                if recent_trades:
                    print(f"   📊 Trades en las últimas 24h: {len(recent_trades)}")
                    print(f"\n   📋 Últimos 3 trades:")
                    for trade in recent_trades[-3:]:
                        symbol = trade.get('symbol', 'N/A')
                        signal = trade.get('signal', 'N/A')
                        mode = trade.get('mode', 'N/A')
                        timestamp = trade.get('timestamp', 'N/A')
                        print(f"      • {symbol} - {signal} ({mode}) - {timestamp}")
                else:
                    print(f"   ⚠️  No hay trades en las últimas 24 horas")
            else:
                print("⚠️  Archivo existe pero está vacío")
        except Exception as e:
            print(f"⚠️  Error leyendo trades: {e}")
    else:
        print("ℹ️  Archivo trades.json no existe (normal si no se han ejecutado trades)")
    
    # 5. Resumen y recomendaciones
    print("\n" + "="*70)
    print("📊 RESUMEN")
    print("="*70)
    
    if bot_running:
        print("✅ Bot está corriendo")
        
        # Verificar actividad reciente
        has_recent_activity = False
        if operations_file.exists():
            try:
                with open(operations_file, 'r', encoding='utf-8') as f:
                    ops = json.load(f)
                    if ops:
                        last_op_time = datetime.fromisoformat(ops[-1].get('timestamp', ''))
                        if (datetime.now() - last_op_time).total_seconds() < 3600:  # Última hora
                            has_recent_activity = True
            except:
                pass
        
        if has_recent_activity:
            print("✅ Hay actividad reciente - El bot está analizando")
        else:
            print("⚠️  No hay actividad reciente - Verifica los logs para más detalles")
            print("   💡 El bot puede estar esperando el siguiente ciclo de análisis")
    else:
        print("❌ Bot no está corriendo")
        print("   💡 Inicia el bot con: python run_bot.py --live")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    verificar_analisis()


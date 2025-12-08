"""
Script para visualizar el crecimiento del entrenamiento del bot
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import sqlite3

def get_trained_models() -> Dict[str, dict]:
    """Obtiene información de modelos entrenados"""
    models_dir = Path("models")
    trained = {}
    
    if not models_dir.exists():
        return trained
    
    # Buscar archivos de modelos
    for model_file in models_dir.glob("*.h5"):
        symbol = model_file.stem.replace("_model", "").replace("_predictor", "")
        trained[symbol] = {
            "model_file": str(model_file),
            "size_mb": model_file.stat().st_size / (1024 * 1024),
            "modified": datetime.fromtimestamp(model_file.stat().st_mtime),
            "has_scaler": (models_dir / f"{symbol}_scaler.pkl").exists()
        }
    
    return trained


def get_training_analytics() -> Dict[str, dict]:
    """Obtiene reportes de análisis de entrenamiento"""
    analytics_dir = Path("training_analytics")
    analytics = {}
    
    if not analytics_dir.exists():
        return analytics
    
    for report_file in analytics_dir.glob("*_analysis_report.json"):
        symbol = report_file.stem.replace("_analysis_report", "")
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                analytics[symbol] = {
                    "report_file": str(report_file),
                    "data_points": data.get("data_quality", {}).get("total_records", 0),
                    "training_date": data.get("training_info", {}).get("date", "N/A"),
                    "epochs": data.get("training_info", {}).get("epochs", 0),
                    "final_loss": data.get("training_history", {}).get("final_loss", "N/A"),
                    "mse": data.get("metrics", {}).get("mse", "N/A"),
                    "mae": data.get("metrics", {}).get("mae", "N/A")
                }
        except Exception as e:
            analytics[symbol] = {"error": str(e)}
    
    return analytics


def get_database_stats() -> Dict[str, int]:
    """Obtiene estadísticas de la base de datos"""
    db_file = Path("trading_bot.db")
    stats = {
        "total_symbols": 0,
        "total_records": 0,
        "symbols_with_data": []
    }
    
    if not db_file.exists():
        return stats
    
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        # Contar símbolos únicos
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM market_data")
        stats["total_symbols"] = cursor.fetchone()[0]
        
        # Contar registros totales
        cursor.execute("SELECT COUNT(*) FROM market_data")
        stats["total_records"] = cursor.fetchone()[0]
        
        # Símbolos con más datos
        cursor.execute("""
            SELECT symbol, COUNT(*) as count 
            FROM market_data 
            GROUP BY symbol 
            ORDER BY count DESC 
            LIMIT 20
        """)
        stats["symbols_with_data"] = [
            {"symbol": row[0], "records": row[1]} 
            for row in cursor.fetchall()
        ]
        
        conn.close()
    except Exception as e:
        stats["error"] = str(e)
    
    return stats


def get_operations_log_stats() -> Dict[str, any]:
    """Obtiene estadísticas del log de operaciones"""
    log_file = Path("data/operations_log.json")
    stats = {
        "total_analyses": 0,
        "symbols_analyzed": set(),
        "date_range": {"first": None, "last": None}
    }
    
    if not log_file.exists():
        return stats
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            operations = json.load(f)
        
        stats["total_analyses"] = len(operations)
        
        dates = []
        for op in operations:
            symbol = op.get("symbol", "UNKNOWN")
            stats["symbols_analyzed"].add(symbol)
            
            timestamp = op.get("timestamp", "")
            if timestamp:
                try:
                    dates.append(datetime.fromisoformat(timestamp.replace('Z', '+00:00')))
                except:
                    pass
        
        if dates:
            stats["date_range"]["first"] = min(dates)
            stats["date_range"]["last"] = max(dates)
        
        stats["symbols_analyzed"] = sorted(list(stats["symbols_analyzed"]))
    except Exception as e:
        stats["error"] = str(e)
    
    return stats


def get_learning_stats() -> Dict[str, any]:
    """Obtiene estadísticas del sistema de aprendizaje"""
    stats = {
        "auto_config_history": 0,
        "trade_history": 0,
        "insights_generated": 0
    }
    
    # Auto-config history
    auto_config_file = Path("data/auto_config_history.json")
    if auto_config_file.exists():
        try:
            with open(auto_config_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
                stats["auto_config_history"] = len(configs) if isinstance(configs, list) else 0
        except:
            pass
    
    # Trade history
    trade_history_file = Path("data/learning/trade_history.json")
    if trade_history_file.exists():
        try:
            with open(trade_history_file, 'r', encoding='utf-8') as f:
                trades = json.load(f)
                stats["trade_history"] = len(trades) if isinstance(trades, list) else 0
        except:
            pass
    
    # Insights
    insights_file = Path("data/learning/insights.json")
    if insights_file.exists():
        try:
            with open(insights_file, 'r', encoding='utf-8') as f:
                insights = json.load(f)
                stats["insights_generated"] = len(insights) if isinstance(insights, list) else 0
        except:
            pass
    
    return stats


def format_size(size_mb: float) -> str:
    """Formatea tamaño en MB"""
    if size_mb < 1:
        return f"{size_mb * 1024:.1f} KB"
    return f"{size_mb:.2f} MB"


def main():
    print("=" * 80)
    print("📈 CRECIMIENTO DEL ENTRENAMIENTO DEL BOT")
    print("=" * 80)
    print()
    
    # 1. Modelos entrenados
    print("🤖 1. MODELOS ENTRENADOS")
    print("-" * 80)
    trained_models = get_trained_models()
    
    if trained_models:
        print(f"✅ Total de modelos: {len(trained_models)}")
        print()
        print(f"{'Símbolo':<15} {'Tamaño':<12} {'Modificado':<20} {'Scaler':<10}")
        print("-" * 80)
        
        for symbol, info in sorted(trained_models.items()):
            size = format_size(info.get("size_mb", 0))
            modified = info.get("modified", datetime.now()).strftime("%Y-%m-%d %H:%M")
            has_scaler = "✅" if info.get("has_scaler") else "❌"
            print(f"{symbol:<15} {size:<12} {modified:<20} {has_scaler:<10}")
    else:
        print("❌ No hay modelos entrenados aún")
    print()
    
    # 2. Análisis de entrenamiento
    print("📊 2. REPORTES DE ANÁLISIS")
    print("-" * 80)
    analytics = get_training_analytics()
    
    if analytics:
        print(f"✅ Total de reportes: {len(analytics)}")
        print()
        print(f"{'Símbolo':<15} {'Datos':<10} {'Epochs':<10} {'MSE':<12} {'Fecha':<15}")
        print("-" * 80)
        
        for symbol, info in sorted(analytics.items()):
            if "error" in info:
                continue
            data_points = info.get("data_points", 0)
            epochs = info.get("epochs", 0)
            mse = info.get("mse", "N/A")
            if isinstance(mse, (int, float)):
                mse = f"{mse:.6f}"
            date = info.get("training_date", "N/A")
            if len(date) > 15:
                date = date[:15]
            print(f"{symbol:<15} {data_points:<10} {epochs:<10} {mse:<12} {date:<15}")
    else:
        print("❌ No hay reportes de análisis")
    print()
    
    # 3. Base de datos
    print("💾 3. BASE DE DATOS")
    print("-" * 80)
    db_stats = get_database_stats()
    
    if "error" not in db_stats:
        print(f"✅ Símbolos únicos: {db_stats['total_symbols']}")
        print(f"✅ Registros totales: {db_stats['total_records']:,}")
        
        if db_stats.get("symbols_with_data"):
            print()
            print("📈 Top 10 símbolos con más datos:")
            for i, item in enumerate(db_stats["symbols_with_data"][:10], 1):
                print(f"   {i:2}. {item['symbol']:<15} {item['records']:>8,} registros")
    else:
        print(f"❌ Error: {db_stats['error']}")
    print()
    
    # 4. Log de operaciones
    print("📝 4. ANÁLISIS REALIZADOS")
    print("-" * 80)
    op_stats = get_operations_log_stats()
    
    if "error" not in op_stats:
        print(f"✅ Total de análisis: {op_stats['total_analyses']:,}")
        print(f"✅ Símbolos analizados: {len(op_stats['symbols_analyzed'])}")
        
        if op_stats['date_range']['first']:
            first = op_stats['date_range']['first'].strftime("%Y-%m-%d %H:%M")
            last = op_stats['date_range']['last'].strftime("%Y-%m-%d %H:%M")
            print(f"✅ Rango de fechas: {first} → {last}")
        
        if op_stats['symbols_analyzed']:
            print()
            print("📋 Símbolos analizados:")
            symbols_list = op_stats['symbols_analyzed']
            # Mostrar en columnas
            for i in range(0, len(symbols_list), 5):
                chunk = symbols_list[i:i+5]
                print("   " + "  ".join(f"{s:<12}" for s in chunk))
    else:
        print(f"❌ Error: {op_stats.get('error', 'Desconocido')}")
    print()
    
    # 5. Sistema de aprendizaje
    print("🧠 5. SISTEMA DE APRENDIZAJE")
    print("-" * 80)
    learning_stats = get_learning_stats()
    
    print(f"✅ Ajustes de auto-configuración: {learning_stats['auto_config_history']}")
    print(f"✅ Trades aprendidos: {learning_stats['trade_history']}")
    print(f"✅ Insights generados: {learning_stats['insights_generated']}")
    print()
    
    # 6. Resumen general
    print("=" * 80)
    print("📊 RESUMEN GENERAL")
    print("=" * 80)
    
    total_models = len(trained_models)
    total_symbols_db = db_stats.get("total_symbols", 0)
    total_analyses = op_stats.get("total_analyses", 0)
    total_records = db_stats.get("total_records", 0)
    
    print(f"🤖 Modelos entrenados: {total_models}")
    print(f"💾 Símbolos en BD: {total_symbols_db}")
    print(f"📝 Análisis realizados: {total_analyses:,}")
    print(f"📊 Registros históricos: {total_records:,}")
    print()
    
    # Cálculo de crecimiento
    if total_models > 0:
        print("📈 CRECIMIENTO:")
        print(f"   • El bot tiene {total_models} modelo(s) entrenado(s)")
        if total_analyses > 0:
            analyses_per_model = total_analyses / total_models if total_models > 0 else 0
            print(f"   • Promedio de {analyses_per_model:.0f} análisis por modelo")
        if total_records > 0:
            records_per_symbol = total_records / total_symbols_db if total_symbols_db > 0 else 0
            print(f"   • Promedio de {records_per_symbol:.0f} registros por símbolo")
    
    print()
    print("=" * 80)
    print("💡 TIP: Ejecuta este script periódicamente para ver el crecimiento")
    print("=" * 80)


if __name__ == "__main__":
    main()


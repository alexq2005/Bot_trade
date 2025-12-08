"""
Monitor continuo del crecimiento del entrenamiento del bot
"""
import time
import json
from pathlib import Path
from datetime import datetime
from ver_crecimiento_entrenamiento import (
    get_trained_models,
    get_database_stats,
    get_operations_log_stats,
    get_learning_stats
)

def save_snapshot():
    """Guarda un snapshot del estado actual"""
    snapshot_dir = Path("data/training_snapshots")
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "models": len(get_trained_models()),
        "db_symbols": get_database_stats().get("total_symbols", 0),
        "db_records": get_database_stats().get("total_records", 0),
        "analyses": get_operations_log_stats().get("total_analyses", 0),
        "learning": get_learning_stats()
    }
    
    snapshot_file = snapshot_dir / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(snapshot_file, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2)
    
    return snapshot


def load_snapshots() -> list:
    """Carga todos los snapshots guardados"""
    snapshot_dir = Path("data/training_snapshots")
    if not snapshot_dir.exists():
        return []
    
    snapshots = []
    for snapshot_file in sorted(snapshot_dir.glob("snapshot_*.json")):
        try:
            with open(snapshot_file, 'r', encoding='utf-8') as f:
                snapshots.append(json.load(f))
        except:
            pass
    
    return snapshots


def show_growth_chart():
    """Muestra un gráfico de crecimiento simple"""
    snapshots = load_snapshots()
    
    if len(snapshots) < 2:
        print("📊 Necesitas al menos 2 snapshots para ver el crecimiento")
        print("   Ejecuta este script varias veces para generar snapshots")
        return
    
    print("=" * 80)
    print("📈 GRÁFICO DE CRECIMIENTO")
    print("=" * 80)
    print()
    
    # Modelos
    print("🤖 Modelos Entrenados:")
    models_values = [s["models"] for s in snapshots]
    max_models = max(models_values) if models_values else 1
    for i, value in enumerate(models_values):
        bar_length = int((value / max_models) * 50) if max_models > 0 else 0
        bar = "█" * bar_length
        timestamp = snapshots[i]["timestamp"][:16].replace("T", " ")
        print(f"   {timestamp} │{bar:<50}│ {value}")
    print()
    
    # Registros en BD
    print("💾 Registros en Base de Datos:")
    records_values = [s["db_records"] for s in snapshots]
    max_records = max(records_values) if records_values else 1
    for i, value in enumerate(records_values):
        bar_length = int((value / max_records) * 50) if max_records > 0 else 0
        bar = "█" * bar_length
        timestamp = snapshots[i]["timestamp"][:16].replace("T", " ")
        print(f"   {timestamp} │{bar:<50}│ {value:,}")
    print()
    
    # Análisis
    print("📝 Análisis Realizados:")
    analyses_values = [s["analyses"] for s in snapshots]
    max_analyses = max(analyses_values) if analyses_values else 1
    for i, value in enumerate(analyses_values):
        bar_length = int((value / max_analyses) * 50) if max_analyses > 0 else 0
        bar = "█" * bar_length
        timestamp = snapshots[i]["timestamp"][:16].replace("T", " ")
        print(f"   {timestamp} │{bar:<50}│ {value:,}")
    print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor del crecimiento del entrenamiento")
    parser.add_argument("--interval", type=int, default=0, help="Intervalo en segundos para monitoreo continuo (0 = una vez)")
    parser.add_argument("--snapshot", action="store_true", help="Guardar snapshot del estado actual")
    parser.add_argument("--chart", action="store_true", help="Mostrar gráfico de crecimiento")
    
    args = parser.parse_args()
    
    if args.chart:
        show_growth_chart()
        return
    
    if args.snapshot or args.interval > 0:
        snapshot = save_snapshot()
        print("=" * 80)
        print("📸 SNAPSHOT GUARDADO")
        print("=" * 80)
        print(f"⏰ Timestamp: {snapshot['timestamp']}")
        print(f"🤖 Modelos: {snapshot['models']}")
        print(f"💾 Símbolos en BD: {snapshot['db_symbols']}")
        print(f"📊 Registros: {snapshot['db_records']:,}")
        print(f"📝 Análisis: {snapshot['analyses']:,}")
        print("=" * 80)
        print()
    
    if args.interval > 0:
        print(f"🔄 Monitoreo continuo cada {args.interval} segundos")
        print("   Presiona Ctrl+C para detener")
        print()
        
        try:
            iteration = 0
            while True:
                iteration += 1
                print(f"\n{'='*80}")
                print(f"📊 ITERACIÓN #{iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*80)
                
                # Ejecutar ver_crecimiento_entrenamiento
                from ver_crecimiento_entrenamiento import main as show_growth
                show_growth()
                
                # Guardar snapshot
                snapshot = save_snapshot()
                print(f"📸 Snapshot #{iteration} guardado")
                
                print(f"\n⏳ Esperando {args.interval} segundos...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\n✅ Monitoreo detenido")
    else:
        # Mostrar estado actual
        from ver_crecimiento_entrenamiento import main as show_growth
        show_growth()
        
        if not args.snapshot:
            print("\n💡 TIP: Usa --snapshot para guardar el estado actual")
            print("💡 TIP: Usa --chart para ver el gráfico de crecimiento")
            print("💡 TIP: Usa --interval 3600 para monitoreo cada hora")


if __name__ == "__main__":
    main()


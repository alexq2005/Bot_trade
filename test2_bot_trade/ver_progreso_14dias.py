"""
Ver progreso del monitoreo de 14 días
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

print("="*70)
print("📊 PROGRESO DEL MONITOREO DE 14 DÍAS")
print("="*70)
print()

monitoring_file = Path("data/monitoring_14dias.json")

if not monitoring_file.exists():
    print("❌ No se encontró archivo de monitoreo")
    print("💡 Inicia el monitoreo con: iniciar_monitoreo_14dias.bat")
    exit(1)

# Cargar datos
with open(monitoring_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Calcular progreso
start_date = datetime.fromisoformat(data['start_date'])
end_date = datetime.fromisoformat(data['end_date'])
now = datetime.now()

days_elapsed = (now - start_date).days
days_total = 14
progress_pct = min((days_elapsed / days_total) * 100, 100)

print(f"📅 Inicio: {start_date.strftime('%Y-%m-%d %H:%M')}")
print(f"📅 Fin esperado: {end_date.strftime('%Y-%m-%d %H:%M')}")
print(f"⏱️  Días transcurridos: {days_elapsed}/{days_total}")
print(f"📊 Progreso: {progress_pct:.1f}%")
print()

# Barra de progreso
bar_length = 50
filled = int(bar_length * progress_pct / 100)
bar = '█' * filled + '░' * (bar_length - filled)
print(f"[{bar}] {progress_pct:.1f}%")
print()

# Estadísticas acumuladas
print("="*70)
print("📈 ESTADÍSTICAS ACUMULADAS")
print("="*70)
print()

daily_reports = data.get('daily_reports', [])

if daily_reports:
    total_trades = sum(d['trades']['total'] for d in daily_reports)
    total_pnl = sum(d['trades']['pnl'] for d in daily_reports)
    total_wins = sum(d['trades']['wins'] for d in daily_reports)
    total_losses = sum(d['trades']['losses'] for d in daily_reports)
    total_analyses = sum(d['analyses'] for d in daily_reports)
    
    win_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
    
    print(f"⚡ Total Trades: {total_trades}")
    print(f"📊 Total Análisis: {total_analyses}")
    print(f"💰 P&L Acumulado: ${total_pnl:,.2f}")
    print(f"✅ Win Rate: {win_rate:.1f}%")
    print(f"🎯 Ganadoras: {total_wins}")
    print(f"❌ Perdedoras: {total_losses}")
    print()
    
    # Comparar con baseline
    baseline = data.get('baseline_metrics', {})
    baseline_wr = baseline.get('win_rate', 50)
    
    improvement = win_rate - baseline_wr
    
    print(f"📊 MEJORA vs BASELINE:")
    print(f"  Win Rate: {baseline_wr}% → {win_rate:.1f}% ({improvement:+.1f}%)")
    print()
    
    if improvement >= 10:
        print("✅ EXCELENTE: Mejora >10% - Listo para producción!")
    elif improvement >= 5:
        print("⚠️  BIEN: Mejora moderada - Evaluar más")
    elif improvement >= 0:
        print("⚠️  LEVE: Mejora pequeña - Necesita más tiempo")
    else:
        print("❌ NEGATIVO: Performance peor que baseline")
    
    print()
    
    # Reportes diarios
    print("="*70)
    print("📋 REPORTES DIARIOS")
    print("="*70)
    print()
    
    for i, report in enumerate(daily_reports, 1):
        print(f"Día {i} ({report['date']}):")
        print(f"  Trades: {report['trades']['total']} | P&L: ${report['trades']['pnl']:,.2f} | Análisis: {report['analyses']}")
    
else:
    print("⚠️  Aún no hay reportes diarios")
    print("💡 El primer reporte se generará hoy a las 18:00")

print()
print("="*70)


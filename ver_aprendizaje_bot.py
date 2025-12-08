"""
Script para ver qué aprendió el bot
Muestra información de aprendizaje de símbolos, horarios, condiciones de mercado e insights
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

def cargar_json(archivo: Path) -> Dict:
    """Carga un archivo JSON, retorna {} si no existe o hay error"""
    if archivo.exists():
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Error cargando {archivo}: {e}")
            return {}
    return {}

def formatear_moneda(valor: float) -> str:
    """Formatea un valor como moneda"""
    if valor >= 0:
        return f"${valor:,.2f}"
    else:
        return f"-${abs(valor):,.2f}"

def mostrar_rendimiento_simbolos():
    """Muestra el rendimiento por símbolo"""
    archivo = Path("data/learning/symbol_performance.json")
    datos = cargar_json(archivo)
    
    if not datos:
        print("   ⚠️  No hay datos de rendimiento por símbolo aún")
        print("   💡 El bot aprenderá después de ejecutar operaciones")
        return
    
    print("\n" + "="*70)
    print("📊 RENDIMIENTO POR SÍMBOLO")
    print("="*70)
    
    # Ordenar por score (win rate + P&L)
    simbolos = []
    for symbol, stats in datos.items():
        total_trades = stats.get('total_trades', 0)
        if total_trades == 0:
            continue
        
        wins = stats.get('wins', 0)
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        total_pnl = stats.get('total_pnl', 0.0)
        avg_pnl = stats.get('avg_pnl', 0.0)
        best_trade = stats.get('best_trade', 0.0)
        worst_trade = stats.get('worst_trade', 0.0)
        
        score = (win_rate * 0.6) + (avg_pnl / 1000 * 0.4)
        
        simbolos.append({
            'symbol': symbol,
            'total_trades': total_trades,
            'wins': wins,
            'losses': stats.get('losses', 0),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'score': score
        })
    
    if not simbolos:
        print("   ⚠️  No hay símbolos con operaciones registradas")
        return
    
    # Ordenar por score
    simbolos.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\n📈 Mejores Símbolos (Top 10):")
    print("-" * 70)
    print(f"{'Símbolo':<10} {'Trades':<8} {'Win Rate':<12} {'P&L Total':<15} {'P&L Prom':<15} {'Mejor':<12} {'Peor':<12}")
    print("-" * 70)
    
    for s in simbolos[:10]:
        emoji = "🟢" if s['win_rate'] >= 60 else "🟡" if s['win_rate'] >= 40 else "🔴"
        print(f"{emoji} {s['symbol']:<8} {s['total_trades']:<8} {s['win_rate']:>6.1f}%     "
              f"{formatear_moneda(s['total_pnl']):<15} {formatear_moneda(s['avg_pnl']):<15} "
              f"{formatear_moneda(s['best_trade']):<12} {formatear_moneda(s['worst_trade']):<12}")
    
    # Mostrar estadísticas por señal
    print("\n📊 Estadísticas por Señal:")
    print("-" * 70)
    for s in simbolos[:5]:  # Top 5
        symbol_data = datos[s['symbol']]
        signals = symbol_data.get('signals', {})
        print(f"\n{s['symbol']}:")
        for signal_type, signal_stats in signals.items():
            wins = signal_stats.get('wins', 0)
            losses = signal_stats.get('losses', 0)
            total = wins + losses
            if total > 0:
                win_rate = (wins / total) * 100
                print(f"  {signal_type}: {wins}W / {losses}L ({win_rate:.1f}% win rate)")

def mostrar_rendimiento_horarios():
    """Muestra el rendimiento por horario"""
    archivo = Path("data/learning/time_performance.json")
    datos = cargar_json(archivo)
    
    if not datos:
        print("   ⚠️  No hay datos de rendimiento por horario aún")
        return
    
    print("\n" + "="*70)
    print("⏰ RENDIMIENTO POR HORARIO")
    print("="*70)
    
    # Filtrar solo horas (int) y días de semana (str)
    horas = []
    dias = []
    
    for key, stats in datos.items():
        if isinstance(key, int):  # Es una hora
            trades = stats.get('trades', 0)
            if trades >= 3:  # Al menos 3 trades
                wins = stats.get('wins', 0)
                win_rate = (wins / trades) * 100 if trades > 0 else 0
                total_pnl = stats.get('total_pnl', 0.0)
                avg_pnl = total_pnl / trades if trades > 0 else 0
                
                horas.append({
                    'hour': key,
                    'trades': trades,
                    'wins': wins,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'avg_pnl': avg_pnl
                })
        elif isinstance(key, str) and key not in ['trades', 'wins', 'total_pnl']:  # Es un día
            trades = stats.get('trades', 0)
            if trades >= 3:
                wins = stats.get('wins', 0)
                win_rate = (wins / trades) * 100 if trades > 0 else 0
                total_pnl = stats.get('total_pnl', 0.0)
                avg_pnl = total_pnl / trades if trades > 0 else 0
                
                dias.append({
                    'day': key,
                    'trades': trades,
                    'wins': wins,
                    'win_rate': win_rate,
                    'total_pnl': total_pnl,
                    'avg_pnl': avg_pnl
                })
    
    if horas:
        horas.sort(key=lambda x: x['win_rate'], reverse=True)
        print("\n🕐 Mejores Horas para Trading:")
        print("-" * 70)
        print(f"{'Hora':<8} {'Trades':<8} {'Win Rate':<12} {'P&L Total':<15} {'P&L Prom':<15}")
        print("-" * 70)
        
        for h in horas[:10]:
            emoji = "🟢" if h['win_rate'] >= 60 else "🟡" if h['win_rate'] >= 40 else "🔴"
            print(f"{emoji} {h['hour']:02d}:00   {h['trades']:<8} {h['win_rate']:>6.1f}%     "
                  f"{formatear_moneda(h['total_pnl']):<15} {formatear_moneda(h['avg_pnl']):<15}")
    
    if dias:
        # Traducir días al español
        dias_es = {
            'Monday': 'Lunes',
            'Tuesday': 'Martes',
            'Wednesday': 'Miércoles',
            'Thursday': 'Jueves',
            'Friday': 'Viernes',
            'Saturday': 'Sábado',
            'Sunday': 'Domingo'
        }
        
        dias.sort(key=lambda x: x['win_rate'], reverse=True)
        print("\n📅 Mejores Días de la Semana:")
        print("-" * 70)
        print(f"{'Día':<12} {'Trades':<8} {'Win Rate':<12} {'P&L Total':<15} {'P&L Prom':<15}")
        print("-" * 70)
        
        for d in dias:
            dia_nombre = dias_es.get(d['day'], d['day'])
            emoji = "🟢" if d['win_rate'] >= 60 else "🟡" if d['win_rate'] >= 40 else "🔴"
            print(f"{emoji} {dia_nombre:<10} {d['trades']:<8} {d['win_rate']:>6.1f}%     "
                  f"{formatear_moneda(d['total_pnl']):<15} {formatear_moneda(d['avg_pnl']):<15}")
    
    if not horas and not dias:
        print("   ⚠️  No hay suficientes datos de horarios (mínimo 3 trades por horario)")

def mostrar_condiciones_mercado():
    """Muestra el rendimiento por condiciones de mercado"""
    archivo = Path("data/learning/market_conditions.json")
    datos = cargar_json(archivo)
    
    if not datos:
        print("   ⚠️  No hay datos de condiciones de mercado aún")
        return
    
    print("\n" + "="*70)
    print("📊 RENDIMIENTO POR CONDICIONES DE MERCADO")
    print("="*70)
    
    condiciones = []
    for condition_key, stats in datos.items():
        trades = stats.get('trades', 0)
        if trades >= 3:  # Al menos 3 trades
            wins = stats.get('wins', 0)
            win_rate = (wins / trades) * 100 if trades > 0 else 0
            total_pnl = stats.get('total_pnl', 0.0)
            avg_pnl = total_pnl / trades if trades > 0 else 0
            
            condiciones.append({
                'condition': condition_key,
                'volatility': stats.get('volatility', 'N/A'),
                'trend': stats.get('trend', 'N/A'),
                'rsi_category': stats.get('rsi_category', 'N/A'),
                'trades': trades,
                'wins': wins,
                'win_rate': win_rate,
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl
            })
    
    if not condiciones:
        print("   ⚠️  No hay suficientes datos de condiciones (mínimo 3 trades por condición)")
        return
    
    condiciones.sort(key=lambda x: x['win_rate'], reverse=True)
    
    print("\n🎯 Mejores Condiciones de Mercado:")
    print("-" * 70)
    print(f"{'Condición':<30} {'Trades':<8} {'Win Rate':<12} {'P&L Total':<15} {'P&L Prom':<15}")
    print("-" * 70)
    
    for c in condiciones[:10]:
        emoji = "🟢" if c['win_rate'] >= 60 else "🟡" if c['win_rate'] >= 40 else "🔴"
        cond_str = f"{c['volatility']}_{c['trend']}_{c['rsi_category']}"
        print(f"{emoji} {cond_str:<28} {c['trades']:<8} {c['win_rate']:>6.1f}%     "
              f"{formatear_moneda(c['total_pnl']):<15} {formatear_moneda(c['avg_pnl']):<15}")

def mostrar_insights():
    """Muestra los insights generados"""
    archivo = Path("data/learning/insights.json")
    datos = cargar_json(archivo)
    
    if not datos:
        print("   ⚠️  No hay insights generados aún")
        print("   💡 Los insights se generan automáticamente cada 24 horas")
        return
    
    print("\n" + "="*70)
    print("💡 INSIGHTS Y RECOMENDACIONES")
    print("="*70)
    
    timestamp = datos.get('timestamp', 'N/A')
    if timestamp != 'N/A':
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            print(f"\n📅 Última actualización: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            print(f"\n📅 Última actualización: {timestamp}")
    
    recommendations = datos.get('recommendations', [])
    if recommendations:
        print("\n🎯 Recomendaciones:")
        print("-" * 70)
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    else:
        print("\n   ⚠️  No hay recomendaciones disponibles aún")
    
    # Mostrar mejores símbolos de insights
    best_symbols = datos.get('best_symbols', [])
    if best_symbols:
        print("\n✅ Mejores Símbolos (según insights):")
        print("-" * 70)
        for s in best_symbols[:5]:
            print(f"  • {s['symbol']}: Win Rate {s['win_rate']*100:.1f}%, "
                  f"P&L Promedio {formatear_moneda(s['avg_pnl'])}, "
                  f"{s['total_trades']} trades")
    
    # Mostrar peores símbolos
    worst_symbols = datos.get('worst_symbols', [])
    if worst_symbols:
        print("\n⚠️  Símbolos con Bajo Rendimiento:")
        print("-" * 70)
        for s in worst_symbols[:5]:
            print(f"  • {s['symbol']}: Win Rate {s['win_rate']*100:.1f}%, "
                  f"P&L Total {formatear_moneda(s['total_pnl'])}, "
                  f"{s['total_trades']} trades")

def mostrar_historial_trades():
    """Muestra el historial de trades para aprendizaje"""
    archivo = Path("data/learning/trade_history.json")
    datos = cargar_json(archivo)
    
    if not datos or not isinstance(datos, list):
        print("   ⚠️  No hay historial de trades aún")
        return
    
    print("\n" + "="*70)
    print("📝 HISTORIAL DE TRADES PARA APRENDIZAJE")
    print("="*70)
    
    total_trades = len(datos)
    completed = [t for t in datos if t.get('outcome') in ['win', 'loss']]
    pending = [t for t in datos if t.get('outcome') == 'pending']
    wins = [t for t in completed if t.get('outcome') == 'win']
    losses = [t for t in completed if t.get('outcome') == 'loss']
    
    print(f"\n📊 Resumen:")
    print(f"  • Total de trades registrados: {total_trades}")
    print(f"  • Trades completados: {len(completed)}")
    print(f"  • Trades pendientes: {len(pending)}")
    
    if completed:
        win_rate = (len(wins) / len(completed)) * 100 if len(completed) > 0 else 0
        total_pnl = sum(t.get('pnl', 0) for t in completed)
        avg_pnl = total_pnl / len(completed) if len(completed) > 0 else 0
        
        print(f"  • Win Rate: {win_rate:.1f}% ({len(wins)}W / {len(losses)}L)")
        print(f"  • P&L Total: {formatear_moneda(total_pnl)}")
        print(f"  • P&L Promedio: {formatear_moneda(avg_pnl)}")
    
    # Mostrar últimos 5 trades
    if datos:
        print(f"\n📋 Últimos 5 Trades:")
        print("-" * 70)
        print(f"{'Fecha':<12} {'Símbolo':<10} {'Señal':<6} {'P&L':<15} {'Estado':<10}")
        print("-" * 70)
        
        for trade in datos[-5:]:
            fecha = trade.get('timestamp', 'N/A')
            if fecha != 'N/A':
                try:
                    dt = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
                    fecha = dt.strftime('%Y-%m-%d')
                except:
                    pass
            
            symbol = trade.get('symbol', 'N/A')
            signal = trade.get('signal', 'N/A')
            pnl = trade.get('pnl', 0)
            outcome = trade.get('outcome', 'pending')
            
            emoji = "🟢" if outcome == 'win' else "🔴" if outcome == 'loss' else "🟡"
            estado = "Ganador" if outcome == 'win' else "Perdedor" if outcome == 'loss' else "Pendiente"
            
            print(f"{fecha:<12} {symbol:<10} {signal:<6} {formatear_moneda(pnl):<15} {emoji} {estado:<10}")

def mostrar_auto_configuracion():
    """Muestra el historial de auto-configuración"""
    archivo = Path("data/auto_config_history.json")
    datos = cargar_json(archivo)
    
    if not datos or not isinstance(datos, list):
        print("   ⚠️  No hay historial de auto-configuración aún")
        return
    
    print("\n" + "="*70)
    print("⚙️  AUTO-CONFIGURACIÓN - Ajustes Automáticos del Bot")
    print("="*70)
    
    print(f"\n📊 Total de ajustes realizados: {len(datos)}")
    
    # Mostrar últimos 3 ajustes
    if datos:
        print(f"\n📋 Últimos 3 Ajustes:")
        print("-" * 70)
        
        for i, ajuste in enumerate(datos[-3:], 1):
            timestamp = ajuste.get('timestamp', 'N/A')
            if timestamp != 'N/A':
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            performance = ajuste.get('performance', {})
            total_trades = performance.get('total_trades', 0)
            win_rate = performance.get('win_rate', 0) * 100
            total_pnl = performance.get('total_pnl', 0)
            
            print(f"\n{i}. {timestamp}")
            print(f"   📊 Performance: {total_trades} trades, Win Rate: {win_rate:.1f}%, P&L: {formatear_moneda(total_pnl)}")
            
            changes = ajuste.get('changes', [])
            if changes:
                print(f"   🔄 Cambios realizados:")
                for change in changes[:3]:  # Mostrar solo los primeros 3
                    print(f"      • {change}")

def main():
    """Función principal"""
    print("="*70)
    print("🧠 QUÉ APRENDIÓ EL BOT - Sistema de Aprendizaje Completo")
    print("="*70)
    print("\nEste reporte muestra todo lo que el bot ha aprendido de sus operaciones:")
    print("  • Rendimiento por símbolo")
    print("  • Mejores horarios para trading")
    print("  • Mejores condiciones de mercado")
    print("  • Historial de trades")
    print("  • Auto-configuración")
    print("  • Insights y recomendaciones")
    
    # Mostrar cada sección
    mostrar_historial_trades()
    mostrar_auto_configuracion()
    mostrar_rendimiento_simbolos()
    mostrar_rendimiento_horarios()
    mostrar_condiciones_mercado()
    mostrar_insights()
    
    print("\n" + "="*70)
    print("💡 NOTAS:")
    print("="*70)
    print("  • El bot aprende de cada operación que ejecuta")
    print("  • Los insights se generan automáticamente cada 24 horas")
    print("  • La auto-configuración ajusta parámetros basándose en el rendimiento")
    print("  • Más operaciones = más aprendizaje = mejores decisiones")
    print("  • Usa estos datos para optimizar tu estrategia de trading")
    print("="*70)

if __name__ == "__main__":
    main()


"""
Monitor Automático de 14 Días - Test Bot con Estrategias Avanzadas
Monitorea performance, estrategias, y genera reportes diarios
"""
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.services.telegram_bot import TelegramAlertBot

class Monitor14Dias:
    def __init__(self):
        self.telegram = TelegramAlertBot() if os.getenv('TELEGRAM_BOT_TOKEN') else None
        self.monitoring_file = Path("data/monitoring_14dias.json")
        self.monitoring_file.parent.mkdir(exist_ok=True)
        
        # Cargar monitoreo existente o inicializar nuevo
        if self.monitoring_file.exists():
            self._load_existing_monitoring()
        else:
            self.start_date = datetime.now()
            self.end_date = self.start_date + timedelta(days=14)
            self._init_monitoring_file()
            self._show_new_monitoring_info()
    
    def _load_existing_monitoring(self):
        """Carga monitoreo existente"""
        try:
            with open(self.monitoring_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.start_date = datetime.fromisoformat(data['start_date'])
            self.end_date = datetime.fromisoformat(data['end_date'])
            
            # Calcular días transcurridos
            days_elapsed = (datetime.now() - self.start_date).days
            days_remaining = (self.end_date - datetime.now()).days
            
            print("="*70)
            print("📊 MONITOR DE 14 DÍAS - CONTINUANDO MONITOREO EXISTENTE")
            print("="*70)
            print(f"📅 Inicio original: {self.start_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📅 Fin programado: {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"⏱️  Días transcurridos: {days_elapsed}")
            print(f"⏱️  Días restantes: {days_remaining}")
            print(f"📊 Reportes diarios: {len(data.get('daily_reports', []))}")
            print(f"💰 Trades totales: {data.get('total_trades', 0)}")
            print(f"📈 Análisis totales: {data.get('total_analyses', 0)}")
            print("="*70)
            print()
            
            # Verificar si el monitoreo ya terminó
            if datetime.now() > self.end_date:
                print("⚠️  El período de monitoreo ya terminó.")
                print(f"   Fecha fin: {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print("   Continuando con el monitoreo existente para completar reportes...")
                print()
            
        except Exception as e:
            print(f"⚠️  Error cargando monitoreo existente: {e}")
            print("   Inicializando nuevo monitoreo...")
            self.start_date = datetime.now()
            self.end_date = self.start_date + timedelta(days=14)
            self._init_monitoring_file()
            self._show_new_monitoring_info()
    
    def _show_new_monitoring_info(self):
        """Muestra información de nuevo monitoreo"""
        print("="*70)
        print("📊 MONITOR DE 14 DÍAS - TEST BOT CON ESTRATEGIAS AVANZADAS")
        print("="*70)
        print(f"Inicio: {self.start_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Fin: {self.end_date.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duración: 14 días")
        print("="*70)
        print()
        
        # Enviar mensaje de inicio
        if self.telegram:
            self.telegram.send_alert(f"""
🚀 *INICIO DE MONITOREO DE 14 DÍAS*

📅 Fecha inicio: {self.start_date.strftime('%Y-%m-%d %H:%M')}
📅 Fecha fin: {self.end_date.strftime('%Y-%m-%d %H:%M')}

🧬 *Estrategias Activas:* 13
🧪 *Modo:* Paper Trading
📊 *Objetivo:* Medir mejora en performance

*Métricas a evaluar:*
• Win Rate
• Retorno total
• Drawdown máximo
• Sharpe Ratio
• Scores promedio

El bot se monitoreará automáticamente y recibirás reportes diarios.

¡Vamos a ganar dinero! 💰
""")
    
    def _init_monitoring_file(self):
        """Inicializa archivo de monitoreo"""
        data = {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'daily_reports': [],
            'total_trades': 0,
            'total_analyses': 0,
            'initial_capital': 21891.65,
            'current_capital': 21891.65,
            'baseline_metrics': {
                'win_rate': 50.0,
                'monthly_return': 7.5,
                'max_drawdown': 12.5
            }
        }
        
        with open(self.monitoring_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def check_bot_status(self):
        """Verifica si el bot está corriendo"""
        pid_file = Path("bot.pid")
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Verificar si el proceso existe
                import psutil
                if psutil.pid_exists(pid):
                    return True, pid
            except:
                pass
        return False, None
    
    def collect_daily_stats(self):
        """Recopila estadísticas del día"""
        stats = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'trades': {'total': 0, 'buys': 0, 'sells': 0, 'wins': 0, 'losses': 0, 'pnl': 0},
            'analyses': 0,
            'strategies_used': {},
            'avg_score': 0,
            'signals': {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        }
        
        # Cargar trades del día
        if Path('trades.json').exists():
            try:
                with open('trades.json', 'r', encoding='utf-8') as f:
                    trades = json.load(f)
                
                today = datetime.now().date()
                today_trades = [
                    t for t in trades 
                    if datetime.fromisoformat(t['timestamp']).date() == today
                ]
                
                stats['trades']['total'] = len(today_trades)
                stats['trades']['buys'] = len([t for t in today_trades if t.get('signal') == 'BUY'])
                stats['trades']['sells'] = len([t for t in today_trades if t.get('signal') == 'SELL'])
                
                # Calcular P&L del día
                sells_with_pnl = [t for t in today_trades if t.get('signal') == 'SELL' and t.get('pnl')]
                stats['trades']['pnl'] = sum(t.get('pnl', 0) for t in sells_with_pnl)
                stats['trades']['wins'] = len([t for t in sells_with_pnl if t.get('pnl', 0) > 0])
                stats['trades']['losses'] = len([t for t in sells_with_pnl if t.get('pnl', 0) < 0])
                
            except Exception as e:
                print(f"⚠️  Error leyendo trades: {e}")
        
        # Cargar análisis del día
        if Path('data/operations_log.json').exists():
            try:
                with open('data/operations_log.json', 'r', encoding='utf-8') as f:
                    operations = json.load(f)
                
                today = datetime.now().date()
                today_ops = [
                    op for op in operations
                    if datetime.fromisoformat(op['timestamp']).date() == today
                ]
                
                analyses = [op for op in today_ops if op['type'] == 'ANALYSIS']
                stats['analyses'] = len(analyses)
                
                # Contar señales
                for analysis in analyses:
                    signal = analysis.get('data', {}).get('final_signal', 'HOLD')
                    stats['signals'][signal] = stats['signals'].get(signal, 0) + 1
                
                # Calcular score promedio
                scores = [op.get('data', {}).get('score', 0) for op in analyses]
                if scores:
                    stats['avg_score'] = sum(scores) / len(scores)
                
            except Exception as e:
                print(f"⚠️  Error leyendo operations: {e}")
        
        return stats
    
    def generate_daily_report(self):
        """Genera reporte diario"""
        stats = self.collect_daily_stats()
        
        # Cargar monitoreo
        with open(self.monitoring_file, 'r', encoding='utf-8') as f:
            monitoring_data = json.load(f)
        
        # Agregar estadísticas del día
        monitoring_data['daily_reports'].append(stats)
        monitoring_data['total_trades'] += stats['trades']['total']
        monitoring_data['total_analyses'] += stats['analyses']
        
        # Guardar
        with open(self.monitoring_file, 'w', encoding='utf-8') as f:
            json.dump(monitoring_data, f, indent=2)
        
        # Enviar reporte por Telegram
        self._send_daily_report(stats, len(monitoring_data['daily_reports']))
        
        return stats
    
    def _send_daily_report(self, stats, day_number):
        """Envía reporte diario por Telegram"""
        if not self.telegram:
            return
        
        trades = stats['trades']
        win_rate = (trades['wins'] / (trades['wins'] + trades['losses']) * 100) if (trades['wins'] + trades['losses']) > 0 else 0
        
        message = f"""
📊 *REPORTE DÍA {day_number}/14 - TEST BOT*

📅 *Fecha:* {stats['date']}

⚡ *Operaciones:*
• Total: {trades['total']}
• Compras: {trades['buys']}
• Ventas: {trades['sells']}
• Win Rate: {win_rate:.1f}%
• P&L del día: ${trades['pnl']:,.2f}

📊 *Análisis realizados:* {stats['analyses']}
📈 *Score promedio:* {stats['avg_score']:.1f}

🎯 *Señales generadas:*
• BUY: {stats['signals']['BUY']}
• SELL: {stats['signals']['SELL']}
• HOLD: {stats['signals']['HOLD']}

🧬 *13 Estrategias Activas*

Progreso: {day_number}/14 días
"""
        
        self.telegram.send_alert(message)
    
    def run_monitoring(self):
        """Ejecuta loop de monitoreo"""
        last_report_date = None
        
        print("🔄 Iniciando monitoreo continuo...")
        print()
        
        while datetime.now() < self.end_date:
            try:
                # Verificar estado del bot
                bot_running, pid = self.check_bot_status()
                
                current_time = datetime.now()
                current_date = current_time.date()
                
                # Generar reporte diario a las 18:00
                if current_time.hour == 18 and current_time.minute < 5:
                    if last_report_date != current_date:
                        print(f"\n📊 Generando reporte diario ({current_date})...")
                        self.generate_daily_report()
                        last_report_date = current_date
                        print("✅ Reporte enviado")
                
                # Mostrar estado cada hora
                if current_time.minute == 0:
                    status = "🟢 ACTIVO" if bot_running else "🔴 DETENIDO"
                    print(f"[{current_time.strftime('%Y-%m-%d %H:%M')}] Bot: {status}")
                    
                    if not bot_running:
                        if self.telegram:
                            self.telegram.send_alert(f"⚠️ *ALERTA*\n\nEl bot de test está DETENIDO.\nPID no encontrado.\n\nFecha: {current_time.strftime('%Y-%m-%d %H:%M')}")
                
                # Dormir 1 minuto
                time.sleep(60)
                
            except KeyboardInterrupt:
                print("\n⚠️  Monitoreo interrumpido por usuario")
                break
            except Exception as e:
                print(f"❌ Error en monitoreo: {e}")
                time.sleep(60)
        
        # Reporte final
        self._generate_final_report()
    
    def _generate_final_report(self):
        """Genera reporte final de 14 días"""
        print("\n" + "="*70)
        print("📊 REPORTE FINAL - 14 DÍAS DE MONITOREO")
        print("="*70)
        
        # Cargar datos
        with open(self.monitoring_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        daily_reports = data['daily_reports']
        
        # Calcular métricas totales
        total_trades = sum(d['trades']['total'] for d in daily_reports)
        total_pnl = sum(d['trades']['pnl'] for d in daily_reports)
        total_wins = sum(d['trades']['wins'] for d in daily_reports)
        total_losses = sum(d['trades']['losses'] for d in daily_reports)
        
        win_rate = (total_wins / (total_wins + total_losses) * 100) if (total_wins + total_losses) > 0 else 0
        
        # Retorno total
        initial = data['initial_capital']
        final = initial + total_pnl
        return_pct = ((final - initial) / initial) * 100
        
        print(f"\n📈 MÉTRICAS FINALES:")
        print(f"  Total Trades: {total_trades}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  P&L Total: ${total_pnl:,.2f}")
        print(f"  Retorno: {return_pct:+.2f}%")
        print(f"  Capital: ${initial:,.2f} → ${final:,.2f}")
        print()
        
        # Comparar con baseline
        baseline = data['baseline_metrics']
        win_rate_improvement = win_rate - baseline['win_rate']
        return_improvement = return_pct - baseline['monthly_return']
        
        print(f"📊 COMPARACIÓN CON BASELINE:")
        print(f"  Win Rate: {baseline['win_rate']}% → {win_rate:.1f}% ({win_rate_improvement:+.1f}%)")
        print(f"  Retorno: {baseline['monthly_return']}% → {return_pct:.1f}% ({return_improvement:+.1f}%)")
        print()
        
        # Decisión
        if win_rate_improvement >= 10 or return_improvement >= 5:
            print("✅ DECISIÓN: APLICAR A PRODUCCIÓN")
            print("   La mejora es significativa (>10% win rate o >5% retorno)")
            recommendation = "APLICAR"
        elif win_rate_improvement >= 5:
            print("⚠️  DECISIÓN: CONSIDERAR APLICACIÓN")
            print("   Hay mejora moderada, evaluar más")
            recommendation = "CONSIDERAR"
        else:
            print("❌ DECISIÓN: NO APLICAR")
            print("   La mejora no es suficiente (<5%)")
            recommendation = "NO_APLICAR"
        
        print("="*70)
        
        # Enviar reporte final por Telegram
        if self.telegram:
            message = f"""
🎉 *REPORTE FINAL - 14 DÍAS COMPLETADOS*

📊 *RESULTADOS:*
• Total Trades: {total_trades}
• Win Rate: {win_rate:.1f}%
• P&L Total: ${total_pnl:,.2f}
• Retorno: {return_pct:+.2f}%

📈 *MEJORA vs BASELINE:*
• Win Rate: {win_rate_improvement:+.1f}%
• Retorno: {return_improvement:+.1f}%

🎯 *DECISIÓN:* {recommendation}

{'✅ Listo para producción!' if recommendation == 'APLICAR' else '⚠️ Evaluar más' if recommendation == 'CONSIDERAR' else '❌ Necesita ajustes'}

🧬 13 Estrategias Avanzadas probadas
"""
            self.telegram.send_alert(message)

if __name__ == "__main__":
    monitor = Monitor14Dias()
    
    try:
        monitor.run_monitoring()
    except KeyboardInterrupt:
        print("\n⚠️  Monitoreo detenido por usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()


"""
Servicio de Reportes Diarios Automáticos
Genera y envía reportes diarios con estadísticas del bot
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from src.core.logger import get_logger

logger = get_logger("daily_report")


class DailyReportService:
    """Genera reportes diarios automáticos del bot"""
    
    def __init__(self, telegram_bot=None):
        self.telegram_bot = telegram_bot
        self.trades_file = Path("trades.json")
        self.operations_file = Path("data/operations_log.json")
        self.portfolio_file = Path("my_portfolio.json")
        self.reports_dir = Path("data/daily_reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_daily_report(self, date: Optional[datetime] = None) -> Dict:
        """
        Genera un reporte diario completo
        
        Args:
            date: Fecha del reporte (default: hoy)
        
        Returns:
            Dict con todas las estadísticas del día
        """
        if date is None:
            date = datetime.now()
        
        report_date = date.strftime("%Y-%m-%d")
        
        # Cargar datos
        trades = self._load_trades()
        operations = self._load_operations()
        portfolio = self._load_portfolio()
        
        # Filtrar datos del día
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_trades = [
            t for t in trades
            if day_start <= datetime.fromisoformat(t.get('timestamp', '')) < day_end
        ]
        
        day_operations = [
            op for op in operations
            if day_start <= datetime.fromisoformat(op.get('timestamp', '')) < day_end
        ]
        
        # Calcular estadísticas
        stats = {
            'date': report_date,
            'timestamp': datetime.now().isoformat(),
            'trades': {
                'total': len(day_trades),
                'buys': len([t for t in day_trades if t.get('signal') == 'BUY']),
                'sells': len([t for t in day_trades if t.get('signal') == 'SELL']),
                'total_volume': sum(t.get('quantity', 0) * t.get('price', 0) for t in day_trades),
                'pnl': sum(t.get('pnl', 0) for t in day_trades if t.get('pnl') is not None),
                'wins': len([t for t in day_trades if t.get('pnl', 0) > 0]),
                'losses': len([t for t in day_trades if t.get('pnl', 0) < 0]),
            },
            'operations': {
                'total': len(day_operations),
                'predictions': len([op for op in day_operations if op.get('type') == 'PREDICTION']),
                'analyses': len([op for op in day_operations if op.get('type') == 'ANALYSIS']),
                'trade_executions': len([op for op in day_operations if op.get('type') == 'TRADE_EXECUTION']),
            },
            'portfolio': {
                'total_value': sum(asset.get('total_val', 0) for asset in portfolio) if portfolio else 0,
                'positions': len(portfolio) if portfolio else 0,
            },
            'performance': self._calculate_performance(day_trades),
            'top_symbols': self._get_top_symbols(day_trades),
        }
        
        # Calcular win rate
        closed_trades = [t for t in day_trades if t.get('pnl') is not None]
        if closed_trades:
            stats['trades']['win_rate'] = (stats['trades']['wins'] / len(closed_trades)) * 100
        else:
            stats['trades']['win_rate'] = 0.0
        
        return stats
    
    def format_report_message(self, stats: Dict) -> str:
        """Formatea el reporte como mensaje de Telegram"""
        date = stats['date']
        trades = stats['trades']
        operations = stats['operations']
        portfolio = stats['portfolio']
        performance = stats['performance']
        
        # Emojis según rendimiento
        pnl_emoji = "📈" if trades['pnl'] > 0 else "📉" if trades['pnl'] < 0 else "➡️"
        win_rate_emoji = "🟢" if trades.get('win_rate', 0) >= 50 else "🟡" if trades.get('win_rate', 0) >= 30 else "🔴"
        
        message = f"""
📊 *REPORTE DIARIO - {date}*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 *OPERACIONES*
• Total: {trades['total']} operaciones
• Compras: {trades['buys']} | Ventas: {trades['sells']}
• Volumen: ${trades['total_volume']:,.2f}
• P&L: {pnl_emoji} ${trades['pnl']:,.2f}
• Win Rate: {win_rate_emoji} {trades.get('win_rate', 0):.1f}% ({trades['wins']}W / {trades['losses']}L)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🤖 *ACTIVIDAD DEL BOT*
• Análisis realizados: {operations['analyses']}
• Predicciones: {operations['predictions']}
• Trades ejecutados: {operations['trade_executions']}
• Total operaciones: {operations['total']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💼 *PORTFOLIO*
• Valor total: ${portfolio['total_value']:,.2f}
• Posiciones abiertas: {portfolio['positions']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 *RENDIMIENTO*
• Mejor trade: ${performance.get('best_trade', 0):,.2f}
• Peor trade: ${performance.get('worst_trade', 0):,.2f}
• Promedio por trade: ${performance.get('avg_trade', 0):,.2f}
"""
        
        # Agregar top símbolos si hay
        if stats.get('top_symbols'):
            message += "\n🏆 *TOP SÍMBOLOS*\n"
            for symbol, count in stats['top_symbols'][:5]:
                message += f"• {symbol}: {count} operaciones\n"
        
        message += f"\n⏰ Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    def save_report(self, stats: Dict) -> Path:
        """Guarda el reporte en un archivo JSON"""
        report_file = self.reports_dir / f"report_{stats['date']}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, default=str)
            logger.info(f"Reporte guardado: {report_file}")
            return report_file
        except Exception as e:
            logger.error(f"Error guardando reporte: {e}")
            raise
    
    def send_daily_report(self, date: Optional[datetime] = None) -> bool:
        """
        Genera y envía el reporte diario
        
        Returns:
            True si se envió correctamente
        """
        try:
            stats = self.generate_daily_report(date)
            message = self.format_report_message(stats)
            
            # Guardar reporte
            self.save_report(stats)
            
            # Enviar por Telegram si está disponible
            if self.telegram_bot:
                self.telegram_bot.send_alert(message)
                logger.info("Reporte diario enviado por Telegram")
            else:
                logger.info("Reporte diario generado (Telegram no disponible)")
                print(message)  # Fallback a consola
            
            return True
        except Exception as e:
            logger.error(f"Error generando/enviando reporte diario: {e}")
            return False
    
    def _load_trades(self) -> List[Dict]:
        """Carga trades desde trades.json"""
        if not self.trades_file.exists():
            return []
        
        try:
            with open(self.trades_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando trades: {e}")
            return []
    
    def _load_operations(self) -> List[Dict]:
        """Carga operaciones desde operations_log.json"""
        if not self.operations_file.exists():
            return []
        
        try:
            with open(self.operations_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando operaciones: {e}")
            return []
    
    def _load_portfolio(self) -> List[Dict]:
        """Carga portfolio desde my_portfolio.json"""
        if not self.portfolio_file.exists():
            return []
        
        try:
            with open(self.portfolio_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Si es un dict con clave 'portfolio', devolver la lista
                if isinstance(data, dict) and 'portfolio' in data:
                    return data['portfolio']
                # Si es una lista directa (formato antiguo), devolverla
                elif isinstance(data, list):
                    return data
                # Si no, devolver lista vacía o lo que sea que se pueda interpretar
                return []
        except Exception as e:
            logger.error(f"Error cargando portfolio: {e}")
            return []
    
    def _calculate_performance(self, trades: List[Dict]) -> Dict:
        """Calcula métricas de rendimiento"""
        closed_trades = [t for t in trades if t.get('pnl') is not None]
        
        if not closed_trades:
            return {
                'best_trade': 0,
                'worst_trade': 0,
                'avg_trade': 0,
            }
        
        pnls = [t.get('pnl', 0) for t in closed_trades]
        
        return {
            'best_trade': max(pnls) if pnls else 0,
            'worst_trade': min(pnls) if pnls else 0,
            'avg_trade': sum(pnls) / len(pnls) if pnls else 0,
        }
    
    def _get_top_symbols(self, trades: List[Dict]) -> List[tuple]:
        """Obtiene los símbolos más operados"""
        symbol_counts = {}
        for trade in trades:
            symbol = trade.get('symbol', 'UNKNOWN')
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        return sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)
    
    def get_recent_reports(self, days: int = 7) -> List[Dict]:
        """Obtiene reportes recientes"""
        reports = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            report_file = self.reports_dir / f"report_{date.strftime('%Y-%m-%d')}.json"
            
            if report_file.exists():
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        reports.append(json.load(f))
                except Exception as e:
                    logger.error(f"Error cargando reporte {report_file}: {e}")
        
        return reports


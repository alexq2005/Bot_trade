"""
MEJORA #8: Sistema de Alertas Inteligentes
Genera alertas proactivas sobre oportunidades, cambios de mercado y recomendaciones
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from src.core.logger import get_logger
from src.services.telegram_bot import TelegramAlertBot
from src.services.enhanced_learning_system import EnhancedLearningSystem

logger = get_logger("smart_alert_system")


class SmartAlertSystem:
    """MEJORA #8: Sistema de alertas inteligentes para oportunidades y cambios"""
    
    def __init__(self):
        self.telegram_bot = TelegramAlertBot()
        self.learning_system = EnhancedLearningSystem()
        self.operations_log_file = Path("data/operations_log.json")
        self.alert_history_file = Path("data/alert_history.json")
        self.alert_history_file.parent.mkdir(parents=True, exist_ok=True)
        self.last_alert_times = {}  # Para evitar spam
        self.alert_cooldowns = {
            'opportunity': 3600,  # 1 hora
            'market_change': 7200,  # 2 horas
            'recommendation': 1800,  # 30 minutos
            'performance': 14400  # 4 horas
        }
    
    def _load_alert_history(self) -> List[Dict]:
        """Carga historial de alertas"""
        if self.alert_history_file.exists():
            try:
                with open(self.alert_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_alert(self, alert: Dict):
        """Guarda alerta en historial"""
        history = self._load_alert_history()
        history.append(alert)
        
        # Mantener solo últimos 500 alertas
        if len(history) > 500:
            history = history[-500:]
        
        try:
            with open(self.alert_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando alerta: {e}")
    
    def _should_send_alert(self, alert_type: str) -> bool:
        """Verifica si debe enviar alerta (evita spam)"""
        now = datetime.now()
        last_time = self.last_alert_times.get(alert_type)
        
        if last_time:
            cooldown = self.alert_cooldowns.get(alert_type, 3600)
            if (now - last_time).total_seconds() < cooldown:
                return False
        
        self.last_alert_times[alert_type] = now
        return True
    
    def check_opportunities(self) -> List[Dict]:
        """MEJORA #8: Detecta oportunidades de trading actuales"""
        if not self.operations_log_file.exists():
            return []
        
        try:
            with open(self.operations_log_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo operations_log.json: {e}")
            return []
        
        # Analizar últimas 50 operaciones
        recent_analyses = [op for op in operations if op.get('type') == 'ANALYSIS'][-50:]
        
        opportunities = []
        
        # Agrupar por símbolo y encontrar los mejores
        symbol_scores = {}
        for analysis in recent_analyses:
            data = analysis.get('data', {})
            symbol = data.get('symbol')
            score = data.get('score', 0)
            signal = data.get('final_signal', 'HOLD')
            timestamp = analysis.get('timestamp')
            
            if not symbol or signal != 'BUY':
                continue
            
            if symbol not in symbol_scores:
                symbol_scores[symbol] = {
                    'scores': [],
                    'signals': 0,
                    'latest_timestamp': timestamp
                }
            
            symbol_scores[symbol]['scores'].append(score)
            symbol_scores[symbol]['signals'] += 1
            if timestamp > symbol_scores[symbol]['latest_timestamp']:
                symbol_scores[symbol]['latest_timestamp'] = timestamp
        
        # Identificar oportunidades (score alto y múltiples señales BUY)
        for symbol, stats in symbol_scores.items():
            if len(stats['scores']) >= 2:  # Al menos 2 señales BUY
                avg_score = sum(stats['scores']) / len(stats['scores'])
                if avg_score > 30:  # Score promedio alto
                    opportunities.append({
                        'symbol': symbol,
                        'avg_score': avg_score,
                        'buy_signals': stats['signals'],
                        'latest_timestamp': stats['latest_timestamp'],
                        'priority': 'high' if avg_score > 40 else 'medium'
                    })
        
        # Ordenar por prioridad y score
        opportunities.sort(key=lambda x: (x['priority'] == 'high', x['avg_score']), reverse=True)
        
        return opportunities[:5]  # Top 5
    
    def check_market_changes(self) -> List[Dict]:
        """MEJORA #8: Detecta cambios significativos en condiciones de mercado"""
        market_learning = self.learning_system.market_learning
        current_condition = market_learning.get_current_market_condition()
        
        changes = []
        
        if current_condition.get('status') == 'detected':
            volatility = current_condition.get('volatility')
            trend = current_condition.get('trend')
            buy_ratio = current_condition.get('buy_ratio', 0)
            
            # Detectar cambios significativos
            if volatility == 'HIGH' and buy_ratio > 0.20:
                changes.append({
                    'type': 'high_volatility_opportunity',
                    'message': f"⚠️ Alta volatilidad detectada con {buy_ratio*100:.1f}% señales BUY - Oportunidades activas",
                    'priority': 'high',
                    'data': current_condition
                })
            
            if trend == 'BULLISH' and buy_ratio > 0.15:
                changes.append({
                    'type': 'bullish_trend',
                    'message': f"📈 Tendencia alcista detectada con {buy_ratio*100:.1f}% señales BUY",
                    'priority': 'medium',
                    'data': current_condition
                })
            
            if trend == 'BEARISH' and buy_ratio < 0.05:
                changes.append({
                    'type': 'bearish_trend',
                    'message': f"📉 Tendencia bajista detectada - Ser más conservador",
                    'priority': 'medium',
                    'data': current_condition
                })
        
        return changes
    
    def check_recommendations(self) -> List[Dict]:
        """MEJORA #8: Obtiene recomendaciones proactivas del sistema de aprendizaje"""
        insights = self.learning_system.generate_insights()
        
        recommendations = []
        
        # Recomendaciones de oportunidades
        proactive_recs = insights.get('proactive_recommendations', [])
        for rec in proactive_recs:
            if rec.get('priority') == 'high':
                recommendations.append({
                    'type': 'proactive_recommendation',
                    'message': rec.get('message', ''),
                    'priority': 'high',
                    'action': rec.get('action', ''),
                    'data': rec
                })
        
        # Recomendaciones de estrategias
        top_strategies = insights.get('top_strategies', [])
        if top_strategies:
            recommendations.append({
                'type': 'strategy_recommendation',
                'message': f"✅ Mejores estrategias detectadas: {', '.join(top_strategies[:3])}",
                'priority': 'medium',
                'action': 'increase_strategy_weights',
                'data': {'strategies': top_strategies}
            })
        
        return recommendations
    
    def generate_smart_alerts(self) -> List[Dict]:
        """MEJORA #8: Genera todas las alertas inteligentes"""
        all_alerts = []
        
        # 1. Oportunidades
        if self._should_send_alert('opportunity'):
            opportunities = self.check_opportunities()
            for opp in opportunities:
                alert = {
                    'type': 'opportunity',
                    'timestamp': datetime.now().isoformat(),
                    'symbol': opp['symbol'],
                    'message': f"🚀 Oportunidad detectada: {opp['symbol']} tiene score promedio {opp['avg_score']:.1f} y {opp['buy_signals']} señales BUY recientes",
                    'priority': opp['priority'],
                    'data': opp
                }
                all_alerts.append(alert)
        
        # 2. Cambios de mercado
        if self._should_send_alert('market_change'):
            market_changes = self.check_market_changes()
            for change in market_changes:
                alert = {
                    'type': 'market_change',
                    'timestamp': datetime.now().isoformat(),
                    'message': change['message'],
                    'priority': change['priority'],
                    'data': change['data']
                }
                all_alerts.append(alert)
        
        # 3. Recomendaciones
        if self._should_send_alert('recommendation'):
            recommendations = self.check_recommendations()
            for rec in recommendations:
                alert = {
                    'type': 'recommendation',
                    'timestamp': datetime.now().isoformat(),
                    'message': rec['message'],
                    'priority': rec['priority'],
                    'action': rec.get('action', ''),
                    'data': rec.get('data', {})
                }
                all_alerts.append(alert)
        
        return all_alerts
    
    def send_alerts(self, alerts: List[Dict] = None) -> int:
        """Envía alertas por Telegram"""
        if alerts is None:
            alerts = self.generate_smart_alerts()
        
        sent_count = 0
        
        for alert in alerts:
            try:
                message = alert.get('message', '')
                if message:
                    self.telegram_bot.send_alert(message)
                    self._save_alert(alert)
                    sent_count += 1
                    logger.info(f"✅ Alerta enviada: {alert.get('type', 'unknown')}")
            except Exception as e:
                logger.error(f"Error enviando alerta: {e}")
        
        return sent_count
    
    def get_alert_summary(self) -> Dict:
        """Obtiene resumen de alertas recientes"""
        history = self._load_alert_history()
        recent_alerts = history[-20:] if len(history) > 20 else history
        
        summary = {
            'total_alerts': len(history),
            'recent_alerts': len(recent_alerts),
            'by_type': {},
            'by_priority': {'high': 0, 'medium': 0, 'low': 0}
        }
        
        for alert in recent_alerts:
            alert_type = alert.get('type', 'unknown')
            summary['by_type'][alert_type] = summary['by_type'].get(alert_type, 0) + 1
            
            priority = alert.get('priority', 'low')
            summary['by_priority'][priority] = summary['by_priority'].get(priority, 0) + 1
        
        return summary


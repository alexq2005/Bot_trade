"""
Análisis de Sentimiento Mejorado
Integración con noticias financieras y redes sociales
"""
import os
import re
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

from src.core.logger import get_logger
from src.core.config_manager import get_config
from src.services.news_fetcher import NewsFetcher

logger = get_logger("enhanced_sentiment")


class EnhancedSentimentAnalysis:
    """Análisis de sentimiento mejorado con múltiples fuentes"""
    
    def __init__(self):
        self.news_cache = {}
        self.sentiment_history = []
        self.sentiment_file = Path("data/sentiment_history.json")
        self.sentiment_file.parent.mkdir(parents=True, exist_ok=True)
        self.news_fetcher = NewsFetcher()  # Servicio para obtener noticias automáticamente
    
    def analyze_news_sentiment(self, symbol: str, news_text: str) -> Dict:
        """
        Analiza sentimiento de noticias
        
        Args:
            symbol: Símbolo a analizar
            news_text: Texto de la noticia
        """
        # Análisis básico de palabras clave
        positive_words = ['ganancia', 'crecimiento', 'sube', 'aumenta', 'mejora', 
                         'éxito', 'fuerte', 'positivo', 'bullish', 'rally']
        negative_words = ['pérdida', 'cae', 'baja', 'débil', 'negativo', 
                         'bearish', 'caída', 'recesión', 'crisis']
        
        text_lower = news_text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calcular score
        total_words = len(news_text.split())
        if total_words > 0:
            positive_score = positive_count / total_words
            negative_score = negative_count / total_words
            sentiment_score = positive_score - negative_score
        else:
            sentiment_score = 0
        
        # Clasificar
        if sentiment_score > 0.1:
            sentiment = 'POSITIVE'
        elif sentiment_score < -0.1:
            sentiment = 'NEGATIVE'
        else:
            sentiment = 'NEUTRAL'
        
        result = {
            'symbol': symbol,
            'sentiment': sentiment,
            'score': sentiment_score,
            'positive_words': positive_count,
            'negative_words': negative_count,
            'timestamp': datetime.now().isoformat(),
        }
        
        self.sentiment_history.append(result)
        self._save_history()
        
        return result
    
    def get_market_sentiment(self, symbol: str, auto_fetch_news: bool = True) -> Dict:
        """
        Obtiene sentimiento general del mercado para un símbolo.
        
        Args:
            symbol: Símbolo a analizar
            auto_fetch_news: Si True, obtiene noticias automáticamente si no hay datos recientes
        """
        # Filtrar sentimientos recientes para este símbolo
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_sentiments = [
            s for s in self.sentiment_history
            if s['symbol'] == symbol and
            datetime.fromisoformat(s['timestamp']) >= recent_cutoff
        ]
        
        # Si no hay sentimientos recientes y auto_fetch está activado, obtener noticias
        if not recent_sentiments and auto_fetch_news:
            logger.info(f"No hay sentimientos recientes para {symbol}, obteniendo noticias automáticamente...")
            self.fetch_and_analyze_news(symbol, days=7, max_news=10)
            
            # Re-filtrar después de obtener noticias
            recent_sentiments = [
                s for s in self.sentiment_history
                if s['symbol'] == symbol and
                datetime.fromisoformat(s['timestamp']) >= recent_cutoff
            ]
        
        if not recent_sentiments:
            return {
                'symbol': symbol,
                'overall_sentiment': 'NEUTRAL',
                'score': 0.0,
                'sample_size': 0,
            }
        
        # Calcular promedio
        avg_score = np.mean([s['score'] for s in recent_sentiments])
        
        if avg_score > 0.1:
            overall = 'POSITIVE'
        elif avg_score < -0.1:
            overall = 'NEGATIVE'
        else:
            overall = 'NEUTRAL'
        
        return {
            'symbol': symbol,
            'overall_sentiment': overall,
            'score': avg_score,
            'sample_size': len(recent_sentiments),
            'positive_count': sum(1 for s in recent_sentiments if s['sentiment'] == 'POSITIVE'),
            'negative_count': sum(1 for s in recent_sentiments if s['sentiment'] == 'NEGATIVE'),
        }
    
    def fetch_and_analyze_news(self, symbol: str, days: int = 7, max_news: int = 10) -> int:
        """
        Obtiene noticias automáticamente y las analiza.
        
        Args:
            symbol: Símbolo a analizar
            days: Días hacia atrás para buscar noticias
            max_news: Máximo de noticias a obtener
        
        Returns:
            Número de noticias analizadas
        """
        try:
            # Obtener noticias desde múltiples fuentes
            news_articles = self.news_fetcher.get_news(symbol, days=days, max_results=max_news)
            
            if not news_articles:
                logger.warning(f"No se obtuvieron noticias para {symbol}")
                return 0
            
            # Analizar cada noticia
            analyzed_count = 0
            for article in news_articles:
                # Combinar título, descripción y contenido
                news_text = f"{article.get('title', '')} {article.get('description', '')} {article.get('content', '')}"
                
                if news_text.strip():
                    # Analizar sentimiento
                    sentiment_result = self.analyze_news_sentiment(symbol, news_text)
                    analyzed_count += 1
                    
                    logger.debug(f"Noticia analizada: {article.get('title', 'Sin título')[:50]}... - Sentimiento: {sentiment_result['sentiment']}")
            
            logger.info(f"✅ {analyzed_count} noticias analizadas para {symbol}")
            return analyzed_count
        
        except Exception as e:
            logger.error(f"Error obteniendo y analizando noticias para {symbol}: {e}")
            return 0
    
    def _save_history(self):
        """Guarda historial de sentimientos"""
        if len(self.sentiment_history) > 1000:
            self.sentiment_history = self.sentiment_history[-1000:]
        
        try:
            with open(self.sentiment_file, 'w', encoding='utf-8') as f:
                json.dump(self.sentiment_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando historial de sentimiento: {e}")


class PortfolioRebalancer:
    """Sistema de rebalanceo automático de portafolio"""
    
    def __init__(self):
        self.rebalance_history = []
        self.rebalance_file = Path("data/rebalance_history.json")
        self.rebalance_file.parent.mkdir(parents=True, exist_ok=True)
    
    def calculate_rebalance_needs(self, current_portfolio: List[Dict], 
                                 target_weights: Dict[str, float]) -> Dict:
        """
        Calcula necesidades de rebalanceo
        
        Args:
            current_portfolio: Portafolio actual
            target_weights: Pesos objetivo por símbolo
        """
        # Calcular valor total
        total_value = sum(p.get('total_val', 0) for p in current_portfolio)
        
        if total_value == 0:
            return {'needs_rebalance': False}
        
        # Calcular pesos actuales
        current_weights = {}
        for position in current_portfolio:
            symbol = position.get('symbol', '')
            current_val = position.get('total_val', 0)
            current_weights[symbol] = (current_val / total_value) * 100
        
        # Calcular desviaciones
        deviations = {}
        rebalance_needs = []
        
        for symbol, target_weight in target_weights.items():
            current_weight = current_weights.get(symbol, 0)
            deviation = current_weight - target_weight
            
            if abs(deviation) > 5:  # Umbral de 5%
                rebalance_needs.append({
                    'symbol': symbol,
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'deviation': deviation,
                    'current_value': current_weights.get(symbol, 0) * total_value / 100,
                    'target_value': target_weight * total_value / 100,
                    'adjustment_needed': (target_weight * total_value / 100) - (current_weight * total_value / 100),
                })
            
            deviations[symbol] = deviation
        
        needs_rebalance = len(rebalance_needs) > 0
        
        return {
            'needs_rebalance': needs_rebalance,
            'total_value': total_value,
            'current_weights': current_weights,
            'target_weights': target_weights,
            'deviations': deviations,
            'rebalance_needs': rebalance_needs,
        }
    
    def generate_rebalance_plan(self, rebalance_analysis: Dict) -> List[Dict]:
        """Genera plan de rebalanceo"""
        if not rebalance_analysis.get('needs_rebalance'):
            return []
        
        plan = []
        for need in rebalance_analysis.get('rebalance_needs', []):
            adjustment = need['adjustment_needed']
            
            if adjustment > 0:
                action = 'BUY'
            elif adjustment < 0:
                action = 'SELL'
            else:
                continue
            
            plan.append({
                'symbol': need['symbol'],
                'action': action,
                'value_adjustment': abs(adjustment),
                'current_weight': need['current_weight'],
                'target_weight': need['target_weight'],
            })
        
        return plan
    
    def record_rebalance(self, rebalance_data: Dict):
        """Registra un rebalanceo ejecutado"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'data': rebalance_data,
        }
        
        self.rebalance_history.append(record)
        self._save_history()
    
    def _save_history(self):
        """Guarda historial de rebalanceos"""
        if len(self.rebalance_history) > 500:
            self.rebalance_history = self.rebalance_history[-500:]
        
        try:
            with open(self.rebalance_file, 'w', encoding='utf-8') as f:
                json.dump(self.rebalance_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando historial de rebalanceo: {e}")


class AdvancedReporter:
    """Sistema de reportes y analytics avanzados"""
    
    def __init__(self):
        self.reports_dir = Path("data/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_daily_report(self, portfolio_data: Dict, trades_data: List[Dict],
                            performance_data: Dict) -> Dict:
        """Genera reporte diario"""
        report = {
            'date': datetime.now().date().isoformat(),
            'portfolio': portfolio_data,
            'trades': trades_data,
            'performance': performance_data,
            'summary': {
                'total_trades': len(trades_data),
                'winning_trades': sum(1 for t in trades_data if t.get('pnl', 0) > 0),
                'total_pnl': sum(t.get('pnl', 0) for t in trades_data),
            }
        }
        
        # Guardar reporte
        filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Reporte diario generado: {filepath}")
        
        return report
    
    def generate_performance_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """Genera reporte de performance"""
        # Cargar datos históricos
        trades_file = Path("trades.json")
        trades = []
        if trades_file.exists():
            try:
                with open(trades_file, 'r', encoding='utf-8') as f:
                    all_trades = json.load(f)
                    trades = [
                        t for t in all_trades
                        if start_date <= datetime.fromisoformat(t['timestamp']) <= end_date
                    ]
            except:
                pass
        
        # Calcular métricas
        if trades:
            wins = [t for t in trades if t.get('pnl', 0) > 0]
            losses = [t for t in trades if t.get('pnl', 0) < 0]
            
            report = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                },
                'trades': {
                    'total': len(trades),
                    'winning': len(wins),
                    'losing': len(losses),
                    'win_rate': (len(wins) / len(trades) * 100) if trades else 0,
                },
                'pnl': {
                    'total': sum(t.get('pnl', 0) for t in trades),
                    'avg_win': np.mean([t.get('pnl', 0) for t in wins]) if wins else 0,
                    'avg_loss': np.mean([t.get('pnl', 0) for t in losses]) if losses else 0,
                },
            }
        else:
            report = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                },
                'trades': {'total': 0},
                'pnl': {'total': 0},
            }
        
        # Guardar
        filename = f"performance_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"
        filepath = self.reports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report


class MultiTimeframeAnalyzer:
    """Análisis multi-timeframe"""
    
    def __init__(self):
        self.timeframes = ['1h', '4h', '1d', '1w']
    
    def analyze_multi_timeframe(self, symbol: str) -> Dict:
        """Analiza símbolo en múltiples timeframes"""
        # Esta es una implementación simplificada
        # En producción, se necesitarían datos agregados por timeframe
        
        analysis = {
            'symbol': symbol,
            'timeframes': {},
            'consensus': 'NEUTRAL',
            'timestamp': datetime.now().isoformat(),
        }
        
        # Por ahora, retornar estructura básica
        for tf in self.timeframes:
            analysis['timeframes'][tf] = {
                'trend': 'NEUTRAL',
                'strength': 0.5,
            }
        
        return analysis


class AdvancedRiskDashboard:
    """Dashboard avanzado de riesgo"""
    
    def calculate_portfolio_risk(self, portfolio: List[Dict]) -> Dict:
        """Calcula métricas de riesgo del portafolio"""
        if not portfolio:
            return {}
        
        total_value = sum(p.get('total_val', 0) for p in portfolio)
        
        # Calcular exposición por símbolo
        exposures = {}
        for position in portfolio:
            symbol = position.get('symbol', '')
            value = position.get('total_val', 0)
            if total_value > 0:
                exposures[symbol] = (value / total_value) * 100
        
        # Calcular concentración (Herfindahl Index)
        concentration = sum(w**2 for w in exposures.values()) / 100
        
        return {
            'total_value': total_value,
            'position_count': len(portfolio),
            'exposures': exposures,
            'concentration_index': concentration,
            'max_exposure': max(exposures.values()) if exposures else 0,
            'max_exposure_symbol': max(exposures.items(), key=lambda x: x[1])[0] if exposures else None,
        }
    
    def calculate_var(self, returns: List[float], confidence_level: float = 0.95) -> float:
        """Calcula Value at Risk (VaR)"""
        if not returns:
            return 0.0
        
        returns_array = np.array(returns)
        var = np.percentile(returns_array, (1 - confidence_level) * 100)
        
        return abs(var)


class EnhancedPaperTrading:
    """Paper Trading mejorado con slippage y comisiones realistas"""
    
    def __init__(self, slippage_pct: float = 0.001, commission_pct: float = 0.001):
        self.slippage_pct = slippage_pct  # 0.1% slippage
        self.commission_pct = commission_pct  # 0.1% comisión
    
    def simulate_trade(self, symbol: str, signal: str, intended_price: float, 
                      quantity: int) -> Dict:
        """Simula trade con slippage y comisiones"""
        # Aplicar slippage
        if signal == 'BUY':
            execution_price = intended_price * (1 + self.slippage_pct)
        else:
            execution_price = intended_price * (1 - self.slippage_pct)
        
        # Calcular costos
        trade_value = execution_price * quantity
        commission = trade_value * self.commission_pct
        total_cost = trade_value + commission
        
        return {
            'symbol': symbol,
            'signal': signal,
            'intended_price': intended_price,
            'execution_price': execution_price,
            'quantity': quantity,
            'trade_value': trade_value,
            'commission': commission,
            'total_cost': total_cost,
            'slippage': execution_price - intended_price,
        }


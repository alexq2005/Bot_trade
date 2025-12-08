"""
Sistema Mejorado de Aprendizaje para Maximizar Ganancias y Minimizar Pérdidas
Aprende de cada trade, símbolo, horario y condición de mercado
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

from src.core.logger import get_logger

logger = get_logger("enhanced_learning")


class SymbolPerformanceTracker:
    """Rastrea el rendimiento por símbolo para identificar los mejores activos"""
    
    def __init__(self, data_file: str = "data/learning/symbol_performance.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.performance = self._load_performance()
    
    def _load_performance(self) -> Dict:
        """Carga historial de rendimiento por símbolo"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_performance(self):
        """Guarda rendimiento por símbolo"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando rendimiento por símbolo: {e}")
    
    def record_trade(self, symbol: str, pnl: float, pnl_pct: float, signal: str, 
                     confidence: str, market_conditions: Dict):
        """Registra un trade para análisis por símbolo"""
        if symbol not in self.performance:
            self.performance[symbol] = {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'total_pnl': 0.0,
                'total_pnl_pct': 0.0,
                'avg_pnl': 0.0,
                'best_trade': 0.0,
                'worst_trade': 0.0,
                'signals': {'BUY': {'wins': 0, 'losses': 0}, 'SELL': {'wins': 0, 'losses': 0}},
                'confidence_levels': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'last_trade': None,
            }
        
        stats = self.performance[symbol]
        stats['total_trades'] += 1
        stats['total_pnl'] += pnl
        stats['total_pnl_pct'] += pnl_pct
        stats['avg_pnl'] = stats['total_pnl'] / stats['total_trades']
        stats['last_trade'] = datetime.now().isoformat()
        
        if pnl > 0:
            stats['wins'] += 1
            stats['best_trade'] = max(stats['best_trade'], pnl)
        else:
            stats['losses'] += 1
            stats['worst_trade'] = min(stats['worst_trade'], pnl)
        
        # Actualizar por señal
        if signal in stats['signals']:
            if pnl > 0:
                stats['signals'][signal]['wins'] += 1
            else:
                stats['signals'][signal]['losses'] += 1
        
        # Actualizar por confianza
        if confidence in stats['confidence_levels']:
            stats['confidence_levels'][confidence] += 1
        
        self._save_performance()
    
    def get_best_symbols(self, min_trades: int = 5) -> List[Dict]:
        """Retorna los mejores símbolos basado en win rate y P&L"""
        best = []
        for symbol, stats in self.performance.items():
            if stats['total_trades'] >= min_trades:
                win_rate = stats['wins'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
                score = (win_rate * 0.6) + (stats['avg_pnl'] / 1000 * 0.4)  # Combinación de win rate y P&L
                best.append({
                    'symbol': symbol,
                    'win_rate': win_rate,
                    'avg_pnl': stats['avg_pnl'],
                    'total_pnl': stats['total_pnl'],
                    'total_trades': stats['total_trades'],
                    'score': score
                })
        
        return sorted(best, key=lambda x: x['score'], reverse=True)
    
    def get_worst_symbols(self, min_trades: int = 5) -> List[Dict]:
        """Retorna los peores símbolos para considerar eliminarlos"""
        worst = []
        for symbol, stats in self.performance.items():
            if stats['total_trades'] >= min_trades:
                win_rate = stats['wins'] / stats['total_trades'] if stats['total_trades'] > 0 else 0
                if win_rate < 0.4 and stats['total_pnl'] < 0:  # Win rate bajo y pérdidas
                    worst.append({
                        'symbol': symbol,
                        'win_rate': win_rate,
                        'avg_pnl': stats['avg_pnl'],
                        'total_pnl': stats['total_pnl'],
                        'total_trades': stats['total_trades'],
                    })
        
        return sorted(worst, key=lambda x: x['win_rate'])


class TimeBasedLearning:
    """Aprende qué horarios son mejores para trading - MEJORADO con análisis temporal"""
    
    def __init__(self, data_file: str = "data/learning/time_performance.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.time_stats = self._load_stats()
        self.operations_log_file = Path("data/operations_log.json")
    
    def _load_stats(self) -> Dict:
        """Carga estadísticas por horario"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_stats(self):
        """Guarda estadísticas por horario"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.time_stats, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando estadísticas por horario: {e}")
    
    def record_trade(self, pnl: float, signal: str):
        """Registra un trade con su horario"""
        now = datetime.now()
        hour = now.hour
        day_of_week = now.strftime('%A')
        
        # Inicializar si no existe
        if hour not in self.time_stats:
            self.time_stats[hour] = {'trades': 0, 'wins': 0, 'total_pnl': 0.0}
        if day_of_week not in self.time_stats:
            self.time_stats[day_of_week] = {'trades': 0, 'wins': 0, 'total_pnl': 0.0}
        
        # Actualizar por hora
        self.time_stats[hour]['trades'] += 1
        self.time_stats[hour]['total_pnl'] += pnl
        if pnl > 0:
            self.time_stats[hour]['wins'] += 1
        
        # Actualizar por día de semana
        self.time_stats[day_of_week]['trades'] += 1
        self.time_stats[day_of_week]['total_pnl'] += pnl
        if pnl > 0:
            self.time_stats[day_of_week]['wins'] += 1
        
        self._save_stats()
    
    def _analyze_temporal_patterns_from_operations(self) -> Dict:
        """MEJORA #2: Analiza patrones temporales desde operations_log.json"""
        if not self.operations_log_file.exists():
            return {}
        
        try:
            with open(self.operations_log_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo operations_log.json para análisis temporal: {e}")
            return {}
        
        analyses = [op for op in operations if op.get('type') == 'ANALYSIS']
        
        if not analyses:
            return {}
        
        # Estadísticas temporales mejoradas
        hour_stats = {}  # Por hora del día
        day_stats = {}   # Por día de semana
        hour_score_stats = {}  # Scores promedio por hora
        
        for analysis in analyses:
            data = analysis.get('data', {})
            score = data.get('score', 0)
            signal = data.get('final_signal', 'HOLD')
            timestamp = analysis.get('timestamp')
            
            if not timestamp:
                continue
            
            try:
                dt = datetime.fromisoformat(timestamp)
                hour = dt.hour
                day_of_week = dt.strftime('%A')
                
                # Estadísticas por hora
                if hour not in hour_stats:
                    hour_stats[hour] = {
                        'total_analyses': 0,
                        'total_score': 0,
                        'avg_score': 0,
                        'buy_signals': 0,
                        'sell_signals': 0,
                        'hold_signals': 0,
                        'high_scores': 0,  # Scores > 30
                        'very_high_scores': 0  # Scores > 50
                    }
                
                hour_stats[hour]['total_analyses'] += 1
                hour_stats[hour]['total_score'] += score
                hour_stats[hour]['avg_score'] = hour_stats[hour]['total_score'] / hour_stats[hour]['total_analyses']
                
                if signal == 'BUY':
                    hour_stats[hour]['buy_signals'] += 1
                elif signal == 'SELL':
                    hour_stats[hour]['sell_signals'] += 1
                else:
                    hour_stats[hour]['hold_signals'] += 1
                
                if score > 30:
                    hour_stats[hour]['high_scores'] += 1
                if score > 50:
                    hour_stats[hour]['very_high_scores'] += 1
                
                # Estadísticas por día de semana
                if day_of_week not in day_stats:
                    day_stats[day_of_week] = {
                        'total_analyses': 0,
                        'total_score': 0,
                        'avg_score': 0,
                        'buy_signals': 0
                    }
                
                day_stats[day_of_week]['total_analyses'] += 1
                day_stats[day_of_week]['total_score'] += score
                day_stats[day_of_week]['avg_score'] = day_stats[day_of_week]['total_score'] / day_stats[day_of_week]['total_analyses']
                
                if signal == 'BUY':
                    day_stats[day_of_week]['buy_signals'] += 1
                    
            except Exception as e:
                logger.debug(f"Error procesando timestamp {timestamp}: {e}")
                continue
        
        return {
            'hour_stats': hour_stats,
            'day_stats': day_stats,
            'total_analyses': len(analyses)
        }
    
    def get_best_hours(self) -> List[Dict]:
        """Retorna las mejores horas para trading - MEJORADO con análisis desde operations_log"""
        # Primero intentar desde trades (si hay)
        trade_hours = []
        for key, stats in self.time_stats.items():
            if isinstance(key, int) and stats['trades'] >= 3:  # Al menos 3 trades
                win_rate = stats['wins'] / stats['trades'] if stats['trades'] > 0 else 0
                avg_pnl = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
                trade_hours.append({
                    'hour': key,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'total_trades': stats['trades'],
                    'source': 'trades'
                })
        
        # MEJORA #2: Analizar desde operations_log.json
        temporal_data = self._analyze_temporal_patterns_from_operations()
        analysis_hours = []
        
        if temporal_data.get('hour_stats'):
            for hour, stats in temporal_data['hour_stats'].items():
                if stats['total_analyses'] >= 5:  # Mínimo 5 análisis
                    buy_ratio = stats['buy_signals'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    high_score_ratio = stats['high_scores'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    very_high_score_ratio = stats['very_high_scores'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    
                    # Score combinado: avg_score + ratio de BUY + ratio de scores altos
                    combined_score = (
                        stats['avg_score'] * 0.3 +
                        buy_ratio * 30 +
                        high_score_ratio * 20 +
                        very_high_score_ratio * 20
                    )
                    
                    analysis_hours.append({
                        'hour': hour,
                        'avg_score': stats['avg_score'],
                        'total_analyses': stats['total_analyses'],
                        'buy_signals': stats['buy_signals'],
                        'buy_ratio': buy_ratio,
                        'high_scores': stats['high_scores'],
                        'very_high_scores': stats['very_high_scores'],
                        'combined_score': combined_score,
                        'source': 'analysis'
                    })
        
        # Combinar y priorizar
        if trade_hours:
            # Si hay datos de trades, usarlos como base y complementar con análisis
            all_hours = trade_hours.copy()
            trade_hour_set = {h['hour'] for h in trade_hours}
            
            for analysis_hour in analysis_hours:
                if analysis_hour['hour'] not in trade_hour_set:
                    all_hours.append(analysis_hour)
            
            # Ordenar por win_rate (trades) o combined_score (análisis)
            all_hours.sort(key=lambda x: x.get('win_rate', x.get('combined_score', 0)), reverse=True)
            return all_hours[:10]
        else:
            # No hay trades, usar solo análisis
            analysis_hours.sort(key=lambda x: x['combined_score'], reverse=True)
            return analysis_hours[:10]
    
    def get_best_days(self) -> List[Dict]:
        """MEJORA #2: Retorna los mejores días de la semana para trading"""
        temporal_data = self._analyze_temporal_patterns_from_operations()
        
        if not temporal_data.get('day_stats'):
            return []
        
        day_list = []
        for day, stats in temporal_data['day_stats'].items():
            if stats['total_analyses'] >= 10:  # Mínimo 10 análisis
                buy_ratio = stats['buy_signals'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                
                day_list.append({
                    'day': day,
                    'avg_score': stats['avg_score'],
                    'total_analyses': stats['total_analyses'],
                    'buy_signals': stats['buy_signals'],
                    'buy_ratio': buy_ratio,
                    'combined_score': stats['avg_score'] * 0.5 + buy_ratio * 30
                })
        
        day_list.sort(key=lambda x: x['combined_score'], reverse=True)
        return day_list


class MarketConditionLearning:
    """Aprende qué condiciones de mercado funcionan mejor - MEJORADO"""
    
    def __init__(self, data_file: str = "data/learning/market_conditions.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.conditions = self._load_conditions()
        self.operations_log_file = Path("data/operations_log.json")
    
    def _load_conditions(self) -> Dict:
        """Carga historial de condiciones de mercado"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_conditions(self):
        """Guarda condiciones de mercado"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.conditions, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando condiciones de mercado: {e}")
    
    def record_trade(self, market_conditions: Dict, pnl: float):
        """Registra un trade con sus condiciones de mercado"""
        # Categorizar condiciones
        volatility = market_conditions.get('volatility', 'MEDIUM')
        trend = market_conditions.get('trend', 'NEUTRAL')
        rsi = market_conditions.get('rsi', 50)
        
        # Categorizar RSI
        if rsi < 30:
            rsi_category = 'OVERSOLD'
        elif rsi > 70:
            rsi_category = 'OVERBOUGHT'
        else:
            rsi_category = 'NEUTRAL'
        
        condition_key = f"{volatility}_{trend}_{rsi_category}"
        
        if condition_key not in self.conditions:
            self.conditions[condition_key] = {
                'trades': 0,
                'wins': 0,
                'total_pnl': 0.0,
                'volatility': volatility,
                'trend': trend,
                'rsi_category': rsi_category
            }
        
        stats = self.conditions[condition_key]
        stats['trades'] += 1
        stats['total_pnl'] += pnl
        if pnl > 0:
            stats['wins'] += 1
        
        self._save_conditions()
    
    def _analyze_market_conditions_from_operations(self) -> Dict:
        """MEJORA #6: Analiza condiciones de mercado desde operations_log.json"""
        if not self.operations_log_file.exists():
            return {}
        
        try:
            with open(self.operations_log_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo operations_log.json para condiciones de mercado: {e}")
            return {}
        
        analyses = [op for op in operations if op.get('type') == 'ANALYSIS']
        
        if not analyses:
            return {}
        
        # Analizar últimas 200 operaciones
        recent_analyses = analyses[-200:] if len(analyses) > 200 else analyses
        
        condition_stats = {}
        
        for analysis in recent_analyses:
            data = analysis.get('data', {})
            score = data.get('score', 0)
            signal = data.get('final_signal', 'HOLD')
            technical = data.get('technical', {})
            
            # Extraer condiciones técnicas si están disponibles
            rsi = technical.get('rsi', 50) if technical else 50
            macd = technical.get('macd', 0) if technical else 0
            volume_ratio = technical.get('volume_ratio', 1.0) if technical else 1.0
            
            # Categorizar condiciones
            if rsi < 30:
                rsi_category = 'OVERSOLD'
            elif rsi > 70:
                rsi_category = 'OVERBOUGHT'
            else:
                rsi_category = 'NEUTRAL'
            
            # Categorizar tendencia por MACD
            if macd > 0:
                trend = 'BULLISH'
            elif macd < 0:
                trend = 'BEARISH'
            else:
                trend = 'NEUTRAL'
            
            # Categorizar volatilidad por volumen
            if volume_ratio > 1.5:
                volatility = 'HIGH'
            elif volume_ratio < 0.7:
                volatility = 'LOW'
            else:
                volatility = 'MEDIUM'
            
            condition_key = f"{volatility}_{trend}_{rsi_category}"
            
            if condition_key not in condition_stats:
                condition_stats[condition_key] = {
                    'total_analyses': 0,
                    'total_score': 0,
                    'avg_score': 0,
                    'buy_signals': 0,
                    'high_scores': 0,  # Scores > 30
                    'volatility': volatility,
                    'trend': trend,
                    'rsi_category': rsi_category
                }
            
            stats = condition_stats[condition_key]
            stats['total_analyses'] += 1
            stats['total_score'] += score
            stats['avg_score'] = stats['total_score'] / stats['total_analyses']
            
            if signal == 'BUY':
                stats['buy_signals'] += 1
            
            if score > 30:
                stats['high_scores'] += 1
        
        return condition_stats
    
    def get_best_conditions(self) -> List[Dict]:
        """Retorna las mejores condiciones de mercado para trading - MEJORADO"""
        # Primero desde trades (si hay)
        trade_conditions = []
        for condition, stats in self.conditions.items():
            if stats['trades'] >= 3:
                win_rate = stats['wins'] / stats['trades'] if stats['trades'] > 0 else 0
                avg_pnl = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
                trade_conditions.append({
                    'condition': condition,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'volatility': stats['volatility'],
                    'trend': stats['trend'],
                    'rsi_category': stats['rsi_category'],
                    'total_trades': stats['trades'],
                    'source': 'trades'
                })
        
        # MEJORA #6: Analizar desde operations_log
        analysis_conditions = self._analyze_market_conditions_from_operations()
        condition_list = []
        
        if analysis_conditions:
            for condition_key, stats in analysis_conditions.items():
                if stats['total_analyses'] >= 10:  # Mínimo 10 análisis
                    buy_ratio = stats['buy_signals'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    high_score_ratio = stats['high_scores'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    
                    # Score combinado
                    combined_score = (
                        stats['avg_score'] * 0.4 +
                        buy_ratio * 30 +
                        high_score_ratio * 30
                    )
                    
                    condition_list.append({
                        'condition': condition_key,
                        'avg_score': stats['avg_score'],
                        'total_analyses': stats['total_analyses'],
                        'buy_signals': stats['buy_signals'],
                        'buy_ratio': buy_ratio,
                        'high_scores': stats['high_scores'],
                        'volatility': stats['volatility'],
                        'trend': stats['trend'],
                        'rsi_category': stats['rsi_category'],
                        'combined_score': combined_score,
                        'source': 'analysis'
                    })
        
        # Combinar y priorizar
        if trade_conditions:
            all_conditions = trade_conditions.copy()
            trade_condition_set = {c['condition'] for c in trade_conditions}
            
            for analysis_condition in condition_list:
                if analysis_condition['condition'] not in trade_condition_set:
                    all_conditions.append(analysis_condition)
            
            # Ordenar por win_rate (trades) o combined_score (análisis)
            all_conditions.sort(key=lambda x: x.get('win_rate', x.get('combined_score', 0)), reverse=True)
            return all_conditions[:10]
        else:
            # No hay trades, usar solo análisis
            condition_list.sort(key=lambda x: x['combined_score'], reverse=True)
            return condition_list[:10]
    
    def get_current_market_condition(self) -> Dict:
        """MEJORA #6: Identifica condiciones de mercado actuales"""
        # Analizar últimas operaciones para determinar condiciones actuales
        analysis_conditions = self._analyze_market_conditions_from_operations()
        
        if not analysis_conditions:
            return {'status': 'unknown', 'message': 'No hay suficientes datos'}
        
        # Obtener condición más frecuente recientemente
        recent_conditions = sorted(
            analysis_conditions.items(),
            key=lambda x: x[1]['total_analyses'],
            reverse=True
        )[:3]
        
        if recent_conditions:
            top_condition = recent_conditions[0][1]
            return {
                'status': 'detected',
                'volatility': top_condition['volatility'],
                'trend': top_condition['trend'],
                'rsi_category': top_condition['rsi_category'],
                'avg_score': top_condition['avg_score'],
                'buy_ratio': top_condition['buy_signals'] / top_condition['total_analyses'] if top_condition['total_analyses'] > 0 else 0,
                'recommendation': self._get_condition_recommendation(top_condition)
            }
        
        return {'status': 'unknown', 'message': 'No se pudo determinar'}
    
    def _get_condition_recommendation(self, condition_stats: Dict) -> str:
        """Genera recomendación basada en condiciones"""
        volatility = condition_stats.get('volatility', 'MEDIUM')
        trend = condition_stats.get('trend', 'NEUTRAL')
        rsi_category = condition_stats.get('rsi_category', 'NEUTRAL')
        avg_score = condition_stats.get('avg_score', 0)
        buy_ratio = condition_stats.get('buy_signals', 0) / condition_stats.get('total_analyses', 1) if condition_stats.get('total_analyses', 0) > 0 else 0
        
        recommendations = []
        
        if volatility == 'HIGH' and trend == 'BULLISH' and buy_ratio > 0.15:
            recommendations.append("Mercado volátil alcista - Oportunidades de trading activas")
        elif volatility == 'LOW' and trend == 'NEUTRAL':
            recommendations.append("Mercado lateral con baja volatilidad - Considerar esperar")
        elif rsi_category == 'OVERSOLD' and trend == 'BULLISH':
            recommendations.append("Condiciones favorables para compra - RSI oversold con tendencia alcista")
        elif rsi_category == 'OVERBOUGHT' and trend == 'BEARISH':
            recommendations.append("Condiciones favorables para venta - RSI overbought con tendencia bajista")
        
        if avg_score > 25 and buy_ratio > 0.10:
            recommendations.append("Scores altos y buena actividad BUY - Aumentar actividad")
        elif avg_score < 5 and buy_ratio < 0.03:
            recommendations.append("Scores bajos y poca actividad - Ser más conservador")
        
        return ' | '.join(recommendations) if recommendations else "Condiciones normales - Mantener estrategia actual"


class StrategyPerformanceTracker:
    """MEJORA #4: Rastrea performance de cada estrategia individual"""
    
    def __init__(self, data_file: str = "data/learning/strategy_performance.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.strategy_stats = self._load_stats()
        self.operations_log_file = Path("data/operations_log.json")
    
    def _load_stats(self) -> Dict:
        """Carga estadísticas de estrategias"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_stats(self):
        """Guarda estadísticas de estrategias"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.strategy_stats, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando estadísticas de estrategias: {e}")
    
    def _analyze_strategies_from_operations(self) -> Dict:
        """Analiza performance de estrategias desde operations_log.json"""
        if not self.operations_log_file.exists():
            return {}
        
        try:
            with open(self.operations_log_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo operations_log.json para análisis de estrategias: {e}")
            return {}
        
        analyses = [op for op in operations if op.get('type') == 'ANALYSIS']
        
        if not analyses:
            return {}
        
        # Estrategias conocidas
        known_strategies = [
            'regime_detection', 'multi_timeframe', 'order_flow', 'seasonal',
            'fractal', 'anomaly', 'volume_profile', 'monte_carlo',
            'pattern_recognition', 'pairs_trading', 'elliott_wave',
            'smart_money', 'meta_learner', 'candlestick', 'correlation',
            'neural_network', 'macroeconomic'
        ]
        
        strategy_stats = {}
        
        for analysis in analyses:
            data = analysis.get('data', {})
            score = data.get('score', 0)
            signal = data.get('final_signal', 'HOLD')
            buy_factors = data.get('buy_factors', [])
            sell_factors = data.get('sell_factors', [])
            
            # Extraer estrategias de buy_factors y sell_factors
            # Formato esperado: "Strategy Name (+score)" o "Strategy Name (score)"
            all_factors = buy_factors + sell_factors
            
            for factor in all_factors:
                # Buscar nombres de estrategias en los factores
                for strategy in known_strategies:
                    if strategy.lower().replace('_', ' ') in factor.lower() or strategy in factor:
                        if strategy not in strategy_stats:
                            strategy_stats[strategy] = {
                                'total_uses': 0,
                                'total_score_contribution': 0,
                                'avg_score_contribution': 0,
                                'buy_signals': 0,
                                'sell_signals': 0,
                                'hold_signals': 0,
                                'high_contribution': 0  # Contribuciones > 5
                            }
                        
                        strategy_stats[strategy]['total_uses'] += 1
                        
                        # Intentar extraer el score de la contribución
                        try:
                            # Buscar número en el factor
                            import re
                            numbers = re.findall(r'[-+]?\d+', factor)
                            if numbers:
                                contribution = int(numbers[-1])  # Último número
                                strategy_stats[strategy]['total_score_contribution'] += abs(contribution)
                                strategy_stats[strategy]['avg_score_contribution'] = (
                                    strategy_stats[strategy]['total_score_contribution'] / 
                                    strategy_stats[strategy]['total_uses']
                                )
                                
                                if abs(contribution) > 5:
                                    strategy_stats[strategy]['high_contribution'] += 1
                        except:
                            pass
                        
                        if signal == 'BUY':
                            strategy_stats[strategy]['buy_signals'] += 1
                        elif signal == 'SELL':
                            strategy_stats[strategy]['sell_signals'] += 1
                        else:
                            strategy_stats[strategy]['hold_signals'] += 1
        
        return strategy_stats
    
    def get_strategy_performance(self) -> Dict:
        """Retorna performance de cada estrategia"""
        # Analizar desde operations_log
        strategy_stats = self._analyze_strategies_from_operations()
        
        if not strategy_stats:
            return {}
        
        # Calcular métricas de performance
        performance = {}
        for strategy, stats in strategy_stats.items():
            if stats['total_uses'] >= 3:  # Mínimo 3 usos
                buy_ratio = stats['buy_signals'] / stats['total_uses'] if stats['total_uses'] > 0 else 0
                high_contribution_ratio = stats['high_contribution'] / stats['total_uses'] if stats['total_uses'] > 0 else 0
                
                # Score de performance combinado
                performance_score = (
                    stats['avg_score_contribution'] * 0.4 +
                    buy_ratio * 30 +
                    high_contribution_ratio * 30
                )
                
                performance[strategy] = {
                    'total_uses': stats['total_uses'],
                    'avg_score_contribution': stats['avg_score_contribution'],
                    'buy_signals': stats['buy_signals'],
                    'buy_ratio': buy_ratio,
                    'high_contribution': stats['high_contribution'],
                    'high_contribution_ratio': high_contribution_ratio,
                    'performance_score': performance_score
                }
        
        # Ordenar por performance_score
        sorted_performance = sorted(
            performance.items(),
            key=lambda x: x[1]['performance_score'],
            reverse=True
        )
        
        return {
            'strategies': dict(sorted_performance),
            'top_strategies': [s[0] for s in sorted_performance[:5]],
            'bottom_strategies': [s[0] for s in sorted_performance[-5:]] if len(sorted_performance) >= 5 else []
        }
    
    def get_strategy_recommendations(self) -> List[Dict]:
        """Genera recomendaciones basadas en performance de estrategias"""
        performance = self.get_strategy_performance()
        
        if not performance.get('strategies'):
            return []
        
        recommendations = []
        strategies = performance['strategies']
        top_strategies = performance.get('top_strategies', [])
        bottom_strategies = performance.get('bottom_strategies', [])
        
        if top_strategies:
            recommendations.append({
                'type': 'strategy_weight',
                'priority': 'medium',
                'message': f"✅ Mejores estrategias (aumentar peso): {', '.join(top_strategies[:3])}",
                'action': 'increase_weight',
                'strategies': top_strategies[:3],
                'reason': 'Estas estrategias muestran mejor performance'
            })
        
        if bottom_strategies:
            recommendations.append({
                'type': 'strategy_weight',
                'priority': 'low',
                'message': f"⚠️ Estrategias con menor performance: {', '.join(bottom_strategies)}",
                'action': 'review_weight',
                'strategies': bottom_strategies,
                'reason': 'Estas estrategias muestran menor contribución'
            })
        
        return recommendations


class EnhancedLearningSystem:
    """Sistema completo de aprendizaje mejorado"""
    
    def __init__(self):
        self.symbol_tracker = SymbolPerformanceTracker()
        self.time_learning = TimeBasedLearning()
        self.market_learning = MarketConditionLearning()
        self.strategy_tracker = StrategyPerformanceTracker()  # MEJORA #4
        self.insights_file = Path("data/learning/insights.json")
        self.insights_file.parent.mkdir(parents=True, exist_ok=True)
        self.operations_log_file = Path("data/operations_log.json")
    
    def learn_from_trade(self, symbol: str, pnl: float, pnl_pct: float, signal: str,
                        confidence: str, market_conditions: Dict):
        """Aprende de un trade completo"""
        # Aprender por símbolo
        self.symbol_tracker.record_trade(symbol, pnl, pnl_pct, signal, confidence, market_conditions)
        
        # Aprender por horario
        self.time_learning.record_trade(pnl, signal)
        
        # Aprender por condiciones de mercado
        self.market_learning.record_trade(market_conditions, pnl)
    
    def _analyze_operations_log(self) -> Dict:
        """Analiza operations_log.json para generar insights desde análisis (no solo trades)"""
        if not self.operations_log_file.exists():
            return {}
        
        try:
            with open(self.operations_log_file, 'r', encoding='utf-8') as f:
                operations = json.load(f)
        except Exception as e:
            logger.error(f"Error leyendo operations_log.json: {e}")
            return {}
        
        # Filtrar solo análisis
        analyses = [op for op in operations if op.get('type') == 'ANALYSIS']
        
        if not analyses:
            return {}
        
        # Analizar por símbolo
        symbol_stats = {}
        hour_stats = {}
        signal_stats = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        
        for analysis in analyses:
            data = analysis.get('data', {})
            symbol = data.get('symbol')
            score = data.get('score', 0)
            signal = data.get('final_signal', 'HOLD')
            timestamp = analysis.get('timestamp')
            
            if not symbol:
                continue
            
            # Estadísticas por símbolo
            if symbol not in symbol_stats:
                symbol_stats[symbol] = {
                    'total_analyses': 0,
                    'total_score': 0,
                    'avg_score': 0,
                    'buy_signals': 0,
                    'sell_signals': 0,
                    'hold_signals': 0,
                    'high_scores': 0  # Scores > 30
                }
            
            symbol_stats[symbol]['total_analyses'] += 1
            symbol_stats[symbol]['total_score'] += score
            symbol_stats[symbol]['avg_score'] = symbol_stats[symbol]['total_score'] / symbol_stats[symbol]['total_analyses']
            
            if signal == 'BUY':
                symbol_stats[symbol]['buy_signals'] += 1
                signal_stats['BUY'] += 1
            elif signal == 'SELL':
                symbol_stats[symbol]['sell_signals'] += 1
                signal_stats['SELL'] += 1
            else:
                symbol_stats[symbol]['hold_signals'] += 1
                signal_stats['HOLD'] += 1
            
            if score > 30:
                symbol_stats[symbol]['high_scores'] += 1
            
            # Estadísticas por hora
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp)
                    hour = dt.hour
                    
                    if hour not in hour_stats:
                        hour_stats[hour] = {
                            'total_analyses': 0,
                            'total_score': 0,
                            'avg_score': 0,
                            'buy_signals': 0,
                            'high_scores': 0
                        }
                    
                    hour_stats[hour]['total_analyses'] += 1
                    hour_stats[hour]['total_score'] += score
                    hour_stats[hour]['avg_score'] = hour_stats[hour]['total_score'] / hour_stats[hour]['total_analyses']
                    
                    if signal == 'BUY':
                        hour_stats[hour]['buy_signals'] += 1
                    
                    if score > 30:
                        hour_stats[hour]['high_scores'] += 1
                except:
                    pass
        
        return {
            'symbol_stats': symbol_stats,
            'hour_stats': hour_stats,
            'signal_stats': signal_stats,
            'total_analyses': len(analyses)
        }
    
    def _generate_insights_from_analyses(self, analysis_data: Dict) -> Dict:
        """Genera insights desde análisis (no solo trades)"""
        insights = {
            'best_symbols': [],
            'worst_symbols': [],
            'best_hours': [],
            'best_market_conditions': [],
            'recommendations': []
        }
        
        symbol_stats = analysis_data.get('symbol_stats', {})
        hour_stats = analysis_data.get('hour_stats', {})
        
        # Mejores símbolos por score promedio y señales BUY
        if symbol_stats:
            symbol_list = []
            for symbol, stats in symbol_stats.items():
                if stats['total_analyses'] >= 3:  # Mínimo 3 análisis
                    # Score combinado: avg_score + ratio de BUY signals
                    buy_ratio = stats['buy_signals'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    high_score_ratio = stats['high_scores'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    combined_score = (stats['avg_score'] * 0.5) + (buy_ratio * 30) + (high_score_ratio * 20)
                    
                    symbol_list.append({
                        'symbol': symbol,
                        'avg_score': stats['avg_score'],
                        'total_analyses': stats['total_analyses'],
                        'buy_signals': stats['buy_signals'],
                        'buy_ratio': buy_ratio,
                        'high_scores': stats['high_scores'],
                        'combined_score': combined_score
                    })
            
            # Ordenar por combined_score
            symbol_list.sort(key=lambda x: x['combined_score'], reverse=True)
            insights['best_symbols'] = symbol_list[:10]  # Top 10
        
        # Mejores horas por actividad de señales BUY y scores altos
        if hour_stats:
            hour_list = []
            for hour, stats in hour_stats.items():
                if stats['total_analyses'] >= 5:  # Mínimo 5 análisis
                    buy_ratio = stats['buy_signals'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    high_score_ratio = stats['high_scores'] / stats['total_analyses'] if stats['total_analyses'] > 0 else 0
                    combined_score = (stats['avg_score'] * 0.4) + (buy_ratio * 30) + (high_score_ratio * 30)
                    
                    hour_list.append({
                        'hour': hour,
                        'avg_score': stats['avg_score'],
                        'total_analyses': stats['total_analyses'],
                        'buy_signals': stats['buy_signals'],
                        'buy_ratio': buy_ratio,
                        'high_scores': stats['high_scores'],
                        'combined_score': combined_score
                    })
            
            # Ordenar por combined_score
            hour_list.sort(key=lambda x: x['combined_score'], reverse=True)
            insights['best_hours'] = hour_list[:5]  # Top 5 horas
        
        # Generar recomendaciones
        recommendations = []
        
        if insights['best_symbols']:
            top_symbols = [s['symbol'] for s in insights['best_symbols'][:5]]
            recommendations.append(
                f"✅ Oportunidades detectadas (mejores scores y señales BUY): {', '.join(top_symbols)}"
            )
        
        if insights['best_hours']:
            top_hours = [f"{h['hour']}:00" for h in insights['best_hours']]
            recommendations.append(
                f"⏰ Mejores horarios para análisis (más actividad BUY y scores altos): {', '.join(top_hours)}"
            )
        
        signal_stats = analysis_data.get('signal_stats', {})
        total_signals = sum(signal_stats.values())
        if total_signals > 0:
            buy_pct = (signal_stats.get('BUY', 0) / total_signals) * 100
            if buy_pct < 5:
                recommendations.append(
                    f"⚠️ Pocas señales BUY generadas ({buy_pct:.1f}%). Considerar ajustar umbrales."
                )
            elif buy_pct > 20:
                recommendations.append(
                    f"✅ Buena actividad de señales BUY ({buy_pct:.1f}%). Mantener estrategia actual."
                )
        
        insights['recommendations'] = recommendations
        
        return insights
    
    def _generate_proactive_recommendations(self, analysis_data: Dict, insights: Dict) -> List[Dict]:
        """MEJORA #3: Genera recomendaciones proactivas basadas en análisis recientes"""
        recommendations = []
        
        # 1. Recomendaciones de oportunidades actuales
        if insights.get('best_symbols'):
            top_symbols = insights['best_symbols'][:5]
            current_hour = datetime.now().hour
            
            # Verificar si hay símbolos con alta actividad BUY en la hora actual
            symbol_stats = analysis_data.get('symbol_stats', {})
            for symbol_info in top_symbols:
                symbol = symbol_info.get('symbol')
                if symbol and symbol in symbol_stats:
                    stats = symbol_stats[symbol]
                    if stats['buy_signals'] > 0 and stats['avg_score'] > 25:
                        recommendations.append({
                            'type': 'opportunity',
                            'priority': 'high',
                            'message': f"🚀 Oportunidad detectada: {symbol} tiene score promedio {stats['avg_score']:.1f} y {stats['buy_signals']} señales BUY",
                            'action': 'analyze_now',
                            'symbol': symbol,
                            'reason': f"Score alto ({stats['avg_score']:.1f}) y actividad BUY ({stats['buy_signals']} señales)"
                        })
        
        # 2. Recomendaciones de ajuste de configuración
        signal_stats = analysis_data.get('signal_stats', {})
        total_signals = sum(signal_stats.values())
        
        if total_signals > 50:  # Suficientes datos
            buy_pct = (signal_stats.get('BUY', 0) / total_signals) * 100
            sell_pct = (signal_stats.get('SELL', 0) / total_signals) * 100
            hold_pct = (signal_stats.get('HOLD', 0) / total_signals) * 100
            
            if buy_pct < 3:
                recommendations.append({
                    'type': 'config_adjustment',
                    'priority': 'medium',
                    'message': f"⚠️ Muy pocas señales BUY ({buy_pct:.1f}%). Considerar reducir umbral de compra.",
                    'action': 'lower_buy_threshold',
                    'suggested_threshold': 30,  # Reducir de 35 a 30
                    'reason': f"Solo {buy_pct:.1f}% de señales son BUY, puede estar perdiendo oportunidades"
                })
            elif buy_pct > 25:
                recommendations.append({
                    'type': 'config_adjustment',
                    'priority': 'low',
                    'message': f"✅ Buena actividad BUY ({buy_pct:.1f}%). Mantener configuración actual.",
                    'action': 'maintain',
                    'reason': f"Actividad BUY saludable: {buy_pct:.1f}%"
                })
            
            if hold_pct > 90:
                recommendations.append({
                    'type': 'config_adjustment',
                    'priority': 'medium',
                    'message': f"⚠️ Demasiadas señales HOLD ({hold_pct:.1f}%). Considerar ajustar umbrales para ser más activo.",
                    'action': 'adjust_thresholds',
                    'reason': f"El {hold_pct:.1f}% de señales son HOLD, puede estar siendo demasiado conservador"
                })
        
        # 3. Recomendaciones de mejores horas
        best_hours = insights.get('best_hours', [])
        if best_hours:
            current_hour = datetime.now().hour
            best_hour = best_hours[0].get('hour')
            
            if best_hour is not None and abs(current_hour - best_hour) <= 1:
                recommendations.append({
                    'type': 'timing',
                    'priority': 'high',
                    'message': f"⏰ Estás en una de las mejores horas para trading ({current_hour}:00). Aumentar actividad.",
                    'action': 'increase_activity',
                    'reason': f"Hora actual ({current_hour}:00) coincide con mejores horas detectadas"
                })
            elif best_hour is not None:
                hours_until_best = (best_hour - current_hour) % 24
                recommendations.append({
                    'type': 'timing',
                    'priority': 'low',
                    'message': f"⏰ Mejor hora para trading: {best_hour}:00 (en {hours_until_best} horas)",
                    'action': 'plan_activity',
                    'reason': f"La hora {best_hour}:00 tiene mejor performance histórica"
                })
        
        # 4. Recomendaciones de condiciones de mercado
        best_conditions = insights.get('best_market_conditions', [])
        if best_conditions:
            recommendations.append({
                'type': 'market_condition',
                'priority': 'medium',
                'message': f"📊 Mejores condiciones detectadas: {', '.join([c.get('condition', 'N/A') for c in best_conditions[:3]])}",
                'action': 'monitor_conditions',
                'reason': 'Estas condiciones han mostrado mejor performance'
            })
        
        # 5. Recomendaciones de diversificación
        if insights.get('best_symbols'):
            symbol_count = len(insights['best_symbols'])
            if symbol_count < 5:
                recommendations.append({
                    'type': 'diversification',
                    'priority': 'low',
                    'message': f"📊 Solo {symbol_count} símbolos con buena performance. Considerar diversificar más.",
                    'action': 'diversify',
                    'reason': f'Pocos símbolos ({symbol_count}) con buena performance detectada'
                })
        
        return recommendations
    
    def generate_insights(self) -> Dict:
        """Genera insights y recomendaciones basadas en el aprendizaje"""
        # Primero intentar desde trades (si hay)
        trade_insights = {
            'timestamp': datetime.now().isoformat(),
            'best_symbols': self.symbol_tracker.get_best_symbols(),
            'worst_symbols': self.symbol_tracker.get_worst_symbols(),
            'best_hours': self.time_learning.get_best_hours(),
            'best_market_conditions': self.market_learning.get_best_conditions(),
            'recommendations': []
        }
        
        # MEJORA #1: Analizar operations_log.json para generar insights desde análisis
        analysis_data = self._analyze_operations_log()
        analysis_insights = self._generate_insights_from_analyses(analysis_data)
        
        # Combinar insights de trades y análisis
        # Priorizar insights de trades si hay suficientes, sino usar análisis
        has_trade_data = len(trade_insights['best_symbols']) > 0 or len(trade_insights['best_hours']) > 0
        
        if has_trade_data:
            # Usar datos de trades como base
            insights = trade_insights
            # Agregar insights de análisis como complemento
            if analysis_insights['best_symbols']:
                # Agregar símbolos de análisis que no estén en trades
                trade_symbols = {s['symbol'] for s in insights['best_symbols']}
                for symbol_insight in analysis_insights['best_symbols']:
                    if symbol_insight['symbol'] not in trade_symbols:
                        insights['best_symbols'].append({
                            'symbol': symbol_insight['symbol'],
                            'avg_score': symbol_insight['avg_score'],
                            'total_analyses': symbol_insight['total_analyses'],
                            'buy_signals': symbol_insight['buy_signals'],
                            'source': 'analysis'
                        })
        else:
            # No hay datos de trades, usar solo análisis
            insights = {
                'timestamp': datetime.now().isoformat(),
                'best_symbols': [{'symbol': s['symbol'], 'avg_score': s['avg_score'], 
                                'total_analyses': s['total_analyses'], 'buy_signals': s['buy_signals'],
                                'source': 'analysis'} for s in analysis_insights['best_symbols']],
                'worst_symbols': [],
                'best_hours': [{'hour': h['hour'], 'avg_score': h['avg_score'], 
                              'total_analyses': h['total_analyses'], 'buy_signals': h['buy_signals'],
                              'source': 'analysis'} for h in analysis_insights['best_hours']],
                'best_market_conditions': [],
                'recommendations': analysis_insights['recommendations']
            }
        
        # Agregar recomendaciones de trades si hay
        if has_trade_data:
            recommendations = []
            
            # Recomendación 1: Mejores símbolos
            best_symbols = trade_insights['best_symbols'][:3]
            if best_symbols:
                symbols_str = ', '.join([s['symbol'] for s in best_symbols])
                recommendations.append(
                    f"✅ Enfócate en estos símbolos (mejor rendimiento): {symbols_str}"
                )
            
            # Recomendación 2: Evitar peores símbolos
            worst_symbols = trade_insights['worst_symbols'][:3]
            if worst_symbols:
                symbols_str = ', '.join([s['symbol'] for s in worst_symbols])
                recommendations.append(
                    f"⚠️ Considera reducir o eliminar estos símbolos (bajo rendimiento): {symbols_str}"
                )
            
            # Recomendación 3: Mejores horarios
            best_hours = trade_insights['best_hours']
            if best_hours:
                hours_str = ', '.join([f"{h['hour']}:00" for h in best_hours])
                recommendations.append(
                    f"⏰ Mejores horarios para trading: {hours_str}"
                )
            
            # Recomendación 4: Mejores condiciones de mercado
            best_conditions = trade_insights['best_market_conditions']
            if best_conditions:
                conditions_str = ', '.join([c['condition'] for c in best_conditions[:3]])
                recommendations.append(
                    f"📊 Mejores condiciones de mercado: {conditions_str}"
                )
            
            # Combinar con recomendaciones de análisis
            insights['recommendations'].extend(recommendations)
        
        # MEJORA #3: Generar recomendaciones proactivas
        proactive_recommendations = self._generate_proactive_recommendations(analysis_data, insights)
        
        # MEJORA #4: Análisis de estrategias por performance
        strategy_performance = self.strategy_tracker.get_strategy_performance()
        strategy_recommendations = self.strategy_tracker.get_strategy_recommendations()
        
        # Agregar performance de estrategias a insights
        insights['strategy_performance'] = strategy_performance.get('strategies', {})
        insights['top_strategies'] = strategy_performance.get('top_strategies', [])
        insights['bottom_strategies'] = strategy_performance.get('bottom_strategies', [])
        
        # Agregar recomendaciones proactivas estructuradas
        if 'proactive_recommendations' not in insights:
            insights['proactive_recommendations'] = []
        
        insights['proactive_recommendations'] = proactive_recommendations
        insights['proactive_recommendations'].extend(strategy_recommendations)
        
        # También agregar mensajes simples a recommendations para compatibilidad
        for rec in proactive_recommendations:
            insights['recommendations'].append(rec.get('message', ''))
        
        for rec in strategy_recommendations:
            insights['recommendations'].append(rec.get('message', ''))
        
        # Guardar insights
        try:
            with open(self.insights_file, 'w', encoding='utf-8') as f:
                json.dump(insights, f, indent=2, default=str)
            logger.info(f"✅ Insights generados: {len(insights.get('best_symbols', []))} símbolos, {len(insights.get('best_hours', []))} horas, {len(proactive_recommendations)} recomendaciones proactivas")
        except Exception as e:
            logger.error(f"Error guardando insights: {e}")
        
        return insights
    
    def get_learning_summary(self) -> Dict:
        """Retorna un resumen del aprendizaje"""
        insights = self.generate_insights()
        
        return {
            'best_symbols_count': len(insights['best_symbols']),
            'worst_symbols_count': len(insights['worst_symbols']),
            'best_hours_count': len(insights['best_hours']),
            'recommendations_count': len(insights['recommendations']),
            'recommendations': insights['recommendations'],
            'last_updated': insights['timestamp']
        }


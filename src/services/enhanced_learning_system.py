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
    """Aprende qué horarios son mejores para trading"""
    
    def __init__(self, data_file: str = "data/learning/time_performance.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.time_stats = self._load_stats()
    
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
    
    def get_best_hours(self) -> List[Dict]:
        """Retorna las mejores horas para trading"""
        hours = []
        for key, stats in self.time_stats.items():
            if isinstance(key, int) and stats['trades'] >= 3:  # Al menos 3 trades
                win_rate = stats['wins'] / stats['trades'] if stats['trades'] > 0 else 0
                avg_pnl = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
                hours.append({
                    'hour': key,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'total_trades': stats['trades']
                })
        
        return sorted(hours, key=lambda x: x['win_rate'], reverse=True)[:5]


class MarketConditionLearning:
    """Aprende qué condiciones de mercado funcionan mejor"""
    
    def __init__(self, data_file: str = "data/learning/market_conditions.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.conditions = self._load_conditions()
    
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
    
    def get_best_conditions(self) -> List[Dict]:
        """Retorna las mejores condiciones de mercado para trading"""
        best = []
        for condition, stats in self.conditions.items():
            if stats['trades'] >= 3:
                win_rate = stats['wins'] / stats['trades'] if stats['trades'] > 0 else 0
                avg_pnl = stats['total_pnl'] / stats['trades'] if stats['trades'] > 0 else 0
                best.append({
                    'condition': condition,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'volatility': stats['volatility'],
                    'trend': stats['trend'],
                    'rsi_category': stats['rsi_category'],
                    'total_trades': stats['trades']
                })
        
        return sorted(best, key=lambda x: x['win_rate'], reverse=True)[:5]


class EnhancedLearningSystem:
    """Sistema completo de aprendizaje mejorado"""
    
    def __init__(self):
        self.symbol_tracker = SymbolPerformanceTracker()
        self.time_learning = TimeBasedLearning()
        self.market_learning = MarketConditionLearning()
        self.insights_file = Path("data/learning/insights.json")
        self.insights_file.parent.mkdir(parents=True, exist_ok=True)
    
    def learn_from_trade(self, symbol: str, pnl: float, pnl_pct: float, signal: str,
                        confidence: str, market_conditions: Dict):
        """Aprende de un trade completo"""
        # Aprender por símbolo
        self.symbol_tracker.record_trade(symbol, pnl, pnl_pct, signal, confidence, market_conditions)
        
        # Aprender por horario
        self.time_learning.record_trade(pnl, signal)
        
        # Aprender por condiciones de mercado
        self.market_learning.record_trade(market_conditions, pnl)
    
    def generate_insights(self) -> Dict:
        """Genera insights y recomendaciones basadas en el aprendizaje"""
        insights = {
            'timestamp': datetime.now().isoformat(),
            'best_symbols': self.symbol_tracker.get_best_symbols(),
            'worst_symbols': self.symbol_tracker.get_worst_symbols(),
            'best_hours': self.time_learning.get_best_hours(),
            'best_market_conditions': self.market_learning.get_best_conditions(),
            'recommendations': []
        }
        
        # Generar recomendaciones
        recommendations = []
        
        # Recomendación 1: Mejores símbolos
        best_symbols = insights['best_symbols'][:3]
        if best_symbols:
            symbols_str = ', '.join([s['symbol'] for s in best_symbols])
            recommendations.append(
                f"✅ Enfócate en estos símbolos (mejor rendimiento): {symbols_str}"
            )
        
        # Recomendación 2: Evitar peores símbolos
        worst_symbols = insights['worst_symbols'][:3]
        if worst_symbols:
            symbols_str = ', '.join([s['symbol'] for s in worst_symbols])
            recommendations.append(
                f"⚠️ Considera reducir o eliminar estos símbolos (bajo rendimiento): {symbols_str}"
            )
        
        # Recomendación 3: Mejores horarios
        best_hours = insights['best_hours']
        if best_hours:
            hours_str = ', '.join([f"{h['hour']}:00" for h in best_hours])
            recommendations.append(
                f"⏰ Mejores horarios para trading: {hours_str}"
            )
        
        # Recomendación 4: Mejores condiciones de mercado
        best_conditions = insights['best_market_conditions']
        if best_conditions:
            conditions_str = ', '.join([c['condition'] for c in best_conditions[:3]])
            recommendations.append(
                f"📊 Mejores condiciones de mercado: {conditions_str}"
            )
        
        insights['recommendations'] = recommendations
        
        # Guardar insights
        try:
            with open(self.insights_file, 'w', encoding='utf-8') as f:
                json.dump(insights, f, indent=2, default=str)
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


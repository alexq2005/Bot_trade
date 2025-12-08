"""
Sistema Avanzado de Aprendizaje Continuo
El bot aprende de cada trade, predicción y resultado para mejorar continuamente
"""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd

from src.core.database import SessionLocal
from src.core.logger import get_logger
from src.core.config_manager import get_config
from src.models.market_data import MarketData
from src.services.continuous_learning import ContinuousLearning

logger = get_logger("advanced_learning")


class TradeLearning:
    """Aprende de cada trade ejecutado"""
    
    def __init__(self, data_file: str = "data/learning/trade_history.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.trades = self._load_trades()
    
    def _load_trades(self) -> List[Dict]:
        """Carga historial de trades"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_trades(self):
        """Guarda historial de trades"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.trades, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando trades: {e}")
    
    def record_trade(self, trade_data: Dict):
        """Registra un trade para aprendizaje"""
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': trade_data.get('symbol'),
            'signal': trade_data.get('signal'),
            'entry_price': trade_data.get('entry_price'),
            'exit_price': trade_data.get('exit_price', None),
            'stop_loss': trade_data.get('stop_loss'),
            'take_profit': trade_data.get('take_profit'),
            'position_size': trade_data.get('position_size'),
            'ai_prediction': trade_data.get('ai_prediction'),
            'technical_score': trade_data.get('technical_score'),
            'confidence': trade_data.get('confidence'),
            'market_conditions': trade_data.get('market_conditions', {}),
            'pnl': trade_data.get('pnl', None),
            'pnl_pct': trade_data.get('pnl_pct', None),
            'outcome': trade_data.get('outcome', 'pending'),  # 'win', 'loss', 'pending'
        }
        
        self.trades.append(trade)
        self._save_trades()
        logger.info(f"Trade registrado para aprendizaje: {trade['symbol']} {trade['signal']}")
    
    def update_trade_outcome(self, trade_id: int, exit_price: float, pnl: float, pnl_pct: float):
        """Actualiza el resultado de un trade"""
        if 0 <= trade_id < len(self.trades):
            self.trades[trade_id]['exit_price'] = exit_price
            self.trades[trade_id]['pnl'] = pnl
            self.trades[trade_id]['pnl_pct'] = pnl_pct
            self.trades[trade_id]['outcome'] = 'win' if pnl > 0 else 'loss'
            self.trades[trade_id]['exit_timestamp'] = datetime.now().isoformat()
            self._save_trades()
    
    def analyze_winning_patterns(self) -> Dict:
        """Analiza patrones de trades ganadores"""
        if not self.trades:
            return {}
        
        df = pd.DataFrame(self.trades)
        completed = df[df['outcome'].isin(['win', 'loss'])]
        
        if len(completed) == 0:
            return {}
        
        wins = completed[completed['outcome'] == 'win']
        losses = completed[completed['outcome'] == 'loss']
        
        patterns = {
            'total_trades': len(completed),
            'win_rate': len(wins) / len(completed) if len(completed) > 0 else 0,
            'avg_win_pct': wins['pnl_pct'].mean() if len(wins) > 0 else 0,
            'avg_loss_pct': losses['pnl_pct'].mean() if len(losses) > 0 else 0,
            'best_signals': {},
            'best_confidence_levels': {},
            'best_technical_scores': {},
        }
        
        # Analizar qué señales funcionan mejor
        for signal in ['BUY', 'SELL']:
            signal_trades = completed[completed['signal'] == signal]
            if len(signal_trades) > 0:
                signal_wins = signal_trades[signal_trades['outcome'] == 'win']
                patterns['best_signals'][signal] = {
                    'win_rate': len(signal_wins) / len(signal_trades),
                    'total': len(signal_trades),
                }
        
        # Analizar niveles de confianza
        for conf in ['HIGH', 'MEDIUM', 'LOW']:
            conf_trades = completed[completed['confidence'] == conf]
            if len(conf_trades) > 0:
                conf_wins = conf_trades[conf_trades['outcome'] == 'win']
                patterns['best_confidence_levels'][conf] = {
                    'win_rate': len(conf_wins) / len(conf_trades),
                    'total': len(conf_trades),
                }
        
        return patterns
    
    def get_lessons_learned(self) -> List[str]:
        """Extrae lecciones aprendidas de los trades"""
        patterns = self.analyze_winning_patterns()
        lessons = []
        
        if not patterns:
            return ["Aún no hay suficientes datos para aprender"]
        
        # Lección 1: Win rate general
        win_rate = patterns.get('win_rate', 0)
        if win_rate > 0.6:
            lessons.append(f"✅ Excelente win rate: {win_rate*100:.1f}%")
        elif win_rate < 0.4:
            lessons.append(f"⚠️ Win rate bajo: {win_rate*100:.1f}% - Revisar estrategia")
        
        # Lección 2: Mejor señal
        best_signals = patterns.get('best_signals', {})
        if best_signals:
            best_signal = max(best_signals.items(), key=lambda x: x[1].get('win_rate', 0))
            lessons.append(f"📊 Mejor señal: {best_signal[0]} con {best_signal[1]['win_rate']*100:.1f}% win rate")
        
        # Lección 3: Nivel de confianza óptimo
        best_conf = patterns.get('best_confidence_levels', {})
        if best_conf:
            best = max(best_conf.items(), key=lambda x: x[1].get('win_rate', 0))
            lessons.append(f"🎯 Mejor confianza: {best[0]} con {best[1]['win_rate']*100:.1f}% win rate")
        
        return lessons


class PredictionFeedback:
    """Sistema de feedback de predicciones vs realidad"""
    
    def __init__(self, data_file: str = "data/learning/prediction_feedback.json"):
        self.data_file = Path(data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.predictions = self._load_predictions()
    
    def _load_predictions(self) -> List[Dict]:
        """Carga historial de predicciones"""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_predictions(self):
        """Guarda historial de predicciones"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.predictions, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando predicciones: {e}")
    
    def record_prediction(self, symbol: str, predicted_price: float, predicted_change: float, 
                         current_price: float, confidence: float, features: Dict):
        """Registra una predicción para evaluación posterior"""
        prediction = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'predicted_price': predicted_price,
            'predicted_change': predicted_change,
            'current_price': current_price,
            'confidence': confidence,
            'features': features,
            'actual_price': None,  # Se actualizará después
            'actual_change': None,
            'error': None,
            'direction_correct': None,
        }
        
        self.predictions.append(prediction)
        self._save_predictions()
    
    def update_with_actual(self, hours_later: int = 24):
        """Actualiza predicciones con precios reales"""
        updated_count = 0
        
        for pred in self.predictions:
            if pred['actual_price'] is not None:
                continue  # Ya actualizado
            
            pred_time = datetime.fromisoformat(pred['timestamp'])
            target_time = pred_time + timedelta(hours=hours_later)
            
            if datetime.now() < target_time:
                continue  # Aún no ha pasado el tiempo
            
            # Obtener precio real
            db = SessionLocal()
            try:
                record = db.query(MarketData).filter(
                    MarketData.symbol == pred['symbol'],
                    MarketData.timestamp >= target_time - timedelta(hours=1),
                    MarketData.timestamp <= target_time + timedelta(hours=1)
                ).order_by(MarketData.timestamp).first()
                
                if record:
                    pred['actual_price'] = record.close
                    pred['actual_change'] = ((record.close - pred['current_price']) / pred['current_price']) * 100
                    pred['error'] = abs(pred['predicted_price'] - record.close)
                    
                    # Verificar dirección
                    pred_direction = pred['predicted_change'] > 0
                    actual_direction = pred['actual_change'] > 0
                    pred['direction_correct'] = pred_direction == actual_direction
                    
                    updated_count += 1
            finally:
                db.close()
        
        if updated_count > 0:
            self._save_predictions()
            logger.info(f"Actualizadas {updated_count} predicciones con precios reales")
    
    def get_prediction_accuracy(self) -> Dict:
        """Calcula precisión de las predicciones"""
        if not self.predictions:
            return {}
        
        df = pd.DataFrame(self.predictions)
        evaluated = df[df['actual_price'].notna()]
        
        if len(evaluated) == 0:
            return {}
        
        return {
            'total_predictions': len(evaluated),
            'direction_accuracy': evaluated['direction_correct'].mean() * 100,
            'avg_error': evaluated['error'].mean(),
            'mape': (evaluated['error'] / evaluated['current_price']).mean() * 100,
            'rmse': np.sqrt((evaluated['error'] ** 2).mean()),
        }


class AdaptiveStrategy:
    """Estrategia adaptativa que aprende y se ajusta"""
    
    def __init__(self):
        self.strategy_params = {
            'buy_threshold': 25,
            'sell_threshold': -25,
            'confidence_weights': {'HIGH': 1.5, 'MEDIUM': 1.0, 'LOW': 0.5},
            'min_confidence': 'MEDIUM',
        }
        self.performance_history = []
        self.adaptation_log = []
    
    def adapt_based_on_performance(self, recent_performance: Dict):
        """Adapta parámetros basado en performance reciente"""
        win_rate = recent_performance.get('win_rate', 0.5)
        avg_return = recent_performance.get('avg_return', 0)
        
        adaptations = []
        
        # Si win rate es bajo, ser más conservador
        if win_rate < 0.4:
            old_threshold = self.strategy_params['buy_threshold']
            self.strategy_params['buy_threshold'] = min(35, old_threshold + 5)
            self.strategy_params['sell_threshold'] = max(-35, self.strategy_params['sell_threshold'] - 5)
            adaptations.append(f"Aumentado umbral de compra a {self.strategy_params['buy_threshold']} (win rate bajo)")
        
        # Si win rate es alto, ser más agresivo
        elif win_rate > 0.7:
            old_threshold = self.strategy_params['buy_threshold']
            self.strategy_params['buy_threshold'] = max(15, old_threshold - 5)
            self.strategy_params['sell_threshold'] = min(-15, self.strategy_params['sell_threshold'] + 5)
            adaptations.append(f"Reducido umbral de compra a {self.strategy_params['buy_threshold']} (win rate alto)")
        
        # Ajustar pesos de confianza
        if avg_return < 0:
            # Si retornos negativos, dar más peso a alta confianza
            self.strategy_params['confidence_weights']['HIGH'] = 2.0
            self.strategy_params['confidence_weights']['MEDIUM'] = 0.8
            adaptations.append("Aumentado peso de confianza alta (retornos negativos)")
        
        if adaptations:
            self.adaptation_log.append({
                'timestamp': datetime.now().isoformat(),
                'adaptations': adaptations,
                'new_params': self.strategy_params.copy(),
            })
            logger.info(f"Estrategia adaptada: {', '.join(adaptations)}")
        
        return adaptations
    
    def get_current_params(self) -> Dict:
        """Obtiene parámetros actuales de la estrategia"""
        return self.strategy_params.copy()


class AdvancedLearningSystem:
    """Sistema completo de aprendizaje avanzado"""
    
    def __init__(self):
        self.trade_learning = TradeLearning()
        self.prediction_feedback = PredictionFeedback()
        self.adaptive_strategy = AdaptiveStrategy()
        self.continuous_learning = ContinuousLearning()
        self.learning_stats = {
            'last_learning_cycle': None,
            'total_learning_cycles': 0,
            'improvements_made': [],
        }
    
    def learn_from_trade(self, trade_data: Dict):
        """Aprende de un trade ejecutado"""
        self.trade_learning.record_trade(trade_data)
    
    def learn_from_prediction(self, symbol: str, predicted_price: float, predicted_change: float,
                             current_price: float, confidence: float, features: Dict):
        """Registra una predicción para aprendizaje"""
        self.prediction_feedback.record_prediction(
            symbol, predicted_price, predicted_change, current_price, confidence, features
        )
    
    def run_learning_cycle(self):
        """Ejecuta un ciclo completo de aprendizaje"""
        logger.info("🔄 Iniciando ciclo de aprendizaje...")
        
        # 1. Actualizar feedback de predicciones
        self.prediction_feedback.update_with_actual()
        
        # 2. Analizar patrones de trades
        trade_patterns = self.trade_learning.analyze_winning_patterns()
        
        # 3. Obtener precisión de predicciones
        pred_accuracy = self.prediction_feedback.get_prediction_accuracy()
        
        # 4. Adaptar estrategia si es necesario
        if trade_patterns:
            recent_perf = {
                'win_rate': trade_patterns.get('win_rate', 0.5),
                'avg_return': trade_patterns.get('avg_win_pct', 0),
            }
            self.adaptive_strategy.adapt_based_on_performance(recent_perf)
        
        # 5. Reentrenar modelos si performance es baja
        if pred_accuracy and pred_accuracy.get('direction_accuracy', 100) < 55:
            logger.warning("Precisión de dirección baja - considerando reentrenamiento")
            # Aquí se podría activar reentrenamiento automático
        
        # 6. Guardar estadísticas
        self.learning_stats['last_learning_cycle'] = datetime.now().isoformat()
        self.learning_stats['total_learning_cycles'] += 1
        
        logger.info("✅ Ciclo de aprendizaje completado")
        
        return {
            'trade_patterns': trade_patterns,
            'prediction_accuracy': pred_accuracy,
            'strategy_params': self.adaptive_strategy.get_current_params(),
            'lessons_learned': self.trade_learning.get_lessons_learned(),
        }
    
    def get_learning_summary(self) -> Dict:
        """Obtiene resumen del aprendizaje"""
        return {
            'total_trades_learned': len(self.trade_learning.trades),
            'total_predictions_tracked': len(self.prediction_feedback.predictions),
            'trade_patterns': self.trade_learning.analyze_winning_patterns(),
            'prediction_accuracy': self.prediction_feedback.get_prediction_accuracy(),
            'strategy_params': self.adaptive_strategy.get_current_params(),
            'adaptations_made': len(self.adaptive_strategy.adaptation_log),
            'lessons_learned': self.trade_learning.get_lessons_learned(),
            'learning_stats': self.learning_stats,
        }
    
    def should_retrain_model(self, symbol: str) -> bool:
        """Determina si un modelo debe reentrenarse basado en aprendizaje"""
        # Verificar precisión de predicciones para este símbolo
        symbol_preds = [p for p in self.prediction_feedback.predictions 
                       if p['symbol'] == symbol and p['direction_correct'] is not None]
        
        if len(symbol_preds) < 10:
            return False  # No hay suficientes datos
        
        accuracy = sum(1 for p in symbol_preds if p['direction_correct']) / len(symbol_preds)
        
        # Si precisión es menor a 50%, reentrenar
        return accuracy < 0.50


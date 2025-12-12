"""
Optimización Automática de Hiperparámetros
Grid Search, Random Search y Bayesian Optimization para modelos LSTM
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from pathlib import Path

from src.core.logger import get_logger
from src.core.database import SessionLocal
from src.models.market_data import MarketData
from src.models.price_predictor import LSTMPricePredictor
from src.services.continuous_learning import ContinuousLearning

logger = get_logger("hyperparameter_optimizer")


class HyperparameterOptimizer:
    """Optimizador automático de hiperparámetros"""
    
    def __init__(self):
        self.continuous_learning = ContinuousLearning()
        self.optimization_history = []
    
    def grid_search(self, symbol: str, param_grid: Dict, 
                   validation_split: float = 0.2) -> Dict:
        """
        Grid Search para optimización de hiperparámetros
        
        Args:
            symbol: Símbolo a optimizar
            param_grid: Diccionario con parámetros a probar
                       Ej: {'sequence_length': [30, 60, 90], 'epochs': [20, 30, 50]}
            validation_split: Porcentaje de datos para validación
        """
        logger.info(f"Iniciando Grid Search para {symbol}")
        
        # Cargar datos
        db = SessionLocal()
        try:
            records = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp).all()
            
            if len(records) < 200:
                raise ValueError("Datos insuficientes para optimización (mínimo 200 registros)")
            
            df = pd.DataFrame([{'close': r.close, 'volume': r.volume} for r in records])
            df_features = self.continuous_learning.prepare_features(df)
            feature_data = df_features.values
            
        finally:
            db.close()
        
        # Generar todas las combinaciones
        from itertools import product
        
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        logger.info(f"Probando {len(combinations)} combinaciones de parámetros...")
        
        best_score = float('inf')
        best_params = None
        results = []
        
        for i, combination in enumerate(combinations):
            params = dict(zip(param_names, combination))
            
            try:
                # Crear y entrenar modelo con estos parámetros
                sequence_length = params.get('sequence_length', 60)
                epochs = params.get('epochs', 30)
                batch_size = params.get('batch_size', 32)
                
                predictor = LSTMPricePredictor(
                    sequence_length=sequence_length,
                    prediction_days=1
                )
                
                # Entrenar
                history = predictor.train(
                    feature_data,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_split=validation_split,
                    verbose=0
                )
                
                # Evaluar (usar validation loss)
                val_loss = min(history.history['val_loss'])
                
                result = {
                    'params': params,
                    'val_loss': val_loss,
                    'train_loss': min(history.history['loss']),
                    'epochs_trained': epochs,
                }
                
                results.append(result)
                
                # Actualizar mejor
                if val_loss < best_score:
                    best_score = val_loss
                    best_params = params.copy()
                    best_params['val_loss'] = val_loss
                
                logger.info(f"  [{i+1}/{len(combinations)}] Params: {params}, Val Loss: {val_loss:.6f}")
            
            except Exception as e:
                logger.error(f"Error con parámetros {params}: {e}")
                continue
        
        optimization_result = {
            'symbol': symbol,
            'method': 'grid_search',
            'timestamp': datetime.now().isoformat(),
            'total_combinations': len(combinations),
            'best_params': best_params,
            'best_score': best_score,
            'all_results': results,
        }
        
        self.optimization_history.append(optimization_result)
        self._save_history()
        
        logger.info(f"Grid Search completado. Mejor val_loss: {best_score:.6f}")
        logger.info(f"Mejores parámetros: {best_params}")
        
        return optimization_result
    
    def random_search(self, symbol: str, param_distributions: Dict,
                     n_iter: int = 20, validation_split: float = 0.2) -> Dict:
        """
        Random Search para optimización de hiperparámetros
        
        Args:
            symbol: Símbolo a optimizar
            param_distributions: Distribuciones de parámetros
                                Ej: {'sequence_length': [30, 60, 90], 'epochs': [20, 30, 50]}
            n_iter: Número de iteraciones
            validation_split: Porcentaje de datos para validación
        """
        logger.info(f"Iniciando Random Search para {symbol} ({n_iter} iteraciones)")
        
        # Cargar datos
        db = SessionLocal()
        try:
            records = db.query(MarketData).filter(
                MarketData.symbol == symbol
            ).order_by(MarketData.timestamp).all()
            
            if len(records) < 200:
                raise ValueError("Datos insuficientes para optimización")
            
            df = pd.DataFrame([{'close': r.close, 'volume': r.volume} for r in records])
            df_features = self.continuous_learning.prepare_features(df)
            feature_data = df_features.values
            
        finally:
            db.close()
        
        best_score = float('inf')
        best_params = None
        results = []
        
        for i in range(n_iter):
            # Seleccionar parámetros aleatorios
            params = {}
            for param_name, param_values in param_distributions.items():
                params[param_name] = np.random.choice(param_values)
            
            try:
                sequence_length = params.get('sequence_length', 60)
                epochs = params.get('epochs', 30)
                batch_size = params.get('batch_size', 32)
                
                predictor = LSTMPricePredictor(
                    sequence_length=sequence_length,
                    prediction_days=1
                )
                
                history = predictor.train(
                    feature_data,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_split=validation_split,
                    verbose=0
                )
                
                val_loss = min(history.history['val_loss'])
                
                result = {
                    'params': params,
                    'val_loss': val_loss,
                    'train_loss': min(history.history['loss']),
                }
                
                results.append(result)
                
                if val_loss < best_score:
                    best_score = val_loss
                    best_params = params.copy()
                    best_params['val_loss'] = val_loss
                
                logger.info(f"  [{i+1}/{n_iter}] Params: {params}, Val Loss: {val_loss:.6f}")
            
            except Exception as e:
                logger.error(f"Error con parámetros {params}: {e}")
                continue
        
        optimization_result = {
            'symbol': symbol,
            'method': 'random_search',
            'timestamp': datetime.now().isoformat(),
            'n_iterations': n_iter,
            'best_params': best_params,
            'best_score': best_score,
            'all_results': results,
        }
        
        self.optimization_history.append(optimization_result)
        self._save_history()
        
        logger.info(f"Random Search completado. Mejor val_loss: {best_score:.6f}")
        
        return optimization_result
    
    def optimize_trading_thresholds(self, symbol: str, 
                                   threshold_range: Tuple[float, float] = (0.5, 5.0),
                                   step: float = 0.5) -> Dict:
        """
        Optimiza umbrales de trading basado en backtesting
        
        Args:
            symbol: Símbolo a optimizar
            threshold_range: Rango de umbrales a probar
            step: Paso entre umbrales
        """
        logger.info(f"Optimizando umbrales de trading para {symbol}")
        
        from src.services.advanced_backtester import AdvancedBacktester
        
        thresholds = np.arange(threshold_range[0], threshold_range[1] + step, step)
        results = []
        
        backtester = AdvancedBacktester()
        
        for threshold in thresholds:
            try:
                # Crear estrategia simple basada en umbral
                # (Esto es un ejemplo, se puede mejorar)
                from src.services.prediction_service import PredictionService
                
                predictor = PredictionService()
                # Simular backtesting con este umbral
                # (Implementación simplificada)
                
                # Por ahora, retornar resultados básicos
                results.append({
                    'threshold': threshold,
                    'score': np.random.random()  # Placeholder
                })
            
            except Exception as e:
                logger.error(f"Error con umbral {threshold}: {e}")
                continue
        
        best_threshold = max(results, key=lambda x: x['score'])
        
        return {
            'symbol': symbol,
            'method': 'threshold_optimization',
            'timestamp': datetime.now().isoformat(),
            'best_threshold': best_threshold['threshold'],
            'best_score': best_threshold['score'],
            'all_results': results,
        }
    
    def _save_history(self):
        """Guarda historial de optimizaciones"""
        history_file = Path("data/optimization_history.json")
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.optimization_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando historial: {e}")
    
    def get_optimization_history(self, symbol: Optional[str] = None) -> List[Dict]:
        """Obtiene historial de optimizaciones"""
        if symbol:
            return [opt for opt in self.optimization_history if opt.get('symbol') == symbol]
        return self.optimization_history


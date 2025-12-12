"""
Meta-Learner - Ensemble inteligente
Aprende cuándo confiar en cada estrategia
"""
import numpy as np
import pandas as pd
from typing import Dict, List
from sklearn.ensemble import RandomForestClassifier
import pickle
from pathlib import Path


class MetaLearner:
    """
    Modelo de IA que aprende pesos óptimos para cada estrategia
    según condiciones del mercado
    """
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100, max_depth=10)
        self.model_file = Path('models/meta_learner.pkl')
        self.is_trained = False
        
        # Intentar cargar modelo existente
        if self.model_file.exists():
            try:
                with open(self.model_file, 'rb') as f:
                    self.model = pickle.load(f)
                    self.is_trained = True
            except:
                pass
    
    def combine_signals(
        self, 
        all_scores: Dict[str, float],
        market_conditions: Dict
    ) -> Dict:
        """
        Combina señales de todas las estrategias
        
        Args:
            all_scores: {'technical': 20, 'sentiment': 5, 'ai': 15, ...}
            market_conditions: {'regime': 'TRENDING', 'volatility': 0.25, ...}
        
        Returns:
            Score final ponderado y confianza
        """
        if not self.is_trained:
            # Si no está entrenado, usar pesos predeterminados
            return self._default_combination(all_scores, market_conditions)
        
        try:
            # Preparar features
            features = self._prepare_features(all_scores, market_conditions)
            
            # Predecir pesos óptimos
            predicted_weights = self.model.predict_proba([features])[0]
            
            # Aplicar pesos
            weighted_score = 0
            for i, (strategy, score) in enumerate(all_scores.items()):
                weight = predicted_weights[min(i, len(predicted_weights)-1)]
                weighted_score += score * weight
            
            return {
                'final_score': round(weighted_score, 2),
                'confidence': 'HIGH',
                'weights_used': 'ML_OPTIMIZED'
            }
            
        except:
            return self._default_combination(all_scores, market_conditions)
    
    def _default_combination(self, all_scores: Dict, market_conditions: Dict) -> Dict:
        """Combinación con pesos predeterminados según régimen"""
        regime = market_conditions.get('regime', 'UNKNOWN')
        
        # Pesos según régimen
        if regime == 'TRENDING':
            weights = {
                'multi_timeframe': 0.30,
                'technical': 0.25,
                'ai_prediction': 0.20,
                'regime': 0.15,
                'sentiment': 0.10
            }
        elif regime == 'RANGING':
            weights = {
                'technical': 0.30,
                'patterns': 0.25,
                'volume_profile': 0.20,
                'fractals': 0.15,
                'sentiment': 0.10
            }
        elif regime == 'VOLATILE':
            weights = {
                'monte_carlo': 0.35,
                'anomaly': 0.25,
                'technical': 0.20,
                'sentiment': 0.20
            }
        else:
            # Default: pesos balanceados
            weights = {k: 1/len(all_scores) for k in all_scores.keys()}
        
        # Calcular score ponderado
        weighted_score = 0
        for strategy, score in all_scores.items():
            weight = weights.get(strategy, 0.1)
            weighted_score += score * weight
        
        return {
            'final_score': round(weighted_score, 2),
            'confidence': 'MEDIUM',
            'weights_used': regime,
            'weights': weights
        }
    
    def _prepare_features(self, scores: Dict, conditions: Dict) -> List[float]:
        """Prepara features para el modelo"""
        features = []
        
        # Agregar scores
        for score in scores.values():
            features.append(score)
        
        # Agregar condiciones
        features.append(conditions.get('volatility', 0.20))
        features.append(1 if conditions.get('regime') == 'TRENDING' else 0)
        features.append(1 if conditions.get('regime') == 'RANGING' else 0)
        features.append(1 if conditions.get('regime') == 'VOLATILE' else 0)
        
        return features


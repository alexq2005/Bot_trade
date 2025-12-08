"""
Elliott Wave Analyzer - Detecta ondas de Elliott
Predice estructura de movimientos
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, List


class ElliottWaveAnalyzer:
    """
    Detecta ondas de Elliott (simplificado)
    
    Ondas impulsivas: 1, 2, 3, 4, 5
    Ondas correctivas: A, B, C
    """
    
    def detect_wave(self, df: pd.DataFrame) -> Dict:
        """Detecta onda actual (versión simplificada)"""
        if len(df) < 50:
            return {'error': 'Datos insuficientes', 'score': 0}
        
        try:
            # Encontrar pivots (máximos y mínimos locales)
            pivots = self._find_pivots(df)
            
            if len(pivots) < 5:
                return {'wave': 'UNKNOWN', 'score': 0}
            
            # Analizar estructura reciente
            recent_pivots = pivots[-5:]
            wave_type = self._classify_wave(recent_pivots, df)
            
            # Calcular score basado en onda
            score = self._get_wave_score(wave_type)
            
            return {
                'wave': wave_type,
                'score': score,
                'confidence': 'MEDIUM',
                'pivots_count': len(pivots)
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}
    
    def _find_pivots(self, df: pd.DataFrame, window: int = 5) -> List[Dict]:
        """Encuentra pivots (máximos y mínimos locales)"""
        pivots = []
        
        for i in range(window, len(df)-window):
            # Pivot alto
            if df['high'].iloc[i] == df['high'].iloc[i-window:i+window+1].max():
                pivots.append({'type': 'HIGH', 'price': df['high'].iloc[i], 'index': i})
            
            # Pivot bajo
            if df['low'].iloc[i] == df['low'].iloc[i-window:i+window+1].min():
                pivots.append({'type': 'LOW', 'price': df['low'].iloc[i], 'index': i})
        
        return pivots
    
    def _classify_wave(self, pivots: List[Dict], df: pd.DataFrame) -> str:
        """Clasifica onda actual (simplificado)"""
        if len(pivots) < 3:
            return 'UNKNOWN'
        
        # Patrón alcista: LOW, HIGH, LOW, HIGH, LOW...
        # Patrón bajista: HIGH, LOW, HIGH, LOW, HIGH...
        
        # Contar transiciones
        types = [p['type'] for p in pivots]
        
        # Si hay más highs que lows = posible impulso alcista
        highs = types.count('HIGH')
        lows = types.count('LOW')
        
        current_price = df['close'].iloc[-1]
        last_pivot = pivots[-1]
        
        # Simplificación de ondas
        if highs > lows and current_price > last_pivot['price']:
            return 'WAVE_3'  # Onda 3 (más fuerte)
        elif lows > highs:
            return 'WAVE_C'  # Corrección
        else:
            return 'WAVE_1'  # Inicio de impulso
    
    def _get_wave_score(self, wave: str) -> int:
        """Score por tipo de onda"""
        wave_scores = {
            'WAVE_1': +10,   # Inicio de impulso
            'WAVE_2': -5,    # Corrección
            'WAVE_3': +25,   # Impulso fuerte (mejor onda)
            'WAVE_4': -5,    # Corrección
            'WAVE_5': +10,   # Final de impulso (cuidado)
            'WAVE_A': -15,   # Corrección inicial
            'WAVE_B': +5,    # Rebote en corrección
            'WAVE_C': +15,   # Final de corrección (oportunidad)
            'UNKNOWN': 0
        }
        return wave_scores.get(wave, 0)


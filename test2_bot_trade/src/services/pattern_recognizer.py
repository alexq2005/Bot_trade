"""
Pattern Recognizer - Detecta patrones gráficos clásicos
Identifica formaciones alcistas y bajistas
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class PatternRecognizer:
    """Detecta patrones gráficos automáticamente"""
    
    def __init__(self):
        self.patterns = {
            # Patrones alcistas
            'CUP_AND_HANDLE': {'score': +30, 'description': 'Cup and Handle (muy alcista)'},
            'INVERSE_H&S': {'score': +35, 'description': 'Inverse Head & Shoulders'},
            'ASCENDING_TRIANGLE': {'score': +25, 'description': 'Triángulo ascendente'},
            'BULL_FLAG': {'score': +20, 'description': 'Bandera alcista'},
            'DOUBLE_BOTTOM': {'score': +30, 'description': 'Doble suelo'},
            
            # Patrones bajistas
            'HEAD_AND_SHOULDERS': {'score': -35, 'description': 'Head & Shoulders'},
            'DESCENDING_TRIANGLE': {'score': -25, 'description': 'Triángulo descendente'},
            'BEAR_FLAG': {'score': -20, 'description': 'Bandera bajista'},
            'DOUBLE_TOP': {'score': -30, 'description': 'Doble techo'}
        }
    
    def detect_all_patterns(self, df: pd.DataFrame) -> Dict:
        """Detecta todos los patrones posibles"""
        if len(df) < 30:
            return {'error': 'Datos insuficientes', 'score': 0}
        
        detected = []
        total_score = 0
        
        # Detectar cada patrón
        if self._detect_double_bottom(df):
            detected.append('DOUBLE_BOTTOM')
            total_score += self.patterns['DOUBLE_BOTTOM']['score']
        
        if self._detect_double_top(df):
            detected.append('DOUBLE_TOP')
            total_score += self.patterns['DOUBLE_TOP']['score']
        
        if self._detect_head_and_shoulders(df):
            detected.append('HEAD_AND_SHOULDERS')
            total_score += self.patterns['HEAD_AND_SHOULDERS']['score']
        
        if self._detect_inverse_head_shoulders(df):
            detected.append('INVERSE_H&S')
            total_score += self.patterns['INVERSE_H&S']['score']
        
        if self._detect_ascending_triangle(df):
            detected.append('ASCENDING_TRIANGLE')
            total_score += self.patterns['ASCENDING_TRIANGLE']['score']
        
        if self._detect_descending_triangle(df):
            detected.append('DESCENDING_TRIANGLE')
            total_score += self.patterns['DESCENDING_TRIANGLE']['score']
        
        if self._detect_bull_flag(df):
            detected.append('BULL_FLAG')
            total_score += self.patterns['BULL_FLAG']['score']
        
        if self._detect_bear_flag(df):
            detected.append('BEAR_FLAG')
            total_score += self.patterns['BEAR_FLAG']['score']
        
        return {
            'score': total_score,
            'patterns_detected': detected,
            'count': len(detected),
            'descriptions': [self.patterns[p]['description'] for p in detected]
        }
    
    def _detect_double_bottom(self, df: pd.DataFrame) -> bool:
        """Detecta doble suelo (alcista)"""
        if len(df) < 20:
            return False
        
        try:
            lows = df['low'].tail(20).values
            
            # Buscar 2 mínimos similares con pico en medio
            for i in range(len(lows)-10):
                for j in range(i+5, len(lows)-2):
                    # Dos mínimos similares (+/- 2%)
                    if abs(lows[i] - lows[j]) / lows[i] < 0.02:
                        # Verificar que hay pico en medio
                        middle_max = lows[i+1:j].max()
                        if middle_max > lows[i] * 1.03:  # 3% más alto
                            # Verificar que precio actual está subiendo
                            if df['close'].iloc[-1] > middle_max:
                                return True
            
            return False
        except:
            return False
    
    def _detect_double_top(self, df: pd.DataFrame) -> bool:
        """Detecta doble techo (bajista)"""
        if len(df) < 20:
            return False
        
        try:
            highs = df['high'].tail(20).values
            
            for i in range(len(highs)-10):
                for j in range(i+5, len(highs)-2):
                    if abs(highs[i] - highs[j]) / highs[i] < 0.02:
                        middle_min = highs[i+1:j].min()
                        if middle_min < highs[i] * 0.97:
                            if df['close'].iloc[-1] < middle_min:
                                return True
            
            return False
        except:
            return False
    
    def _detect_head_and_shoulders(self, df: pd.DataFrame) -> bool:
        """Detecta H&S (bajista)"""
        if len(df) < 15:
            return False
        
        try:
            highs = df['high'].tail(15).values
            
            # Buscar 3 picos: hombro, cabeza (más alto), hombro
            for i in range(2, len(highs)-2):
                left_shoulder = highs[i-2]
                head = highs[i]
                right_shoulder = highs[i+2] if i+2 < len(highs) else 0
                
                # Cabeza más alta que hombros
                if (head > left_shoulder * 1.03 and
                    head > right_shoulder * 1.03 and
                    abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                    
                    # Precio actual bajó debajo de neckline
                    neckline = min(df['low'].iloc[i-2:i+3])
                    if df['close'].iloc[-1] < neckline:
                        return True
            
            return False
        except:
            return False
    
    def _detect_inverse_head_shoulders(self, df: pd.DataFrame) -> bool:
        """Detecta H&S inverso (alcista)"""
        if len(df) < 15:
            return False
        
        try:
            lows = df['low'].tail(15).values
            
            for i in range(2, len(lows)-2):
                left_shoulder = lows[i-2]
                head = lows[i]
                right_shoulder = lows[i+2] if i+2 < len(lows) else float('inf')
                
                # Cabeza más baja que hombros
                if (head < left_shoulder * 0.97 and
                    head < right_shoulder * 0.97 and
                    abs(left_shoulder - right_shoulder) / left_shoulder < 0.05):
                    
                    neckline = max(df['high'].iloc[i-2:i+3])
                    if df['close'].iloc[-1] > neckline:
                        return True
            
            return False
        except:
            return False
    
    def _detect_ascending_triangle(self, df: pd.DataFrame) -> bool:
        """Triángulo ascendente (alcista)"""
        if len(df) < 15:
            return False
        
        try:
            # Resistencia horizontal + soporte ascendente
            highs = df['high'].tail(15).values
            lows = df['low'].tail(15).values
            
            # Resistencia horizontal (highs similares)
            resistance_level = highs[-5:].max()
            touches_resistance = sum(1 for h in highs if abs(h - resistance_level) / resistance_level < 0.01)
            
            # Soporte ascendente (lows subiendo)
            low_slope = (lows[-1] - lows[0]) / len(lows)
            
            if touches_resistance >= 2 and low_slope > 0:
                # Precio cerca de resistance = posible breakout
                if df['close'].iloc[-1] > resistance_level * 0.98:
                    return True
            
            return False
        except:
            return False
    
    def _detect_descending_triangle(self, df: pd.DataFrame) -> bool:
        """Triángulo descendente (bajista)"""
        if len(df) < 15:
            return False
        
        try:
            highs = df['high'].tail(15).values
            lows = df['low'].tail(15).values
            
            # Soporte horizontal
            support_level = lows[-5:].min()
            touches_support = sum(1 for l in lows if abs(l - support_level) / support_level < 0.01)
            
            # Resistencia descendente
            high_slope = (highs[-1] - highs[0]) / len(highs)
            
            if touches_support >= 2 and high_slope < 0:
                if df['close'].iloc[-1] < support_level * 1.02:
                    return True
            
            return False
        except:
            return False
    
    def _detect_bull_flag(self, df: pd.DataFrame) -> bool:
        """Bandera alcista"""
        if len(df) < 10:
            return False
        
        try:
            # Impulso alcista seguido de consolidación
            prices = df['close'].tail(10).values
            
            # Verificar impulso inicial (primeras 3-4 velas)
            impulse = (prices[3] - prices[0]) / prices[0]
            
            if impulse > 0.05:  # Subida >5%
                # Consolidación (últimas 4-6 velas laterales)
                consolidation = prices[-6:]
                consolidation_range = (consolidation.max() - consolidation.min()) / consolidation.mean()
                
                if consolidation_range < 0.03:  # Rango <3%
                    return True
            
            return False
        except:
            return False
    
    def _detect_bear_flag(self, df: pd.DataFrame) -> bool:
        """Bandera bajista"""
        if len(df) < 10:
            return False
        
        try:
            prices = df['close'].tail(10).values
            
            impulse = (prices[0] - prices[3]) / prices[0]
            
            if impulse > 0.05:  # Caída >5%
                consolidation = prices[-6:]
                consolidation_range = (consolidation.max() - consolidation.min()) / consolidation.mean()
                
                if consolidation_range < 0.03:
                    return True
            
            return False
        except:
            return False


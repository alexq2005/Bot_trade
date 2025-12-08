"""
Candlestick Pattern Analyzer - Detecta patrones de velas japonesas
Identifica señales de reversión y continuación
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class CandlestickAnalyzer:
    """Analiza patrones de velas japonesas"""
    
    def __init__(self):
        # Patrones alcistas (bullish)
        self.bullish_patterns = {
            'HAMMER': {'score': +15, 'description': 'Hammer (reversión alcista)'},
            'INVERTED_HAMMER': {'score': +12, 'description': 'Inverted Hammer (reversión alcista)'},
            'BULLISH_ENGULFING': {'score': +20, 'description': 'Bullish Engulfing (muy alcista)'},
            'PIERCING_PATTERN': {'score': +18, 'description': 'Piercing Pattern (reversión alcista)'},
            'MORNING_STAR': {'score': +25, 'description': 'Morning Star (muy alcista)'},
            'THREE_WHITE_SOLDIERS': {'score': +22, 'description': 'Three White Soldiers (continuación alcista)'},
            'BULLISH_HARAMI': {'score': +10, 'description': 'Bullish Harami (reversión alcista débil)'},
            'DOJI_BULLISH': {'score': +8, 'description': 'Doji en soporte (indecisión alcista)'},
        }
        
        # Patrones bajistas (bearish)
        self.bearish_patterns = {
            'HANGING_MAN': {'score': -15, 'description': 'Hanging Man (reversión bajista)'},
            'SHOOTING_STAR': {'score': -18, 'description': 'Shooting Star (reversión bajista)'},
            'BEARISH_ENGULFING': {'score': -20, 'description': 'Bearish Engulfing (muy bajista)'},
            'DARK_CLOUD': {'score': -18, 'description': 'Dark Cloud Cover (reversión bajista)'},
            'EVENING_STAR': {'score': -25, 'description': 'Evening Star (muy bajista)'},
            'THREE_BLACK_CROWS': {'score': -22, 'description': 'Three Black Crows (continuación bajista)'},
            'BEARISH_HARAMI': {'score': -10, 'description': 'Bearish Harami (reversión bajista débil)'},
            'DOJI_BEARISH': {'score': -8, 'description': 'Doji en resistencia (indecisión bajista)'},
        }
    
    def analyze(self, df: pd.DataFrame, lookback: int = 5) -> Dict:
        """
        Analiza patrones de velas en los últimos N períodos
        
        Args:
            df: DataFrame con OHLCV
            lookback: Número de velas a analizar (default: 5)
            
        Returns:
            Dict con patrones detectados y score
        """
        if len(df) < 3:
            return {'error': 'Datos insuficientes', 'score': 0}
        
        # Tomar últimas velas
        recent_df = df.tail(lookback).copy()
        
        detected_patterns = []
        total_score = 0
        
        # Analizar cada patrón
        for i in range(len(recent_df) - 1, -1, -1):  # Desde la más reciente hacia atrás
            if i >= len(recent_df):
                continue
                
            current = recent_df.iloc[i]
            
            # Patrones de 1 vela
            if i >= 0:
                pattern = self._detect_single_candle(current, recent_df, i)
                if pattern:
                    detected_patterns.append(pattern)
                    score = self._get_pattern_score(pattern)
                    total_score += score
            
            # Patrones de 2 velas
            if i >= 1:
                prev = recent_df.iloc[i-1]
                pattern = self._detect_two_candle(current, prev, recent_df, i)
                if pattern:
                    detected_patterns.append(pattern)
                    score = self._get_pattern_score(pattern)
                    total_score += score
            
            # Patrones de 3 velas
            if i >= 2:
                prev1 = recent_df.iloc[i-1]
                prev2 = recent_df.iloc[i-2]
                pattern = self._detect_three_candle(current, prev1, prev2, recent_df, i)
                if pattern:
                    detected_patterns.append(pattern)
                    score = self._get_pattern_score(pattern)
                    total_score += score
        
        # Eliminar duplicados (mismo patrón en diferentes posiciones)
        unique_patterns = []
        seen = set()
        for p in detected_patterns:
            if p['pattern'] not in seen:
                unique_patterns.append(p)
                seen.add(p['pattern'])
        
        return {
            'score': total_score,
            'patterns_detected': [p['pattern'] for p in unique_patterns],
            'patterns': unique_patterns,
            'count': len(unique_patterns),
            'descriptions': [p['description'] for p in unique_patterns]
        }
    
    def _detect_single_candle(self, candle: pd.Series, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detecta patrones de 1 vela"""
        open_price = candle['open']
        high = candle['high']
        low = candle['low']
        close = candle['close']
        
        body = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        total_range = high - low
        
        if total_range == 0:
            return None
        
        body_ratio = body / total_range
        upper_ratio = upper_shadow / total_range
        lower_ratio = lower_shadow / total_range
        
        # Doji (cuerpo muy pequeño)
        if body_ratio < 0.1:
            # Verificar contexto (soporte/resistencia)
            if idx > 0:
                prev_close = df.iloc[idx-1]['close']
                if close < prev_close * 0.98:  # En soporte
                    return {'pattern': 'DOJI_BULLISH', 'description': 'Doji en soporte', 'position': idx}
                elif close > prev_close * 1.02:  # En resistencia
                    return {'pattern': 'DOJI_BEARISH', 'description': 'Doji en resistencia', 'position': idx}
        
        # Hammer (cuerpo pequeño, sombra inferior larga)
        if body_ratio < 0.3 and lower_ratio > 0.6 and upper_ratio < 0.1:
            if close > open_price:  # Vela alcista
                return {'pattern': 'HAMMER', 'description': 'Hammer (alcista)', 'position': idx}
        
        # Inverted Hammer (cuerpo pequeño, sombra superior larga)
        if body_ratio < 0.3 and upper_ratio > 0.6 and lower_ratio < 0.1:
            if close > open_price:  # Vela alcista
                return {'pattern': 'INVERTED_HAMMER', 'description': 'Inverted Hammer (alcista)', 'position': idx}
        
        # Hanging Man (similar a Hammer pero en resistencia)
        if body_ratio < 0.3 and lower_ratio > 0.6 and upper_ratio < 0.1:
            if close < open_price and idx > 0:  # Vela bajista en resistencia
                prev_high = df.iloc[idx-1]['high']
                if high > prev_high * 0.99:
                    return {'pattern': 'HANGING_MAN', 'description': 'Hanging Man (bajista)', 'position': idx}
        
        # Shooting Star (sombra superior larga, cuerpo pequeño)
        if body_ratio < 0.3 and upper_ratio > 0.6 and lower_ratio < 0.1:
            if close < open_price:  # Vela bajista
                return {'pattern': 'SHOOTING_STAR', 'description': 'Shooting Star (bajista)', 'position': idx}
        
        return None
    
    def _detect_two_candle(self, current: pd.Series, prev: pd.Series, df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detecta patrones de 2 velas"""
        prev_open = prev['open']
        prev_close = prev['close']
        prev_high = prev['high']
        prev_low = prev['low']
        
        curr_open = current['open']
        curr_close = current['close']
        curr_high = current['high']
        curr_low = current['low']
        
        # Bullish Engulfing
        if (prev_close < prev_open and  # Vela anterior bajista
            curr_close > curr_open and  # Vela actual alcista
            curr_open < prev_close and  # Abre por debajo del cierre anterior
            curr_close > prev_open):  # Cierra por encima de la apertura anterior
            return {'pattern': 'BULLISH_ENGULFING', 'description': 'Bullish Engulfing', 'position': idx}
        
        # Bearish Engulfing
        if (prev_close > prev_open and  # Vela anterior alcista
            curr_close < curr_open and  # Vela actual bajista
            curr_open > prev_close and  # Abre por encima del cierre anterior
            curr_close < prev_open):  # Cierra por debajo de la apertura anterior
            return {'pattern': 'BEARISH_ENGULFING', 'description': 'Bearish Engulfing', 'position': idx}
        
        # Piercing Pattern
        if (prev_close < prev_open and  # Vela anterior bajista
            curr_close > curr_open and  # Vela actual alcista
            curr_open < prev_low and  # Abre por debajo del mínimo anterior
            curr_close > (prev_open + prev_close) / 2):  # Cierra en la mitad superior del cuerpo anterior
            return {'pattern': 'PIERCING_PATTERN', 'description': 'Piercing Pattern', 'position': idx}
        
        # Dark Cloud Cover
        if (prev_close > prev_open and  # Vela anterior alcista
            curr_close < curr_open and  # Vela actual bajista
            curr_open > prev_high and  # Abre por encima del máximo anterior
            curr_close < (prev_open + prev_close) / 2):  # Cierra en la mitad inferior del cuerpo anterior
            return {'pattern': 'DARK_CLOUD', 'description': 'Dark Cloud Cover', 'position': idx}
        
        # Bullish Harami
        if (prev_close < prev_open and  # Vela anterior bajista
            curr_open > prev_close and  # Abre por encima del cierre anterior
            curr_close < prev_open):  # Cierra por debajo de la apertura anterior
            body_prev = abs(prev_close - prev_open)
            body_curr = abs(curr_close - curr_open)
            if body_curr < body_prev * 0.5:  # Cuerpo actual mucho más pequeño
                return {'pattern': 'BULLISH_HARAMI', 'description': 'Bullish Harami', 'position': idx}
        
        # Bearish Harami
        if (prev_close > prev_open and  # Vela anterior alcista
            curr_open < prev_close and  # Abre por debajo del cierre anterior
            curr_close > prev_open):  # Cierra por encima de la apertura anterior
            body_prev = abs(prev_close - prev_open)
            body_curr = abs(curr_close - curr_open)
            if body_curr < body_prev * 0.5:  # Cuerpo actual mucho más pequeño
                return {'pattern': 'BEARISH_HARAMI', 'description': 'Bearish Harami', 'position': idx}
        
        return None
    
    def _detect_three_candle(self, current: pd.Series, prev1: pd.Series, prev2: pd.Series, 
                            df: pd.DataFrame, idx: int) -> Optional[Dict]:
        """Detecta patrones de 3 velas"""
        # Morning Star
        if (prev2['close'] < prev2['open'] and  # Primera vela bajista
            abs(prev1['close'] - prev1['open']) / (prev1['high'] - prev1['low']) < 0.3 and  # Segunda vela pequeña (estrella)
            current['close'] > current['open'] and  # Tercera vela alcista
            current['close'] > (prev2['open'] + prev2['close']) / 2):  # Cierra en mitad superior de primera
            return {'pattern': 'MORNING_STAR', 'description': 'Morning Star', 'position': idx}
        
        # Evening Star
        if (prev2['close'] > prev2['open'] and  # Primera vela alcista
            abs(prev1['close'] - prev1['open']) / (prev1['high'] - prev1['low']) < 0.3 and  # Segunda vela pequeña (estrella)
            current['close'] < current['open'] and  # Tercera vela bajista
            current['close'] < (prev2['open'] + prev2['close']) / 2):  # Cierra en mitad inferior de primera
            return {'pattern': 'EVENING_STAR', 'description': 'Evening Star', 'position': idx}
        
        # Three White Soldiers
        if (len(df) >= 3 and idx >= 2):
            three_candles = df.iloc[idx-2:idx+1]
            if all(c['close'] > c['open'] for _, c in three_candles.iterrows()):  # Todas alcistas
                if all(three_candles.iloc[i]['close'] > three_candles.iloc[i-1]['close'] 
                       for i in range(1, len(three_candles))):  # Cada una más alta
                    return {'pattern': 'THREE_WHITE_SOLDIERS', 'description': 'Three White Soldiers', 'position': idx}
        
        # Three Black Crows
        if (len(df) >= 3 and idx >= 2):
            three_candles = df.iloc[idx-2:idx+1]
            if all(c['close'] < c['open'] for _, c in three_candles.iterrows()):  # Todas bajistas
                if all(three_candles.iloc[i]['close'] < three_candles.iloc[i-1]['close'] 
                       for i in range(1, len(three_candles))):  # Cada una más baja
                    return {'pattern': 'THREE_BLACK_CROWS', 'description': 'Three Black Crows', 'position': idx}
        
        return None
    
    def _get_pattern_score(self, pattern: Dict) -> int:
        """Obtiene score de un patrón"""
        pattern_name = pattern['pattern']
        
        if pattern_name in self.bullish_patterns:
            return self.bullish_patterns[pattern_name]['score']
        elif pattern_name in self.bearish_patterns:
            return self.bearish_patterns[pattern_name]['score']
        
        return 0


# Test
if __name__ == "__main__":
    import pandas as pd
    
    # Crear datos de prueba
    dates = pd.date_range('2025-01-01', periods=10, freq='D')
    data = {
        'open': [100, 98, 97, 99, 101, 103, 102, 100, 99, 101],
        'high': [102, 99, 98, 101, 103, 105, 104, 102, 101, 103],
        'low': [98, 97, 96, 98, 100, 102, 101, 99, 98, 100],
        'close': [99, 97, 98, 100, 102, 104, 103, 101, 100, 102],
        'volume': [1000] * 10
    }
    df = pd.DataFrame(data, index=dates)
    
    analyzer = CandlestickAnalyzer()
    result = analyzer.analyze(df, lookback=5)
    
    print("=== Análisis de Velas ===")
    print(f"Patrones detectados: {result['count']}")
    print(f"Score total: {result['score']}")
    print(f"Patrones: {result['patterns_detected']}")
    print(f"Descripciones: {result['descriptions']}")


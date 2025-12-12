"""
Fractal Analyzer - Detecta fractales de Williams
Identifica soportes y resistencias dinámicos
"""
import pandas as pd
import numpy as np
from typing import List, Dict


class FractalAnalyzer:
    """Detecta fractales para identificar reversiones"""
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Detecta fractales alcistas y bajistas
        
        Fractal alcista: Mínimo con 2 velas mayores a cada lado
        Fractal bajista: Máximo con 2 velas menores a cada lado
        """
        if len(df) < 5:
            return {'error': 'Datos insuficientes', 'score': 0}
        
        try:
            bullish_fractals = []
            bearish_fractals = []
            
            for i in range(2, len(df)-2):
                # Fractal alcista (soporte)
                if (df['low'].iloc[i] < df['low'].iloc[i-1] and
                    df['low'].iloc[i] < df['low'].iloc[i-2] and
                    df['low'].iloc[i] < df['low'].iloc[i+1] and
                    df['low'].iloc[i] < df['low'].iloc[i+2]):
                    
                    bullish_fractals.append({
                        'index': i,
                        'price': df['low'].iloc[i],
                        'date': df.index[i]
                    })
                
                # Fractal bajista (resistencia)
                if (df['high'].iloc[i] > df['high'].iloc[i-1] and
                    df['high'].iloc[i] > df['high'].iloc[i-2] and
                    df['high'].iloc[i] > df['high'].iloc[i+1] and
                    df['high'].iloc[i] > df['high'].iloc[i+2]):
                    
                    bearish_fractals.append({
                        'index': i,
                        'price': df['high'].iloc[i],
                        'date': df.index[i]
                    })
            
            current_price = df['close'].iloc[-1]
            score = 0
            factors = []
            
            # Verificar si precio está cerca de fractal
            if bullish_fractals:
                nearest_support = min(bullish_fractals, key=lambda f: abs(f['price'] - current_price))
                distance = abs(current_price - nearest_support['price']) / current_price
                
                if distance < 0.02:  # Dentro del 2%
                    score += 15
                    factors.append(f'Cerca de soporte fractal (+15)')
            
            if bearish_fractals:
                nearest_resistance = min(bearish_fractals, key=lambda f: abs(f['price'] - current_price))
                distance = abs(current_price - nearest_resistance['price']) / current_price
                
                if distance < 0.02:
                    score -= 15
                    factors.append(f'Cerca de resistencia fractal (-15)')
            
            return {
                'score': score,
                'bullish_fractals': len(bullish_fractals),
                'bearish_fractals': len(bearish_fractals),
                'factors': factors
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}


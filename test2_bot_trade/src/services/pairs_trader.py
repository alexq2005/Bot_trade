"""
Pairs Trader - Statistical Arbitrage
Detecta desbalances en pares correlacionados
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class PairsTrader:
    """Estrategia de arbitraje estadístico con pares"""
    
    def __init__(self):
        # Pares conocidos en mercado argentino
        self.pairs = [
            ('GGAL', 'BMA'),    # Bancos
            ('YPFD', 'PAMP'),   # Energía
            ('BYMA', 'COME'),   # Utilities
            ('TGNO4', 'TGSU2'), # Transener
        ]
    
    def analyze_pair(self, symbol_a: str, symbol_b: str, df_a: pd.DataFrame, df_b: pd.DataFrame) -> Dict:
        """
        Analiza un par de activos correlacionados
        
        Returns:
            Señales para cada símbolo si hay desbalance
        """
        if len(df_a) < 60 or len(df_b) < 60:
            return {'error': 'Datos insuficientes', 'score': 0}
        
        try:
            # Alinear fechas
            common_dates = df_a.index.intersection(df_b.index)
            if len(common_dates) < 60:
                return {'error': 'Fechas no coinciden', 'score': 0}
            
            price_a = df_a.loc[common_dates, 'close']
            price_b = df_b.loc[common_dates, 'close']
            
            # Calcular ratio de precios
            ratio = price_a / price_b
            
            # Calcular estadísticas del ratio
            mean_ratio = ratio.mean()
            std_ratio = ratio.std()
            current_ratio = ratio.iloc[-1]
            
            # Z-score
            z_score = (current_ratio - mean_ratio) / std_ratio if std_ratio > 0 else 0
            
            # Generar señales
            signals = {}
            
            if z_score > 2:
                # symbol_a muy caro vs symbol_b
                signals[symbol_a] = {'signal': 'SELL', 'score': -20, 'reason': f'{symbol_a} sobrevalorado vs {symbol_b}'}
                signals[symbol_b] = {'signal': 'BUY', 'score': +20, 'reason': f'{symbol_b} infravalorado vs {symbol_a}'}
            elif z_score < -2:
                # symbol_a muy barato vs symbol_b
                signals[symbol_a] = {'signal': 'BUY', 'score': +20, 'reason': f'{symbol_a} infravalorado vs {symbol_b}'}
                signals[symbol_b] = {'signal': 'SELL', 'score': -20, 'reason': f'{symbol_b} sobrevalorado vs {symbol_a}'}
            
            return {
                'pair': f'{symbol_a}/{symbol_b}',
                'z_score': round(z_score, 2),
                'mean_ratio': round(mean_ratio, 4),
                'current_ratio': round(current_ratio, 4),
                'signals': signals,
                'total_score': sum(s['score'] for s in signals.values()) if signals else 0
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}


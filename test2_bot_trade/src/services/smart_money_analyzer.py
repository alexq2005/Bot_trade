"""
Smart Money Concepts (SMC) Analyzer
Sigue institucionales para detectar manipulación y oportunidades
"""
import pandas as pd
import numpy as np
from typing import Dict, List


class SmartMoneyAnalyzer:
    """Implementa conceptos de Smart Money (ICT)"""
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Analiza según Smart Money Concepts
        
        Detecta:
        - Order Blocks (zonas de acumulación institucional)
        - Fair Value Gaps (desbalances de precio)
        - Liquidity Sweeps (barridas de liquidez)
        """
        if len(df) < 50:
            return {'error': 'Datos insuficientes', 'score': 0}
        
        try:
            score = 0
            factors = []
            
            # 1. Detectar Order Blocks
            ob = self._detect_order_block(df)
            if ob:
                score += ob['score']
                factors.append(ob['reason'])
            
            # 2. Detectar Fair Value Gaps
            fvg = self._detect_fair_value_gap(df)
            if fvg:
                score += fvg['score']
                factors.append(fvg['reason'])
            
            # 3. Detectar Liquidity Sweep
            sweep = self._detect_liquidity_sweep(df)
            if sweep:
                score += sweep['score']
                factors.append(sweep['reason'])
            
            return {
                'score': score,
                'factors': factors,
                'order_block': ob,
                'fvg': fvg,
                'liquidity_sweep': sweep
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}
    
    def _detect_order_block(self, df: pd.DataFrame) -> Dict:
        """Detecta Order Block (zona de acumulación)"""
        try:
            # Order block = última vela bajista antes de impulso alcista
            for i in range(len(df)-10, len(df)-1):
                if df['close'].iloc[i] < df['open'].iloc[i]:  # Vela bajista
                    # Verificar impulso alcista después
                    if df['close'].iloc[i+1:].max() > df['high'].iloc[i] * 1.05:
                        # Precio actual cerca del order block
                        current = df['close'].iloc[-1]
                        ob_low = df['low'].iloc[i]
                        ob_high = df['high'].iloc[i]
                        
                        if ob_low <= current <= ob_high:
                            return {
                                'score': +25,
                                'reason': 'Precio en Order Block alcista (+25)',
                                'zone': (ob_low, ob_high)
                            }
            
            return None
        except:
            return None
    
    def _detect_fair_value_gap(self, df: pd.DataFrame) -> Dict:
        """Detecta Fair Value Gap (FVG) - Desbalances"""
        try:
            # FVG = gap entre vela[i-1].low y vela[i+1].high
            for i in range(len(df)-3, len(df)-1):
                prev_high = df['high'].iloc[i-1]
                next_low = df['low'].iloc[i+1]
                
                # Gap alcista
                if next_low > prev_high:
                    gap_size = (next_low - prev_high) / prev_high
                    if gap_size > 0.02:  # Gap >2%
                        current = df['close'].iloc[-1]
                        if prev_high <= current <= next_low:
                            return {
                                'score': +20,
                                'reason': f'FVG alcista llenándose (+20)',
                                'gap': (prev_high, next_low)
                            }
            
            return None
        except:
            return None
    
    def _detect_liquidity_sweep(self, df: pd.DataFrame) -> Dict:
        """Detecta barrida de liquidez"""
        try:
            # Sweep = precio baja bajo mínimo previo y revierte rápido
            recent = df.tail(10)
            
            for i in range(len(recent)-3):
                local_low = recent['low'].iloc[i]
                
                # Precio baja bajo el mínimo
                if recent['low'].iloc[i+1] < local_low:
                    # Revierte rápidamente
                    if recent['close'].iloc[i+2] > local_low:
                        return {
                            'score': +25,
                            'reason': 'Liquidity sweep detectado (+25)',
                            'swept_level': local_low
                        }
            
            return None
        except:
            return None


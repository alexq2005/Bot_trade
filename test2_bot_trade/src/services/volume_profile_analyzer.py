"""
Volume Profile Analyzer - Perfil de volumen por precio
Identifica zonas de valor, soportes y resistencias reales
"""
import pandas as pd
import numpy as np
from typing import Dict


class VolumeProfileAnalyzer:
    """Analiza distribución de volumen por nivel de precio"""
    
    def analyze(self, df: pd.DataFrame, num_bins: int = 20) -> Dict:
        """
        Crea perfil de volumen
        
        Args:
            df: DataFrame con OHLCV
            num_bins: Número de niveles de precio
        """
        if len(df) < 30:
            return {'error': 'Datos insuficientes', 'score': 0}
        
        try:
            # Crear bins de precio
            price_min = df['low'].min()
            price_max = df['high'].max()
            bins = np.linspace(price_min, price_max, num_bins)
            
            # Asignar volumen a cada bin
            volume_by_price = {}
            
            for i in range(len(df)):
                price_level = (df['high'].iloc[i] + df['low'].iloc[i]) / 2
                volume = df['volume'].iloc[i]
                
                # Encontrar bin más cercano
                bin_idx = np.digitize(price_level, bins) - 1
                bin_idx = max(0, min(bin_idx, len(bins)-2))
                
                bin_key = round(bins[bin_idx], 2)
                volume_by_price[bin_key] = volume_by_price.get(bin_key, 0) + volume
            
            # Encontrar Point of Control (POC) = precio con más volumen
            if not volume_by_price:
                return {'error': 'Sin datos de volumen', 'score': 0}
            
            poc_price = max(volume_by_price, key=volume_by_price.get)
            poc_volume = volume_by_price[poc_price]
            
            # Encontrar Value Area (70% del volumen total)
            total_volume = sum(volume_by_price.values())
            value_area = self._find_value_area(volume_by_price, total_volume * 0.70)
            
            # Precio actual
            current_price = df['close'].iloc[-1]
            
            # Calcular score basado en posición vs value area
            score = 0
            factors = []
            
            if current_price < value_area['low']:
                # Precio por debajo de value area = barato
                distance = ((value_area['low'] - current_price) / current_price) * 100
                score = min(25, int(distance * 5))
                factors.append(f'Debajo de value area (+{score})')
            elif current_price > value_area['high']:
                # Precio por encima de value area = caro
                distance = ((current_price - value_area['high']) / current_price) * 100
                score = max(-25, -int(distance * 5))
                factors.append(f'Encima de value area ({score})')
            else:
                # Dentro de value area
                if abs(current_price - poc_price) / current_price < 0.01:
                    factors.append('En POC (zona de equilibrio)')
            
            return {
                'score': score,
                'poc': poc_price,
                'value_area_low': value_area['low'],
                'value_area_high': value_area['high'],
                'current_price': current_price,
                'factors': factors
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}
    
    def _find_value_area(self, volume_by_price: Dict, target_volume: float) -> Dict:
        """Encuentra value area (70% del volumen)"""
        # Ordenar por volumen descendente
        sorted_prices = sorted(volume_by_price.items(), key=lambda x: x[1], reverse=True)
        
        accumulated_volume = 0
        prices_in_va = []
        
        for price, volume in sorted_prices:
            accumulated_volume += volume
            prices_in_va.append(price)
            
            if accumulated_volume >= target_volume:
                break
        
        if not prices_in_va:
            return {'low': 0, 'high': 0}
        
        return {
            'low': min(prices_in_va),
            'high': max(prices_in_va)
        }


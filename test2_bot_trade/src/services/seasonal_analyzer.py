"""
Seasonal Analyzer - Detecta patrones estacionales
Aprovecha tendencias históricas por mes, día, hora
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict


class SeasonalAnalyzer:
    """
    Analiza patrones estacionales históricos
    """
    
    def __init__(self):
        # Efectos conocidos
        self.month_effects = {
            1: ('January Effect', +5),  # Acciones pequeñas suben
            12: ('Santa Rally', +8),     # Rally de fin de año
            9: ('September Effect', -5), # Históricamente bajista
            10: ('October Volatility', -3), # Volatile
        }
        
        self.day_effects = {
            0: ('Monday Effect', -3),    # Lunes tiende a bajar
            4: ('Friday Effect', +5),    # Viernes tiende a subir
        }
    
    def analyze(self, symbol: str, df: pd.DataFrame) -> Dict:
        """
        Analiza patrones estacionales
        
        Args:
            symbol: Símbolo del activo
            df: DataFrame con datos históricos (mínimo 1 año)
        
        Returns:
            Dict con análisis estacional
        """
        if len(df) < 250:  # Menos de 1 año
            return {'error': 'Datos insuficientes (necesita 1 año)', 'score': 0}
        
        try:
            score = 0
            factors = []
            
            now = datetime.now()
            current_month = now.month
            current_day = now.weekday()
            
            # 1. Análisis mensual
            month_score = self._analyze_month_pattern(df, current_month)
            if month_score:
                score += month_score['score']
                factors.extend(month_score['factors'])
            
            # 2. Análisis día de la semana
            day_score = self._analyze_day_pattern(df, current_day)
            if day_score:
                score += day_score['score']
                factors.extend(day_score['factors'])
            
            # 3. Efectos conocidos
            if current_month in self.month_effects:
                effect_name, effect_score = self.month_effects[current_month]
                score += effect_score
                factors.append(f'{effect_name} ({effect_score:+d})')
            
            if current_day in self.day_effects:
                effect_name, effect_score = self.day_effects[current_day]
                score += effect_score
                factors.append(f'{effect_name} ({effect_score:+d})')
            
            return {
                'score': score,
                'factors': factors,
                'month': current_month,
                'day': current_day,
                'confidence': 'HIGH' if abs(score) > 10 else 'MEDIUM' if abs(score) > 5 else 'LOW'
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}
    
    def _analyze_month_pattern(self, df: pd.DataFrame, month: int) -> Dict:
        """Analiza rendimiento histórico en este mes"""
        try:
            # Filtrar datos de este mes en años anteriores
            df['month'] = pd.to_datetime(df.index).month
            month_data = df[df['month'] == month].copy()
            
            if len(month_data) < 10:
                return None
            
            # Calcular retorno promedio
            month_data['return'] = month_data['close'].pct_change()
            avg_return = month_data['return'].mean()
            
            # Convertir a score
            score = int(avg_return * 100)  # % a puntos
            
            if abs(score) > 2:
                return {
                    'score': score,
                    'factors': [f'Patrón mensual ({avg_return*100:.1f}% promedio en mes {month})']
                }
            
            return None
            
        except:
            return None
    
    def _analyze_day_pattern(self, df: pd.DataFrame, day: int) -> Dict:
        """Analiza rendimiento histórico en este día de la semana"""
        try:
            # Filtrar datos de este día de semana
            df['dayofweek'] = pd.to_datetime(df.index).dayofweek
            day_data = df[df['dayofweek'] == day].copy()
            
            if len(day_data) < 20:
                return None
            
            # Calcular retorno promedio
            day_data['return'] = day_data['close'].pct_change()
            avg_return = day_data['return'].mean()
            
            # Convertir a score
            score = int(avg_return * 200)  # Menor peso que mes
            
            if abs(score) > 1:
                day_names = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
                return {
                    'score': score,
                    'factors': [f'{day_names[day]} ({avg_return*100:.2f}% promedio)']
                }
            
            return None
            
        except:
            return None


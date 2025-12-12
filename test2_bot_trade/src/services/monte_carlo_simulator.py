"""
Monte Carlo Simulator - Simulación probabilística de trades
Calcula probabilidad de éxito y expected value
"""
import numpy as np
import pandas as pd
from typing import Dict


class MonteCarloSimulator:
    """Simula miles de escenarios para calcular probabilidad de éxito"""
    
    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations
    
    def simulate_trade(
        self,
        symbol: str,
        current_price: float,
        volatility: float,
        days_forward: int = 30,
        position_size: int = 1
    ) -> Dict:
        """
        Simula trade futuro
        
        Args:
            symbol: Símbolo
            current_price: Precio actual
            volatility: Volatilidad histórica (anualizada)
            days_forward: Días a simular
            position_size: Tamaño de posición
        
        Returns:
            Probabilidades y expected value
        """
        try:
            # Ajustar volatilidad por días
            daily_vol = volatility / np.sqrt(252)
            period_vol = daily_vol * np.sqrt(days_forward)
            
            # Simular N escenarios
            final_prices = []
            
            for _ in range(self.num_simulations):
                # Retorno aleatorio basado en volatilidad
                random_return = np.random.normal(0, period_vol)
                final_price = current_price * (1 + random_return)
                final_prices.append(final_price)
            
            final_prices = np.array(final_prices)
            
            # Calcular P&L para cada escenario
            pnls = (final_prices - current_price) * position_size
            
            # Estadísticas
            win_scenarios = pnls > 0
            win_rate = win_scenarios.sum() / len(pnls)
            
            avg_win = pnls[pnls > 0].mean() if pnls[pnls > 0].size > 0 else 0
            avg_loss = pnls[pnls < 0].mean() if pnls[pnls < 0].size > 0 else 0
            
            expected_value = pnls.mean()
            
            # Percentiles
            pct_5 = np.percentile(pnls, 5)   # Peor caso 5%
            pct_50 = np.percentile(pnls, 50)  # Mediana
            pct_95 = np.percentile(pnls, 95)  # Mejor caso 5%
            
            # Calcular score
            score = 0
            factors = []
            
            if expected_value > 0 and win_rate > 0.55:
                score = min(30, int(expected_value / current_price * 100))
                factors.append(f'Expected value positivo (+{score})')
            elif expected_value < 0:
                score = max(-25, int(expected_value / current_price * 100))
                factors.append(f'Expected value negativo ({score})')
            
            if win_rate > 0.65:
                score += 10
                factors.append(f'Alta probabilidad de éxito (+10)')
            elif win_rate < 0.40:
                score -= 15
                factors.append(f'Baja probabilidad de éxito (-15)')
            
            return {
                'score': score,
                'win_rate': round(win_rate * 100, 2),
                'expected_value': round(expected_value, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'worst_case': round(pct_5, 2),
                'median': round(pct_50, 2),
                'best_case': round(pct_95, 2),
                'factors': factors,
                'recommendation': 'TAKE_TRADE' if expected_value > 0 and win_rate > 0.55 else 'SKIP_TRADE'
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}


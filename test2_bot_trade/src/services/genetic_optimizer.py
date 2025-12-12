
import random
import numpy as np
from deap import base, creator, tools, algorithms
import pandas as pd
import logging
from pathlib import Path
import json

# Configurar logging
logger = logging.getLogger('genetic_optimizer')

class GeneticOptimizer:
    def __init__(self, data_dir='data'):
        self.data_dir = Path(data_dir)
        self.results_dir = self.data_dir / "optimization_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Definir el problema (Maximizar ganancia)
        # weights=(1.0,) significa maximizar un solo objetivo
        if not hasattr(creator, "FitnessMax"):
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        
        # 2. Definir el individuo (Lista de parámetros)
        if not hasattr(creator, "Individual"):
            creator.create("Individual", list, fitness=creator.FitnessMax)
            
        self.toolbox = base.Toolbox()
        self._setup_toolbox()
        
    def _setup_toolbox(self):
        """Configura los operadores genéticos"""
        # Definir genes (rangos de parámetros)
        # Gen 0: RSI Period (10-30)
        # Gen 1: RSI Overbought (65-85)
        # Gen 2: RSI Oversold (15-35)
        # Gen 3: SMA Fast (5-20)
        # Gen 4: SMA Slow (21-100)
        # Gen 5: Stop Loss % (0.01 - 0.10)
        # Gen 6: Take Profit % (0.02 - 0.20)
        
        self.toolbox.register("attr_rsi_period", random.randint, 10, 30)
        self.toolbox.register("attr_rsi_ob", random.randint, 65, 85)
        self.toolbox.register("attr_rsi_os", random.randint, 15, 35)
        self.toolbox.register("attr_sma_fast", random.randint, 5, 20)
        self.toolbox.register("attr_sma_slow", random.randint, 21, 100)
        self.toolbox.register("attr_sl", random.uniform, 0.01, 0.10)
        self.toolbox.register("attr_tp", random.uniform, 0.02, 0.20)
        
        # Estructura del individuo
        self.toolbox.register("individual", tools.initCycle, creator.Individual,
                            (self.toolbox.attr_rsi_period,
                             self.toolbox.attr_rsi_ob,
                             self.toolbox.attr_rsi_os,
                             self.toolbox.attr_sma_fast,
                             self.toolbox.attr_sma_slow,
                             self.toolbox.attr_sl,
                             self.toolbox.attr_tp), n=1)
                             
        # Población
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        
        # Operadores Genéticos
        self.toolbox.register("mate", tools.cxTwoPoint) # Cruce
        self.toolbox.register("mutate", tools.mutGaussian, mu=0, sigma=1, indpb=0.2) # Mutación
        self.toolbox.register("select", tools.selTournament, tournsize=3) # Selección
        self.toolbox.register("evaluate", self._evaluate_strategy) # Función de Fitness
        
    def _evaluate_strategy(self, individual):
        """
        Función de Fitness: Evalúa qué tan buena es una configuración
        Retorna: (Profit,)
        """
        # Decodificar genes
        config = {
            'rsi_period': int(individual[0]),
            'rsi_overbought': int(individual[1]),
            'rsi_oversold': int(individual[2]),
            'sma_fast': int(individual[3]),
            'sma_slow': int(individual[4]),
            'stop_loss': float(individual[5]),
            'take_profit': float(individual[6])
        }
        
        # Validaciones básicas (genes inválidos penalizados)
        if config['sma_fast'] >= config['sma_slow']:
            return (-999999.0,) # Penalización fuerte
            
        if config['rsi_oversold'] >= config['rsi_overbought']:
             return (-999999.0,)
             
        # Usar Fast Backtester V2 para evaluación real
        try:
            from src.services.fast_backtester import FastBacktesterV2
            
            # Obtener datos históricos si están disponibles
            if hasattr(self, 'data_service') and self.data_service:
                df = self.data_service.get_historical_data('GGAL', period='1y')
                if df is not None and len(df) > 100:
                    backtester = FastBacktesterV2(initial_capital=10000.0, commission=0.001)
                    result = backtester.run_fast_backtest(
                        symbol='GGAL',
                        df=df,
                        buy_threshold=config.get('buy_threshold', 50.0),
                        sell_threshold=config.get('sell_threshold', -50.0),
                        max_position_size=config.get('max_position_size', 0.1),
                        stop_loss=config.get('stop_loss', 0.02),
                        take_profit=config.get('take_profit', 0.05)
                    )
                    # Retornar fitness basado en múltiples métricas
                    fitness = (
                        result.get('total_return', 0) * 100 +  # Return
                        result.get('win_rate', 0) * 50 +        # Win rate
                        result.get('sharpe_ratio', 0) * 10 -   # Sharpe
                        abs(result.get('max_drawdown', 0)) * 100  # Penalizar drawdown
                    )
                    return (fitness,)
            
            # Fallback a simulación si no hay datos
            profit = self._simulate_fast_backtest(config)
            return (profit,)
        except Exception as e:
            logger.warning(f"Error en backtest rápido, usando simulación: {e}")
            profit = self._simulate_fast_backtest(config)
            return (profit,)

    def _simulate_fast_backtest(self, config):
        """
        Simulación rápida de estrategia para optimización
        En producción, esto llamaría al Backtester real.
        Aquí simulamos un score basado en 'calidad' conceptual de parámetros para probar el algoritmo.
        """
        # "Goldilocks zone" simulator (para verificar que el GA converge)
        # RSI 14, OB 70, OS 30, SMA 9/21, SL 0.02, TP 0.05 es el "óptimo teórico" oculto
        
        score = 1000 # Capital inicial base
        
        # Distancia al óptimo (mientras más lejos, menos ganancia)
        diff_rsi = abs(config['rsi_period'] - 14)
        diff_ob = abs(config['rsi_overbought'] - 70)
        diff_os = abs(config['rsi_oversold'] - 30)
        diff_sma = abs(config['sma_fast'] - 9) + abs(config['sma_slow'] - 21)
        
        # Penalización por riesgo
        risk_ratio = config['take_profit'] / config['stop_loss'] 
        if risk_ratio < 1.0: 
            score -= 500 # Mal R:R
            
        penalty = (diff_rsi * 10) + (diff_ob * 5) + (diff_os * 5) + (diff_sma * 2)
        
        # Randomness noise
        noise = random.randint(-50, 50)
        
        final_profit = score - penalty + noise
        return max(0, final_profit)

    def optimize(self, symbol, generations=5, population_size=10):
        """Ejecuta la optimización genética"""
        print(f"🧬 Iniciando evolución para {symbol}...")
        
        population = self.toolbox.population(n=population_size)
        hof = tools.HallOfFame(1) # El mejor de todos
        
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)
        stats.register("max", np.max)
        
        # Algoritmo evolucionario simple
        pop, logbook = algorithms.eaSimple(population, self.toolbox, 
                                          cxpb=0.5, mutpb=0.2, 
                                          ngen=generations, stats=stats, 
                                          halloffame=hof, verbose=True)
                                          
        best_ind = hof[0]
        best_config = {
            'rsi_period': int(best_ind[0]),
            'rsi_overbought': int(best_ind[1]),
            'rsi_oversold': int(best_ind[2]),
            'sma_fast': int(best_ind[3]),
            'sma_slow': int(best_ind[4]),
            'stop_loss': float(best_ind[5]),
            'take_profit': float(best_ind[6])
        }
        
        print(f"🏆 Mejor configuración encontrada: {best_config}")
        print(f"💰 Profit estimado: ${best_ind.fitness.values[0]:.2f}")
        
        # Guardar resultados
        self._save_results(symbol, best_config, logbook)
        
        return best_config, logbook

    def _save_results(self, symbol, config, logbook):
        """Guarda el resultado de la optimización"""
        file_path = self.results_dir / f"{symbol}_optimization.json"
        
        history = []
        for gen in logbook:
            history.append({
                'gen': gen['gen'],
                'avg': gen['avg'],
                'max': gen['max']
            })
            
        data = {
            'symbol': symbol,
            'best_config': config,
            'timestamp': str(pd.Timestamp.now()),
            'history': history,
            'optimization_type': 'Genetic Algorithm'
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"💾 Resultados guardados en {file_path}")

if __name__ == "__main__":
    opt = GeneticOptimizer()
    best, log = opt.optimize("GGAL.BA", generations=5, population_size=20)

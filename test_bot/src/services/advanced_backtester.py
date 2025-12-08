"""
Sistema Avanzado de Backtesting
Backtesting completo con múltiples estrategias, métricas avanzadas y visualizaciones
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Callable
import json
from pathlib import Path

from src.core.database import SessionLocal
from src.core.logger import get_logger
from src.models.market_data import MarketData
from src.services.technical_analysis import TechnicalAnalysisService

logger = get_logger("advanced_backtester")


class Strategy:
    """Estrategia de trading para backtesting"""
    
    def __init__(self, name: str, entry_condition: Callable, exit_condition: Callable):
        self.name = name
        self.entry_condition = entry_condition
        self.exit_condition = exit_condition
        self.trades = []
        self.equity_curve = []
    
    def should_enter(self, data: pd.DataFrame, index: int) -> bool:
        """Determina si se debe entrar en una posición"""
        return self.entry_condition(data, index)
    
    def should_exit(self, data: pd.DataFrame, index: int, position: Dict) -> bool:
        """Determina si se debe salir de una posición"""
        return self.exit_condition(data, index, position)


class AdvancedBacktester:
    """Sistema avanzado de backtesting"""
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission  # 0.1% por defecto
        self.results = {}
    
    def load_data(self, symbol: str, start_date: Optional[datetime] = None, 
                  end_date: Optional[datetime] = None) -> pd.DataFrame:
        """Carga datos históricos"""
        db = SessionLocal()
        try:
            query = db.query(MarketData).filter(MarketData.symbol == symbol)
            
            if start_date:
                query = query.filter(MarketData.timestamp >= start_date)
            if end_date:
                query = query.filter(MarketData.timestamp <= end_date)
            
            records = query.order_by(MarketData.timestamp).all()
            
            if not records:
                raise ValueError(f"No hay datos para {symbol}")
            
            df = pd.DataFrame([{
                'date': r.timestamp,
                'open': r.open,
                'high': r.high,
                'low': r.low,
                'close': r.close,
                'volume': r.volume
            } for r in records])
            
            df.set_index('date', inplace=True)
            return df
        
        finally:
            db.close()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos"""
        import ta
        
        # RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        
        # Bollinger Bands
        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_middle'] = bb.bollinger_mavg()
        df['bb_lower'] = bb.bollinger_lband()
        
        # Moving Averages
        df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
        df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
        df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
        df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
        
        # ATR
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
        
        # ADX
        df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
        
        # Stochastic
        stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        
        return df
    
    def backtest_strategy(self, symbol: str, strategy: Strategy, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         stop_loss_pct: float = 0.02,
                         take_profit_pct: float = 0.04) -> Dict:
        """
        Ejecuta backtesting de una estrategia
        
        Args:
            symbol: Símbolo a probar
            strategy: Estrategia a probar
            start_date: Fecha de inicio
            end_date: Fecha de fin
            stop_loss_pct: Stop loss en porcentaje
            take_profit_pct: Take profit en porcentaje
        """
        logger.info(f"Iniciando backtesting de {strategy.name} para {symbol}")
        
        # Cargar datos
        df = self.load_data(symbol, start_date, end_date)
        
        if len(df) < 100:
            raise ValueError("Datos insuficientes para backtesting (mínimo 100 registros)")
        
        # Calcular indicadores
        df = self.calculate_technical_indicators(df)
        
        # Inicializar variables
        capital = self.initial_capital
        position = None
        trades = []
        equity_curve = [capital]
        
        # Iterar sobre los datos
        for i in range(50, len(df)):  # Empezar después de calcular indicadores
            current_price = df.iloc[i]['close']
            current_date = df.index[i]
            
            # Si hay posición abierta
            if position:
                # Verificar stop loss y take profit
                entry_price = position['entry_price']
                pnl_pct = (current_price - entry_price) / entry_price
                
                should_exit = False
                exit_reason = None
                
                if position['side'] == 'LONG':
                    if pnl_pct <= -stop_loss_pct:
                        should_exit = True
                        exit_reason = 'STOP_LOSS'
                    elif pnl_pct >= take_profit_pct:
                        should_exit = True
                        exit_reason = 'TAKE_PROFIT'
                    elif strategy.should_exit(df, i, position):
                        should_exit = True
                        exit_reason = 'STRATEGY_EXIT'
                
                if should_exit:
                    # Cerrar posición
                    quantity = position['quantity']
                    exit_value = current_price * quantity
                    commission_cost = exit_value * self.commission
                    net_exit_value = exit_value - commission_cost
                    
                    pnl = net_exit_value - position['cost_basis']
                    pnl_pct = (pnl / position['cost_basis']) * 100
                    
                    trade = {
                        'entry_date': position['entry_date'],
                        'exit_date': current_date,
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'quantity': quantity,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason,
                        'duration_days': (current_date - position['entry_date']).days
                    }
                    
                    trades.append(trade)
                    capital += pnl
                    position = None
            
            # Si no hay posición, verificar entrada
            else:
                if strategy.should_enter(df, i):
                    # Calcular cantidad (usar 90% del capital disponible)
                    available_capital = capital * 0.9
                    quantity = int(available_capital / current_price)
                    
                    if quantity > 0:
                        cost_basis = current_price * quantity
                        commission_cost = cost_basis * self.commission
                        total_cost = cost_basis + commission_cost
                        
                        if total_cost <= capital:
                            position = {
                                'entry_date': current_date,
                                'entry_price': current_price,
                                'quantity': quantity,
                                'cost_basis': total_cost,
                                'side': 'LONG'
                            }
                            capital -= total_cost
            
            equity_curve.append(capital)
        
        # Cerrar posición abierta si existe
        if position:
            final_price = df.iloc[-1]['close']
            quantity = position['quantity']
            exit_value = final_price * quantity
            commission_cost = exit_value * self.commission
            net_exit_value = exit_value - commission_cost
            
            pnl = net_exit_value - position['cost_basis']
            pnl_pct = (pnl / position['cost_basis']) * 100
            
            trade = {
                'entry_date': position['entry_date'],
                'exit_date': df.index[-1],
                'entry_price': position['entry_price'],
                'exit_price': final_price,
                'quantity': quantity,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'exit_reason': 'END_OF_DATA',
                'duration_days': (df.index[-1] - position['entry_date']).days
            }
            
            trades.append(trade)
            capital += pnl
            equity_curve[-1] = capital
        
        # Calcular métricas
        metrics = self._calculate_metrics(trades, equity_curve, df)
        
        result = {
            'strategy_name': strategy.name,
            'symbol': symbol,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'initial_capital': self.initial_capital,
            'final_capital': capital,
            'total_return': ((capital - self.initial_capital) / self.initial_capital) * 100,
            'trades': trades,
            'equity_curve': equity_curve,
            'dates': [d.isoformat() if isinstance(d, datetime) else str(d) for d in df.index],
            'metrics': metrics
        }
        
        logger.info(f"Backtesting completado: {len(trades)} trades, {result['total_return']:.2f}% retorno")
        
        return result
    
    def _calculate_metrics(self, trades: List[Dict], equity_curve: List[float], 
                          df: pd.DataFrame) -> Dict:
        """Calcula métricas avanzadas de performance"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'max_drawdown': 0,
                'avg_win': 0,
                'avg_loss': 0,
            }
        
        # Métricas básicas
        wins = [t for t in trades if t['pnl'] > 0]
        losses = [t for t in trades if t['pnl'] < 0]
        
        win_rate = len(wins) / len(trades) if trades else 0
        avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t['pnl'] for t in losses])) if losses else 0
        profit_factor = (sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses))) if losses else float('inf')
        
        # Equity curve returns
        equity_array = np.array(equity_curve)
        returns = np.diff(equity_array) / equity_array[:-1]
        
        # Sharpe Ratio (asumiendo 252 días de trading por año)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio (solo desviación negativa)
        negative_returns = returns[returns < 0]
        if len(negative_returns) > 0 and np.std(negative_returns) > 0:
            sortino_ratio = (np.mean(returns) / np.std(negative_returns)) * np.sqrt(252)
        else:
            sortino_ratio = 0
        
        # Max Drawdown
        peak = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - peak) / peak
        max_drawdown = abs(np.min(drawdown)) * 100
        
        # Calmar Ratio (retorno anualizado / max drawdown)
        total_return = (equity_array[-1] - equity_array[0]) / equity_array[0]
        days = len(df)
        annualized_return = (1 + total_return) ** (252 / days) - 1 if days > 0 else 0
        calmar_ratio = (annualized_return / (max_drawdown / 100)) if max_drawdown > 0 else 0
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(wins),
            'losing_trades': len(losses),
            'win_rate': win_rate * 100,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'max_drawdown': max_drawdown,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': max([t['pnl'] for t in wins]) if wins else 0,
            'largest_loss': min([t['pnl'] for t in losses]) if losses else 0,
            'avg_trade_duration_days': np.mean([t['duration_days'] for t in trades]) if trades else 0,
        }
    
    def compare_strategies(self, symbol: str, strategies: List[Strategy],
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> Dict:
        """Compara múltiples estrategias"""
        results = {}
        
        for strategy in strategies:
            try:
                result = self.backtest_strategy(symbol, strategy, start_date, end_date)
                results[strategy.name] = result
            except Exception as e:
                logger.error(f"Error en backtesting de {strategy.name}: {e}")
                results[strategy.name] = {'error': str(e)}
        
        # Comparación
        comparison = {
            'symbol': symbol,
            'strategies_tested': len(strategies),
            'results': results,
            'best_strategy': None,
            'comparison_metrics': {}
        }
        
        # Encontrar mejor estrategia por Sharpe Ratio
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        if valid_results:
            best = max(valid_results.items(), 
                     key=lambda x: x[1].get('metrics', {}).get('sharpe_ratio', -999))
            comparison['best_strategy'] = best[0]
            
            # Métricas comparativas
            comparison['comparison_metrics'] = {
                'best_sharpe': best[1]['metrics']['sharpe_ratio'],
                'best_return': best[1]['total_return'],
                'best_win_rate': best[1]['metrics']['win_rate'],
            }
        
        return comparison
    
    def save_results(self, result: Dict, filename: Optional[str] = None):
        """Guarda resultados de backtesting"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"backtest_results_{result['strategy_name']}_{timestamp}.json"
        
        results_dir = Path("data/backtest_results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Resultados guardados en {filepath}")
        return filepath


# Estrategias predefinidas
def create_ma_crossover_strategy(fast_period: int = 20, slow_period: int = 50) -> Strategy:
    """Estrategia de cruce de medias móviles"""
    def entry_condition(df: pd.DataFrame, index: int) -> bool:
        if index < slow_period:
            return False
        
        fast_ma = df.iloc[index]['sma_20'] if 'sma_20' in df.columns else None
        slow_ma = df.iloc[index]['sma_50'] if 'sma_50' in df.columns else None
        prev_fast = df.iloc[index-1]['sma_20'] if 'sma_20' in df.columns else None
        prev_slow = df.iloc[index-1]['sma_50'] if 'sma_50' in df.columns else None
        
        if fast_ma and slow_ma and prev_fast and prev_slow:
            # Cruce alcista: fast cruza por encima de slow
            return prev_fast <= prev_slow and fast_ma > slow_ma
        
        return False
    
    def exit_condition(df: pd.DataFrame, index: int, position: Dict) -> bool:
        if index < slow_period:
            return False
        
        fast_ma = df.iloc[index]['sma_20'] if 'sma_20' in df.columns else None
        slow_ma = df.iloc[index]['sma_50'] if 'sma_50' in df.columns else None
        prev_fast = df.iloc[index-1]['sma_20'] if 'sma_20' in df.columns else None
        prev_slow = df.iloc[index-1]['sma_50'] if 'sma_50' in df.columns else None
        
        if fast_ma and slow_ma and prev_fast and prev_slow:
            # Cruce bajista: fast cruza por debajo de slow
            return prev_fast >= prev_slow and fast_ma < slow_ma
        
        return False
    
    return Strategy(f"MA Crossover ({fast_period}/{slow_period})", entry_condition, exit_condition)


def create_rsi_strategy(oversold: int = 30, overbought: int = 70) -> Strategy:
    """Estrategia basada en RSI"""
    def entry_condition(df: pd.DataFrame, index: int) -> bool:
        if 'rsi' not in df.columns:
            return False
        
        rsi = df.iloc[index]['rsi']
        prev_rsi = df.iloc[index-1]['rsi'] if index > 0 else None
        
        # Entrar cuando RSI sale de zona de sobreventa
        if prev_rsi:
            return prev_rsi <= oversold and rsi > oversold
        
        return False
    
    def exit_condition(df: pd.DataFrame, index: int, position: Dict) -> bool:
        if 'rsi' not in df.columns:
            return False
        
        rsi = df.iloc[index]['rsi']
        prev_rsi = df.iloc[index-1]['rsi'] if index > 0 else None
        
        # Salir cuando RSI entra en zona de sobrecompra
        if prev_rsi:
            return prev_rsi < overbought and rsi >= overbought
        
        return False
    
    return Strategy(f"RSI Strategy ({oversold}/{overbought})", entry_condition, exit_condition)


def create_macd_strategy() -> Strategy:
    """Estrategia basada en MACD"""
    def entry_condition(df: pd.DataFrame, index: int) -> bool:
        if 'macd' not in df.columns or 'macd_signal' not in df.columns:
            return False
        
        macd = df.iloc[index]['macd']
        signal = df.iloc[index]['macd_signal']
        prev_macd = df.iloc[index-1]['macd'] if index > 0 else None
        prev_signal = df.iloc[index-1]['macd_signal'] if index > 0 else None
        
        # Cruce alcista
        if prev_macd and prev_signal:
            return prev_macd <= prev_signal and macd > signal
        
        return False
    
    def exit_condition(df: pd.DataFrame, index: int, position: Dict) -> bool:
        if 'macd' not in df.columns or 'macd_signal' not in df.columns:
            return False
        
        macd = df.iloc[index]['macd']
        signal = df.iloc[index]['macd_signal']
        prev_macd = df.iloc[index-1]['macd'] if index > 0 else None
        prev_signal = df.iloc[index-1]['macd_signal'] if index > 0 else None
        
        # Cruce bajista
        if prev_macd and prev_signal:
            return prev_macd >= prev_signal and macd < signal
        
        return False
    
    return Strategy("MACD Strategy", entry_condition, exit_condition)


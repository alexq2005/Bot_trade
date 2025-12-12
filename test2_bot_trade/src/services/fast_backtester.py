"""
Fast Backtesting Engine V2
Motor de backtesting rápido optimizado para el optimizador genético
Diseñado para ejecutar miles de backtests rápidamente
"""
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger('fast_backtester')

class FastBacktesterV2:
    """
    Motor de backtesting rápido para optimización
    Optimizado para velocidad: vectorizado, sin loops innecesarios
    """
    
    def __init__(self, initial_capital: float = 10000.0, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        
    def run_fast_backtest(self, 
                          symbol: str,
                          df: pd.DataFrame,
                          buy_threshold: float = 50.0,
                          sell_threshold: float = -50.0,
                          max_position_size: float = 0.1,
                          stop_loss: float = 0.05,
                          take_profit: float = 0.10) -> Dict:
        """
        Ejecuta backtesting rápido vectorizado
        
        Args:
            symbol: Símbolo a analizar
            df: DataFrame con OHLCV y señales
            buy_threshold: Score mínimo para comprar
            sell_threshold: Score máximo para vender
            max_position_size: % máximo del capital por posición
            stop_loss: % de pérdida máxima
            take_profit: % de ganancia objetivo
            
        Returns:
            Dict con métricas de performance
        """
        try:
            if len(df) < 100:
                return self._empty_result(symbol, "Datos insuficientes")
            
            # Asegurar columnas necesarias
            required_cols = ['Close', 'Open', 'High', 'Low']
            if not all(col in df.columns for col in required_cols):
                df.columns = [c.capitalize() for c in df.columns]
            
            # Vectorizar cálculos
            prices = df['Close'].values
            opens = df['Open'].values
            highs = df['High'].values
            lows = df['Low'].values
            
            # Simular señales (en producción vendrían del análisis)
            # Por ahora, usar score si existe, sino simular
            if 'Score' in df.columns:
                scores = df['Score'].values
            else:
                # Simular señales basadas en momentum simple
                returns = np.diff(prices) / prices[:-1]
                scores = np.concatenate([[0], returns * 100])
            
            # Inicializar estado
            capital = self.initial_capital
            position = 0.0  # Cantidad de acciones
            position_price = 0.0
            trades = []
            equity_curve = [capital]
            
            # Vectorizar decisiones (más rápido que loop)
            buy_signals = scores >= buy_threshold
            sell_signals = scores <= sell_threshold
            
            # Ejecutar trading simulado
            for i in range(len(df)):
                current_price = prices[i]
                current_score = scores[i]
                
                # Calcular equity actual
                if position > 0:
                    current_equity = capital + (position * current_price)
                    pnl_pct = (current_price - position_price) / position_price
                    
                    # Stop Loss
                    if pnl_pct <= -stop_loss:
                        # Vender por stop loss
                        capital = position * current_price * (1 - self.commission)
                        trades.append({
                            'entry': position_price,
                            'exit': current_price,
                            'pnl': capital - (position * position_price),
                            'pnl_pct': pnl_pct,
                            'reason': 'stop_loss',
                            'entry_idx': len(trades),
                            'exit_idx': i
                        })
                        position = 0.0
                        position_price = 0.0
                    
                    # Take Profit
                    elif pnl_pct >= take_profit:
                        # Vender por take profit
                        capital = position * current_price * (1 - self.commission)
                        trades.append({
                            'entry': position_price,
                            'exit': current_price,
                            'pnl': capital - (position * position_price),
                            'pnl_pct': pnl_pct,
                            'reason': 'take_profit',
                            'entry_idx': len(trades),
                            'exit_idx': i
                        })
                        position = 0.0
                        position_price = 0.0
                    
                    # Señal de venta
                    elif sell_signals[i] and position > 0:
                        capital = position * current_price * (1 - self.commission)
                        trades.append({
                            'entry': position_price,
                            'exit': current_price,
                            'pnl': capital - (position * position_price),
                            'pnl_pct': (current_price - position_price) / position_price,
                            'reason': 'signal',
                            'entry_idx': len(trades),
                            'exit_idx': i
                        })
                        position = 0.0
                        position_price = 0.0
                
                # Señal de compra
                elif buy_signals[i] and position == 0:
                    position_size = capital * max_position_size
                    position = (position_size / current_price) * (1 - self.commission)
                    position_price = current_price
                    capital -= position_size
                
                # Actualizar equity curve
                if position > 0:
                    equity = capital + (position * current_price)
                else:
                    equity = capital
                equity_curve.append(equity)
            
            # Cerrar posición final si existe
            if position > 0:
                final_price = prices[-1]
                capital = position * final_price * (1 - self.commission)
                trades.append({
                    'entry': position_price,
                    'exit': final_price,
                    'pnl': capital - (position * position_price),
                    'pnl_pct': (final_price - position_price) / position_price,
                    'reason': 'close',
                    'entry_idx': len(trades),
                    'exit_idx': len(df) - 1
                })
            
            # Calcular métricas
            return self._calculate_metrics(symbol, trades, equity_curve, self.initial_capital)
            
        except Exception as e:
            logger.error(f"Error en fast backtest para {symbol}: {e}")
            return self._empty_result(symbol, str(e))
    
    def _calculate_metrics(self, symbol: str, trades: List[Dict], 
                          equity_curve: List[float], initial_capital: float) -> Dict:
        """Calcula métricas de performance"""
        if not trades:
            return self._empty_result(symbol, "Sin trades")
        
        # Métricas básicas
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        total_pnl = sum(t['pnl'] for t in trades)
        total_return = (equity_curve[-1] - initial_capital) / initial_capital if initial_capital > 0 else 0
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum(t['pnl'] for t in winning_trades) / sum(t['pnl'] for t in losing_trades)) if losing_trades and sum(t['pnl'] for t in losing_trades) != 0 else float('inf')
        
        # Drawdown
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Sharpe ratio (simplificado)
        returns = np.diff(equity_array) / equity_array[:-1]
        sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252) if len(returns) > 1 else 0
        
        return {
            'symbol': symbol,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'final_capital': equity_curve[-1],
            'initial_capital': initial_capital,
            'trades': trades[:10],  # Solo primeros 10 para no saturar
            'equity_curve': equity_curve[-100:],  # Últimos 100 puntos
            'success': True
        }
    
    def _empty_result(self, symbol: str, reason: str) -> Dict:
        """Retorna resultado vacío"""
        return {
            'symbol': symbol,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_pnl': 0,
            'total_return': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'final_capital': self.initial_capital,
            'initial_capital': self.initial_capital,
            'trades': [],
            'equity_curve': [self.initial_capital],
            'success': False,
            'error': reason
        }
    
    def batch_backtest(self, 
                      symbols: List[str],
                      data_dict: Dict[str, pd.DataFrame],
                      config: Dict) -> Dict[str, Dict]:
        """
        Ejecuta backtesting en batch para múltiples símbolos
        
        Args:
            symbols: Lista de símbolos
            data_dict: Dict con DataFrames por símbolo
            config: Configuración de backtesting
            
        Returns:
            Dict con resultados por símbolo
        """
        results = {}
        
        for symbol in symbols:
            if symbol in data_dict:
                result = self.run_fast_backtest(
                    symbol=symbol,
                    df=data_dict[symbol],
                    buy_threshold=config.get('buy_threshold', 50.0),
                    sell_threshold=config.get('sell_threshold', -50.0),
                    max_position_size=config.get('max_position_size', 0.1),
                    stop_loss=config.get('stop_loss', 0.05),
                    take_profit=config.get('take_profit', 0.10)
                )
                results[symbol] = result
        
        return results

if __name__ == "__main__":
    # Test rápido
    print("🚀 Testing Fast Backtester V2...")
    backtester = FastBacktesterV2(initial_capital=10000.0)
    
    # Crear datos de prueba
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
    
    df = pd.DataFrame({
        'Date': dates,
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Close': prices,
        'Volume': np.random.randint(1000000, 5000000, len(dates))
    })
    
    result = backtester.run_fast_backtest("TEST", df)
    print(f"\n📊 Resultados:")
    print(f"   Trades: {result['total_trades']}")
    print(f"   Win Rate: {result['win_rate']:.2%}")
    print(f"   Return: {result['total_return']:.2%}")
    print(f"   Sharpe: {result['sharpe_ratio']:.2f}")


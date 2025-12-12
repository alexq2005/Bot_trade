"""
Paper Trading Validator
Sistema de validación continua en Paper Trading con parámetros optimizados
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger('paper_trading_validator')

class PaperTradingValidator:
    """
    Valida estrategias en Paper Trading de forma continua
    Monitorea performance y ajusta parámetros automáticamente
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.validation_results = {}
        self.performance_history = {}
        self.results_dir = Path("data/paper_trading_validation")
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def validate_strategy(self, 
                         symbol: str,
                         strategy_config: Dict,
                         historical_data: pd.DataFrame,
                         days: int = 30) -> Dict:
        """
        Valida una estrategia en Paper Trading
        
        Args:
            symbol: Símbolo a validar
            strategy_config: Configuración de la estrategia (umbrales, etc.)
            historical_data: Datos históricos
            days: Días de validación
            
        Returns:
            Dict con resultados de validación
        """
        try:
            # Filtrar últimos N días
            if len(historical_data) < days:
                days = len(historical_data)
            
            validation_data = historical_data.tail(days).copy()
            
            # Simular trading con la estrategia
            results = self._simulate_trading(
                symbol=symbol,
                df=validation_data,
                config=strategy_config
            )
            
            # Calcular métricas
            metrics = self._calculate_validation_metrics(results)
            
            # Guardar resultados
            validation_result = {
                'symbol': symbol,
                'config': strategy_config,
                'metrics': metrics,
                'validation_date': datetime.now().isoformat(),
                'days_validated': days,
                'success': True
            }
            
            self.validation_results[symbol] = validation_result
            self._save_validation_result(validation_result)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validando estrategia para {symbol}: {e}")
            return {
                'symbol': symbol,
                'config': strategy_config,
                'success': False,
                'error': str(e)
            }
    
    def _simulate_trading(self, symbol: str, df: pd.DataFrame, config: Dict) -> Dict:
        """Simula trading con la estrategia"""
        capital = self.initial_capital
        position = 0.0
        position_price = 0.0
        trades = []
        equity_curve = [capital]
        
        buy_threshold = config.get('buy_threshold', 50.0)
        sell_threshold = config.get('sell_threshold', -50.0)
        max_position_size = config.get('max_position_size', 0.1)
        stop_loss = config.get('stop_loss', 0.05)
        take_profit = config.get('take_profit', 0.10)
        commission = config.get('commission', 0.001)
        
        prices = df['Close'].values if 'Close' in df.columns else df['close'].values
        
        # Simular señales (en producción vendrían del análisis real)
        if 'Score' in df.columns:
            scores = df['Score'].values
        else:
            # Simular señales
            returns = np.diff(prices) / prices[:-1]
            scores = np.concatenate([[0], returns * 100])
        
        for i in range(len(df)):
            current_price = prices[i]
            current_score = scores[i] if i < len(scores) else 0
            
            # Gestión de posición existente
            if position > 0:
                pnl_pct = (current_price - position_price) / position_price
                
                # Stop Loss
                if pnl_pct <= -stop_loss:
                    capital = position * current_price * (1 - commission)
                    trades.append({
                        'entry': position_price,
                        'exit': current_price,
                        'pnl_pct': pnl_pct,
                        'reason': 'stop_loss',
                        'entry_time': df.index[i] if hasattr(df.index[i], 'isoformat') else str(i),
                        'exit_time': df.index[i]
                    })
                    position = 0.0
                    position_price = 0.0
                
                # Take Profit
                elif pnl_pct >= take_profit:
                    capital = position * current_price * (1 - commission)
                    trades.append({
                        'entry': position_price,
                        'exit': current_price,
                        'pnl_pct': pnl_pct,
                        'reason': 'take_profit',
                        'entry_time': df.index[i] if hasattr(df.index[i], 'isoformat') else str(i),
                        'exit_time': df.index[i]
                    })
                    position = 0.0
                    position_price = 0.0
                
                # Señal de venta
                elif current_score <= sell_threshold:
                    capital = position * current_price * (1 - commission)
                    trades.append({
                        'entry': position_price,
                        'exit': current_price,
                        'pnl_pct': pnl_pct,
                        'reason': 'signal',
                        'entry_time': df.index[i] if hasattr(df.index[i], 'isoformat') else str(i),
                        'exit_time': df.index[i]
                    })
                    position = 0.0
                    position_price = 0.0
            
            # Señal de compra
            elif current_score >= buy_threshold and position == 0:
                position_size = capital * max_position_size
                position = (position_size / current_price) * (1 - commission)
                position_price = current_price
                capital -= position_size
            
            # Actualizar equity
            if position > 0:
                equity = capital + (position * current_price)
            else:
                equity = capital
            equity_curve.append(equity)
        
        # Cerrar posición final
        if position > 0:
            final_price = prices[-1]
            capital = position * final_price * (1 - commission)
            trades.append({
                'entry': position_price,
                'exit': final_price,
                'pnl_pct': (final_price - position_price) / position_price,
                'reason': 'close',
                'entry_time': df.index[-1] if hasattr(df.index[-1], 'isoformat') else str(len(df)-1),
                'exit_time': df.index[-1]
            })
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'final_capital': equity_curve[-1] if equity_curve else capital
        }
    
    def _calculate_validation_metrics(self, results: Dict) -> Dict:
        """Calcula métricas de validación"""
        trades = results.get('trades', [])
        equity_curve = results.get('equity_curve', [])
        final_capital = results.get('final_capital', self.initial_capital)
        
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_return': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'profit_factor': 0,
                'validation_passed': False
            }
        
        # Métricas básicas
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.get('pnl_pct', 0) > 0]
        losing_trades = [t for t in trades if t.get('pnl_pct', 0) <= 0]
        
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        total_return = (final_capital - self.initial_capital) / self.initial_capital
        
        # Profit factor
        total_wins = sum(t.get('pnl_pct', 0) for t in winning_trades)
        total_losses = abs(sum(t.get('pnl_pct', 0) for t in losing_trades))
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')
        
        # Drawdown
        equity_array = np.array(equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # Sharpe (simplificado)
        returns = np.diff(equity_array) / equity_array[:-1]
        sharpe = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252) if len(returns) > 1 else 0
        
        # Criterios de validación
        validation_passed = (
            win_rate >= 0.5 and  # Win rate >= 50%
            total_return > 0 and  # Retorno positivo
            profit_factor >= 1.5 and  # Profit factor >= 1.5
            max_drawdown > -0.20  # Drawdown máximo < 20%
        )
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'total_return': total_return,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe,
            'final_capital': final_capital,
            'validation_passed': validation_passed
        }
    
    def _save_validation_result(self, result: Dict):
        """Guarda resultado de validación"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_{result['symbol']}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        logger.info(f"Resultado de validación guardado: {filepath}")
    
    def continuous_validation(self, 
                            symbol: str,
                            strategy_config: Dict,
                            data_service,
                            validation_interval_days: int = 7) -> Dict:
        """
        Validación continua en Paper Trading
        
        Args:
            symbol: Símbolo a validar
            strategy_config: Configuración de estrategia
            data_service: Servicio de datos
            validation_interval_days: Intervalo de validación en días
            
        Returns:
            Dict con resultados de validación continua
        """
        try:
            # Obtener datos históricos
            df = data_service.get_historical_data(symbol, period='3mo')
            if df is None or len(df) < 30:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'Datos insuficientes'
                }
            
            # Validar estrategia
            result = self.validate_strategy(
                symbol=symbol,
                strategy_config=strategy_config,
                historical_data=df,
                days=validation_interval_days * 4  # Validar últimos 4 intervalos
            )
            
            # Actualizar historial
            if symbol not in self.performance_history:
                self.performance_history[symbol] = []
            
            self.performance_history[symbol].append({
                'date': datetime.now().isoformat(),
                'metrics': result.get('metrics', {}),
                'config': strategy_config
            })
            
            # Mantener solo últimos 10 validaciones
            if len(self.performance_history[symbol]) > 10:
                self.performance_history[symbol] = self.performance_history[symbol][-10:]
            
            return result
            
        except Exception as e:
            logger.error(f"Error en validación continua para {symbol}: {e}")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e)
            }
    
    def get_validation_summary(self) -> Dict:
        """Obtiene resumen de todas las validaciones"""
        summary = {
            'total_validations': len(self.validation_results),
            'passed_validations': sum(1 for r in self.validation_results.values() 
                                     if r.get('metrics', {}).get('validation_passed', False)),
            'failed_validations': sum(1 for r in self.validation_results.values() 
                                     if not r.get('metrics', {}).get('validation_passed', True)),
            'symbols': list(self.validation_results.keys()),
            'latest_results': {}
        }
        
        for symbol, result in self.validation_results.items():
            summary['latest_results'][symbol] = {
                'validation_passed': result.get('metrics', {}).get('validation_passed', False),
                'win_rate': result.get('metrics', {}).get('win_rate', 0),
                'total_return': result.get('metrics', {}).get('total_return', 0),
                'date': result.get('validation_date', 'N/A')
            }
        
        return summary

if __name__ == "__main__":
    print("📊 Testing Paper Trading Validator...")
    validator = PaperTradingValidator(initial_capital=100000.0)
    print("✅ Validator initialized")


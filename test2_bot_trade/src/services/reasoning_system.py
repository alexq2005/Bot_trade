"""
Reasoning System - Sistema de Razonamiento Autónomo
Permite al bot razonar sobre su propio comportamiento y tomar decisiones
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path


class ReasoningSystem:
    """
    Sistema que permite al bot razonar sobre su comportamiento
    y tomar decisiones autónomas
    """
    
    def __init__(self, bot_directory: str = "."):
        self.bot_directory = Path(bot_directory)
        self.reasoning_history_file = self.bot_directory / "data" / "reasoning_history.json"
        self.reasoning_history = self._load_history()
        
    def _load_history(self) -> List[Dict]:
        """Carga historial de razonamientos"""
        if self.reasoning_history_file.exists():
            try:
                with open(self.reasoning_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_history(self):
        """Guarda historial de razonamientos"""
        self.reasoning_history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.reasoning_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.reasoning_history, f, indent=2, ensure_ascii=False)
    
    def reason_about_trade(self, trade_data: Dict) -> Dict:
        """
        Razonamiento sobre si ejecutar un trade
        """
        reasoning = {
            'timestamp': datetime.now().isoformat(),
            'trade_data': trade_data,
            'decision': 'HOLD',
            'confidence': 0.0,
            'reasoning_steps': [],
            'factors': {}
        }
        
        symbol = trade_data.get('symbol')
        signal = trade_data.get('signal')
        score = trade_data.get('score', 0)
        
        # Factor 1: Score del análisis
        if score >= 30:
            reasoning['factors']['strong_score'] = True
            reasoning['reasoning_steps'].append(f"Score alto ({score}) indica señal fuerte")
        elif score >= 20:
            reasoning['factors']['moderate_score'] = True
            reasoning['reasoning_steps'].append(f"Score moderado ({score}) indica señal válida")
        else:
            reasoning['factors']['weak_score'] = True
            reasoning['reasoning_steps'].append(f"Score bajo ({score}) - señal débil")
        
        # Factor 2: Historial reciente del símbolo
        recent_performance = self._analyze_symbol_performance(symbol)
        if recent_performance:
            win_rate = recent_performance.get('win_rate', 50)
            if win_rate > 60:
                reasoning['factors']['good_history'] = True
                reasoning['reasoning_steps'].append(f"Historial positivo: {win_rate:.1f}% win rate")
                reasoning['confidence'] += 0.2
            elif win_rate < 40:
                reasoning['factors']['poor_history'] = True
                reasoning['reasoning_steps'].append(f"Historial negativo: {win_rate:.1f}% win rate")
                reasoning['confidence'] -= 0.2
        
        # Factor 3: Condiciones de mercado
        market_conditions = trade_data.get('market_conditions', {})
        volatility = market_conditions.get('volatility', 'MEDIUM')
        
        if volatility == 'HIGH':
            reasoning['factors']['high_volatility'] = True
            reasoning['reasoning_steps'].append("Alta volatilidad - mayor riesgo pero mayor oportunidad")
            if signal == 'BUY' and score > 25:
                reasoning['confidence'] += 0.1  # Alta volatilidad puede ser oportunidad
            else:
                reasoning['confidence'] -= 0.1  # Alta volatilidad aumenta riesgo
        
        # Factor 4: Diversificación actual
        current_positions = trade_data.get('current_positions', [])
        if len(current_positions) < 3:
            reasoning['factors']['low_diversification'] = True
            reasoning['reasoning_steps'].append("Portafolio poco diversificado - agregar posición puede ayudar")
            reasoning['confidence'] += 0.1
        
        # Decisión final
        if signal == 'BUY' and score >= 20:
            if reasoning['confidence'] >= 0.3:
                reasoning['decision'] = 'EXECUTE'
            elif reasoning['confidence'] >= 0.1:
                reasoning['decision'] = 'CONSIDER'
            else:
                reasoning['decision'] = 'HOLD'
        elif signal == 'SELL' and score <= -20:
            if reasoning['confidence'] >= 0.2:
                reasoning['decision'] = 'EXECUTE'
            else:
                reasoning['decision'] = 'HOLD'
        
        # Guardar razonamiento
        self.reasoning_history.append(reasoning)
        if len(self.reasoning_history) > 1000:  # Limitar tamaño
            self.reasoning_history = self.reasoning_history[-1000:]
        self._save_history()
        
        return reasoning
    
    def _analyze_symbol_performance(self, symbol: str) -> Optional[Dict]:
        """Analiza performance histórico de un símbolo"""
        trades_file = self.bot_directory / "trades.json"
        if not trades_file.exists():
            return None
        
        try:
            with open(trades_file, 'r') as f:
                trades = json.load(f)
            
            symbol_trades = [t for t in trades 
                           if t.get('symbol') == symbol 
                           and t.get('status') == 'FILLED'
                           and t.get('pnl') is not None]
            
            if not symbol_trades:
                return None
            
            wins = [t for t in symbol_trades if t.get('pnl', 0) > 0]
            losses = [t for t in symbol_trades if t.get('pnl', 0) < 0]
            
            return {
                'total_trades': len(symbol_trades),
                'wins': len(wins),
                'losses': len(losses),
                'win_rate': len(wins) / len(symbol_trades) * 100 if symbol_trades else 0,
                'avg_pnl': sum(t.get('pnl', 0) for t in symbol_trades) / len(symbol_trades)
            }
        except:
            return None
    
    def reason_about_strategy(self, strategy_performance: Dict) -> Dict:
        """
        Razonamiento sobre efectividad de estrategias
        """
        reasoning = {
            'timestamp': datetime.now().isoformat(),
            'strategy_analysis': strategy_performance,
            'recommendations': [],
            'adjustments': []
        }
        
        # Analizar win rate por estrategia
        for strategy, perf in strategy_performance.items():
            win_rate = perf.get('win_rate', 50)
            avg_pnl = perf.get('avg_pnl', 0)
            
            if win_rate < 45:
                reasoning['recommendations'].append({
                    'strategy': strategy,
                    'action': 'reduce_weight',
                    'reason': f"Win rate bajo ({win_rate:.1f}%)",
                    'priority': 'high'
                })
            elif win_rate > 65 and avg_pnl > 0:
                reasoning['recommendations'].append({
                    'strategy': strategy,
                    'action': 'increase_weight',
                    'reason': f"Win rate excelente ({win_rate:.1f}%) con P&L positivo",
                    'priority': 'medium'
                })
        
        return reasoning
    
    def reason_about_self_improvement(self, current_state: Dict) -> Dict:
        """
        Razonamiento sobre mejoras a sí mismo
        """
        reasoning = {
            'timestamp': datetime.now().isoformat(),
            'current_state': current_state,
            'improvement_areas': [],
            'priority': 'medium'
        }
        
        # Analizar métricas clave
        win_rate = current_state.get('win_rate', 50)
        profit_factor = current_state.get('profit_factor', 1.0)
        drawdown = current_state.get('max_drawdown', 0)
        
        # Razonar sobre mejoras necesarias
        if win_rate < 50:
            reasoning['improvement_areas'].append({
                'area': 'entry_filters',
                'description': 'Mejorar filtros de entrada para aumentar win rate',
                'priority': 'high',
                'reasoning': f"Win rate actual ({win_rate:.1f}%) está por debajo del objetivo (50%+)"
            })
        
        if profit_factor < 1.2:
            reasoning['improvement_areas'].append({
                'area': 'risk_management',
                'description': 'Mejorar gestión de riesgo para mejorar profit factor',
                'priority': 'high',
                'reasoning': f"Profit factor ({profit_factor:.2f}) indica que pérdidas son mayores que ganancias"
            })
        
        if drawdown > 20:
            reasoning['improvement_areas'].append({
                'area': 'position_sizing',
                'description': 'Reducir tamaño de posición para limitar drawdown',
                'priority': 'high',
                'reasoning': f"Drawdown actual ({drawdown:.1f}%) excede límite recomendado (20%)"
            })
        
        return reasoning


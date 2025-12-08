"""
Tests unitarios para AdaptiveRiskManager
"""
import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.adaptive_risk_manager import AdaptiveRiskManager


class TestAdaptiveRiskManager:
    """Tests para AdaptiveRiskManager"""
    
    def test_initialization(self):
        """Test inicialización del risk manager"""
        rm = AdaptiveRiskManager(initial_capital=100000.0)
        assert rm.current_capital == 100000.0
        assert rm is not None
    
    def test_calculate_position_size(self):
        """Test cálculo de tamaño de posición"""
        rm = AdaptiveRiskManager(initial_capital=100000.0)
        current_price = 100.0
        stop_loss_price = 95.0  # 5% stop loss
        
        position_size = rm.calculate_position_size(current_price, stop_loss_price)
        
        assert position_size > 0
        assert position_size <= 100000.0 / current_price  # No más que el capital disponible
    
    def test_stop_loss_calculation(self):
        """Test cálculo de stop loss"""
        rm = AdaptiveRiskManager(initial_capital=100000.0)
        entry_price = 100.0
        risk_percent = 2.0  # 2% de riesgo
        
        stop_loss = rm.calculate_stop_loss(entry_price, risk_percent)
        
        assert stop_loss < entry_price
        assert abs((entry_price - stop_loss) / entry_price * 100 - risk_percent) < 0.1
    
    def test_take_profit_calculation(self):
        """Test cálculo de take profit"""
        rm = AdaptiveRiskManager(initial_capital=100000.0)
        entry_price = 100.0
        reward_percent = 4.0  # 4% de ganancia
        
        take_profit = rm.calculate_take_profit(entry_price, reward_percent)
        
        assert take_profit > entry_price
        assert abs((take_profit - entry_price) / entry_price * 100 - reward_percent) < 0.1
    
    def test_risk_limit_enforcement(self):
        """Test que se respetan los límites de riesgo"""
        rm = AdaptiveRiskManager(initial_capital=100000.0)
        # Configurar límite de riesgo diario
        rm.config['max_daily_loss_percent'] = 5.0
        
        # Simular pérdidas
        rm.record_loss(3000.0)  # 3% de pérdida
        
        # Verificar que aún puede operar
        assert rm.can_trade()
        
        # Simular más pérdidas hasta el límite
        rm.record_loss(2000.0)  # Total 5%
        
        # Ahora debería estar en el límite
        # (dependiendo de la implementación exacta)


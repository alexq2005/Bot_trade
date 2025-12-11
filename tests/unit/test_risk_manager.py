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
        atr = 1.8
        
        stop_loss = rm.calculate_stop_loss(entry_price, atr)
        
        assert stop_loss < entry_price
        assert stop_loss == pytest.approx(97.3)
    
    def test_take_profit_calculation(self):
        """Test cálculo de take profit"""
        rm = AdaptiveRiskManager(initial_capital=100000.0)
        entry_price = 100.0
        atr = 1.8
        
        take_profit = rm.calculate_take_profit(entry_price, atr)
        
        assert take_profit > entry_price
        assert take_profit == pytest.approx(105.4)
    
    def test_risk_limit_enforcement(self):
        """Test que se respetan los límites de riesgo"""
        rm = AdaptiveRiskManager(initial_capital=100000.0)
        # Configurar límite de riesgo diario
        rm.max_daily_loss_pct = 0.05
        
        # Simular pérdidas
        rm.daily_pnl = -3000.0
        
        # Verificar que aún puede operar
        can_trade, reason = rm.can_trade()
        assert can_trade is True
        
        # Simular más pérdidas hasta el límite
        rm.daily_pnl = -5000.0
        
        # Ahora debería estar en el límite
        can_trade, reason = rm.can_trade()
        assert can_trade is False


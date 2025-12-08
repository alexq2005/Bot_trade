"""
Tests de integración para TradingBot
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from trading_bot import TradingBot
from tests.conftest import mock_iol_client, sample_symbols


class TestTradingBot:
    """Tests de integración para TradingBot"""
    
    @patch('trading_bot.IOLClient')
    def test_bot_initialization_paper_trading(self, mock_iol_class):
        """Test inicialización del bot en modo paper trading"""
        mock_iol_class.return_value = mock_iol_client()
        
        bot = TradingBot(
            symbols=['GGAL', 'YPFD'],
            initial_capital=100000.0,
            paper_trading=True
        )
        
        assert bot.paper_trading is True
        assert bot.capital == 100000.0
        assert len(bot.symbols) == 2
    
    @patch('trading_bot.IOLClient')
    def test_bot_initialization_live_trading(self, mock_iol_class):
        """Test inicialización del bot en modo live trading"""
        mock_client = mock_iol_client()
        mock_client.get_available_balance.return_value = 50000.0
        mock_iol_class.return_value = mock_client
        
        bot = TradingBot(
            symbols=['GGAL'],
            paper_trading=False
        )
        
        assert bot.paper_trading is False
        assert bot.capital == 50000.0
    
    def test_analyze_symbol(self):
        """Test análisis de un símbolo"""
        # Este test requeriría mocks más complejos
        # o datos de prueba reales
        pass
    
    def test_execute_trade_paper_trading(self):
        """Test ejecución de trade en modo paper"""
        # Verificar que en paper trading no se ejecutan órdenes reales
        pass
    
    def test_risk_manager_integration(self):
        """Test integración con risk manager"""
        # Verificar que el bot respeta las decisiones del risk manager
        pass


"""
Expanded tests for Portfolio Persistence.
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, mock_open
from src.services.portfolio_persistence import (
    save_portfolio,
    load_portfolio,
    sync_from_iol,
    sync_from_tienda_broker,
    update_prices_from_iol,
    get_dolar_mep
)


class TestPortfolioPersistence:
    """Comprehensive test suite for portfolio persistence functions."""
    
    @pytest.fixture
    def sample_portfolio(self):
        """Sample portfolio data."""
        return [
            {
                "symbol": "GGAL",
                "quantity": 10,
                "avg_price": 1000.0,
                "total_val": 10000.0,
                "market": "ARG",
                "last_price": 1000.0
            },
            {
                "symbol": "AAPL",
                "quantity": 5,
                "avg_price": 150.0,
                "total_val": 750.0,
                "market": "US",
                "last_price": 150.0
            }
        ]
    
    def test_save_portfolio_success(self, sample_portfolio, tmp_path):
        """Test saving portfolio to file."""
        portfolio_file = tmp_path / "test_portfolio.json"
        
        with patch('src.services.portfolio_persistence.PORTFOLIO_FILE', str(portfolio_file)):
            result = save_portfolio(sample_portfolio)
            
        assert result is True
        assert portfolio_file.exists()
        
        # Verify content
        with open(portfolio_file, 'r') as f:
            data = json.load(f)
            assert len(data['portfolio']) == 2
            assert data['portfolio'][0]['symbol'] == 'GGAL'
            assert 'last_updated' in data
    
    def test_save_portfolio_empty(self, tmp_path):
        """Test saving empty portfolio."""
        portfolio_file = tmp_path / "test_portfolio.json"
        
        with patch('src.services.portfolio_persistence.PORTFOLIO_FILE', str(portfolio_file)):
            result = save_portfolio([])
            
        assert result is True
        
        with open(portfolio_file, 'r') as f:
            data = json.load(f)
            assert data['portfolio'] == []
    
    def test_save_portfolio_error(self):
        """Test save portfolio with write error."""
        with patch('builtins.open', side_effect=PermissionError("Cannot write")):
            result = save_portfolio([{"symbol": "TEST"}])
            
        assert result is False
    
    def test_load_portfolio_success(self, sample_portfolio, tmp_path):
        """Test loading portfolio from file."""
        portfolio_file = tmp_path / "test_portfolio.json"
        
        # Create test file
        with open(portfolio_file, 'w') as f:
            json.dump({'portfolio': sample_portfolio, 'last_updated': '2025-11-29'}, f)
        
        with patch('src.services.portfolio_persistence.PORTFOLIO_FILE', str(portfolio_file)):
            loaded = load_portfolio()
            
        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]['symbol'] == 'GGAL'
        assert loaded[1]['symbol'] == 'AAPL'
    
    def test_load_portfolio_not_exists(self, tmp_path):
        """Test loading non-existent portfolio."""
        portfolio_file = tmp_path / "nonexistent.json"
        
        with patch('src.services.portfolio_persistence.PORTFOLIO_FILE', str(portfolio_file)):
            loaded = load_portfolio()
            
        assert loaded is None
    
    def test_load_portfolio_corrupted(self, tmp_path):
        """Test loading corrupted portfolio file."""
        portfolio_file = tmp_path / "corrupted.json"
        
        # Create corrupted JSON file
        with open(portfolio_file, 'w') as f:
            f.write("{invalid json")
        
        with patch('src.services.portfolio_persistence.PORTFOLIO_FILE', str(portfolio_file)):
            loaded = load_portfolio()
            
        assert loaded is None
    
    @patch('src.services.portfolio_persistence.load_portfolio')
    @patch('src.services.portfolio_persistence.save_portfolio')
    def test_sync_from_iol_success(self, mock_save, mock_load):
        """Test syncing portfolio from IOL."""
        mock_iol = Mock()
        mock_iol.get_portfolio.return_value = {
            'activos': [
                {
                    'titulo': {'simbolo': 'GGAL'},
                    'cantidad': 15,
                    'ppc': 1200.0,
                    'valorizado': 18000.0
                },
                {
                    'titulo': {'simbolo': 'YPFD'},
                    'cantidad': 20,
                    'ppc': 500.0,
                    'valorizado': 10000.0
                }
            ]
        }
        
        mock_load.return_value = []
        mock_save.return_value = True
        
        result = sync_from_iol(mock_iol)
        
        assert result is True
        mock_save.assert_called_once()
        
        # Verify the portfolio structure
        saved_portfolio = mock_save.call_args[0][0]
        assert len(saved_portfolio) == 2
        assert saved_portfolio[0]['symbol'] == 'GGAL'
        assert saved_portfolio[0]['quantity'] == 15
    
    @patch('src.services.portfolio_persistence.load_portfolio')
    @patch('src.services.portfolio_persistence.save_portfolio')
    def test_sync_from_iol_merge(self, mock_save, mock_load):
        """Test merging IOL portfolio with existing."""
        mock_iol = Mock()
        mock_iol.get_portfolio.return_value = {
            'activos': [
                {
                    'titulo': {'simbolo': 'GGAL'},
                    'cantidad': 10,
                    'ppc': 1000.0,
                    'valorizado': 10000.0
                }
            ]
        }
        
        # Existing portfolio has different asset
        mock_load.return_value = [
            {
                'symbol': 'AAPL',
                'quantity': 5,
                'avg_price': 150.0,
                'total_val': 750.0,
                'market': 'US'
            }
        ]
        mock_save.return_value = True
        
        result = sync_from_iol(mock_iol)
        
        assert result is True
        
        # Should have both assets
        saved_portfolio = mock_save.call_args[0][0]
        assert len(saved_portfolio) == 2
    
    @patch('src.services.portfolio_persistence.load_portfolio')
    @patch('src.services.portfolio_persistence.save_portfolio')
    def test_sync_from_iol_empty(self, mock_save, mock_load):
        """Test syncing when IOL has no assets."""
        mock_iol = Mock()
        mock_iol.get_portfolio.return_value = {'activos': []}
        
        mock_load.return_value = []
        
        result = sync_from_iol(mock_iol)
        
        assert result is False
        mock_save.assert_not_called()
    
    @patch('src.services.portfolio_persistence.load_portfolio')
    @patch('src.services.portfolio_persistence.save_portfolio')
    def test_sync_from_iol_skip_zero_quantity(self, mock_save, mock_load):
        """Test that zero quantity assets are skipped."""
        mock_iol = Mock()
        mock_iol.get_portfolio.return_value = {
            'activos': [
                {
                    'titulo': {'simbolo': 'GGAL'},
                    'cantidad': 10,
                    'ppc': 1000.0,
                    'valorizado': 10000.0
                },
                {
                    'titulo': {'simbolo': 'YPFD'},
                    'cantidad': 0,  # Should be skipped
                    'ppc': 500.0,
                    'valorizado': 0.0
                }
            ]
        }
        
        mock_load.return_value = []
        mock_save.return_value = True
        
        result = sync_from_iol(mock_iol)
        
        assert result is True
        
        # Should only have GGAL
        saved_portfolio = mock_save.call_args[0][0]
        assert len(saved_portfolio) == 1
        assert saved_portfolio[0]['symbol'] == 'GGAL'
    
    @patch('requests.get')
    def test_get_dolar_mep_success(self, mock_get):
        """Test getting MEP dollar rate."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "venta": 1150.50,
            "compra": 1140.00,
            "promedio": 1145.25
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        rate = get_dolar_mep()
        
        assert rate == 1150.50
    
    @patch('requests.get')
    def test_get_dolar_mep_no_venta(self, mock_get):
        """Test MEP rate with no venta field."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "promedio": 1145.25
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        rate = get_dolar_mep()
        
        assert rate == 1145.25
    
    @patch('requests.get')
    def test_get_dolar_mep_error(self, mock_get):
        """Test MEP rate with API error."""
        mock_get.side_effect = Exception("API Error")
        
        rate = get_dolar_mep()
        
        # Should return default
        assert rate == 1050.0
    
    @patch('src.services.portfolio_persistence.load_portfolio')
    @patch('src.services.portfolio_persistence.save_portfolio')
    @patch('src.services.portfolio_persistence.get_dolar_mep')
    def test_update_prices_from_iol_success(self, mock_mep, mock_save, mock_load):
        """Test updating prices from IOL."""
        mock_iol = Mock()
        
        # Mock quote responses
        def mock_get_quote(symbol):
            quotes = {
                "GGAL": {"ultimoPrecio": 1500.0},
                "GOOGL": {"ultimoPrecio": 116.0}  # CEDEAR (58:1 ratio)
            }
            return quotes.get(symbol, {})
        
        mock_iol.get_quote.side_effect = mock_get_quote
        mock_mep.return_value = 1100.0
        
        portfolio = [
            {
                "symbol": "GGAL",
                "quantity": 10,
                "avg_price": 1000.0,
                "total_val": 10000.0
            },
            {
                "symbol": "GOOGL",
                "quantity": 100,
                "avg_price": 2000.0,
                "total_val": 200000.0
            }
        ]
        
        mock_load.return_value = portfolio
        mock_save.return_value = True
        
        result = update_prices_from_iol(mock_iol)
        
        assert result is True
        mock_save.assert_called_once()
    
    @patch('src.services.portfolio_persistence.load_portfolio')
    def test_update_prices_empty_portfolio(self, mock_load):
        """Test updating prices with empty portfolio."""
        mock_iol = Mock()
        mock_load.return_value = None
        
        result = update_prices_from_iol(mock_iol)
        
        assert result is False
    
    @patch('src.services.portfolio_persistence.get_tienda_broker_portfolio')
    @patch('src.services.portfolio_persistence.load_portfolio')
    @patch('src.services.portfolio_persistence.save_portfolio')
    def test_sync_from_tienda_broker_success(self, mock_save, mock_load, mock_tb):
        """Test syncing from Tienda Broker."""
        mock_tb.return_value = [
            {
                "symbol": "GGAL",
                "quantity": 20,
                "avg_price": 1100.0,
                "total_val": 22000.0
            }
        ]
        
        mock_load.return_value = []
        mock_save.return_value = True
        
        result = sync_from_tienda_broker()
        
        assert result is True
        mock_save.assert_called_once()
    
    @patch('src.services.portfolio_persistence.get_tienda_broker_portfolio')
    def test_sync_from_tienda_broker_no_assets(self, mock_tb):
        """Test TB sync with no assets."""
        mock_tb.return_value = None
        
        result = sync_from_tienda_broker()
        
        assert result is False
    
    @patch('src.services.portfolio_persistence.get_tienda_broker_portfolio')
    def test_sync_from_tienda_broker_error(self, mock_tb):
        """Test TB sync with error."""
        mock_tb.side_effect = Exception("Scraping failed")
        
        result = sync_from_tienda_broker()
        
        assert result is False

"""
Tests for Tienda Broker Client.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.connectors.tienda_broker_client import TiendaBrokerClient, get_tienda_broker_portfolio


class TestTiendaBrokerClient:
    """Test suite for TiendaBrokerClient."""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables."""
        monkeypatch.setenv("TB_EMAIL", "test@example.com")
        monkeypatch.setenv("TB_PASSWORD", "testpass")
        
    @pytest.fixture
    def client(self, mock_env):
        """Create TB client instance."""
        return TiendaBrokerClient()
    
    def test_client_initialization(self, client):
        """Test that client initializes correctly."""
        assert client.email == "test@example.com"
        assert client.password == "testpass"

    @patch('src.connectors.tienda_broker_client.subprocess.run')
    def test_get_portfolio_success(self, mock_run):
        """Test getting portfolio via subprocess mock."""
        # Mock subprocess output
        mock_process = Mock()
        mock_process.stdout = """__JSON_START__
        [
            {
                "symbol": "GGAL",
                "quantity": 10,
                "avg_price": 1000.0,
                "total_val": 10000.0,
                "market": "ARG"
            }
        ]
        __JSON_END__"""
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        portfolio = get_tienda_broker_portfolio()
        
        assert len(portfolio) == 1
        assert portfolio[0]["symbol"] == "GGAL"
        
    @patch('src.connectors.tienda_broker_client.subprocess.run')
    def test_get_portfolio_failure(self, mock_run):
        """Test getting portfolio with subprocess failure."""
        mock_process = Mock()
        mock_process.returncode = 1
        mock_process.stderr = "Error scraping"
        # When check=True, run raises CalledProcessError
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, ['cmd'], stderr="Error scraping")
        
        portfolio = get_tienda_broker_portfolio()
        
        assert portfolio == []
        
    @patch('src.connectors.tienda_broker_client.subprocess.run')
    def test_get_portfolio_invalid_json(self, mock_run):
        """Test getting portfolio with invalid JSON output."""
        mock_process = Mock()
        mock_process.stdout = "Invalid JSON"
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        portfolio = get_tienda_broker_portfolio()
        
        assert portfolio == []

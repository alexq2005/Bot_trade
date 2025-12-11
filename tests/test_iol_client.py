"""
Expanded tests for IOL Client with full coverage.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.connectors.iol_client import IOLClient
import requests
from tenacity import RetryError


class TestIOLClient:
    """Comprehensive test suite for IOLClient."""
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables."""
        monkeypatch.setenv("IOL_USERNAME", "test@example.com")
        monkeypatch.setenv("IOL_PASSWORD", "testpass")
        
    @pytest.fixture
    def client(self, mock_env):
        """Create IOL client instance."""
        with patch('src.connectors.iol_client.settings') as mock_settings:
            mock_settings.IOL_API_URL = "https://api.invertironline.com/api/v2"
            mock_settings.IOL_TOKEN_URL = "https://api.invertironline.com/token"
            mock_settings.IOL_USERNAME = "test@example.com"
            mock_settings.IOL_PASSWORD = "testpass"
            return IOLClient()
    
    def test_client_initialization(self, client):
        """Test that client initializes correctly."""
        assert client.username == "test@example.com"
        assert client.password == "testpass"
        assert client.access_token is None
        assert client.base_url == "https://api.invertironline.com/api/v2"
        
    def test_market_codes_mapping(self, client):
        """Test market code mappings."""
        assert client.MARKET_CODES["GGAL"] == "bCBA"
        assert client.MARKET_CODES["AAPL"] == "NASDAQ"
        assert client.MARKET_CODES["KO"] == "NYSE"
        
    @patch('requests.post')
    def test_login_success(self, mock_post, client):
        """Test successful login."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_token_123",
            "refresh_token": "refresh_token_456",
            "expires_in": 3600
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        client._login()
        
        assert client.access_token == "test_token_123"
        assert client.refresh_token == "refresh_token_456"
        assert client.token_expiry > 0
        
    @patch('requests.post')
    def test_login_failure(self, mock_post, client):
        """Test login failure with retry."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        with pytest.raises(requests.exceptions.ConnectionError):
            client._login()
            
    def test_is_token_expired_no_token(self, client):
        """Test token expiration check with no token."""
        assert client._is_token_expired() is True
        
    def test_is_token_expired_valid_token(self, client):
        """Test token expiration check with valid token."""
        import time
        client.access_token = "valid_token"
        client.token_expiry = time.time() + 3600  # 1 hour from now
        
        assert client._is_token_expired() is False
        
    def test_is_token_expired_expired_token(self, client):
        """Test token expiration check with expired token."""
        import time
        client.access_token = "expired_token"
        client.token_expiry = time.time() - 100  # 100 seconds ago
        
        assert client._is_token_expired() is True
        
    def test_detect_market_arg(self, client):
        """Test market detection for Argentine stocks."""
        assert client._detect_market("GGAL") == "bCBA"
        assert client._detect_market("ypfd") == "bCBA"  # Case insensitive
        
    def test_detect_market_us(self, client):
        """Test market detection for US stocks."""
        assert client._detect_market("AAPL") == "NASDAQ"
        assert client._detect_market("KO") == "NYSE"
        
    def test_detect_market_unknown(self, client):
        """Test market detection for unknown symbols."""
        assert client._detect_market("UNKNOWN") == "bCBA"  # Default
        
    @patch('requests.get')
    def test_get_quote_success(self, mock_get, client):
        """Test getting a quote successfully."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999  # Far future
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "ultimoPrecio": 1500.75,
            "variacion": 2.5,
            "apertura": 1480.0,
            "maximo": 1520.0,
            "minimo": 1475.0
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        quote = client.get_quote("GGAL")
        
        assert quote["ultimoPrecio"] == 1500.75
        assert quote["variacion"] == 2.5
        assert "error" not in quote
        
    @patch('requests.get')
    def test_get_quote_with_retry(self, mock_get, client):
        """Test quote retrieval with automatic retry."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999
        
        # Fail twice, succeed third time
        mock_response_fail = Mock()
        mock_response_fail.side_effect = requests.exceptions.Timeout("Timeout")
        
        mock_response_success = Mock()
        mock_response_success.json.return_value = {"ultimoPrecio": 1500.0}
        mock_response_success.status_code = 200
        
        mock_get.side_effect = [
            requests.exceptions.Timeout("Timeout 1"),
            requests.exceptions.Timeout("Timeout 2"),
            mock_response_success
        ]
        
        quote = client.get_quote("GGAL")
        assert quote.get("ultimoPrecio") == 1500.0
        assert mock_get.call_count == 3  # 2 failures + 1 success
        
    @patch('requests.get')
    def test_get_account_status_success(self, mock_get, client):
        """Test getting account status."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "cuentas": [
                {
                    "tipo": "inversion_Argentina_Pesos",
                    "saldos": [
                        {
                            "liquidacion": "hrs48",
                            "disponibleOperar": 50000.0
                        }
                    ]
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        account = client.get_account_status()
        
        assert "cuentas" in account
        assert account["cuentas"][0]["tipo"] == "inversion_Argentina_Pesos"
        
    @patch('requests.get')
    def test_get_portfolio_argentina(self, mock_get, client):
        """Test getting Argentina portfolio."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "activos": [
                {
                    "titulo": {"simbolo": "GGAL"},
                    "cantidad": 10,
                    "ppc": 1450.0,
                    "valorizado": 15000.0
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        portfolio = client.get_portfolio("argentina")
        
        assert "activos" in portfolio
        assert len(portfolio["activos"]) == 1
        assert portfolio["activos"][0]["titulo"]["simbolo"] == "GGAL"
        
    @patch('requests.get')
    def test_get_available_balance_success(self, mock_get, client):
        """Test getting available balance."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "cuentas": [
                {
                    "tipo": "inversion_Argentina_Pesos",
                    "saldos": [
                        {
                            "liquidacion": "hrs48",
                            "disponibleOperar": 75000.50
                        }
                    ]
                }
            ]
        }
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        balance = client.get_available_balance()
        
        assert balance == 75000.50
        
    @patch('requests.get')
    def test_get_available_balance_no_account(self, mock_get, client):
        """Test getting balance when no account found."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999
        
        mock_response = Mock()
        mock_response.json.return_value = {"cuentas": []}
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        balance = client.get_available_balance()
        
        assert balance == 0.0
        
    @patch('requests.get')
    def test_get_available_balance_error(self, mock_get, client):
        """Test balance retrieval with error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        balance = client.get_available_balance()
        
        assert balance == 0.0
        
    @patch('requests.post')
    def test_place_order_buy_success(self, mock_post, client):
        """Test placing a buy order."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "numeroOperacion": "12345",
            "estado": "Pendiente"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = client.place_order("GGAL", 10, 1500.0, "buy")
        
        assert result["numeroOperacion"] == "12345"
        assert "error" not in result
        
    @patch('requests.post')
    def test_place_order_sell_success(self, mock_post, client):
        """Test placing a sell order."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "numeroOperacion": "67890",
            "estado": "Ejecutada"
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = client.place_order("GGAL", 5, 1550.0, "sell")
        
        assert result["numeroOperacion"] == "67890"
        
    @patch('requests.post')
    def test_place_order_failure(self, mock_post, client):
        """Test order placement failure."""
        client.access_token = "test_token"
        client.token_expiry = 999999999999
        
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Saldo insuficiente"
        mock_post.return_value = mock_response
        
        result = client.place_order("GGAL", 100, 1500.0, "buy")
        
        assert "error" in result
        assert result["status_code"] == 400
        
    @patch('requests.get')
    def test_get_headers_auto_login(self, mock_get, client):
        """Test that get_headers automatically logs in if needed."""
        # Token is expired
        client.access_token = None
        
        with patch.object(client, '_login') as mock_login:
            mock_login.return_value = None
            client.access_token = "new_token"
            
            headers = client._get_headers()
            
            mock_login.assert_called_once()
            assert headers["Authorization"] == "Bearer new_token"

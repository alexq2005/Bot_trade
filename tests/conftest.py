"""
Configuración compartida para tests (pytest fixtures)
"""
import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configurar variables de entorno para testing
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TESTING'] = 'true'

@pytest.fixture
def mock_iol_client():
    """Mock de IOLClient para tests"""
    mock = MagicMock()
    mock.get_available_balance.return_value = 100000.0
    mock.get_quote.return_value = {
        'price': 100.0,
        'change_percent': 1.5,
        'volume': 1000000
    }
    mock.place_order.return_value = {
        'success': True,
        'numeroOperacion': '12345'
    }
    return mock

@pytest.fixture
def mock_prediction_service():
    """Mock de PredictionService para tests"""
    mock = MagicMock()
    mock.generate_signal.return_value = {
        'signal': 'BUY',
        'change_pct': 2.5,
        'current_price': 100.0,
        'predicted_price': 102.5,
        'confidence': 0.75
    }
    return mock

@pytest.fixture
def sample_symbols():
    """Lista de símbolos de prueba"""
    return ['GGAL', 'YPFD', 'AAPL']

@pytest.fixture
def sample_trade_data():
    """Datos de trade de ejemplo"""
    return {
        'timestamp': '2025-12-01T10:00:00',
        'symbol': 'GGAL',
        'signal': 'BUY',
        'price': 100.0,
        'quantity': 10,
        'pnl': 0.0
    }

@pytest.fixture
def temp_config_file(tmp_path):
    """Archivo de configuración temporal para tests"""
    config_file = tmp_path / "test_config.json"
    config_file.write_text('{"test": true}')
    return config_file

@pytest.fixture(autouse=True)
def reset_environment():
    """Resetear variables de entorno antes de cada test"""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


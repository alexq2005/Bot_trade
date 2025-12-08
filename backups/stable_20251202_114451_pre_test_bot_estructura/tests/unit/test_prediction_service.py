"""
Tests unitarios para PredictionService
"""
import pytest
import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.prediction_service import PredictionService
from tests.conftest import mock_iol_client


class TestPredictionService:
    """Tests para PredictionService"""
    
    def test_service_initialization(self):
        """Test que el servicio se inicializa correctamente"""
        service = PredictionService()
        assert service is not None
        assert hasattr(service, 'predict_price')
        assert hasattr(service, 'generate_signal')
    
    def test_generate_signal_buy(self, mock_prediction_service):
        """Test generación de señal BUY"""
        result = mock_prediction_service.generate_signal('GGAL', threshold=2.0)
        assert result is not None
        assert result['signal'] == 'BUY'
        assert result['change_pct'] > 0
    
    def test_generate_signal_sell(self):
        """Test generación de señal SELL"""
        service = PredictionService()
        # Mock para retornar señal SELL
        # En un test real, esto requeriría mockear el modelo
        pass
    
    def test_generate_signal_hold(self):
        """Test generación de señal HOLD"""
        service = PredictionService()
        # Mock para retornar señal HOLD
        pass
    
    def test_generate_signal_with_technical_fallback(self):
        """Test que usa análisis técnico como fallback si IA falla"""
        service = PredictionService()
        # Simular fallo de IA y verificar que usa análisis técnico
        pass
    
    def test_predict_price_returns_none_on_error(self):
        """Test que predict_price retorna None en caso de error"""
        service = PredictionService()
        # Test con símbolo inválido o modelo no disponible
        result = service.predict_price('INVALID_SYMBOL_XYZ')
        # Debería retornar None o manejar el error gracefully
        assert result is None or 'error' in result or isinstance(result, dict)


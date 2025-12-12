"""
IOL Client Mejorado con Circuit Breakers, Cache y Retry Logic
Wrapper alrededor de IOLClient original con mejoras
"""
from typing import Dict, Any, Optional
from src.connectors.iol_client import IOLClient
from src.core.circuit_breaker import get_iol_circuit_breaker
from src.core.retry_handler import retry_on_network_error, retry_on_api_error
from src.core.enhanced_cache import get_quote_cache, get_prediction_cache
from src.core.logger import get_logger

logger = get_logger("iol_client_enhanced")


class EnhancedIOLClient:
    """
    Cliente IOL mejorado con circuit breakers, caché y retry logic
    """
    
    def __init__(self):
        """Inicializa el cliente mejorado"""
        self.client = IOLClient()
        self.circuit_breaker = get_iol_circuit_breaker()
        self.quote_cache = get_quote_cache()
        self.logger = logger
    
    def get_quote(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Obtiene cotización con caché y circuit breaker
        
        Args:
            symbol: Símbolo a consultar
            use_cache: Si usar caché (default: True, TTL: 30 seg)
        
        Returns:
            Dict con cotización
        """
        cache_key = f"quote_{symbol}"
        
        # Intentar obtener del caché
        if use_cache:
            cached_quote = self.quote_cache.get(cache_key)
            if cached_quote:
                self.logger.debug(f"Quote de {symbol} obtenida del caché")
                return cached_quote
        
        # Obtener con circuit breaker y retry
        @retry_on_network_error(max_retries=3)
        def _get_quote():
            return self.circuit_breaker.call(self.client.get_quote, symbol)
        
        try:
            quote = _get_quote()
            
            # Cachear si es exitoso
            if use_cache and "error" not in quote:
                self.quote_cache.set(cache_key, quote, ttl_seconds=30)
            
            return quote
        except Exception as e:
            self.logger.error(f"Error obteniendo quote de {symbol}: {e}")
            # Retornar caché si está disponible, aunque esté expirado
            if use_cache:
                cached_quote = self.quote_cache.get(cache_key)
                if cached_quote:
                    self.logger.warning(f"Usando quote cacheada (posiblemente expirada) para {symbol}")
                    return cached_quote
            return {"error": str(e)}
    
    def get_available_balance(self, use_cache: bool = False) -> float:
        """
        Obtiene saldo disponible con circuit breaker
        
        Args:
            use_cache: Si usar caché (default: False para saldo siempre actualizado)
        
        Returns:
            Saldo disponible
        """
        @retry_on_network_error(max_retries=3)
        def _get_balance():
            return self.circuit_breaker.call(self.client.get_available_balance)
        
        try:
            return _get_balance()
        except Exception as e:
            self.logger.error(f"Error obteniendo saldo: {e}")
            return 0.0
    
    def place_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        side: str,
        market: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coloca una orden con validación y circuit breaker
        
        Args:
            symbol: Símbolo
            quantity: Cantidad
            price: Precio
            side: 'buy' o 'sell'
            market: Mercado (opcional)
        
        Returns:
            Dict con resultado de la orden
        """
        from src.core.security import get_order_validator, get_audit_logger
        
        validator = get_order_validator()
        audit = get_audit_logger()
        
        # Validar orden
        capital = self.get_available_balance()
        is_valid, error_msg = validator.validate_order(
            symbol, quantity, price, capital, side
        )
        
        if not is_valid:
            self.logger.error(f"Orden inválida: {error_msg}")
            return {"error": error_msg, "success": False}
        
        # Ejecutar con circuit breaker
        @retry_on_api_error(max_retries=2)  # Menos reintentos para órdenes
        def _place_order():
            return self.circuit_breaker.call(
                self.client.place_order,
                symbol, quantity, price, side, market
            )
        
        try:
            result = _place_order()
            
            # Log de auditoría
            if result.get("success") or "numeroOperacion" in result:
                audit.log_operation("ORDER_EXECUTED", {
                    "symbol": symbol,
                    "quantity": quantity,
                    "price": price,
                    "side": side,
                    "order_id": result.get("numeroOperacion")
                })
            
            return result
        except Exception as e:
            self.logger.error(f"Error colocando orden: {e}")
            return {"error": str(e), "success": False}
    
    def get_portfolio(self) -> Dict[str, Any]:
        """Obtiene portafolio con circuit breaker"""
        @retry_on_network_error(max_retries=3)
        def _get_portfolio():
            return self.circuit_breaker.call(self.client.get_portfolio)
        
        try:
            return _get_portfolio()
        except Exception as e:
            self.logger.error(f"Error obteniendo portafolio: {e}")
            return {"error": str(e)}
    
    def get_account_status(self) -> Dict[str, Any]:
        """Obtiene estado de cuenta con circuit breaker"""
        @retry_on_network_error(max_retries=3)
        def _get_status():
            return self.circuit_breaker.call(self.client.get_account_status)
        
        try:
            return _get_status()
        except Exception as e:
            self.logger.error(f"Error obteniendo estado de cuenta: {e}")
            return {"error": str(e)}
    
    def get_all_balances(self) -> Dict[str, float]:
        """Obtiene todos los balances con circuit breaker"""
        @retry_on_network_error(max_retries=3)
        def _get_balances():
            return self.circuit_breaker.call(self.client.get_all_balances)
        
        try:
            return _get_balances()
        except Exception as e:
            self.logger.error(f"Error obteniendo balances: {e}")
            return {}
    
    # Exponer propiedades del cliente original
    @property
    def username(self) -> str:
        return self.client.username
    
    @property
    def access_token(self) -> Optional[str]:
        return self.client.access_token


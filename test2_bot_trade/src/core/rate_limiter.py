"""
Rate Limiter para controlar frecuencia de llamadas a APIs
"""
import time
import logging
from collections import defaultdict
from threading import Lock
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RateLimiter:
    """Limitador de tasa para APIs con ventana deslizante"""
    
    def __init__(self, max_calls: int = 100, period: int = 60):
        """
        Inicializa el rate limiter
        
        Args:
            max_calls: Número máximo de llamadas permitidas
            period: Período en segundos para la ventana
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = defaultdict(list)  # key -> [timestamps]
        self.lock = Lock()
        self._last_warning = {}  # Para evitar spam de warnings
    
    def wait_if_needed(self, key: str, silent: bool = False) -> bool:
        """
        Espera si se excedió el límite de rate
        
        Args:
            key: Clave única para el rate limit (ej: 'iol_api', 'telegram')
            silent: Si True, no registra warnings
            
        Returns:
            True si esperó, False si no fue necesario
        """
        with self.lock:
            now = time.time()
            
            # Limpiar llamadas antiguas (fuera de la ventana)
            self.calls[key] = [
                call_time for call_time in self.calls[key]
                if now - call_time < self.period
            ]
            
            # Verificar si se excedió el límite
            if len(self.calls[key]) >= self.max_calls:
                # Calcular tiempo de espera
                oldest_call = self.calls[key][0]
                sleep_time = self.period - (now - oldest_call)
                
                if sleep_time > 0:
                    if not silent:
                        # Evitar spam de warnings (máximo uno cada 10 segundos)
                        last_warn = self._last_warning.get(key, 0)
                        if now - last_warn > 10:
                            logger.warning(
                                f"⏳ Rate limit alcanzado para '{key}'. "
                                f"Esperando {sleep_time:.2f}s... "
                                f"({len(self.calls[key])}/{self.max_calls} llamadas)"
                            )
                            self._last_warning[key] = now
                    
                    time.sleep(sleep_time)
                    # Limpiar después de esperar
                    now = time.time()
                    self.calls[key] = [
                        call_time for call_time in self.calls[key]
                        if now - call_time < self.period
                    ]
                    return True
            
            # Registrar esta llamada
            self.calls[key].append(now)
            return False
    
    def get_remaining_calls(self, key: str) -> int:
        """
        Obtiene el número de llamadas restantes en la ventana actual
        
        Args:
            key: Clave del rate limit
            
        Returns:
            Número de llamadas restantes
        """
        with self.lock:
            now = time.time()
            # Limpiar llamadas antiguas
            self.calls[key] = [
                call_time for call_time in self.calls[key]
                if now - call_time < self.period
            ]
            return max(0, self.max_calls - len(self.calls[key]))
    
    def reset(self, key: Optional[str] = None):
        """
        Resetea el contador de llamadas
        
        Args:
            key: Clave a resetear. Si es None, resetea todas
        """
        with self.lock:
            if key:
                self.calls[key] = []
            else:
                self.calls.clear()


# Instancias globales para diferentes APIs
iol_rate_limiter = RateLimiter(max_calls=100, period=60)  # 100 llamadas por minuto
telegram_rate_limiter = RateLimiter(max_calls=30, period=60)  # 30 mensajes por minuto
yahoo_rate_limiter = RateLimiter(max_calls=2000, period=3600)  # 2000 llamadas por hora
news_api_rate_limiter = RateLimiter(max_calls=100, period=3600)  # 100 llamadas por hora


def rate_limit(key: str, max_calls: int = 100, period: int = 60):
    """
    Decorador para aplicar rate limiting a una función
    
    Args:
        key: Clave única para el rate limit
        max_calls: Número máximo de llamadas
        period: Período en segundos
    """
    limiter = RateLimiter(max_calls=max_calls, period=period)
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            limiter.wait_if_needed(key)
            return func(*args, **kwargs)
        return wrapper
    return decorator


"""
Sistema de Reintentos con Exponential Backoff
"""
import time
import random
from typing import Callable, Optional, Type, Tuple, Any
from functools import wraps

from src.core.logger import get_logger

logger = get_logger("retry_handler")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    Decorador para reintentos con exponential backoff
    
    Args:
        max_retries: Número máximo de reintentos
        initial_delay: Delay inicial en segundos
        max_delay: Delay máximo en segundos
        exponential_base: Base exponencial para el delay
        jitter: Si agregar jitter aleatorio al delay
        exceptions: Tupla de excepciones que deben causar reintento
        on_retry: Callback llamado en cada reintento
    
    Example:
        @retry_with_backoff(max_retries=5, initial_delay=1.0)
        def my_function():
            # código que puede fallar
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        # Último intento falló
                        logger.error(
                            f"Función {func.__name__} falló después de {max_retries + 1} intentos: {e}"
                        )
                        raise
                    
                    # Calcular delay con exponential backoff
                    delay = min(initial_delay * (exponential_base ** attempt), max_delay)
                    
                    # Agregar jitter si está habilitado
                    if jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay = delay + jitter_amount
                    
                    # Llamar callback si existe
                    if on_retry:
                        try:
                            on_retry(attempt + 1, delay, e)
                        except Exception:
                            pass
                    
                    logger.warning(
                        f"Función {func.__name__} falló (intento {attempt + 1}/{max_retries + 1}). "
                        f"Reintentando en {delay:.2f} segundos... Error: {e}"
                    )
                    
                    time.sleep(delay)
            
            # No debería llegar aquí, pero por si acaso
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_on_network_error(
    max_retries: int = 5,
    initial_delay: float = 2.0
):
    """
    Decorador específico para errores de red
    
    Args:
        max_retries: Número máximo de reintentos
        initial_delay: Delay inicial en segundos
    """
    import requests
    
    return retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=120.0,
        exponential_base=2.0,
        exceptions=(requests.RequestException, ConnectionError, TimeoutError)
    )


def retry_on_api_error(
    max_retries: int = 3,
    initial_delay: float = 1.0
):
    """
    Decorador específico para errores de API (429, 500, etc.)
    
    Args:
        max_retries: Número máximo de reintentos
        initial_delay: Delay inicial en segundos
    """
    import requests
    
    def should_retry(exception: Exception) -> bool:
        """Determina si se debe reintentar basado en el código de estado"""
        if isinstance(exception, requests.HTTPError):
            status_code = exception.response.status_code
            # Reintentar en errores del servidor (5xx) y rate limiting (429)
            return status_code >= 500 or status_code == 429
        return True
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if not should_retry(e) or attempt == max_retries:
                        logger.error(
                            f"Función {func.__name__} falló después de {attempt + 1} intentos: {e}"
                        )
                        raise
                    
                    delay = min(initial_delay * (2 ** attempt), 60.0)
                    
                    logger.warning(
                        f"Función {func.__name__} falló (intento {attempt + 1}/{max_retries}). "
                        f"Reintentando en {delay:.2f} segundos... Error: {e}"
                    )
                    
                    time.sleep(delay)
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


class RetryHandler:
    """
    Clase para manejar reintentos de forma más flexible
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    def execute(
        self,
        func: Callable,
        *args,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        **kwargs
    ) -> Any:
        """
        Ejecuta una función con reintentos
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            exceptions: Excepciones que deben causar reintento
        
        Returns:
            Resultado de la función
        
        Raises:
            Exception: Si todos los reintentos fallan
        """
        delay = self.initial_delay
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(
                        f"Función {func.__name__} falló después de {self.max_retries + 1} intentos: {e}"
                    )
                    raise
                
                delay = min(self.initial_delay * (self.exponential_base ** attempt), self.max_delay)
                
                logger.warning(
                    f"Función {func.__name__} falló (intento {attempt + 1}/{self.max_retries + 1}). "
                    f"Reintentando en {delay:.2f} segundos..."
                )
                
                time.sleep(delay)
        
        if last_exception:
            raise last_exception


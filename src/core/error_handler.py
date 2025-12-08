"""
Manejo robusto de errores con reintentos automáticos
"""
import time
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class RetryHandler:
    """Manejo de errores con reintentos automáticos y backoff exponencial"""
    
    @staticmethod
    def retry_on_failure(
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        on_retry: Optional[Callable] = None
    ):
        """
        Decorador para reintentos automáticos con backoff exponencial
        
        Args:
            max_retries: Número máximo de reintentos
            delay: Delay inicial en segundos
            backoff: Multiplicador para backoff exponencial
            exceptions: Tupla de excepciones a capturar
            on_retry: Función callback a ejecutar en cada reintento
            
        Returns:
            Decorador que envuelve la función
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                current_delay = delay
                
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        
                        if attempt == max_retries - 1:
                            logger.error(
                                f"❌ {func.__name__} falló después de {max_retries} intentos: {e}",
                                exc_info=True
                            )
                            raise
                        
                        logger.warning(
                            f"⚠️  Intento {attempt + 1}/{max_retries} falló en {func.__name__}: {e}. "
                            f"Reintentando en {current_delay:.2f}s..."
                        )
                        
                        if on_retry:
                            try:
                                on_retry(attempt + 1, e, current_delay)
                            except Exception as callback_error:
                                logger.warning(f"Error en callback on_retry: {callback_error}")
                        
                        time.sleep(current_delay)
                        current_delay *= backoff
                
                # Esto no debería ejecutarse, pero por seguridad
                raise last_exception
            
            return wrapper
        return decorator


class ErrorHandler:
    """Clase utilitaria para manejo de errores"""
    
    @staticmethod
    def safe_execute(
        func: Callable,
        default_return: Any = None,
        log_error: bool = True,
        *args,
        **kwargs
    ) -> Any:
        """
        Ejecuta una función de forma segura, retornando un valor por defecto si falla
        
        Args:
            func: Función a ejecutar
            default_return: Valor a retornar si la función falla
            log_error: Si True, registra el error en el log
            *args: Argumentos posicionales para la función
            **kwargs: Argumentos nombrados para la función
            
        Returns:
            Resultado de la función o default_return si falla
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                logger.error(
                    f"Error ejecutando {func.__name__}: {e}",
                    exc_info=True
                )
            return default_return
    
    @staticmethod
    def handle_critical_error(
        error: Exception,
        context: str = "",
        notify: bool = True
    ):
        """
        Maneja errores críticos con logging detallado y notificaciones
        
        Args:
            error: Excepción capturada
            context: Contexto adicional del error
            notify: Si True, intenta enviar notificación
        """
        error_msg = f"❌ ERROR CRÍTICO"
        if context:
            error_msg += f" en {context}"
        error_msg += f": {type(error).__name__}: {str(error)}"
        
        logger.critical(error_msg, exc_info=True)
        
        if notify:
            try:
                # Intentar enviar notificación (si Telegram está configurado)
                from src.services.telegram_bot import TelegramAlertBot
                telegram_bot = TelegramAlertBot()
                if telegram_bot.bot:
                    telegram_bot.send_alert(
                        f"🚨 ERROR CRÍTICO\n\n"
                        f"Contexto: {context}\n"
                        f"Error: {type(error).__name__}\n"
                        f"Mensaje: {str(error)}"
                    )
            except Exception as notify_error:
                logger.warning(f"No se pudo enviar notificación: {notify_error}")


# Decoradores de conveniencia
def retry_on_network_error(max_retries: int = 3):
    """Decorador específico para errores de red"""
    return RetryHandler.retry_on_failure(
        max_retries=max_retries,
        delay=2.0,
        backoff=2.0,
        exceptions=(ConnectionError, TimeoutError, OSError)
    )


def retry_on_api_error(max_retries: int = 3):
    """Decorador específico para errores de API"""
    return RetryHandler.retry_on_failure(
        max_retries=max_retries,
        delay=1.0,
        backoff=1.5,
        exceptions=(Exception,)
    )


def safe_execute(default_return=None, log_error=True):
    """
    Decorador para ejecutar función de forma segura
    
    Args:
        default_return: Valor a retornar si falla
        log_error: Si True, registra el error
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return ErrorHandler.safe_execute(
                func,
                default_return=default_return,
                log_error=log_error,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


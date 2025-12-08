"""
Circuit Breaker Pattern para APIs y servicios externos
Previene llamadas repetidas a servicios que están fallando
"""
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Optional, Any
from dataclasses import dataclass, field

from src.core.logger import get_logger

logger = get_logger("circuit_breaker")


class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Fallando, no permitir llamadas
    HALF_OPEN = "half_open"  # Probando si el servicio se recuperó


@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    failure_threshold: int = 5  # Número de fallos antes de abrir
    success_threshold: int = 2  # Número de éxitos para cerrar desde half-open
    timeout_seconds: int = 60  # Tiempo antes de intentar half-open
    expected_exception: type = Exception  # Excepción esperada que cuenta como fallo


@dataclass
class CircuitBreakerStats:
    """Estadísticas del circuit breaker"""
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0


class CircuitBreaker:
    """
    Circuit Breaker para proteger llamadas a servicios externos
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        """
        Args:
            name: Nombre del circuit breaker (para logging)
            config: Configuración personalizada
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()
        self.logger = logger
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función protegida por el circuit breaker
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
        
        Returns:
            Resultado de la función
        
        Raises:
            CircuitBreakerOpenError: Si el circuit está abierto
            Exception: Si la función falla
        """
        self.stats.total_calls += 1
        
        # Verificar estado
        if self.stats.state == CircuitState.OPEN:
            # Verificar si es tiempo de intentar half-open
            if self._should_attempt_half_open():
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.successes = 0
                self.logger.info(f"Circuit breaker '{self.name}' moviendo a HALF_OPEN")
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' está OPEN. "
                    f"Espera {self.config.timeout_seconds} segundos antes de reintentar."
                )
        
        # Ejecutar función
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_half_open(self) -> bool:
        """Determina si se debe intentar half-open"""
        if self.stats.last_failure_time is None:
            return True
        
        elapsed = (datetime.now() - self.stats.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_seconds
    
    def _on_success(self):
        """Maneja un éxito"""
        self.stats.total_successes += 1
        self.stats.last_success_time = datetime.now()
        
        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.successes += 1
            if self.stats.successes >= self.config.success_threshold:
                self.stats.state = CircuitState.CLOSED
                self.stats.failures = 0
                self.logger.info(f"Circuit breaker '{self.name}' cerrado (recuperado)")
        elif self.stats.state == CircuitState.CLOSED:
            # Resetear contador de fallos en caso de éxito
            if self.stats.failures > 0:
                self.stats.failures = max(0, self.stats.failures - 1)
    
    def _on_failure(self):
        """Maneja un fallo"""
        self.stats.total_failures += 1
        self.stats.last_failure_time = datetime.now()
        self.stats.failures += 1
        
        if self.stats.state == CircuitState.HALF_OPEN:
            # Fallo en half-open, volver a abrir
            self.stats.state = CircuitState.OPEN
            self.stats.successes = 0
            self.logger.warning(f"Circuit breaker '{self.name}' abierto nuevamente (fallo en half-open)")
        elif self.stats.state == CircuitState.CLOSED:
            if self.stats.failures >= self.config.failure_threshold:
                self.stats.state = CircuitState.OPEN
                self.logger.error(
                    f"Circuit breaker '{self.name}' abierto después de {self.stats.failures} fallos"
                )
    
    def reset(self):
        """Resetea el circuit breaker manualmente"""
        self.stats = CircuitBreakerStats()
        self.logger.info(f"Circuit breaker '{self.name}' reseteado manualmente")
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del circuit breaker"""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "failures": self.stats.failures,
            "successes": self.stats.successes,
            "total_calls": self.stats.total_calls,
            "total_failures": self.stats.total_failures,
            "total_successes": self.stats.total_successes,
            "last_failure": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
        }


class CircuitBreakerOpenError(Exception):
    """Excepción lanzada cuando el circuit breaker está abierto"""
    pass


# Circuit breakers globales para servicios comunes
_iol_circuit_breaker = None
_telegram_circuit_breaker = None
_yahoo_circuit_breaker = None


def get_iol_circuit_breaker() -> CircuitBreaker:
    """Obtiene el circuit breaker para IOL API"""
    global _iol_circuit_breaker
    if _iol_circuit_breaker is None:
        _iol_circuit_breaker = CircuitBreaker(
            "IOL_API",
            CircuitBreakerConfig(
                failure_threshold=5,
                timeout_seconds=60,
                expected_exception=Exception
            )
        )
    return _iol_circuit_breaker


def get_telegram_circuit_breaker() -> CircuitBreaker:
    """Obtiene el circuit breaker para Telegram API"""
    global _telegram_circuit_breaker
    if _telegram_circuit_breaker is None:
        _telegram_circuit_breaker = CircuitBreaker(
            "Telegram_API",
            CircuitBreakerConfig(
                failure_threshold=3,
                timeout_seconds=30,
                expected_exception=Exception
            )
        )
    return _telegram_circuit_breaker


def get_yahoo_circuit_breaker() -> CircuitBreaker:
    """Obtiene el circuit breaker para Yahoo Finance API"""
    global _yahoo_circuit_breaker
    if _yahoo_circuit_breaker is None:
        _yahoo_circuit_breaker = CircuitBreaker(
            "Yahoo_Finance_API",
            CircuitBreakerConfig(
                failure_threshold=10,
                timeout_seconds=120,
                expected_exception=Exception
            )
        )
    return _yahoo_circuit_breaker


"""
Sistema de Caché Mejorado con TTL y invalidación inteligente
"""
import time
import json
from datetime import datetime, timedelta
from typing import Any, Optional, Callable, Dict
from pathlib import Path
import hashlib
import pickle

from src.core.logger import get_logger

logger = get_logger("cache")


class CacheEntry:
    """Entrada de caché con TTL"""
    
    def __init__(self, value: Any, ttl_seconds: float, created_at: Optional[datetime] = None):
        """
        Args:
            value: Valor a cachear
            ttl_seconds: Tiempo de vida en segundos
            created_at: Fecha de creación (default: ahora)
        """
        self.value = value
        self.ttl_seconds = ttl_seconds
        self.created_at = created_at or datetime.now()
    
    def is_expired(self) -> bool:
        """Verifica si la entrada ha expirado"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed >= self.ttl_seconds
    
    def time_until_expiry(self) -> float:
        """Retorna segundos hasta que expire"""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return max(0, self.ttl_seconds - elapsed)


class EnhancedCache:
    """
    Sistema de caché mejorado con TTL, persistencia y invalidación
    """
    
    def __init__(self, cache_dir: Optional[Path] = None, max_memory_size: int = 1000):
        """
        Args:
            cache_dir: Directorio para caché persistente (opcional)
            max_memory_size: Número máximo de entradas en memoria
        """
        self.cache_dir = cache_dir or Path(".cache")
        self.max_memory_size = max_memory_size
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._access_times: Dict[str, datetime] = {}
        self.logger = logger
        
        # Crear directorio de caché si no existe
        if self.cache_dir:
            self.cache_dir.mkdir(exist_ok=True)
    
    def _make_key(self, *args, **kwargs) -> str:
        """Genera una clave única para los argumentos"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Obtiene un valor del caché
        
        Args:
            key: Clave del caché
            default: Valor por defecto si no existe o expiró
        
        Returns:
            Valor cacheado o default
        """
        # Verificar caché en memoria
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if not entry.is_expired():
                self._access_times[key] = datetime.now()
                return entry.value
            else:
                # Eliminar entrada expirada
                del self._memory_cache[key]
                if key in self._access_times:
                    del self._access_times[key]
        
        # Verificar caché persistente
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    
                    if not entry.is_expired():
                        # Mover a memoria
                        self._memory_cache[key] = entry
                        self._access_times[key] = datetime.now()
                        return entry.value
                    else:
                        # Eliminar archivo expirado
                        cache_file.unlink()
                except Exception as e:
                    self.logger.warning(f"Error leyendo caché persistente para '{key}': {e}")
        
        return default
    
    def set(self, key: str, value: Any, ttl_seconds: float = 300.0):
        """
        Almacena un valor en el caché
        
        Args:
            key: Clave del caché
            value: Valor a almacenar
            ttl_seconds: Tiempo de vida en segundos (default: 5 minutos)
        """
        entry = CacheEntry(value, ttl_seconds)
        
        # Almacenar en memoria
        self._memory_cache[key] = entry
        self._access_times[key] = datetime.now()
        
        # Limpiar si excede el tamaño máximo (LRU)
        if len(self._memory_cache) > self.max_memory_size:
            self._evict_lru()
        
        # Almacenar en disco si está configurado
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.cache"
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(entry, f)
            except Exception as e:
                self.logger.warning(f"Error escribiendo caché persistente para '{key}': {e}")
    
    def _evict_lru(self):
        """Elimina la entrada menos usada recientemente (LRU)"""
        if not self._access_times:
            return
        
        # Encontrar la entrada menos usada
        lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
        
        del self._memory_cache[lru_key]
        del self._access_times[lru_key]
        
        self.logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    def delete(self, key: str):
        """Elimina una entrada del caché"""
        if key in self._memory_cache:
            del self._memory_cache[key]
        if key in self._access_times:
            del self._access_times[key]
        
        if self.cache_dir:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                cache_file.unlink()
    
    def clear(self):
        """Limpia todo el caché"""
        self._memory_cache.clear()
        self._access_times.clear()
        
        if self.cache_dir:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass
    
    def cleanup_expired(self):
        """Limpia entradas expiradas"""
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            self.delete(key)
        
        # Limpiar archivos expirados en disco
        if self.cache_dir:
            for cache_file in self.cache_dir.glob("*.cache"):
                try:
                    with open(cache_file, 'rb') as f:
                        entry = pickle.load(f)
                    if entry.is_expired():
                        cache_file.unlink()
                except Exception:
                    pass
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del caché"""
        self.cleanup_expired()
        
        return {
            "memory_entries": len(self._memory_cache),
            "max_memory_size": self.max_memory_size,
            "persistent_entries": len(list(self.cache_dir.glob("*.cache"))) if self.cache_dir else 0,
            "total_size": len(self._memory_cache)
        }


def cached(ttl_seconds: float = 300.0, cache_key_prefix: str = ""):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        ttl_seconds: Tiempo de vida del caché en segundos
        cache_key_prefix: Prefijo para las claves de caché
    
    Example:
        @cached(ttl_seconds=60)
        def expensive_function(x, y):
            # código costoso
            return result
    """
    cache = EnhancedCache()
    
    def decorator(func: Callable) -> Callable:
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generar clave única
            key = cache._make_key(*args, **kwargs)
            if cache_key_prefix:
                key = f"{cache_key_prefix}:{key}"
            
            # Intentar obtener del caché
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            
            return result
        
        wrapper.cache = cache  # Exponer caché para control manual
        return wrapper
    
    return decorator


# Instancias globales para diferentes tipos de caché
_prediction_cache = None
_quote_cache = None
_analysis_cache = None


def get_prediction_cache() -> EnhancedCache:
    """Caché para predicciones (TTL: 5 minutos)"""
    global _prediction_cache
    if _prediction_cache is None:
        _prediction_cache = EnhancedCache(cache_dir=Path(".cache/predictions"), max_memory_size=500)
    return _prediction_cache


def get_quote_cache() -> EnhancedCache:
    """Caché para cotizaciones (TTL: 30 segundos)"""
    global _quote_cache
    if _quote_cache is None:
        _quote_cache = EnhancedCache(cache_dir=Path(".cache/quotes"), max_memory_size=1000)
    return _quote_cache


def get_analysis_cache() -> EnhancedCache:
    """Caché para análisis técnico (TTL: 1 minuto)"""
    global _analysis_cache
    if _analysis_cache is None:
        _analysis_cache = EnhancedCache(cache_dir=Path(".cache/analysis"), max_memory_size=500)
    return _analysis_cache


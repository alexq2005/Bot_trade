"""
Sistema de caché inteligente con TTL y invalidación
"""
import time
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from threading import Lock

logger = logging.getLogger(__name__)


class CacheManager:
    """Sistema de caché con TTL y invalidación por patrón"""
    
    def __init__(self, default_ttl: int = 300, max_size: int = 1000):
        """
        Inicializa el cache manager
        
        Args:
            default_ttl: TTL por defecto en segundos (5 minutos)
            max_size: Tamaño máximo del caché (número de entradas)
        """
        self.cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.lock = Lock()
        self._access_times = {}  # Para LRU eviction
    
    def _generate_key(self, *args, **kwargs) -> str:
        """
        Genera una clave única basada en argumentos
        
        Args:
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Clave hash generada
        """
        # Crear representación estable de los argumentos
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del caché si es válido
        
        Args:
            key: Clave del caché
            
        Returns:
            Valor almacenado o None si expiró/no existe
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            value, expiry = self.cache[key]
            
            # Verificar si expiró
            if datetime.now() >= expiry:
                del self.cache[key]
                if key in self._access_times:
                    del self._access_times[key]
                return None
            
            # Actualizar tiempo de acceso (para LRU)
            self._access_times[key] = time.time()
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Guarda un valor en el caché con TTL
        
        Args:
            key: Clave del caché
            value: Valor a almacenar
            ttl: TTL en segundos (usa default si es None)
            
        Returns:
            True si se guardó exitosamente, False si el caché está lleno
        """
        with self.lock:
            # Verificar tamaño máximo
            if len(self.cache) >= self.max_size and key not in self.cache:
                # Evict LRU entry
                if self._access_times:
                    lru_key = min(self._access_times.items(), key=lambda x: x[1])[0]
                    del self.cache[lru_key]
                    del self._access_times[lru_key]
                else:
                    # Si no hay access times, eliminar el más antiguo
                    oldest_key = next(iter(self.cache))
                    del self.cache[oldest_key]
            
            ttl = ttl or self.default_ttl
            expiry = datetime.now() + timedelta(seconds=ttl)
            self.cache[key] = (value, expiry)
            self._access_times[key] = time.time()
            return True
    
    def invalidate(self, pattern: str):
        """
        Invalida claves que coincidan con un patrón
        
        Args:
            pattern: Patrón a buscar en las claves
        """
        with self.lock:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self.cache[key]
                if key in self._access_times:
                    del self._access_times[key]
            
            if keys_to_delete:
                logger.debug(f"Invalidadas {len(keys_to_delete)} entradas del caché con patrón '{pattern}'")
    
    def clear(self):
        """Limpia todo el caché"""
        with self.lock:
            self.cache.clear()
            self._access_times.clear()
            logger.debug("Caché limpiado completamente")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del caché
        
        Returns:
            Diccionario con estadísticas
        """
        with self.lock:
            now = datetime.now()
            expired_count = sum(
                1 for _, expiry in self.cache.values()
                if now >= expiry
            )
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'expired_entries': expired_count,
                'valid_entries': len(self.cache) - expired_count,
                'default_ttl': self.default_ttl
            }
    
    def cleanup_expired(self):
        """Limpia entradas expiradas del caché"""
        with self.lock:
            now = datetime.now()
            keys_to_delete = [
                key for key, (_, expiry) in self.cache.items()
                if now >= expiry
            ]
            
            for key in keys_to_delete:
                del self.cache[key]
                if key in self._access_times:
                    del self._access_times[key]
            
            if keys_to_delete:
                logger.debug(f"Limpiadas {len(keys_to_delete)} entradas expiradas del caché")


# Instancia global del caché
_cache_instance: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """
    Obtiene la instancia global del caché
    
    Returns:
        Instancia de CacheManager
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheManager(default_ttl=300, max_size=1000)
    return _cache_instance


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorador para cachear resultados de funciones
    
    Args:
        ttl: TTL en segundos
        key_prefix: Prefijo para la clave del caché
    """
    def decorator(func):
        cache = get_cache()
        
        def wrapper(*args, **kwargs):
            # Generar clave única
            cache_key = f"{key_prefix}:{func.__name__}:{cache._generate_key(*args, **kwargs)}"
            
            # Intentar obtener del caché
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT para {func.__name__}")
                return cached_value
            
            # Ejecutar función y cachear resultado
            logger.debug(f"Cache MISS para {func.__name__}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator


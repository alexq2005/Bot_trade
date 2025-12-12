"""
Logger seguro que maneja errores de I/O sin interrumpir el programa
"""
import logging
import sys
import io
from typing import Optional, Any


def safe_log(logger: logging.Logger, level: str, message: str, *args, **kwargs):
    """
    Función helper para logging seguro que no falla si hay errores de I/O
    
    Args:
        logger: Logger instance
        level: Nivel de log ('info', 'error', 'warning', 'debug')
        message: Mensaje a loguear
        *args, **kwargs: Argumentos adicionales para el logger
    """
    try:
        log_method = getattr(logger, level.lower(), None)
        if log_method:
            log_method(message, *args, **kwargs)
    except (ValueError, IOError, OSError, AttributeError):
        # Ignorar errores de logging (archivos cerrados, etc.)
        # No interrumpir el programa por problemas de logging
        pass
    except Exception:
        # Ignorar cualquier otro error de logging
        pass


def safe_info(logger: logging.Logger, message: str, *args, **kwargs):
    """Log seguro a nivel INFO"""
    safe_log(logger, 'info', message, *args, **kwargs)


def safe_error(logger: logging.Logger, message: str, *args, **kwargs):
    """Log seguro a nivel ERROR"""
    safe_log(logger, 'error', message, *args, **kwargs)


def safe_warning(logger: logging.Logger, message: str, *args, **kwargs):
    """Log seguro a nivel WARNING"""
    safe_log(logger, 'warning', message, *args, **kwargs)


def safe_debug(logger: logging.Logger, message: str, *args, **kwargs):
    """Log seguro a nivel DEBUG"""
    safe_log(logger, 'debug', message, *args, **kwargs)


class SafeStreamHandler(logging.StreamHandler):
    """
    StreamHandler seguro que no falla si el stream está cerrado
    """
    
    def emit(self, record):
        """Emitir un registro de forma segura"""
        try:
            # Verificar si el stream está cerrado
            if hasattr(self.stream, 'closed') and self.stream.closed:
                return
            
            # Intentar emitir normalmente
            super().emit(record)
        except (ValueError, IOError, OSError, AttributeError):
            # Si el stream está cerrado o hay error de I/O, ignorar
            pass
        except Exception:
            # Ignorar cualquier otro error
            pass
    
    def flush(self):
        """Flush seguro"""
        try:
            if hasattr(self.stream, 'closed') and not self.stream.closed:
                super().flush()
        except (ValueError, IOError, OSError, AttributeError):
            pass
        except Exception:
            pass


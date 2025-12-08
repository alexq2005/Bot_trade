"""
Sistema de Logging Centralizado
Proporciona logging estructurado y configurable para todo el proyecto
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.core.console_utils import setup_windows_console

setup_windows_console()


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para la consola"""
    
    # Códigos de color ANSI
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',        # Green
        'WARNING': '\033[33m',     # Yellow
        'ERROR': '\033[31m',       # Red
        'CRITICAL': '\033[35m',    # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record):
        # Agregar color según el nivel
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{self.BOLD}{record.levelname}{self.RESET}"
        return super().format(record)


class ProjectLogger:
    """Logger centralizado para el proyecto"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        try:
            self.log_dir = Path("logs")
            self.log_dir.mkdir(exist_ok=True)
        except (ValueError, IOError, OSError, Exception):
            # Si no se puede crear el directorio, continuar sin logging a archivo
            self.log_dir = None
        
        # Configurar logger principal
        self.logger = logging.getLogger("trading_bot")
        self.logger.setLevel(logging.DEBUG)
        
        # Evitar duplicación de handlers
        if self.logger.handlers:
            return
        
        # Handler para consola (con colores) - con manejo de errores
        try:
            from src.core.safe_logger import SafeStreamHandler
            # Verificar que stdout no esté cerrado antes de crear handler
            if hasattr(sys.stdout, 'closed') and sys.stdout.closed:
                # Si stdout está cerrado, no crear handler de consola
                pass
            else:
                console_handler = SafeStreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)
                console_formatter = ColoredFormatter(
                    '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                console_handler.setFormatter(console_formatter)
                # Agregar filtro para manejar errores de I/O
                console_handler.addFilter(self._safe_filter)
                self.logger.addHandler(console_handler)
        except Exception:
            # Si falla, crear un handler básico que no falle
            try:
                if hasattr(sys.stdout, 'closed') and not sys.stdout.closed:
                    console_handler = SafeStreamHandler()
                    console_handler.setLevel(logging.INFO)
                    self.logger.addHandler(console_handler)
            except Exception:
                pass  # Continuar sin handler de consola si falla
        
        # Handler para archivo (detallado) - con manejo de errores
        try:
            if self.log_dir is None:
                raise IOError("Log directory not available")
            log_file = self.log_dir / f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(self._safe_filter)
            self.logger.addHandler(file_handler)
        except (ValueError, IOError, OSError, AttributeError, Exception) as e:
            # Ignorar cualquier error de I/O al crear handlers de archivo
            pass
        
        # Handler para errores (archivo separado) - con manejo de errores
        try:
            if self.log_dir is None:
                raise IOError("Log directory not available")
            error_file = self.log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
            error_handler = logging.FileHandler(error_file, encoding='utf-8')
            error_handler.setLevel(logging.ERROR)
            if 'file_formatter' in locals():
                error_handler.setFormatter(file_formatter)
            error_handler.addFilter(self._safe_filter)
            self.logger.addHandler(error_handler)
        except (ValueError, IOError, OSError, AttributeError, Exception) as e:
            # Ignorar cualquier error de I/O al crear handlers de archivo
            pass
        
        self._initialized = True
    
    @staticmethod
    def _safe_filter(record):
        """Filtro para manejar errores de logging de forma segura"""
        try:
            return True
        except Exception:
            return False
    
    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """Obtiene un logger con el nombre especificado"""
        if name:
            return logging.getLogger(f"trading_bot.{name}")
        return self.logger
    
    def set_level(self, level: str):
        """Establece el nivel de logging"""
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(level.upper(), logging.INFO))
        for handler in self.logger.handlers:
            handler.setLevel(level_map.get(level.upper(), logging.INFO))


# Instancia global
_logger_instance = ProjectLogger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Función helper para obtener un logger"""
    return _logger_instance.get_logger(name)


def setup_logging(level: str = "INFO"):
    """Configura el sistema de logging"""
    _logger_instance.set_level(level)
    return _logger_instance.get_logger()


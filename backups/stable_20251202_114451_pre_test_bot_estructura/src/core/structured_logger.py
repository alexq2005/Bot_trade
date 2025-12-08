"""
Sistema de Logging Estructurado en JSON
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

from src.core.logger import get_logger

logger = get_logger("structured_logger")


class LogLevel(Enum):
    """Niveles de log"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredLogger:
    """
    Logger estructurado que escribe en formato JSON
    """
    
    def __init__(
        self,
        name: str,
        log_dir: Optional[Path] = None,
        console_output: bool = True,
        json_output: bool = True
    ):
        """
        Args:
            name: Nombre del logger
            log_dir: Directorio para archivos de log
            console_output: Si mostrar logs en consola
            json_output: Si escribir logs en formato JSON
        """
        self.name = name
        self.log_dir = log_dir or Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        self.console_output = console_output
        self.json_output = json_output
        
        # Configurar logger estándar
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Handler para JSON
        if json_output:
            json_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.jsonl"
            self.json_handler = logging.FileHandler(json_file, encoding='utf-8')
            self.json_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(self.json_handler)
        
        # Handler para consola (formato legible)
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Crea una entrada de log estructurada"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "logger": self.name,
            "message": message,
        }
        
        # Agregar campos adicionales
        if kwargs:
            entry.update(kwargs)
        
        return entry
    
    def _write_json_log(self, entry: Dict[str, Any]):
        """Escribe un log en formato JSON"""
        if self.json_output:
            json_str = json.dumps(entry, ensure_ascii=False, default=str)
            # Escribir directamente al handler de archivo
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler) and handler.baseFilename.endswith('.jsonl'):
                    handler.stream.write(json_str + '\n')
                    handler.stream.flush()
    
    def debug(self, message: str, **kwargs):
        """Log a nivel DEBUG"""
        entry = self._create_log_entry("DEBUG", message, **kwargs)
        self._write_json_log(entry)
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log a nivel INFO"""
        entry = self._create_log_entry("INFO", message, **kwargs)
        self._write_json_log(entry)
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a nivel WARNING"""
        entry = self._create_log_entry("WARNING", message, **kwargs)
        self._write_json_log(entry)
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log a nivel ERROR"""
        entry = self._create_log_entry("ERROR", message, **kwargs)
        
        if error:
            entry["error_type"] = type(error).__name__
            entry["error_message"] = str(error)
            import traceback
            entry["traceback"] = traceback.format_exc()
        
        self._write_json_log(entry)
        self.logger.error(message, exc_info=error, extra=kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log a nivel CRITICAL"""
        entry = self._create_log_entry("CRITICAL", message, **kwargs)
        
        if error:
            entry["error_type"] = type(error).__name__
            entry["error_message"] = str(error)
            import traceback
            entry["traceback"] = traceback.format_exc()
        
        self._write_json_log(entry)
        self.logger.critical(message, exc_info=error, extra=kwargs)
    
    def log_trade(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        order_id: Optional[str] = None,
        **kwargs
    ):
        """Log específico para operaciones de trading"""
        entry = self._create_log_entry(
            "INFO",
            f"Trade executed: {action} {quantity} {symbol} @ ${price:.2f}",
            event_type="trade_execution",
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            order_id=order_id,
            **kwargs
        )
        self._write_json_log(entry)
        self.logger.info(entry["message"], extra=kwargs)
    
    def log_prediction(
        self,
        symbol: str,
        signal: str,
        predicted_price: float,
        current_price: float,
        confidence: float,
        **kwargs
    ):
        """Log específico para predicciones"""
        entry = self._create_log_entry(
            "INFO",
            f"Prediction: {symbol} -> {signal} (confidence: {confidence:.2%})",
            event_type="prediction",
            symbol=symbol,
            signal=signal,
            predicted_price=predicted_price,
            current_price=current_price,
            confidence=confidence,
            **kwargs
        )
        self._write_json_log(entry)
        self.logger.info(entry["message"], extra=kwargs)
    
    def log_analysis(
        self,
        symbol: str,
        score: float,
        factors: Dict[str, Any],
        **kwargs
    ):
        """Log específico para análisis"""
        entry = self._create_log_entry(
            "INFO",
            f"Analysis: {symbol} score={score:.2f}",
            event_type="analysis",
            symbol=symbol,
            score=score,
            factors=factors,
            **kwargs
        )
        self._write_json_log(entry)
        self.logger.info(entry["message"], extra=kwargs)


# Instancias globales por módulo
_loggers: Dict[str, StructuredLogger] = {}


def get_structured_logger(name: str, **kwargs) -> StructuredLogger:
    """
    Obtiene o crea un logger estructurado
    
    Args:
        name: Nombre del logger
        **kwargs: Argumentos adicionales para StructuredLogger
    
    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, **kwargs)
    return _loggers[name]


# Función de conveniencia para migración gradual
def use_structured_logging(enable: bool = True):
    """
    Habilita o deshabilita el logging estructurado globalmente
    
    Args:
        enable: Si habilitar logging estructurado
    """
    global _structured_logging_enabled
    _structured_logging_enabled = enable


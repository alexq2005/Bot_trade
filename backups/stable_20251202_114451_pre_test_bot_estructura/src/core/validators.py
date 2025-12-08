"""
Validación de entrada con Pydantic para prevenir errores
"""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
import re

try:
    from pydantic import BaseModel, validator, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback básico sin Pydantic
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


class TradeRequest(BaseModel if PYDANTIC_AVAILABLE else object):
    """Modelo validado para requests de trading"""
    
    symbol: str
    action: str  # BUY/SELL
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    
    if PYDANTIC_AVAILABLE:
        @validator('symbol')
        def validate_symbol(cls, v):
            """Validar formato de símbolo"""
            if not v or len(v) > 20:
                raise ValueError('Símbolo inválido: debe tener entre 1 y 20 caracteres')
            
            # Limpiar y normalizar
            v = v.strip().upper()
            
            # Validar caracteres permitidos (letras, números, punto, guión)
            if not re.match(r'^[A-Z0-9\.\-]+$', v):
                raise ValueError(f'Símbolo contiene caracteres inválidos: {v}')
            
            return v
        
        @validator('action')
        def validate_action(cls, v):
            """Validar acción de trading"""
            v = v.upper().strip()
            if v not in ['BUY', 'SELL']:
                raise ValueError(f'Acción debe ser BUY o SELL, recibido: {v}')
            return v
        
        @validator('quantity')
        def validate_quantity(cls, v):
            """Validar cantidad"""
            if isinstance(v, (int, float)):
                v = Decimal(str(v))
            
            if v <= 0:
                raise ValueError(f'Cantidad debe ser positiva, recibido: {v}')
            
            if v > Decimal('1000000'):
                raise ValueError(f'Cantidad excesiva: {v} (máximo 1,000,000)')
            
            return v
        
        @validator('price')
        def validate_price(cls, v):
            """Validar precio"""
            if v is None:
                return v
            
            if isinstance(v, (int, float)):
                v = Decimal(str(v))
            
            if v <= 0:
                raise ValueError(f'Precio debe ser positivo, recibido: {v}')
            
            if v > Decimal('1000000'):
                raise ValueError(f'Precio excesivo: {v} (máximo 1,000,000)')
            
            return v
        
        @validator('stop_loss')
        def validate_stop_loss(cls, v, values):
            """Validar stop loss"""
            if v is None:
                return v
            
            if isinstance(v, (int, float)):
                v = Decimal(str(v))
            
            price = values.get('price')
            if price and v >= price:
                raise ValueError(f'Stop loss ({v}) debe ser menor que precio ({price})')
            
            return v
        
        @validator('take_profit')
        def validate_take_profit(cls, v, values):
            """Validar take profit"""
            if v is None:
                return v
            
            if isinstance(v, (int, float)):
                v = Decimal(str(v))
            
            price = values.get('price')
            if price and v <= price:
                raise ValueError(f'Take profit ({v}) debe ser mayor que precio ({price})')
            
            return v
        
        class Config:
            """Configuración de Pydantic"""
            arbitrary_types_allowed = True
            json_encoders = {
                Decimal: str
            }
    else:
        # Validación manual sin Pydantic
        def __init__(self, **kwargs):
            self.symbol = self._validate_symbol(kwargs.get('symbol', ''))
            self.action = self._validate_action(kwargs.get('action', ''))
            self.quantity = self._validate_quantity(kwargs.get('quantity'))
            self.price = kwargs.get('price')
            self.stop_loss = kwargs.get('stop_loss')
            self.take_profit = kwargs.get('take_profit')
        
        def _validate_symbol(self, v):
            if not v or len(v) > 20:
                raise ValueError('Símbolo inválido')
            return v.strip().upper()
        
        def _validate_action(self, v):
            v = v.upper().strip()
            if v not in ['BUY', 'SELL']:
                raise ValueError('Acción debe ser BUY o SELL')
            return v
        
        def _validate_quantity(self, v):
            if isinstance(v, (int, float)):
                v = Decimal(str(v))
            if v <= 0:
                raise ValueError('Cantidad debe ser positiva')
            return v


class SymbolValidator:
    """Validador de símbolos de trading"""
    
    # Patrones comunes de símbolos
    SYMBOL_PATTERNS = {
        'argentina': re.compile(r'^[A-Z]{1,6}\.BA$'),  # GGAL.BA
        'usa': re.compile(r'^[A-Z]{1,5}$'),  # AAPL
        'crypto': re.compile(r'^[A-Z]{2,10}(-USD|-ARS)?$'),  # BTC-USD
    }
    
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        """
        Valida si un símbolo tiene formato válido
        
        Args:
            symbol: Símbolo a validar
            
        Returns:
            True si es válido, False en caso contrario
        """
        if not symbol or len(symbol) > 20:
            return False
        
        symbol = symbol.strip().upper()
        
        # Verificar contra patrones conocidos
        for pattern in SymbolValidator.SYMBOL_PATTERNS.values():
            if pattern.match(symbol):
                return True
        
        # Permitir caracteres alfanuméricos, punto y guión
        if re.match(r'^[A-Z0-9\.\-]+$', symbol):
            return True
        
        return False
    
    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        Normaliza un símbolo (mayúsculas, sin espacios)
        
        Args:
            symbol: Símbolo a normalizar
            
        Returns:
            Símbolo normalizado
        """
        if not symbol:
            raise ValueError("Símbolo no puede estar vacío")
        
        return symbol.strip().upper()


class ConfigValidator:
    """Validador de configuración"""
    
    @staticmethod
    def validate_risk_per_trade(value: float) -> float:
        """Valida riesgo por operación (0.1% - 10%)"""
        if not isinstance(value, (int, float)):
            raise ValueError("Riesgo por operación debe ser numérico")
        
        value = float(value)
        
        if value < 0.1 or value > 10.0:
            raise ValueError(f"Riesgo por operación debe estar entre 0.1% y 10%, recibido: {value}%")
        
        return value
    
    @staticmethod
    def validate_threshold(value: float) -> float:
        """Valida umbral de trading (-100 a 100)"""
        if not isinstance(value, (int, float)):
            raise ValueError("Umbral debe ser numérico")
        
        value = float(value)
        
        if value < -100 or value > 100:
            raise ValueError(f"Umbral debe estar entre -100 y 100, recibido: {value}")
        
        return value
    
    @staticmethod
    def validate_interval(value: int) -> int:
        """Valida intervalo de análisis (1 - 1440 minutos)"""
        if not isinstance(value, int):
            raise ValueError("Intervalo debe ser un entero")
        
        if value < 1 or value > 1440:
            raise ValueError(f"Intervalo debe estar entre 1 y 1440 minutos, recibido: {value}")
        
        return value


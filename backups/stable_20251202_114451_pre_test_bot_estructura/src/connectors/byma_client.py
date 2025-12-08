"""
BYMA (Bolsas y Mercados Argentinos) Client
Obtiene datos históricos de acciones argentinas desde múltiples fuentes.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

from src.connectors.yahoo_client import YahooFinanceClient
from src.core.logger import get_logger

logger = get_logger("byma_client")


class BYMAClient:
    """
    Cliente para obtener datos históricos de BYMA (Bolsas y Mercados Argentinos).
    
    Utiliza múltiples fuentes en orden de prioridad:
    1. Yahoo Finance (gratis, datos históricos completos)
    2. IOL API (si está disponible, datos actuales)
    3. Web scraping de BYMA (último recurso, limitado)
    """
    
    def __init__(self):
        self.yahoo_client = YahooFinanceClient()
        self.base_url = "https://www.byma.com.ar"
    
    def get_symbol_with_suffix(self, symbol: str) -> str:
        """
        Agrega el sufijo .BA si no lo tiene (para Yahoo Finance).
        
        Args:
            symbol: Símbolo sin sufijo (ej: 'GGAL')
        
        Returns:
            Símbolo con sufijo (ej: 'GGAL.BA')
        """
        if not symbol.endswith('.BA') and not symbol.endswith('.AR'):
            return f"{symbol}.BA"
        return symbol
    
    def get_history_from_yahoo(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """
        Obtiene datos históricos desde Yahoo Finance (método principal).
        
        Args:
            symbol: Símbolo (con o sin .BA)
            period: Período ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Intervalo ('1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1wk', '1mo', '3mo')
        
        Returns:
            DataFrame con datos históricos
        """
        try:
            # Asegurar sufijo .BA
            symbol_with_suffix = self.get_symbol_with_suffix(symbol)
            
            logger.info(f"Obteniendo datos históricos de Yahoo Finance para {symbol_with_suffix}")
            history = self.yahoo_client.get_history(symbol_with_suffix, period=period, interval=interval)
            
            if not history.empty:
                logger.info(f"✅ Obtenidos {len(history)} registros desde Yahoo Finance para {symbol}")
                return history
            else:
                logger.warning(f"⚠️ No se encontraron datos en Yahoo Finance para {symbol_with_suffix}")
                return pd.DataFrame()
        
        except (ValueError, IOError) as e:
            # Manejar específicamente errores de I/O cerrado
            if "closed file" in str(e).lower() or "I/O operation" in str(e):
                logger.warning(f"Error de I/O con Yahoo Finance para {symbol} (archivo cerrado) - reintentando...")
                # Reintentar una vez más
                try:
                    history = self.yahoo_client.get_history(symbol_with_suffix, period=period, interval=interval)
                    if not history.empty:
                        logger.info(f"✅ Obtenidos {len(history)} registros desde Yahoo Finance para {symbol} (reintento)")
                        return history
                except:
                    pass
            logger.error(f"Error obteniendo datos desde Yahoo Finance para {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error obteniendo datos desde Yahoo Finance para {symbol}: {e}")
            return pd.DataFrame()
    
    def get_history_from_iol(self, symbol: str, iol_client, days: int = 365) -> pd.DataFrame:
        """
        Intenta obtener datos históricos desde IOL API.
        
        Nota: IOL API generalmente solo proporciona datos actuales, no históricos completos.
        Este método intenta obtener datos recientes y acumularlos.
        
        Args:
            symbol: Símbolo sin sufijo
            iol_client: Instancia de IOLClient
            days: Días de datos a intentar obtener
        
        Returns:
            DataFrame con datos (puede estar vacío si IOL no tiene históricos)
        """
        try:
            # IOL generalmente no tiene endpoint de históricos, pero intentamos
            # obtener cotizaciones actuales y recientes
            logger.info(f"Intentando obtener datos desde IOL para {symbol}...")
            
            # Limpiar símbolo para IOL
            clean_symbol = symbol.replace(".BA", "")
            
            # Obtener cotización actual
            quote = iol_client.get_quote(clean_symbol)
            
            if 'error' in quote:
                logger.warning(f"IOL no tiene datos para {symbol}: {quote.get('error')}")
                return pd.DataFrame()
            
            # Convertir cotización actual a DataFrame (solo un punto de datos)
            price = quote.get('ultimoPrecio') or quote.get('precio') or quote.get('price')
            if price:
                data = {
                    'Open': [quote.get('apertura', price) or quote.get('open', price)],
                    'High': [quote.get('maximo', price) or quote.get('high', price)],
                    'Low': [quote.get('minimo', price) or quote.get('low', price)],
                    'Close': [price],
                    'Volume': [quote.get('volumen', 0) or quote.get('volume', 0)]
                }
                df = pd.DataFrame(data, index=[datetime.now()])
                logger.info(f"✅ Obtenida cotización actual desde IOL para {symbol}")
                return df
            else:
                return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"Error obteniendo datos desde IOL para {symbol}: {e}")
            return pd.DataFrame()
    
    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d", 
                   iol_client: Optional[Any] = None) -> pd.DataFrame:
        """
        Obtiene datos históricos usando el mejor método disponible.
        
        Args:
            symbol: Símbolo (con o sin .BA)
            period: Período para Yahoo Finance
            interval: Intervalo para Yahoo Finance
            iol_client: Cliente IOL opcional (para intentar como fallback)
        
        Returns:
            DataFrame con datos históricos
        """
        # Método 1: Yahoo Finance (siempre intentar primero)
        history = self.get_history_from_yahoo(symbol, period, interval)
        
        if not history.empty:
            return history
        
        # Método 2: IOL API (si está disponible y Yahoo falló)
        if iol_client:
            logger.info(f"Yahoo Finance falló, intentando IOL para {symbol}...")
            history = self.get_history_from_iol(symbol, iol_client)
            if not history.empty:
                return history
        
        # Método 3: Web scraping de BYMA (último recurso)
        logger.warning(f"⚠️ No se pudieron obtener datos históricos para {symbol} desde fuentes principales")
        logger.info(f"💡 Recomendación: Usa Yahoo Finance directamente o importa datos desde CSV")
        
        return pd.DataFrame()
    
    def get_available_symbols(self) -> List[str]:
        """
        Obtiene lista de símbolos disponibles en BYMA.
        
        Nota: BYMA no tiene API pública gratuita para listar símbolos.
        Retorna una lista predefinida de símbolos comunes.
        
        Returns:
            Lista de símbolos comunes de BYMA
        """
        # Lista de símbolos comunes de BYMA
        common_symbols = [
            # Acciones líderes
            "GGAL", "YPFD", "PAMP", "TRAN", "METR", "EDN", "CEPU", "LOMA",
            "TGNO4", "TGSU2", "ECOG", "COME", "BYMA",
            # Bonos
            "BA37D", "BPOC7", "GD35", "T15D5", "TTM26", "TX26",
            # Otros
            "MIRG", "SUPV", "BBAR", "BMA", "CRESY", "GGAL", "IRS", "PAM"
        ]
        
        return common_symbols
    
    def validate_symbol(self, symbol: str) -> bool:
        """
        Valida si un símbolo existe en BYMA.
        
        Args:
            symbol: Símbolo a validar
        
        Returns:
            True si el símbolo es válido
        """
        # Intentar obtener datos desde Yahoo Finance
        symbol_with_suffix = self.get_symbol_with_suffix(symbol)
        history = self.get_history_from_yahoo(symbol_with_suffix, period="5d")
        
        return not history.empty


if __name__ == "__main__":
    # Test del cliente
    client = BYMAClient()
    
    # Test con símbolo argentino
    print("Probando GGAL...")
    history = client.get_history("GGAL", period="1mo")
    print(f"Registros obtenidos: {len(history)}")
    if not history.empty:
        print(history.head())
        print(history.tail())


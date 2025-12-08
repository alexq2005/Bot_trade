"""
Multi-Source Data Client
Sistema modular para obtener datos históricos desde múltiples fuentes.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import requests
import time

from src.connectors.yahoo_client import YahooFinanceClient
from src.connectors.byma_client import BYMAClient
from src.core.logger import get_logger

logger = get_logger("multi_source_client")


class AlphaVantageClient:
    """
    Cliente para Alpha Vantage API.
    Tier gratuito: 5 calls/min, 500 calls/día
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Obtiene datos históricos desde Alpha Vantage"""
        if not self.api_key:
            logger.warning("Alpha Vantage API key no configurada")
            return pd.DataFrame()
        
        try:
            # Mapear período a función de Alpha Vantage
            function = "TIME_SERIES_DAILY"  # Daily data
            
            params = {
                'function': function,
                'symbol': symbol.replace('.BA', ''),  # Alpha Vantage no usa sufijos
                'apikey': self.api_key,
                'outputsize': 'full' if period in ['1y', '2y', '5y'] else 'compact'
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Error Message' in data or 'Note' in data:
                logger.warning(f"Alpha Vantage error: {data.get('Error Message', data.get('Note', 'Unknown error'))}")
                return pd.DataFrame()
            
            # Parsear datos
            time_series = data.get('Time Series (Daily)', {})
            if not time_series:
                return pd.DataFrame()
            
            records = []
            for date_str, values in time_series.items():
                records.append({
                    'Date': pd.to_datetime(date_str),
                    'Open': float(values['1. open']),
                    'High': float(values['2. high']),
                    'Low': float(values['3. low']),
                    'Close': float(values['4. close']),
                    'Volume': float(values['5. volume'])
                })
            
            df = pd.DataFrame(records)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"✅ Obtenidos {len(df)} registros desde Alpha Vantage para {symbol}")
            return df
        
        except Exception as e:
            logger.error(f"Error obteniendo datos desde Alpha Vantage para {symbol}: {e}")
            return pd.DataFrame()


class FinnhubClient:
    """
    Cliente para Finnhub API.
    Tier gratuito: 60 calls/min
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
    
    def get_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Obtiene datos históricos desde Finnhub"""
        if not self.api_key:
            logger.warning("Finnhub API key no configurada")
            return pd.DataFrame()
        
        try:
            # Calcular timestamps
            end_date = int(datetime.now().timestamp())
            days_map = {'1y': 365, '6mo': 180, '3mo': 90, '1mo': 30, '5d': 5}
            days = days_map.get(period, 365)
            start_date = int((datetime.now() - timedelta(days=days)).timestamp())
            
            # Limpiar símbolo
            clean_symbol = symbol.replace('.BA', '')
            
            endpoint = f"{self.base_url}/stock/candle"
            params = {
                'symbol': clean_symbol,
                'resolution': 'D',  # Daily
                'from': start_date,
                'to': end_date,
                'token': self.api_key
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('s') != 'ok':
                logger.warning(f"Finnhub error: {data.get('s', 'Unknown error')}")
                return pd.DataFrame()
            
            # Parsear datos
            if not data.get('c'):
                return pd.DataFrame()
            
            records = []
            for i in range(len(data['t'])):
                records.append({
                    'Date': pd.to_datetime(data['t'][i], unit='s'),
                    'Open': data['o'][i],
                    'High': data['h'][i],
                    'Low': data['l'][i],
                    'Close': data['c'][i],
                    'Volume': data['v'][i]
                })
            
            df = pd.DataFrame(records)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"✅ Obtenidos {len(df)} registros desde Finnhub para {symbol}")
            return df
        
        except requests.exceptions.HTTPError as e:
            # Manejar errores HTTP específicos
            if e.response.status_code == 403:
                logger.warning(f"⚠️  Finnhub API: 403 Forbidden para {symbol}. Posibles causas: API key inválida/expirada, límite excedido, o símbolo no disponible. El bot usará fuentes alternativas.")
            elif e.response.status_code == 429:
                logger.warning(f"⚠️  Finnhub API: Rate limit excedido para {symbol}. Esperando y usando fuentes alternativas.")
            else:
                logger.error(f"Error obteniendo datos desde Finnhub para {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error obteniendo datos desde Finnhub para {symbol}: {e}")
            return pd.DataFrame()


class TwelveDataClient:
    """
    Cliente para Twelve Data API.
    Tier gratuito: 800 calls/día, 2 calls/min
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('TWELVE_DATA_API_KEY')
        self.base_url = "https://api.twelvedata.com"
    
    def get_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Obtiene datos históricos desde Twelve Data"""
        if not self.api_key:
            logger.warning("Twelve Data API key no configurada")
            return pd.DataFrame()
        
        try:
            # Mapear período
            interval = "1day"
            outputsize_map = {'1y': 365, '6mo': 180, '3mo': 90, '1mo': 30, '5d': 5}
            outputsize = outputsize_map.get(period, 365)
            
            # Limpiar símbolo
            clean_symbol = symbol.replace('.BA', '')
            
            endpoint = f"{self.base_url}/time_series"
            params = {
                'symbol': clean_symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key,
                'format': 'json'
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'status' in data and data['status'] != 'ok':
                logger.warning(f"Twelve Data error: {data.get('message', 'Unknown error')}")
                return pd.DataFrame()
            
            # Parsear datos
            if 'values' not in data:
                return pd.DataFrame()
            
            records = []
            for value in data['values']:
                records.append({
                    'Date': pd.to_datetime(value['datetime']),
                    'Open': float(value['open']),
                    'High': float(value['high']),
                    'Low': float(value['low']),
                    'Close': float(value['close']),
                    'Volume': float(value.get('volume', 0))
                })
            
            df = pd.DataFrame(records)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"✅ Obtenidos {len(df)} registros desde Twelve Data para {symbol}")
            return df
        
        except Exception as e:
            logger.error(f"Error obteniendo datos desde Twelve Data para {symbol}: {e}")
            return pd.DataFrame()


class IEXCloudClient:
    """
    Cliente para IEX Cloud API.
    Tier gratuito: 50,000 messages/mes
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('IEX_CLOUD_API_KEY')
        self.base_url = "https://cloud.iexapis.com/stable"
    
    def get_history(self, symbol: str, period: str = "1y") -> pd.DataFrame:
        """Obtiene datos históricos desde IEX Cloud"""
        if not self.api_key:
            logger.warning("IEX Cloud API key no configurada")
            return pd.DataFrame()
        
        try:
            # Calcular rango de fechas
            days_map = {'1y': 365, '6mo': 180, '3mo': 90, '1mo': 30, '5d': 5}
            days = days_map.get(period, 365)
            date_str = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            # Limpiar símbolo
            clean_symbol = symbol.replace('.BA', '')
            
            endpoint = f"{self.base_url}/stock/{clean_symbol}/chart/{period}"
            params = {
                'token': self.api_key
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            # Parsear datos
            records = []
            for item in data:
                records.append({
                    'Date': pd.to_datetime(item['date']),
                    'Open': item.get('open', 0),
                    'High': item.get('high', 0),
                    'Low': item.get('low', 0),
                    'Close': item.get('close', 0),
                    'Volume': item.get('volume', 0)
                })
            
            df = pd.DataFrame(records)
            df.set_index('Date', inplace=True)
            df.sort_index(inplace=True)
            
            logger.info(f"✅ Obtenidos {len(df)} registros desde IEX Cloud para {symbol}")
            return df
        
        except Exception as e:
            logger.error(f"Error obteniendo datos desde IEX Cloud para {symbol}: {e}")
            return pd.DataFrame()


class MultiSourceDataClient:
    """
    Cliente unificado que intenta múltiples fuentes de datos.
    
    Orden de prioridad:
    1. IOL (para instrumentos argentinos: ONs, bonos, letras, acciones locales)
    2. Yahoo Finance (gratis, sin API key)
    3. BYMA/Yahoo (específico para Argentina)
    4. Alpha Vantage (requiere API key)
    5. Finnhub (requiere API key)
    6. Twelve Data (requiere API key)
    7. IEX Cloud (requiere API key)
    
    APIs públicas y gratuitas adicionales:
    - BCRA (Banco Central): Variables macroeconómicas y estadísticas cambiarias
    - MonedAPI: Cotizaciones de divisas
    - Argentina Gobierno: Series de tiempo oficiales
    """
    
    def __init__(self, iol_client=None):
        # IOL client para instrumentos argentinos (ONs, bonos, letras)
        try:
            if iol_client is None:
                from src.connectors.iol_client import IOLClient
                self.iol_client = IOLClient()
            else:
                self.iol_client = iol_client
        except Exception as e:
            logger.warning(f"No se pudo inicializar IOL client: {e}")
            self.iol_client = None
        
        self.yahoo_client = YahooFinanceClient()
        self.byma_client = BYMAClient()
        self.alpha_vantage = AlphaVantageClient() if os.getenv('ALPHA_VANTAGE_API_KEY') else None
        self.finnhub = FinnhubClient() if os.getenv('FINNHUB_API_KEY') else None
        self.twelve_data = TwelveDataClient() if os.getenv('TWELVE_DATA_API_KEY') else None
        self.iex_cloud = IEXCloudClient() if os.getenv('IEX_CLOUD_API_KEY') else None
        
        self.sources = []
        # IOL primero para instrumentos argentinos específicos
        if self.iol_client:
            self.sources.append(('IOL', self._get_from_iol))
        if self.yahoo_client:
            self.sources.append(('Yahoo Finance', self._get_from_yahoo))
        if self.byma_client:
            self.sources.append(('BYMA/Yahoo', self._get_from_byma))
        if self.alpha_vantage:
            self.sources.append(('Alpha Vantage', self._get_from_alpha_vantage))
        if self.finnhub:
            self.sources.append(('Finnhub', self._get_from_finnhub))
        if self.twelve_data:
            self.sources.append(('Twelve Data', self._get_from_twelve_data))
        if self.iex_cloud:
            self.sources.append(('IEX Cloud', self._get_from_iex_cloud))
    
    def _get_from_yahoo(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Wrapper para Yahoo Finance"""
        return self.yahoo_client.get_history(symbol, period, interval)
    
    def _get_from_byma(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Wrapper para BYMA"""
        return self.byma_client.get_history_from_yahoo(symbol, period, interval)
    
    def _get_from_alpha_vantage(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Wrapper para Alpha Vantage"""
        return self.alpha_vantage.get_history(symbol, period) if self.alpha_vantage else pd.DataFrame()
    
    def _get_from_finnhub(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Wrapper para Finnhub"""
        return self.finnhub.get_history(symbol, period) if self.finnhub else pd.DataFrame()
    
    def _get_from_twelve_data(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Wrapper para Twelve Data"""
        return self.twelve_data.get_history(symbol, period) if self.twelve_data else pd.DataFrame()
    
    def _get_from_iex_cloud(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """Wrapper para IEX Cloud"""
        return self.iex_cloud.get_history(symbol, period) if self.iex_cloud else pd.DataFrame()
    
    def _get_from_iol(self, symbol: str, period: str, interval: str) -> pd.DataFrame:
        """
        Obtiene datos desde IOL (prioritario para instrumentos argentinos: ONs, bonos, letras)
        
        Nota: IOL no tiene endpoint directo de histórico, pero podemos:
        1. Detectar si es un instrumento argentino específico (ONs, bonos, letras)
        2. Intentar obtener cotización actual
        3. Para instrumentos argentinos específicos, devolver datos básicos
        """
        if not self.iol_client:
            return pd.DataFrame()
        
        try:
            # Detectar si es un instrumento argentino específico
            # ONs suelen tener formato: PAMPY, PAMPO, TGNO6, etc.
            # Bonos: GD30, GD35, AL30, etc.
            # Letras: S30E5, S31M5, etc.
            
            # Limpiar símbolo
            clean_symbol = symbol.replace('.BA', '').upper()
            
            # Detectar tipo de instrumento
            is_on = any(x in clean_symbol for x in ['PAMP', 'TGNO', 'TGSU', 'TXAR', 'CRCC', 'IRCP', 'YPF'])
            is_bono = any(x in clean_symbol for x in ['GD', 'AL', 'AE', 'BA', 'BPOC', 'T15', 'TTM', 'TX'])
            is_letra = any(x in clean_symbol for x in ['S30', 'S31', 'X26', 'X18'])
            is_argentine = is_on or is_bono or is_letra or clean_symbol.endswith('.BA')
            
            # Si es un instrumento argentino específico, intentar obtener cotización
            if is_argentine:
                quote = self.iol_client.get_quote(clean_symbol)
                
                if 'error' not in quote and quote:
                    # Obtener precio actual
                    precio = None
                    if 'ultimoPrecio' in quote:
                        precio = quote['ultimoPrecio']
                    elif 'precio' in quote:
                        precio = quote['precio']
                    elif 'cotizacion' in quote and isinstance(quote['cotizacion'], dict):
                        precio = quote['cotizacion'].get('ultimoPrecio') or quote['cotizacion'].get('precio')
                    
                    if precio:
                        # Crear DataFrame básico con precio actual
                        # Para instrumentos argentinos sin histórico, usamos precio actual
                        today = datetime.now().date()
                        records = [{
                            'Date': pd.to_datetime(today),
                            'Open': float(precio),
                            'High': float(precio),
                            'Low': float(precio),
                            'Close': float(precio),
                            'Volume': quote.get('volumen', 0) if isinstance(quote.get('volumen'), (int, float)) else 0
                        }]
                        
                        df = pd.DataFrame(records)
                        df.set_index('Date', inplace=True)
                        
                        logger.info(f"✅ Obtenida cotización actual desde IOL para {symbol}: ${precio}")
                        return df
            
            # Para otros símbolos, intentar obtener cotización pero no forzar
            return pd.DataFrame()
            
        except Exception as e:
            logger.warning(f"Error obteniendo datos desde IOL para {symbol}: {e}")
            return pd.DataFrame()
    
    def get_history(self, symbol: str, period: str = "1y", interval: str = "1d") -> Dict[str, Any]:
        """
        Obtiene datos históricos intentando múltiples fuentes.
        
        Returns:
            Dict con 'data' (DataFrame), 'source' (nombre de la fuente), 'success' (bool)
        """
        for source_name, source_func in self.sources:
            try:
                logger.info(f"Intentando obtener datos desde {source_name} para {symbol}...")
                df = source_func(symbol, period, interval)
                
                if not df.empty and len(df) > 0:
                    return {
                        'data': df,
                        'source': source_name,
                        'success': True
                    }
            except (ValueError, IOError) as e:
                # Manejar específicamente errores de I/O cerrado
                if "closed file" in str(e).lower() or "I/O operation" in str(e):
                    logger.warning(f"Error de I/O con {source_name} para {symbol} (archivo cerrado) - continuando con siguiente fuente")
                else:
                    logger.warning(f"Error con {source_name} para {symbol}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Error con {source_name} para {symbol}: {e}")
                continue
        
        # Si todas las fuentes fallaron
        logger.error(f"❌ No se pudieron obtener datos para {symbol} desde ninguna fuente")
        return {
            'data': pd.DataFrame(),
            'source': None,
            'success': False
        }
    
    def get_available_sources(self) -> List[str]:
        """Retorna lista de fuentes disponibles"""
        return [name for name, _ in self.sources]
    
    def get_source_info(self) -> Dict[str, Dict]:
        """Retorna información sobre cada fuente"""
        info = {
            'Yahoo Finance': {
                'free': True,
                'api_key_required': False,
                'rate_limit': 'No oficial',
                'coverage': 'Global (incluye Argentina con .BA)'
            },
            'BYMA/Yahoo': {
                'free': True,
                'api_key_required': False,
                'rate_limit': 'No oficial',
                'coverage': 'Argentina (acciones BYMA)'
            },
            'Alpha Vantage': {
                'free': True,
                'api_key_required': True,
                'rate_limit': '5 calls/min, 500 calls/día',
                'coverage': 'Global (principalmente USA)',
                'signup': 'https://www.alphavantage.co/support/#api-key'
            },
            'Finnhub': {
                'free': True,
                'api_key_required': True,
                'rate_limit': '60 calls/min',
                'coverage': 'Global',
                'signup': 'https://finnhub.io/register'
            },
            'Twelve Data': {
                'free': True,
                'api_key_required': True,
                'rate_limit': '800 calls/día, 2 calls/min',
                'coverage': 'Global',
                'signup': 'https://twelvedata.com/pricing'
            },
            'IEX Cloud': {
                'free': True,
                'api_key_required': True,
                'rate_limit': '50,000 messages/mes',
                'coverage': 'USA principalmente',
                'signup': 'https://iexcloud.io/console/sign-up'
            }
        }
        
        return {k: v for k, v in info.items() if k in self.get_available_sources()}


if __name__ == "__main__":
    # Test del cliente multi-fuente
    client = MultiSourceDataClient()
    
    print("Fuentes disponibles:")
    for source in client.get_available_sources():
        print(f"  - {source}")
    
    print("\nInformación de fuentes:")
    info = client.get_source_info()
    for name, details in info.items():
        print(f"\n{name}:")
        for key, value in details.items():
            print(f"  {key}: {value}")
    
    print("\nProbando obtención de datos para AAPL...")
    result = client.get_history("AAPL", period="1mo")
    if result['success']:
        print(f"✅ Datos obtenidos desde {result['source']}")
        print(f"   Registros: {len(result['data'])}")
        print(result['data'].head())


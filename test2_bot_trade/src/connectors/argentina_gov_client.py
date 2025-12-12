"""
Argentina Gobierno - API de Series de Tiempo
API pública y gratuita con más de 30,000 series de tiempo de indicadores oficiales
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import requests

from src.core.logger import get_logger

logger = get_logger("argentina_gov_client")


class ArgentinaGovClient:
    """
    Cliente para API de Series de Tiempo del Gobierno Argentino.
    
    URL: https://www.argentina.gob.ar/datos-abiertos/api-series-de-tiempo
    Más de 30,000 series de tiempo de indicadores oficiales
    """
    
    def __init__(self):
        self.base_url = "https://apis.datos.gob.ar/series/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_series(self, ids: List[str], start_date: Optional[str] = None, 
                   end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene series de tiempo por IDs.
        
        Args:
            ids: Lista de IDs de series (ej: ['168.1_T_CAMBIOR_D_0_0_26'])
            start_date: Fecha inicio (YYYY-MM-DD), por defecto hace 1 año
            end_date: Fecha fin (YYYY-MM-DD), por defecto hoy
        
        Returns:
            DataFrame con las series solicitadas
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            params = {
                'ids': ','.join(ids),
                'start_date': start_date,
                'end_date': end_date
            }
            
            logger.info(f"Obteniendo series de tiempo del Gobierno Argentino: {ids}")
            response = self.session.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                # Convertir a DataFrame
                df = pd.DataFrame(data['data'])
                
                # La primera columna suele ser la fecha
                if len(df.columns) > 0:
                    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0])
                    df.set_index(df.columns[0], inplace=True)
                
                logger.info(f"✅ Obtenidas {len(df)} registros de series de tiempo")
                return df
            else:
                logger.warning("No se encontraron datos en las series solicitadas")
                return pd.DataFrame()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo series de tiempo: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error procesando series de tiempo: {e}")
            return pd.DataFrame()
    
    def search_series(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Busca series de tiempo disponibles.
        
        Args:
            query: Término de búsqueda
            limit: Límite de resultados
        
        Returns:
            Lista de series encontradas
        """
        try:
            # Endpoint de búsqueda (puede variar según la API)
            search_url = f"{self.base_url}/search"
            params = {
                'q': query,
                'limit': limit
            }
            
            logger.info(f"Buscando series de tiempo: {query}")
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'results' in data:
                logger.info(f"✅ Encontradas {len(data['results'])} series")
                return data['results']
            elif isinstance(data, list):
                logger.info(f"✅ Encontradas {len(data)} series")
                return data
            else:
                logger.warning("No se encontraron series")
                return []
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error buscando series: {e}")
            return []
        except Exception as e:
            logger.error(f"Error procesando búsqueda: {e}")
            return []


if __name__ == "__main__":
    # Test del cliente
    client = ArgentinaGovClient()
    
    print("Probando API de Series de Tiempo del Gobierno Argentino...")
    
    # Test: Buscar series relacionadas con dólar
    print("\n1. Buscando series relacionadas con dólar...")
    series = client.search_series('dolar', limit=5)
    if series:
        print(f"✅ Encontradas {len(series)} series")
        for s in series[:3]:
            print(f"   - {s.get('id', 'N/A')}: {s.get('title', 'N/A')}")
    else:
        print("⚠️ No se encontraron series")


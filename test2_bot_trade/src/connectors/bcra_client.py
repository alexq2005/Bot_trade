"""
BCRA (Banco Central de la República Argentina) Client
APIs públicas y gratuitas del BCRA para datos macroeconómicos y cambiarios
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import requests
import json

from src.core.logger import get_logger

logger = get_logger("bcra_client")


class BCRAClient:
    """
    Cliente para APIs públicas del BCRA.
    
    APIs disponibles:
    1. Principales Variables: Variables económicas relevantes
    2. Estadísticas Cambiarias: Cotizaciones de divisas
    """
    
    def __init__(self):
        self.base_url = "https://api.bcra.gob.ar"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_principal_variables(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene principales variables económicas del BCRA.
        
        Args:
            start_date: Fecha inicio (YYYY-MM-DD), por defecto hace 1 año
            end_date: Fecha fin (YYYY-MM-DD), por defecto hoy
        
        Returns:
            DataFrame con variables económicas
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Endpoint de principales variables
            endpoint = f"{self.base_url}/estadisticas/v2.0/principalesvariables"
            params = {
                'fechaDesde': start_date,
                'fechaHasta': end_date
            }
            
            logger.info(f"Obteniendo principales variables del BCRA desde {start_date} hasta {end_date}")
            response = self.session.get(endpoint, params=params, timeout=15, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                # Convertir fecha si existe
                if 'fecha' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    df.set_index('fecha', inplace=True)
                
                logger.info(f"✅ Obtenidas {len(df)} registros de principales variables del BCRA")
                return df
            else:
                logger.warning("No se encontraron datos de principales variables")
                return pd.DataFrame()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo principales variables del BCRA: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error procesando datos del BCRA: {e}")
            return pd.DataFrame()
    
    def get_currency_statistics(self, currency: str = "USD", start_date: Optional[str] = None, 
                                end_date: Optional[str] = None) -> pd.DataFrame:
        """
        Obtiene estadísticas cambiarias del BCRA.
        
        Args:
            currency: Moneda ('USD', 'EUR', etc.), por defecto USD
            start_date: Fecha inicio (YYYY-MM-DD), por defecto hace 1 año
            end_date: Fecha fin (YYYY-MM-DD), por defecto hoy
        
        Returns:
            DataFrame con estadísticas cambiarias
        """
        try:
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')
            if start_date is None:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Endpoint de estadísticas cambiarias
            endpoint = f"{self.base_url}/estadisticas/v2.0/estadisticasCambiarias"
            params = {
                'moneda': currency,
                'fechaDesde': start_date,
                'fechaHasta': end_date
            }
            
            logger.info(f"Obteniendo estadísticas cambiarias del BCRA para {currency} desde {start_date} hasta {end_date}")
            response = self.session.get(endpoint, params=params, timeout=15, verify=False)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                # Convertir fecha si existe
                if 'fecha' in df.columns:
                    df['fecha'] = pd.to_datetime(df['fecha'])
                    df.set_index('fecha', inplace=True)
                
                logger.info(f"✅ Obtenidas {len(df)} registros de estadísticas cambiarias del BCRA para {currency}")
                return df
            else:
                logger.warning(f"No se encontraron datos de estadísticas cambiarias para {currency}")
                return pd.DataFrame()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error obteniendo estadísticas cambiarias del BCRA: {e}")
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error procesando estadísticas cambiarias del BCRA: {e}")
            return pd.DataFrame()
    
    def get_usd_rate(self) -> Optional[float]:
        """
        Obtiene el tipo de cambio USD/ARS actual.
        
        Returns:
            Tipo de cambio actual o None si hay error
        """
        try:
            # Obtener estadísticas cambiarias más recientes
            df = self.get_currency_statistics('USD', 
                                             start_date=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                                             end_date=datetime.now().strftime('%Y-%m-%d'))
            
            if not df.empty:
                # Buscar columna con tipo de cambio
                for col in ['tipoCambio', 'cotizacion', 'precio', 'valor']:
                    if col in df.columns:
                        # Obtener último valor
                        last_value = df[col].iloc[-1] if len(df) > 0 else None
                        if last_value:
                            return float(last_value)
                
                # Si no encuentra columna específica, usar primera numérica
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                if len(numeric_cols) > 0:
                    return float(df[numeric_cols[0]].iloc[-1])
            
            return None
        
        except Exception as e:
            logger.error(f"Error obteniendo tipo de cambio USD: {e}")
            return None
    
    def get_inflation_rate(self) -> Optional[float]:
        """
        Obtiene la tasa de inflación más reciente.
        
        Returns:
            Tasa de inflación o None si hay error
        """
        try:
            df = self.get_principal_variables(
                start_date=(datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
                end_date=datetime.now().strftime('%Y-%m-%d')
            )
            
            if not df.empty:
                # Buscar columna de inflación
                for col in ['inflacion', 'ipc', 'indicePrecios', 'variacion']:
                    if col.lower() in [c.lower() for c in df.columns]:
                        matching_col = [c for c in df.columns if col.lower() in c.lower()][0]
                        last_value = df[matching_col].iloc[-1] if len(df) > 0 else None
                        if last_value:
                            return float(last_value)
            
            return None
        
        except Exception as e:
            logger.error(f"Error obteniendo tasa de inflación: {e}")
            return None


if __name__ == "__main__":
    # Test del cliente BCRA
    client = BCRAClient()
    
    print("Probando BCRA API...")
    
    # Test 1: Principales variables
    print("\n1. Obteniendo principales variables...")
    variables = client.get_principal_variables()
    if not variables.empty:
        print(f"✅ Obtenidas {len(variables)} variables")
        print(variables.head())
    else:
        print("⚠️ No se obtuvieron variables")
    
    # Test 2: Estadísticas cambiarias USD
    print("\n2. Obteniendo estadísticas cambiarias USD...")
    currency = client.get_currency_statistics('USD')
    if not currency.empty:
        print(f"✅ Obtenidas {len(currency)} estadísticas")
        print(currency.head())
    else:
        print("⚠️ No se obtuvieron estadísticas cambiarias")
    
    # Test 3: Tipo de cambio USD actual
    print("\n3. Obteniendo tipo de cambio USD actual...")
    usd_rate = client.get_usd_rate()
    if usd_rate:
        print(f"✅ Tipo de cambio USD/ARS: ${usd_rate:.2f}")
    else:
        print("⚠️ No se pudo obtener tipo de cambio")


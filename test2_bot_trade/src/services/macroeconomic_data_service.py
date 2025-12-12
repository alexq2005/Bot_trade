"""
Servicio de Datos Macroeconómicos
Integra APIs públicas y gratuitas para obtener datos macroeconómicos argentinos
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import pandas as pd

from src.connectors.bcra_client import BCRAClient
from src.connectors.monedapi_client import MonedAPIClient
from src.connectors.argentina_gov_client import ArgentinaGovClient
from src.connectors.dolar_api_client import DolarAPIClient
from src.core.logger import get_logger

logger = get_logger("macroeconomic_data_service")


class MacroeconomicDataService:
    """
    Servicio unificado para obtener datos macroeconómicos argentinos
    desde múltiples APIs públicas y gratuitas.
    """
    
    def __init__(self):
        self.bcra_client = BCRAClient()
        self.monedapi_client = MonedAPIClient()
        self.argentina_gov_client = ArgentinaGovClient()
        self.dolar_api_client = DolarAPIClient()  # API alternativa para dólar
    
    def get_usd_rates(self) -> Dict[str, Optional[float]]:
        """
        Obtiene todos los tipos de cambio USD disponibles.
        
        Returns:
            Dict con diferentes tipos de cambio USD
        """
        rates = {
            'oficial': None,
            'blue': None,
            'mep': None,
            'ccl': None,
            'bcra': None
        }
        
        try:
            # Desde BCRA (puede fallar por SSL, pero intentamos)
            try:
                bcra_rate = self.bcra_client.get_usd_rate()
                if bcra_rate:
                    rates['bcra'] = bcra_rate
                    rates['oficial'] = bcra_rate  # BCRA generalmente es oficial
            except Exception as e:
                logger.debug(f"BCRA no disponible: {e}")
            
            # Desde MonedAPI (puede fallar si el endpoint no existe)
            try:
                blue_rate = self.monedapi_client.get_usd_blue_rate()
                if blue_rate:
                    rates['blue'] = blue_rate
            except Exception as e:
                logger.debug(f"MonedAPI blue no disponible: {e}")
            
            try:
                official_rate = self.monedapi_client.get_usd_official_rate()
                if official_rate:
                    rates['oficial'] = official_rate if not rates['oficial'] else rates['oficial']
            except Exception as e:
                logger.debug(f"MonedAPI oficial no disponible: {e}")
            
            # Si no obtuvimos datos, intentar API alternativa de dólar
            if not rates.get('oficial') and not rates.get('blue'):
                try:
                    dolar_rates = self.dolar_api_client.get_dolar_rates()
                    if dolar_rates.get('oficial'):
                        rates['oficial'] = dolar_rates['oficial']
                    if dolar_rates.get('blue'):
                        rates['blue'] = dolar_rates['blue']
                    if dolar_rates.get('mep'):
                        rates['mep'] = dolar_rates['mep']
                    if dolar_rates.get('ccl'):
                        rates['ccl'] = dolar_rates['ccl']
                except Exception as e:
                    logger.debug(f"API alternativa de dólar no disponible: {e}")
            
            logger.info(f"✅ Obtenidos tipos de cambio USD: {rates}")
            return rates
        
        except Exception as e:
            logger.warning(f"Error obteniendo tipos de cambio USD: {e}")
            return rates
    
    def get_inflation_data(self, months: int = 12) -> pd.DataFrame:
        """
        Obtiene datos de inflación.
        
        Args:
            months: Número de meses de datos a obtener
        
        Returns:
            DataFrame con datos de inflación
        """
        try:
            start_date = (datetime.now() - timedelta(days=months*30)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            # Intentar desde BCRA
            df = self.bcra_client.get_principal_variables(start_date, end_date)
            
            if not df.empty:
                # Buscar columnas relacionadas con inflación
                inflation_cols = [col for col in df.columns if any(term in col.lower() 
                                 for term in ['inflacion', 'ipc', 'indice', 'precios'])]
                if inflation_cols:
                    result_df = df[inflation_cols]
                    logger.info(f"✅ Obtenidos datos de inflación: {len(result_df)} registros")
                    return result_df
            
            logger.warning("No se encontraron datos de inflación")
            return pd.DataFrame()
        
        except Exception as e:
            logger.error(f"Error obteniendo datos de inflación: {e}")
            return pd.DataFrame()
    
    def get_currency_statistics(self, currency: str = "USD", days: int = 365) -> pd.DataFrame:
        """
        Obtiene estadísticas cambiarias.
        
        Args:
            currency: Moneda ('USD', 'EUR', etc.)
            days: Días de datos históricos
        
        Returns:
            DataFrame con estadísticas cambiarias
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            df = self.bcra_client.get_currency_statistics(currency, start_date, end_date)
            
            if not df.empty:
                logger.info(f"✅ Obtenidas estadísticas cambiarias para {currency}: {len(df)} registros")
            
            return df
        
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas cambiarias: {e}")
            return pd.DataFrame()
    
    def get_economic_indicators(self) -> Dict[str, Any]:
        """
        Obtiene indicadores económicos principales.
        
        Returns:
            Dict con indicadores económicos
        """
        indicators = {
            'usd_official': None,
            'usd_blue': None,
            'inflation_rate': None,
            'last_update': datetime.now().isoformat()
        }
        
        try:
            # Tipos de cambio
            usd_rates = self.get_usd_rates()
            indicators['usd_official'] = usd_rates.get('oficial')
            indicators['usd_blue'] = usd_rates.get('blue')
            
            # Inflación
            inflation_data = self.get_inflation_data(months=1)
            if not inflation_data.empty:
                # Obtener último valor
                last_value = inflation_data.iloc[-1, 0] if len(inflation_data) > 0 else None
                indicators['inflation_rate'] = float(last_value) if last_value else None
            
            logger.info(f"✅ Obtenidos indicadores económicos: {indicators}")
            return indicators
        
        except Exception as e:
            logger.error(f"Error obteniendo indicadores económicos: {e}")
            return indicators


if __name__ == "__main__":
    # Test del servicio
    service = MacroeconomicDataService()
    
    print("Probando Servicio de Datos Macroeconómicos...")
    
    # Test 1: Tipos de cambio USD
    print("\n1. Obteniendo tipos de cambio USD...")
    rates = service.get_usd_rates()
    print(f"✅ Tipos de cambio: {rates}")
    
    # Test 2: Indicadores económicos
    print("\n2. Obteniendo indicadores económicos...")
    indicators = service.get_economic_indicators()
    print(f"✅ Indicadores: {indicators}")
    
    # Test 3: Estadísticas cambiarias
    print("\n3. Obteniendo estadísticas cambiarias USD (últimos 30 días)...")
    currency_stats = service.get_currency_statistics('USD', days=30)
    if not currency_stats.empty:
        print(f"✅ Obtenidas {len(currency_stats)} estadísticas")
        print(currency_stats.head())


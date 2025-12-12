"""
MonedAPI Client
API gratuita para cotizaciones de divisas en Argentina
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import requests

from src.core.logger import get_logger

logger = get_logger("monedapi_client")


class MonedAPIClient:
    """
    Cliente para MonedAPI - API gratuita de cotizaciones de divisas en Argentina.
    
    URL: https://monedapi.ar/
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('MONEDAPI_KEY')
        self.base_url = "https://api.monedapi.ar"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Si hay API key, agregarla a headers
        if self.api_key:
            self.session.headers.update({'Authorization': f'Bearer {self.api_key}'})
    
    def get_currency_rates(self, currency: str = "USD") -> Dict[str, Any]:
        """
        Obtiene cotizaciones de divisas.
        
        Args:
            currency: Moneda ('USD', 'EUR', 'BRL', etc.)
        
        Returns:
            Dict con cotizaciones
        """
        try:
            # Intentar diferentes endpoints posibles
            endpoints = [
                f"{self.base_url}/v1/cotizaciones/{currency}",
                f"{self.base_url}/cotizaciones/{currency}",
                f"{self.base_url}/api/v1/cotizaciones/{currency}",
                f"{self.base_url}/dolar/{currency.lower()}"
            ]
            
            for endpoint in endpoints:
                try:
                    logger.info(f"Intentando obtener cotizaciones de {currency} desde {endpoint}...")
                    response = self.session.get(endpoint, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"✅ Obtenidas cotizaciones de {currency} desde MonedAPI")
                        return data
                except:
                    continue
            
            # Si todos los endpoints fallan, retornar vacío
            logger.warning(f"No se pudo obtener cotizaciones de {currency} desde MonedAPI (endpoints no disponibles)")
            return {}
        
        except Exception as e:
            logger.warning(f"Error obteniendo cotizaciones desde MonedAPI: {e}")
            return {}
    
    def get_all_currencies(self) -> Dict[str, Any]:
        """
        Obtiene todas las cotizaciones disponibles.
        
        Returns:
            Dict con todas las cotizaciones
        """
        try:
            endpoint = f"{self.base_url}/v1/cotizaciones"
            
            logger.info("Obteniendo todas las cotizaciones desde MonedAPI...")
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info("✅ Obtenidas todas las cotizaciones desde MonedAPI")
            return data
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Error obteniendo cotizaciones desde MonedAPI: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error procesando datos de MonedAPI: {e}")
            return {}
    
    def get_usd_blue_rate(self) -> Optional[float]:
        """
        Obtiene el tipo de cambio dólar blue.
        
        Returns:
            Precio del dólar blue o None
        """
        try:
            data = self.get_currency_rates('USD')
            
            # Buscar precio blue en diferentes formatos posibles
            if isinstance(data, dict):
                # Intentar diferentes claves posibles
                for key in ['blue', 'dolarBlue', 'bluePrice', 'precioBlue', 'compra', 'venta']:
                    if key in data:
                        value = data[key]
                        if isinstance(value, (int, float)):
                            return float(value)
                        elif isinstance(value, dict):
                            # Si es un dict, buscar precio dentro
                            for sub_key in ['precio', 'price', 'valor', 'value']:
                                if sub_key in value:
                                    return float(value[sub_key])
            
            return None
        
        except Exception as e:
            logger.error(f"Error obteniendo dólar blue desde MonedAPI: {e}")
            return None
    
    def get_usd_official_rate(self) -> Optional[float]:
        """
        Obtiene el tipo de cambio dólar oficial.
        
        Returns:
            Precio del dólar oficial o None
        """
        try:
            data = self.get_currency_rates('USD')
            
            if isinstance(data, dict):
                # Intentar diferentes claves posibles
                for key in ['oficial', 'dolarOficial', 'oficialPrice', 'precioOficial', 'bcra']:
                    if key in data:
                        value = data[key]
                        if isinstance(value, (int, float)):
                            return float(value)
                        elif isinstance(value, dict):
                            for sub_key in ['precio', 'price', 'valor', 'value']:
                                if sub_key in value:
                                    return float(value[sub_key])
            
            return None
        
        except Exception as e:
            logger.error(f"Error obteniendo dólar oficial desde MonedAPI: {e}")
            return None


if __name__ == "__main__":
    # Test del cliente MonedAPI
    client = MonedAPIClient()
    
    print("Probando MonedAPI...")
    
    # Test 1: Cotizaciones USD
    print("\n1. Obteniendo cotizaciones USD...")
    usd_data = client.get_currency_rates('USD')
    if usd_data:
        print(f"✅ Datos obtenidos: {usd_data}")
    else:
        print("⚠️ No se obtuvieron datos")
    
    # Test 2: Dólar Blue
    print("\n2. Obteniendo dólar blue...")
    blue_rate = client.get_usd_blue_rate()
    if blue_rate:
        print(f"✅ Dólar blue: ${blue_rate:.2f}")
    else:
        print("⚠️ No se pudo obtener dólar blue")
    
    # Test 3: Dólar Oficial
    print("\n3. Obteniendo dólar oficial...")
    official_rate = client.get_usd_official_rate()
    if official_rate:
        print(f"✅ Dólar oficial: ${official_rate:.2f}")
    else:
        print("⚠️ No se pudo obtener dólar oficial")


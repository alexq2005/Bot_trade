"""
Dólar API Client - API alternativa para cotizaciones de dólar en Argentina
Usa APIs públicas conocidas como alternativa a MonedAPI
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from typing import Dict, Optional, Any
import requests
import json

from src.core.logger import get_logger

logger = get_logger("dolar_api_client")


class DolarAPIClient:
    """
    Cliente para APIs alternativas de cotizaciones de dólar en Argentina.
    
    Fuentes alternativas:
    - API de Dólar (dolarapi.com)
    - API de Dólar Hoy (dolarhoy.com)
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_dolar_rates(self) -> Dict[str, Optional[float]]:
        """
        Obtiene cotizaciones de dólar desde APIs alternativas.
        
        Returns:
            Dict con cotizaciones (oficial, blue, mep, ccl)
        """
        rates = {
            'oficial': None,
            'blue': None,
            'mep': None,
            'ccl': None
        }
        
        # Intentar múltiples APIs alternativas para dólar oficial
        endpoints_oficial = [
            "https://api-dolar-argentina.herokuapp.com/api/dolaroficial",
            "https://dolarapi.com/v1/dolares/oficial",
            "https://api.bluelytics.com.ar/v2/latest"
        ]
        
        for endpoint in endpoints_oficial:
            try:
                response = self.session.get(endpoint, timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    # Diferentes formatos de respuesta
                    if isinstance(data, dict):
                        if 'venta' in data:
                            rates['oficial'] = float(data['venta'])
                            logger.info(f"✅ Obtenido dólar oficial: ${rates['oficial']:.2f}")
                            break
                        elif 'value' in data:
                            rates['oficial'] = float(data['value'])
                            logger.info(f"✅ Obtenido dólar oficial: ${rates['oficial']:.2f}")
                            break
                        elif 'oficial' in data and isinstance(data['oficial'], dict):
                            if 'venta' in data['oficial']:
                                rates['oficial'] = float(data['oficial']['venta'])
                                logger.info(f"✅ Obtenido dólar oficial: ${rates['oficial']:.2f}")
                                break
                    elif isinstance(data, list) and len(data) > 0:
                        # Algunas APIs devuelven arrays
                        for item in data:
                            if isinstance(item, dict) and 'venta' in item:
                                rates['oficial'] = float(item['venta'])
                                logger.info(f"✅ Obtenido dólar oficial: ${rates['oficial']:.2f}")
                                break
                        if rates['oficial']:
                            break
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} no disponible: {e}")
                continue
        
        # Intentar múltiples APIs alternativas para dólar blue
        endpoints_blue = [
            "https://api-dolar-argentina.herokuapp.com/api/dolarblue",
            "https://dolarapi.com/v1/dolares/blue",
            "https://api.bluelytics.com.ar/v2/latest"
        ]
        
        for endpoint in endpoints_blue:
            try:
                response = self.session.get(endpoint, timeout=10, verify=False)
                if response.status_code == 200:
                    data = response.json()
                    # Diferentes formatos de respuesta
                    if isinstance(data, dict):
                        if 'venta' in data:
                            rates['blue'] = float(data['venta'])
                            logger.info(f"✅ Obtenido dólar blue: ${rates['blue']:.2f}")
                            break
                        elif 'value' in data:
                            rates['blue'] = float(data['value'])
                            logger.info(f"✅ Obtenido dólar blue: ${rates['blue']:.2f}")
                            break
                        elif 'blue' in data and isinstance(data['blue'], dict):
                            if 'venta' in data['blue']:
                                rates['blue'] = float(data['blue']['venta'])
                                logger.info(f"✅ Obtenido dólar blue: ${rates['blue']:.2f}")
                                break
                    elif isinstance(data, list) and len(data) > 0:
                        for item in data:
                            if isinstance(item, dict) and 'venta' in item:
                                rates['blue'] = float(item['venta'])
                                logger.info(f"✅ Obtenido dólar blue: ${rates['blue']:.2f}")
                                break
                        if rates['blue']:
                            break
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} no disponible: {e}")
                continue
        
        # Intentar obtener dólar MEP
        try:
            endpoint = "https://api-dolar-argentina.herokuapp.com/api/dolarbolsa"
            response = self.session.get(endpoint, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                if 'venta' in data:
                    rates['mep'] = float(data['venta'])
                    logger.info(f"✅ Obtenido dólar MEP: ${rates['mep']:.2f}")
        except Exception as e:
            logger.debug(f"API dolarapi.com MEP no disponible: {e}")
        
        # Intentar obtener dólar CCL
        try:
            endpoint = "https://api-dolar-argentina.herokuapp.com/api/contadoliqui"
            response = self.session.get(endpoint, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                if 'venta' in data:
                    rates['ccl'] = float(data['venta'])
                    logger.info(f"✅ Obtenido dólar CCL: ${rates['ccl']:.2f}")
        except Exception as e:
            logger.debug(f"API dolarapi.com CCL no disponible: {e}")
        
        return rates


if __name__ == "__main__":
    # Test del cliente
    client = DolarAPIClient()
    
    print("Probando Dólar API Client...")
    rates = client.get_dolar_rates()
    print(f"✅ Cotizaciones obtenidas: {rates}")


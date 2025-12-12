import time
from datetime import datetime
from typing import Any, Dict, Optional, cast

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.rate_limiter import iol_rate_limiter
from src.core.error_handler import retry_on_network_error, ErrorHandler


class IOLClient:
    def __init__(self) -> None:
        self.base_url: str = settings.IOL_API_URL
        self.token_url: str = settings.IOL_TOKEN_URL
        self.username: str = settings.IOL_USERNAME
        self.password: str = settings.IOL_PASSWORD
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expiry: float = 0

        # Mapeo de mercados
        self.MARKET_CODES: Dict[str, str] = {
            # Acciones Argentinas
            "GGAL": "bCBA",
            "YPFD": "bCBA",
            "PAMP": "bCBA",
            "BYMA": "bCBA",
            "VENIR": "bCBA",
            "CEPU": "bCBA",
            "EDN": "bCBA",
            "TGNO4": "bCBA",
            "LOMA": "bCBA",
            "TGSU2": "bCBA",
            "TRAN": "bCBA",
            "METR": "bCBA",
            "ECOG": "bCBA",
            # Bonos
            "BA37D": "bCBA",
            "BPOC7": "bCBA",
            "GD35": "bCBA",
            "T15D5": "bCBA",
            "TTM26": "bCBA",
            "TX26": "bCBA",
            # Acciones USA (se manejan diferente)
            "AAPL": "NASDAQ",
            "MSFT": "NASDAQ",
            "GOOGL": "NASDAQ",
            "AMZN": "NASDAQ",
            "TSLA": "NASDAQ",
            "NVDA": "NASDAQ",
            "META": "NASDAQ",
            "KO": "NYSE",
            "TSM": "NYSE",
            "NU": "NYSE",
        }

    def _get_headers(self) -> Dict[str, str]:
        """Returns headers with valid access token."""
        if self._is_token_expired():
            self._login()
        return {"Authorization": f"Bearer {self.access_token}"}

    def _is_token_expired(self) -> bool:
        """Checks if the current access token is expired or about to expire."""
        if not self.access_token or not self.token_expiry:
            return True
        # Buffer of 60 seconds
        return time.time() > (self.token_expiry - 60)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,
    )
    def _login(self) -> None:
        """Authenticates with IOL to get access and refresh tokens."""
        print(f"Autenticando con IOL como {self.username}...")
        payload = {"username": self.username, "password": self.password, "grant_type": "password"}

        try:
            response = requests.post(self.token_url, data=payload)
            response.raise_for_status()
            data = response.json()

            self.access_token = data["access_token"]
            self.refresh_token = data["refresh_token"]
            self.token_expiry = time.time() + data["expires_in"]
            print("Autenticación exitosa.")

        except requests.exceptions.RequestException as e:
            print(f"Autenticación fallida: {e}")
            raise

    def _detect_market(self, symbol: str) -> str:
        """Detecta el código de mercado para un símbolo"""
        return self.MARKET_CODES.get(symbol.upper(), "bCBA")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def get_quote(self, symbol: str, market: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves the current quote for a given symbol using working endpoint.

        Args:
            symbol: The ticker symbol (e.g., 'GGAL')
            market: The market code (auto-detected if None)

        Returns:
            dict with quote data
        """
        # Rate limiting para IOL API
        iol_rate_limiter.wait_if_needed('iol_api')
        
        if market is None:
            market = self._detect_market(symbol)

        # Clean symbol for IOL (remove .BA suffix)
        clean_symbol = symbol.replace(".BA", "")

        endpoint = f"{self.base_url}/{market}/Titulos/{clean_symbol}/Cotizacion"

        try:
            response = requests.get(endpoint, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors (4xx, 5xx)
            # Para errores 404, no imprimir (símbolo no existe en IOL)
            if response.status_code == 404:
                return {"error": f"Símbolo {symbol} no encontrado en IOL", "status_code": 404}
            error_msg = f"HTTP {response.status_code}: {response.text[:200] if hasattr(response, 'text') else str(e)}"
            if response.status_code != 404:  # Solo imprimir si no es 404
                print(f"Error obteniendo cotización para {symbol}: {error_msg}")
            return {"error": error_msg, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            # Handle network errors, timeouts, etc.
            error_msg = f"Request failed: {str(e)}"
            print(f"Error obteniendo cotización para {symbol}: {error_msg}")
            return {"error": error_msg}
        except Exception as e:
            # For any other exceptions, return error immediately
            error_msg = f"Unexpected error: {str(e)}"
            print(f"Error obteniendo cotización para {symbol}: {error_msg}")
            return {"error": error_msg}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Método genérico para hacer peticiones HTTP a la API de IOL
        
        Args:
            method: Método HTTP ('GET', 'POST', etc.)
            endpoint: Endpoint relativo (ej: 'Titulos/Cotizacion/acciones')
            **kwargs: Argumentos adicionales para requests
        
        Returns:
            dict con la respuesta JSON
        """
        # Rate limiting para IOL API
        iol_rate_limiter.wait_if_needed('iol_api')
        
        # Construir URL completa
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        # Detectar mercado si es necesario (por ahora usar bCBA como default)
        url = f"{self.base_url}/bCBA/{endpoint}"
        
        try:
            headers = self._get_headers()
            headers.update(kwargs.get('headers', {}))
            
            response = requests.request(
                method.upper(),
                url,
                headers=headers,
                timeout=kwargs.get('timeout', 10),
                **{k: v for k, v in kwargs.items() if k not in ['headers', 'timeout']}
            )
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {response.status_code}: {response.text[:200] if hasattr(response, 'text') else str(e)}"
            print(f"Error en petición {method} {endpoint}: {error_msg}")
            return {"error": error_msg, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"Error en petición {method} {endpoint}: {error_msg}")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"Error en petición {method} {endpoint}: {error_msg}")
            return {"error": error_msg}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def get_account_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de cuenta actual.

        Returns:
            dict with account information including balances
        """
        # Rate limiting para IOL API
        iol_rate_limiter.wait_if_needed('iol_api')
        
        endpoint = f"{self.base_url}/estadocuenta"

        try:
            response = requests.get(endpoint, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo estado de cuenta: {e}")
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def get_portfolio(self, country: str = "argentina") -> Dict[str, Any]:
        """
        Obtiene el portafolio actual.

        Args:
            country: 'argentina' o 'estados_Unidos'

        Returns:
            dict with portfolio holdings
        """
        endpoint = f"{self.base_url}/portafolio/{country}"

        try:
            response = requests.get(endpoint, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo portafolio: {e}")
            raise e

    def get_available_balance(self, prefer_immediate: bool = True) -> float:
        """
        Obtiene el saldo disponible para operar.

        Args:
            prefer_immediate: Si True, prioriza saldo inmediato (T+0), si False, prioriza T+1 (hrs48)

        Returns:
            float: Saldo disponible en ARS
        """
        try:
            account = self.get_account_status()
        except Exception:
            return 0.0

        if "error" in account:
            return 0.0

        # Buscar cuenta en pesos argentinos
        for cuenta in account.get("cuentas", []):
            if cuenta.get("tipo") == "inversion_Argentina_Pesos":
                saldos = cuenta.get("saldos", [])
                
                if not saldos:
                    return 0.0
                
                # Si prefer_immediate, buscar primero saldo inmediato (T+0)
                if prefer_immediate:
                    for saldo in saldos:
                        liquidacion = saldo.get("liquidacion", "").lower()
                        # T+0 puede ser "inmediato", "inmediata", "t0", "hrs0", etc.
                        if liquidacion in ["inmediato", "inmediata", "t0", "hrs0", "0"]:
                            disponible = saldo.get("disponibleOperar", saldo.get("disponible", 0.0))
                            if disponible > 0:
                                return float(disponible)
                
                # Buscar saldo T+1 (hrs48) - más común para operaciones
                for saldo in saldos:
                    if saldo.get("liquidacion") == "hrs48":
                        disponible = saldo.get("disponibleOperar", saldo.get("disponible", 0.0))
                        if disponible > 0:
                            return float(disponible)
                
                # Fallback: usar el mayor saldo disponible de todos
                max_disponible = 0.0
                for saldo in saldos:
                    disponible = saldo.get("disponibleOperar", saldo.get("disponible", 0.0))
                    if disponible > max_disponible:
                        max_disponible = disponible
                
                if max_disponible > 0:
                    return float(max_disponible)
                
                # Último fallback: usar disponibleOperar del primer saldo
                return float(saldos[0].get("disponibleOperar", saldos[0].get("disponible", 0.0)))

        return 0.0
    
    def get_all_balances(self) -> Dict[str, float]:
        """
        Obtiene todos los saldos disponibles de la cuenta.
        
        Returns:
            dict con los saldos por tipo de liquidación
        """
        try:
            account = self.get_account_status()
        except Exception:
            return {}

        if "error" in account:
            return {}

        balances = {}
        
        # Buscar cuenta en pesos argentinos
        for cuenta in account.get("cuentas", []):
            if cuenta.get("tipo") == "inversion_Argentina_Pesos":
                saldos = cuenta.get("saldos", [])
                for saldo in saldos:
                    liquidacion = saldo.get("liquidacion", "desconocido")
                    disponible = saldo.get("disponibleOperar", saldo.get("disponible", 0.0))
                    balances[liquidacion] = float(disponible)
                break
        
        return balances

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def place_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        side: str,
        market: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Places a buy or sell order.

        Args:
            symbol: Ticker symbol
            quantity: Number of shares
            price: Limit price
            side: 'buy' or 'sell'
            market: Market code (auto-detected if None)

        Returns:
            dict with order response
        """
        # Rate limiting para IOL API
        iol_rate_limiter.wait_if_needed('iol_api')
        
        if market is None:
            market = self._detect_market(symbol)

        # Endpoint para comprar o vender
        if side.lower() == "buy":
            endpoint = f"{self.base_url}/operar/Comprar"
        else:
            endpoint = f"{self.base_url}/operar/Vender"

        payload = {
            "mercado": market,
            "simbolo": symbol,
            "cantidad": quantity,
            "precio": price,
            "plazo": "t1",  # Settlement T+1
            "validez": "2025-12-31",  # Valid until date
        }

        try:
            print(f"🚀 Colocando orden {side.upper()} de {quantity} {symbol} a ${price:.2f}")
            response = requests.post(
                endpoint, json=payload, headers=self._get_headers(), timeout=10
            )

            # Aceptar códigos 200-299 como exitosos (200 OK, 201 Created, 202 Accepted, etc.)
            if not (200 <= response.status_code < 300):
                print(f"❌ Orden fallida (código {response.status_code}): {response.text}")
                return {"error": response.text, "status_code": response.status_code}

            data = response.json()
            
            # Si hay número de operación, la orden se colocó exitosamente
            # IOL puede devolver solo {"numeroOperacion": X} sin "ok": true
            if "numeroOperacion" in data:
                operation_id = data.get('numeroOperacion')
                print(f"✅ Orden colocada exitosamente: ID {operation_id} (código {response.status_code})")
                # Asegurar que el resultado indique éxito
                data['success'] = True
                data['status_code'] = response.status_code
            elif "error" in data or (data.get("ok") == False):
                print(f"❌ Orden fallida: {data}")
                data['success'] = False
            else:
                print(f"✅ Orden procesada: {data} (código {response.status_code})")
                data['success'] = True
            
            return cast(Dict[str, Any], data)

        except requests.exceptions.RequestException as e:
            print(f"❌ Error colocando orden: {e}")
            raise e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def get_operation_history(self, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene el historial de operaciones realizadas.
        
        Args:
            fecha_desde: Fecha desde (formato: YYYY-MM-DD). Si es None, últimos 30 días
            fecha_hasta: Fecha hasta (formato: YYYY-MM-DD). Si es None, fecha actual
        
        Returns:
            dict con historial de operaciones
        """
        from datetime import datetime, timedelta
        
        # Si no se especifican fechas, usar últimos 30 días
        if fecha_desde is None:
            fecha_desde = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if fecha_hasta is None:
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        
        endpoint = f"{self.base_url}/operaciones"
        params = {
            "fechaDesde": fecha_desde,
            "fechaHasta": fecha_hasta
        }
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), params=params, timeout=10)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo historial de operaciones: {e}")
            return {"error": str(e)}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def get_operation_detail(self, operation_id: int) -> Dict[str, Any]:
        """
        Obtiene el detalle de una operación específica.
        
        Args:
            operation_id: Número de operación
        
        Returns:
            dict con detalle de la operación
        """
        endpoint = f"{self.base_url}/operaciones/{operation_id}"
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo detalle de operación {operation_id}: {e}")
            return {"error": str(e)}
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
    )
    def get_panel_general(self) -> Dict[str, Any]:
        """
        Obtiene el Panel General completo de IOL con TODOS los instrumentos disponibles.
        Este es el método más completo para obtener todos los símbolos operables.
        
        Returns:
            dict con todos los instrumentos del panel general
        """
        # Rate limiting para IOL API
        iol_rate_limiter.wait_if_needed('iol_api')
        
        # Endpoint del Panel General de IOL
        endpoint = f"{self.base_url}/bCBA/Titulos/Cotizacion/PanelGeneral"
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP {response.status_code}: {response.text[:200] if hasattr(response, 'text') else str(e)}"
            print(f"⚠️  Error obteniendo Panel General: {error_msg}")
            return {"error": error_msg, "status_code": response.status_code}
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            print(f"⚠️  Error obteniendo Panel General: {error_msg}")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"⚠️  Error obteniendo Panel General: {error_msg}")
            return {"error": error_msg}

    def get_account_movements(self, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene los movimientos de cuenta (depósitos, retiros, liquidaciones).
        
        Args:
            fecha_desde: Fecha desde (formato: YYYY-MM-DD). Si es None, últimos 30 días
            fecha_hasta: Fecha hasta (formato: YYYY-MM-DD). Si es None, fecha actual
        
        Returns:
            dict con movimientos de cuenta
        """
        from datetime import datetime, timedelta
        
        # Si no se especifican fechas, usar últimos 30 días
        if fecha_desde is None:
            fecha_desde = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if fecha_hasta is None:
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        
        endpoint = f"{self.base_url}/movimientos"
        params = {
            "fechaDesde": fecha_desde,
            "fechaHasta": fecha_hasta
        }
        
        try:
            response = requests.get(endpoint, headers=self._get_headers(), params=params, timeout=10)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error obteniendo movimientos de cuenta: {e}")
            return {"error": str(e)}


# Simple test block
if __name__ == "__main__":
    try:
        client = IOLClient()

        # Test 1: Account Status
        print("=== Test 1: Account Status ===")
        account = client.get_account_status()
        if "error" not in account:
            print(f"Saldo disponible: ${client.get_available_balance():.2f} ARS")

        # Test 2: Quote
        print("\n=== Test 2: Quote GGAL ===")
        quote = client.get_quote("GGAL")
        if "error" not in quote:
            print(f"GGAL: ${quote.get('ultimoPrecio', 'N/A')}")

        # Test 3: Portfolio
        print("\n=== Test 3: Portfolio ===")
        portfolio = client.get_portfolio()
        if "error" not in portfolio:
            print(f"Activos en portafolio: {len(portfolio.get('activos', []))}")

    except Exception as e:
        print(f"Test failed: {e}")

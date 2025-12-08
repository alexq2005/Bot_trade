"""
Ejemplos de uso de las nuevas mejoras implementadas
"""
from src.core.error_handler import (
    RetryHandler,
    retry_on_network_error,
    retry_on_api_error,
    safe_execute,
    ErrorHandler
)
from src.core.rate_limiter import (
    RateLimiter,
    iol_rate_limiter,
    telegram_rate_limiter,
    rate_limit
)
from src.core.validators import (
    TradeRequest,
    SymbolValidator,
    ConfigValidator
)
from src.core.cache_manager import (
    CacheManager,
    get_cache,
    cached
)


# ============================================
# EJEMPLO 1: Manejo de Errores con Reintentos
# ============================================

def ejemplo_error_handler():
    """Ejemplo de uso del manejo de errores"""
    print("📋 Ejemplo de manejo de errores:")
    
    # Ejemplo con decorador
    @retry_on_network_error(max_retries=2)
    def fetch_data_from_api(url):
        """Función que se reintentará automáticamente si falla"""
        import requests
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        return response.json()
    
    # Uso con safe_execute (no fallará)
    result = ErrorHandler.safe_execute(
        func=fetch_data_from_api,
        default_return={"status": "error", "message": "No se pudo conectar"},
        log_error=False,  # No loguear en el ejemplo
        url="https://httpbin.org/delay/1"  # URL de prueba que funciona
    )
    print(f"   Resultado: {result}")
    print()


# ============================================
# EJEMPLO 2: Rate Limiting
# ============================================

# Uso directo del rate limiter
iol_rate_limiter.wait_if_needed('iol_api')
# Ahora puedes hacer la llamada a IOL sin preocuparte por exceder límites


# Uso como decorador
@rate_limit(key='my_api', max_calls=100, period=60)
def call_external_api():
    """Función con rate limiting automático"""
    pass


# ============================================
# EJEMPLO 3: Validación de Entrada
# ============================================

# Validar request de trading
try:
    trade = TradeRequest(
        symbol="AAPL",
        action="BUY",
        quantity=10,
        price=150.0,
        stop_loss=145.0,
        take_profit=160.0
    )
    print(f"✅ Trade válido: {trade.symbol} {trade.action} {trade.quantity}")
except ValueError as e:
    print(f"❌ Error de validación: {e}")


# Validar símbolo
if SymbolValidator.validate_symbol("GGAL.BA"):
    print("✅ Símbolo válido")
else:
    print("❌ Símbolo inválido")


# Normalizar símbolo
normalized = SymbolValidator.normalize_symbol("  aapl  ")
print(f"Símbolo normalizado: {normalized}")  # "AAPL"


# Validar configuración
try:
    risk = ConfigValidator.validate_risk_per_trade(3.0)  # ✅ OK
    threshold = ConfigValidator.validate_threshold(25)  # ✅ OK
    interval = ConfigValidator.validate_interval(60)  # ✅ OK
except ValueError as e:
    print(f"❌ Error: {e}")


# ============================================
# EJEMPLO 4: Sistema de Caché
# ============================================

# Uso directo del caché
cache = get_cache()

# Guardar en caché
cache.set("quote:AAPL", {"price": 150.0, "volume": 1000}, ttl=60)

# Obtener del caché
quote = cache.get("quote:AAPL")
if quote:
    print(f"✅ Precio desde caché: {quote['price']}")
else:
    print("❌ No en caché, necesitas obtener de API")


# Uso como decorador
@cached(ttl=300, key_prefix="analysis")
def analyze_symbol(symbol: str):
    """Análisis que se cachea automáticamente"""
    # Análisis costoso aquí
    return {"score": 45, "signal": "BUY"}


# Primera llamada: ejecuta la función
result1 = analyze_symbol("AAPL")  # Cache MISS

# Segunda llamada: usa caché
result2 = analyze_symbol("AAPL")  # Cache HIT (más rápido)


# Invalidar caché por patrón
cache.invalidate("quote:")  # Invalida todas las cotizaciones


# Obtener estadísticas del caché
stats = cache.get_stats()
print(f"Caché: {stats['valid_entries']}/{stats['max_size']} entradas")


# ============================================
# EJEMPLO 5: Integración Completa
# ============================================

@retry_on_network_error(max_retries=3)
@cached(ttl=60, key_prefix="iol_quote")
def get_quote_with_improvements(symbol: str):
    """Función mejorada con caché y reintentos"""
    # Rate limiting
    iol_rate_limiter.wait_if_needed('iol_api')
    
    # Validar símbolo
    if not SymbolValidator.validate_symbol(symbol):
        raise ValueError(f"Símbolo inválido: {symbol}")
    
    symbol = SymbolValidator.normalize_symbol(symbol)
    
    # Llamada a API (con reintentos automáticos)
    from src.connectors.iol_client import IOLClient
    client = IOLClient()
    return client.get_quote(symbol)


# Uso
try:
    quote = get_quote_with_improvements("AAPL")
    print(f"✅ Cotización obtenida: {quote}")
except Exception as e:
    ErrorHandler.handle_critical_error(e, context="get_quote_with_improvements")


# ============================================
# EJEMPLO 6: En trading_bot.py
# ============================================

"""
# En trading_bot.py, puedes usar así:

from src.core.error_handler import retry_on_api_error, safe_execute
from src.core.validators import TradeRequest, SymbolValidator
from src.core.cache_manager import cached

class TradingBot:
    @retry_on_api_error(max_retries=3)
    @cached(ttl=300, key_prefix="analysis")
    def analyze_symbol(self, symbol: str):
        # Validar símbolo
        if not SymbolValidator.validate_symbol(symbol):
            raise ValueError(f"Símbolo inválido: {symbol}")
        
        symbol = SymbolValidator.normalize_symbol(symbol)
        
        # Tu análisis aquí
        ...
    
    def execute_trade(self, symbol, action, quantity, price, stop_loss, take_profit):
        # Validar request
        try:
            trade_request = TradeRequest(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        except ValueError as e:
            logger.error(f"Error de validación: {e}")
            return False
        
        # Ejecutar trade con manejo de errores
        return safe_execute(
            func=self._execute_trade_internal,
            default_return=False,
            log_error=True,
            trade_request=trade_request
        )
"""


if __name__ == "__main__":
    print("=" * 70)
    print("🚀 EJEMPLOS DE USO DE MEJORAS - IOL Quantum AI Trading Bot")
    print("=" * 70)
    print()
    
    # Ejemplo 1: Validación
    print("📋 EJEMPLO 1: Validación de Entrada")
    print("-" * 70)
    try:
        trade = TradeRequest(
            symbol="AAPL",
            action="BUY",
            quantity=10,
            price=150.0,
            stop_loss=145.0,
            take_profit=160.0
        )
        print(f"✅ Trade válido: {trade.symbol} {trade.action} {trade.quantity} @ ${trade.price}")
    except ValueError as e:
        print(f"❌ Error de validación: {e}")
    print()
    
    # Ejemplo 2: Validación de símbolo
    print("📋 EJEMPLO 2: Validación de Símbolos")
    print("-" * 70)
    symbols = ["AAPL", "GGAL.BA", "INVALID!!!"]
    for symbol in symbols:
        if SymbolValidator.validate_symbol(symbol):
            normalized = SymbolValidator.normalize_symbol(symbol)
            print(f"✅ Símbolo válido: {symbol} → {normalized}")
        else:
            print(f"❌ Símbolo inválido: {symbol}")
    print()
    
    # Ejemplo 3: Caché
    print("📋 EJEMPLO 3: Sistema de Caché")
    print("-" * 70)
    cache = get_cache()
    cache.set("test:key1", {"data": "valor1"}, ttl=60)
    value = cache.get("test:key1")
    if value:
        print(f"✅ Valor obtenido del caché: {value}")
    stats = cache.get_stats()
    print(f"📊 Estadísticas del caché: {stats['valid_entries']}/{stats['max_size']} entradas")
    print()
    
    # Ejemplo 4: Rate Limiter
    print("📋 EJEMPLO 4: Rate Limiting")
    print("-" * 70)
    print("⏳ Aplicando rate limiting a IOL API...")
    iol_rate_limiter.wait_if_needed('iol_api', silent=True)
    remaining = iol_rate_limiter.get_remaining_calls('iol_api')
    print(f"✅ Rate limit aplicado. Llamadas restantes: {remaining}/{iol_rate_limiter.max_calls}")
    print()
    
    # Ejemplo 5: Config Validator
    print("📋 EJEMPLO 5: Validación de Configuración")
    print("-" * 70)
    try:
        risk = ConfigValidator.validate_risk_per_trade(3.0)
        threshold = ConfigValidator.validate_threshold(25)
        interval = ConfigValidator.validate_interval(60)
        print(f"✅ Configuración válida:")
        print(f"   - Riesgo por operación: {risk}%")
        print(f"   - Umbral: {threshold}")
        print(f"   - Intervalo: {interval} minutos")
    except ValueError as e:
        print(f"❌ Error: {e}")
    print()
    
    print("=" * 70)
    print("✅ Todos los ejemplos ejecutados correctamente")
    print("📚 Revisa el código fuente para ver más ejemplos de uso")
    print("=" * 70)


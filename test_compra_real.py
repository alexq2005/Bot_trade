"""
Script de prueba para ejecutar una compra real en IOL
"""
import os
import sys
from pathlib import Path
from datetime import datetime, time

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Agregar el directorio al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Configurar TensorFlow para suprimir mensajes
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

print("="*70)
print("PRUEBA DE COMPRA REAL EN IOL")
print("="*70)
print()

# 1. Verificar horario
print("1️⃣ VERIFICANDO HORARIO DE TRADING")
print("-"*70)
now = datetime.now()
current_time = now.time()
trading_start = time(11, 0)
trading_end = time(17, 0)

print(f"   Hora actual: {current_time.strftime('%H:%M:%S')}")
print(f"   Horario IOL: {trading_start.strftime('%H:%M')} - {trading_end.strftime('%H:%M')}")

force_execution = '--force' in sys.argv or '-f' in sys.argv

if current_time < trading_start:
    print(f"   ❌ ANTES del horario de trading")
    print(f"   ⏰ Espera hasta las {trading_start.strftime('%H:%M')}")
    if not force_execution:
        print(f"   💡 Usa --force para intentar de todas formas (puede fallar)")
        sys.exit(1)
    else:
        print(f"   ⚠️  FORZANDO ejecución fuera del horario...")
elif current_time > trading_end:
    print(f"   ❌ DESPUÉS del horario de trading")
    print(f"   ⏰ El mercado cerró a las {trading_end.strftime('%H:%M')}")
    print(f"   💡 IOL solo opera de 11:00 a 17:00")
    if not force_execution:
        print(f"   💡 Usa --force para intentar de todas formas (puede fallar)")
        sys.exit(1)
    else:
        print(f"   ⚠️  FORZANDO ejecución fuera del horario...")
        print(f"   ⚠️  ADVERTENCIA: IOL probablemente rechazará la orden")
else:
    print(f"   ✅ Dentro del horario de trading")
    
    # Verificar primeros/últimos minutos
    avoid_first = 15
    avoid_last = 15
    
    minutes_since_open = (current_time.hour - trading_start.hour) * 60 + (current_time.minute - trading_start.minute)
    minutes_to_close = (trading_end.hour - current_time.hour) * 60 + (trading_end.minute - current_time.minute)
    
    if minutes_since_open < avoid_first:
        print(f"   ⚠️  Primeros {avoid_first} minutos - Alta volatilidad")
        print(f"   ⏰ Espera {avoid_first - minutes_since_open} minutos más")
    elif minutes_to_close < avoid_last:
        print(f"   ⚠️  Últimos {avoid_last} minutos - Cierre de mercado")
        print(f"   ⏰ Solo quedan {minutes_to_close} minutos")
    else:
        print(f"   ✅ Horario válido para operar")

print()

# 2. Conectar a IOL
print("2️⃣ CONECTANDO A IOL")
print("-"*70)
try:
    from src.connectors.iol_client import IOLClient
    
    iol_client = IOLClient()
    print(f"   ✅ Conectado a IOL como: {iol_client.username}")
    
    # Obtener saldo
    available_balance = iol_client.get_available_balance()
    print(f"   💰 Saldo disponible: ${available_balance:,.2f} ARS")
    
    if available_balance < 1000:
        print(f"   ⚠️  Saldo bajo - Se recomienda al menos $1,000 para operar")
    
except Exception as e:
    print(f"   ❌ Error conectando a IOL: {e}")
    sys.exit(1)

print()

# 3. Seleccionar símbolo
print("3️⃣ SELECCIONAR SÍMBOLO")
print("-"*70)

# Símbolos comunes en IOL
common_symbols = ['GGAL', 'YPFD', 'PAMP', 'LOMA', 'KO', 'AAPL', 'MSFT']

print("   Símbolos disponibles para prueba:")
for i, sym in enumerate(common_symbols, 1):
    print(f"      {i}. {sym}")

# Si se pasa como argumento, usarlo (ignorar --force)
args_symbols = [arg for arg in sys.argv[1:] if arg not in ['--force', '-f']]
if args_symbols:
    symbol = args_symbols[0].upper()
    print(f"\n   📌 Símbolo seleccionado desde argumento: {symbol}")
else:
    # Pedir al usuario
    print(f"\n   💡 Ejecuta: python test_compra_real.py <SIMBOLO>")
    print(f"   Ejemplo: python test_compra_real.py GGAL")
    print(f"\n   O ingresa el símbolo ahora:")
    symbol = input("   Símbolo: ").strip().upper()
    
    if not symbol:
        print("   ❌ No se ingresó símbolo")
        sys.exit(1)

print(f"   ✅ Símbolo: {symbol}")

# Verificar disponibilidad
print(f"\n   🔍 Verificando disponibilidad en IOL...")
try:
    from src.services.iol_availability_checker import IOLAvailabilityChecker
    availability_checker = IOLAvailabilityChecker(iol_client)
    is_available, error_msg = availability_checker.is_symbol_available(symbol)
    
    if not is_available:
        print(f"   ❌ Símbolo no disponible: {error_msg}")
        sys.exit(1)
    else:
        print(f"   ✅ Símbolo disponible en IOL")
except Exception as e:
    print(f"   ⚠️  No se pudo verificar disponibilidad: {e}")
    print(f"   💡 Continuando de todas formas...")

print()

# 4. Obtener cotización
print("4️⃣ OBTENIENDO COTIZACIÓN")
print("-"*70)
try:
    quote = iol_client.get_quote(symbol)
    if 'error' in quote:
        print(f"   ❌ Error obteniendo cotización: {quote['error']}")
        sys.exit(1)
    
    current_price = quote.get('price', 0)
    print(f"   💵 Precio actual: ${current_price:,.2f}")
    print(f"   📊 Cambio: {quote.get('change_percent', 0):+.2f}%")
    
    if current_price <= 0:
        print(f"   ❌ Precio inválido")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ Error obteniendo cotización: {e}")
    sys.exit(1)

print()

# 5. Calcular cantidad
print("5️⃣ CALCULANDO CANTIDAD")
print("-"*70)

# Calcular cantidad basada en un monto fijo (ej: $5,000 ARS)
monto_compra = 5000.0  # Monto fijo para la prueba

# Buscar monto en argumentos (después del símbolo, ignorar --force)
if len(args_symbols) > 1:
    try:
        monto_compra = float(args_symbols[1])
    except:
        pass

quantity = int(monto_compra / current_price)
order_value = quantity * current_price

print(f"   💰 Monto de compra: ${monto_compra:,.2f} ARS")
print(f"   📦 Cantidad calculada: {quantity} acciones")
print(f"   💵 Valor de la orden: ${order_value:,.2f} ARS")

if order_value > available_balance:
    print(f"   ❌ Fondos insuficientes")
    print(f"   💡 Necesitas ${order_value - available_balance:,.2f} más")
    sys.exit(1)
else:
    remaining = available_balance - order_value
    print(f"   ✅ Fondos suficientes")
    print(f"   💵 Saldo restante: ${remaining:,.2f} ARS")

print()

# 6. Confirmación
print("6️⃣ CONFIRMACIÓN")
print("-"*70)
print(f"   📋 RESUMEN DE LA ORDEN:")
print(f"      • Símbolo: {symbol}")
print(f"      • Cantidad: {quantity} acciones")
print(f"      • Precio: ${current_price:,.2f}")
print(f"      • Valor total: ${order_value:,.2f} ARS")
print(f"      • Modo: LIVE (dinero real)")
print()
print(f"   ⚠️  ADVERTENCIA: Esta es una orden REAL con dinero REAL")
print(f"   💡 Esta orden se ejecutará en tu cuenta de IOL")
print()

confirm = input("   ¿Confirmas la compra? (escribe 'SI' para confirmar): ").strip().upper()

if confirm != 'SI':
    print("   ❌ Compra cancelada por el usuario")
    sys.exit(0)

print()

# 7. Ejecutar orden
print("7️⃣ EJECUTANDO ORDEN DE COMPRA")
print("-"*70)
print(f"   🚀 Enviando orden a IOL...")

try:
    # Usar precio de mercado (market order) o precio límite
    # Para prueba, usar precio límite ligeramente por encima del actual
    limit_price = current_price * 1.01  # 1% por encima para asegurar ejecución
    
    result = iol_client.place_order(
        symbol=symbol,
        quantity=quantity,
        price=limit_price,
        side='buy',
        market=None  # Auto-detect
    )
    
    if 'error' in result:
        print(f"   ❌ Error ejecutando orden: {result['error']}")
        if 'status_code' in result:
            print(f"   📊 Código de estado: {result['status_code']}")
        sys.exit(1)
    elif 'numeroOperacion' in result or result.get('success'):
        operation_id = result.get('numeroOperacion', 'N/A')
        print(f"   ✅ ORDEN EJECUTADA EXITOSAMENTE")
        print(f"   📋 Número de operación: {operation_id}")
        print(f"   💰 Valor: ${order_value:,.2f} ARS")
        print(f"   📦 Cantidad: {quantity} acciones de {symbol}")
        print(f"   💵 Precio: ${limit_price:,.2f}")
        print()
        print(f"   ✅ La orden ha sido enviada a IOL")
        print(f"   💡 Verifica en tu cuenta de IOL para confirmar")
    else:
        print(f"   ⚠️  Respuesta inesperada de IOL:")
        print(f"   {result}")
        
except Exception as e:
    print(f"   ❌ Error ejecutando orden: {e}")
    import traceback
    print(f"\n   📋 Detalles del error:")
    traceback.print_exc()
    sys.exit(1)

print()
print("="*70)
print("✅ PRUEBA COMPLETADA")
print("="*70)


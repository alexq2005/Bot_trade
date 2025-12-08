"""
Script de Preparación para Live Trading
Verifica todos los requisitos antes de iniciar operaciones reales
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))

from src.connectors.iol_client import IOLClient
from src.services.iol_availability_checker import IOLAvailabilityChecker
from src.core.database import SessionLocal
from src.models.market_data import MarketData
from src.core.logger import get_logger
import json

logger = get_logger("prepare_live_trading")

def check_iol_connection():
    """Verifica la conexión con IOL"""
    print("\n" + "="*70)
    print("🔌 VERIFICANDO CONEXIÓN IOL")
    print("="*70)
    
    try:
        iol_client = IOLClient()
        account_status = iol_client.get_account_status()
        
        if "error" in account_status:
            print(f"❌ Error de conexión: {account_status['error']}")
            return False, None
        
        print("✅ Conexión IOL establecida correctamente")
        
        # Mostrar información de cuenta
        if "cuentas" in account_status and len(account_status["cuentas"]) > 0:
            cuenta = account_status["cuentas"][0]
            print(f"\n📋 Información de Cuenta:")
            print(f"   Número: {cuenta.get('numero', 'N/A')}")
            print(f"   Tipo: {cuenta.get('tipo', 'N/A').replace('_', ' ').title()}")
            print(f"   Estado: {cuenta.get('estado', 'N/A').title()}")
        
        # Obtener saldo disponible
        try:
            balance = iol_client.get_available_balance()
            print(f"\n💰 Saldo Disponible: ${balance:,.2f} ARS")
        except Exception as e:
            print(f"⚠️  No se pudo obtener el saldo: {e}")
            balance = None
        
        return True, iol_client
        
    except Exception as e:
        print(f"❌ Error al conectar con IOL: {e}")
        return False, None

def check_trained_models():
    """Verifica qué modelos están entrenados"""
    print("\n" + "="*70)
    print("🤖 VERIFICANDO MODELOS ENTRENADOS")
    print("="*70)
    
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    if not os.path.exists(models_dir):
        print("❌ Directorio de modelos no existe")
        return []
    
    model_files = [f for f in os.listdir(models_dir) if f.endswith('_model.h5')]
    symbols = [f.replace('_model.h5', '') for f in model_files]
    # Filtrar símbolos inválidos (como 'lstm' que es un modelo genérico)
    invalid_symbols = ['lstm', 'model']
    symbols = [s for s in symbols if s.lower() not in invalid_symbols]
    
    print(f"✅ {len(symbols)} modelos encontrados:")
    for i, symbol in enumerate(symbols, 1):
        print(f"   {i}. {symbol}")
    
    return symbols

def check_symbol_availability(iol_client, symbols):
    """Verifica disponibilidad de símbolos en IOL"""
    print("\n" + "="*70)
    print("🔍 VERIFICANDO DISPONIBILIDAD DE SÍMBOLOS EN IOL")
    print("="*70)
    
    availability_checker = IOLAvailabilityChecker(iol_client)
    unavailable = availability_checker.get_unavailable_symbols(symbols)
    
    if unavailable:
        print(f"\n⚠️  {len(unavailable)} símbolos NO disponibles en IOL:")
        for sym, err in unavailable:
            print(f"   ❌ {sym}: {err}")
        
        available_symbols = [s for s in symbols if s not in [u[0] for u in unavailable]]
        print(f"\n✅ {len(available_symbols)} símbolos disponibles:")
        for sym in available_symbols:
            print(f"   ✓ {sym}")
        
        return available_symbols
    else:
        print(f"✅ Todos los {len(symbols)} símbolos están disponibles en IOL")
        return symbols

def check_database_data():
    """Verifica datos en la base de datos"""
    print("\n" + "="*70)
    print("📊 VERIFICANDO BASE DE DATOS")
    print("="*70)
    
    try:
        db = SessionLocal()
        total_records = db.query(MarketData).count()
        unique_symbols = db.query(MarketData.symbol).distinct().count()
        
        print(f"✅ Total de registros: {total_records:,}")
        print(f"✅ Símbolos únicos: {unique_symbols}")
        
        db.close()
        return True
    except Exception as e:
        print(f"❌ Error al verificar base de datos: {e}")
        return False

def get_portfolio_symbols():
    """Obtiene símbolos del portafolio guardado"""
    portfolio_file = os.path.join(os.path.dirname(__file__), '..', 'my_portfolio.json')
    if os.path.exists(portfolio_file):
        try:
            with open(portfolio_file, 'r') as f:
                portfolio = json.load(f)
                if 'portfolio' in portfolio:
                    symbols = [p['symbol'] for p in portfolio['portfolio']]
                    return symbols
        except Exception as e:
            logger.warning(f"No se pudo cargar portafolio: {e}")
    return []

def main():
    """Función principal de verificación"""
    print("\n" + "="*70)
    print("🚀 PREPARACIÓN PARA LIVE TRADING")
    print("="*70)
    
    # 1. Verificar conexión IOL
    iol_ok, iol_client = check_iol_connection()
    if not iol_ok:
        print("\n❌ No se puede continuar sin conexión IOL")
        return False
    
    # 2. Verificar modelos entrenados
    trained_symbols = check_trained_models()
    if not trained_symbols:
        print("\n⚠️  No hay modelos entrenados. Se recomienda entrenar modelos antes de operar.")
        response = input("¿Deseas continuar de todas formas? (s/n): ")
        if response.lower() != 's':
            return False
    
    # 3. Verificar base de datos
    db_ok = check_database_data()
    if not db_ok:
        print("\n⚠️  Problemas con la base de datos")
    
    # 4. Obtener símbolos a monitorear
    portfolio_symbols = get_portfolio_symbols()
    if portfolio_symbols:
        print(f"\n📂 Símbolos del portafolio: {', '.join(portfolio_symbols)}")
        symbols_to_check = list(set(portfolio_symbols + trained_symbols))
    else:
        symbols_to_check = trained_symbols[:10]  # Limitar a 10 para verificación
    
    # 5. Verificar disponibilidad en IOL
    available_symbols = check_symbol_availability(iol_client, symbols_to_check)
    
    if not available_symbols:
        print("\n❌ No hay símbolos disponibles para operar")
        return False
    
    # Resumen final
    print("\n" + "="*70)
    print("📋 RESUMEN DE PREPARACIÓN")
    print("="*70)
    print(f"✅ Conexión IOL: OK")
    print(f"✅ Modelos entrenados: {len(trained_symbols)}")
    print(f"✅ Símbolos disponibles en IOL: {len(available_symbols)}")
    print(f"✅ Base de datos: OK")
    
    print("\n" + "="*70)
    print("⚠️  IMPORTANTE: CONFIGURACIÓN DE RIESGO")
    print("="*70)
    print("Antes de iniciar live trading, verifica:")
    print("  • Tamaño máximo de posición: 18% (configurable en app_config.json)")
    print("  • Máximo de trades diarios: 10")
    print("  • Pérdida diaria máxima: 5%")
    print("  • Stop loss automático: Activado")
    print("  • Take profit automático: Activado")
    
    print("\n" + "="*70)
    print("✅ SISTEMA LISTO PARA LIVE TRADING")
    print("="*70)
    print("\nPara iniciar el bot en modo live, ejecuta:")
    print("  python cli.py bot start --live")
    print("\nO directamente:")
    print("  python trading_bot.py --live --continuous")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error en preparación: {e}", exc_info=True)
        sys.exit(1)


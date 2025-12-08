"""
Script para Iniciar Live Trading
Inicia el bot en modo live con todas las verificaciones y confirmaciones
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from trading_bot import TradingBot
from src.connectors.iol_client import IOLClient
from src.core.logger import get_logger
import json

logger = get_logger("start_live_trading")

def confirm_live_trading():
    """Solicita confirmación explícita para live trading"""
    print("\n" + "="*70)
    print("⚠️  ADVERTENCIA: LIVE TRADING MODE")
    print("="*70)
    print("Estás a punto de iniciar el bot en modo LIVE TRADING.")
    print("Esto significa que se realizarán operaciones REALES con dinero REAL.")
    print("\nRiesgos:")
    print("  • Puedes perder dinero")
    print("  • Las operaciones son irreversibles")
    print("  • El bot operará automáticamente según sus señales")
    print("\nProtecciones activas:")
    print("  • Stop loss automático")
    print("  • Take profit automático")
    print("  • Límite de posición: 18% del capital")
    print("  • Máximo 10 trades por día")
    print("  • Pérdida diaria máxima: 5%")
    
    print("\n" + "="*70)
    response = input("¿Estás SEGURO que deseas continuar? (escribe 'SI' para confirmar): ")
    
    if response != 'SI':
        print("\n❌ Operación cancelada. El bot NO se iniciará.")
        return False
    
    print("\n✅ Confirmación recibida. Iniciando bot en modo LIVE...")
    return True

def get_symbols_from_portfolio():
    """Obtiene símbolos del portafolio"""
    portfolio_file = os.path.join(os.path.dirname(__file__), 'my_portfolio.json')
    if os.path.exists(portfolio_file):
        try:
            with open(portfolio_file, 'r') as f:
                portfolio = json.load(f)
                if 'portfolio' in portfolio:
                    symbols = [p['symbol'] for p in portfolio['portfolio']]
                    # Limpiar símbolos (remover .BA si existe para verificación IOL)
                    clean_symbols = []
                    for s in symbols:
                        if s.endswith('.BA'):
                            clean_symbols.append(s.replace('.BA', ''))
                        else:
                            clean_symbols.append(s)
                    return list(set(clean_symbols))  # Remover duplicados
        except Exception as e:
            logger.warning(f"No se pudo cargar portafolio: {e}")
    
    # Fallback: símbolos comunes
    return ['GGAL', 'YPFD', 'PAMP', 'AAPL', 'MSFT', 'GOOGL']

def show_account_info():
    """Muestra información de la cuenta IOL"""
    try:
        iol_client = IOLClient()
        balance = iol_client.get_available_balance()
        account_status = iol_client.get_account_status()
        
        print("\n" + "="*70)
        print("💰 INFORMACIÓN DE CUENTA IOL")
        print("="*70)
        
        if "cuentas" in account_status and len(account_status["cuentas"]) > 0:
            cuenta = account_status["cuentas"][0]
            print(f"Cuenta: {cuenta.get('numero', 'N/A')}")
            print(f"Tipo: {cuenta.get('tipo', 'N/A').replace('_', ' ').title()}")
            print(f"Estado: {cuenta.get('estado', 'N/A').title()}")
        
        print(f"Saldo Disponible: ${balance:,.2f} ARS")
        print(f"Capital máximo por posición (18%): ${balance * 0.18:,.2f} ARS")
        print("="*70 + "\n")
        
        return balance
    except Exception as e:
        logger.error(f"Error obteniendo información de cuenta: {e}")
        return None

def main():
    """Función principal"""
    print("\n" + "="*70)
    print("🚀 INICIADOR DE LIVE TRADING")
    print("="*70)
    
    # 1. Mostrar información de cuenta
    balance = show_account_info()
    if balance is None:
        print("❌ No se pudo obtener información de la cuenta")
        return
    
    if balance < 1000:
        print(f"⚠️  Advertencia: Saldo bajo (${balance:,.2f} ARS)")
        print("Se recomienda tener al menos $1,000 ARS para operar de forma segura.")
        response = input("¿Deseas continuar de todas formas? (s/n): ")
        if response.lower() != 's':
            print("❌ Operación cancelada")
            return
    
    # 2. Confirmación explícita
    if not confirm_live_trading():
        return
    
    # 3. Obtener símbolos
    symbols = get_symbols_from_portfolio()
    print(f"\n📊 Símbolos a monitorear: {', '.join(symbols[:10])}{'...' if len(symbols) > 10 else ''}")
    
    # 4. Inicializar bot en modo LIVE
    print("\n" + "="*70)
    print("🤖 INICIALIZANDO BOT EN MODO LIVE")
    print("="*70 + "\n")
    
    try:
        bot = TradingBot(
            symbols=symbols,
            initial_capital=None,  # Se obtendrá de IOL
            paper_trading=False  # MODO LIVE
        )
        
        print("\n" + "="*70)
        print("✅ BOT INICIADO EN MODO LIVE TRADING")
        print("="*70)
        print("\nEl bot está ahora operando con dinero REAL.")
        print("Presiona Ctrl+C para detener el bot en cualquier momento.\n")
        
        # Ejecutar ciclo continuo
        try:
            # Primero ejecutar un ciclo de análisis
            print("🔄 Ejecutando primer ciclo de análisis...\n")
            bot.run_analysis_cycle()
            
            # Luego continuar en modo continuo
            print("\n🔄 Iniciando modo continuo (revisión cada 60 minutos)...\n")
            bot.run_continuous(interval_minutes=60)  # Revisar cada hora
        except KeyboardInterrupt:
            print("\n\n🛑 Bot detenido por el usuario")
            print("✅ Todas las operaciones pendientes se completarán normalmente")
        
    except Exception as e:
        logger.error(f"Error iniciando bot: {e}", exc_info=True)
        print(f"\n❌ Error al iniciar el bot: {e}")
        print("Verifica los logs para más detalles.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


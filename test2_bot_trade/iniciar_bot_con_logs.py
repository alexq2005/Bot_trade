"""
Script para iniciar el bot con logging detallado y captura de errores
"""
import sys
import os
import traceback
from pathlib import Path
from datetime import datetime

# Configurar logging detallado
log_file = Path("data/bot_startup.log")
log_file.parent.mkdir(parents=True, exist_ok=True)

def log_message(message):
    """Escribe mensaje tanto a consola como a archivo"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    print(message)
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    except:
        pass

def main():
    """Inicia el bot con manejo robusto de errores"""
    
    log_message("="*70)
    log_message("🚀 INICIANDO BOT AUTÓNOMO")
    log_message("="*70)
    log_message(f"Directorio de trabajo: {os.getcwd()}")
    log_message(f"Python: {sys.version}")
    log_message("")
    
    try:
        # Cambiar al directorio del script
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        log_message(f"📁 Cambiado a directorio: {script_dir}")
        
        # Verificar archivos necesarios
        required_files = ['trading_bot.py', 'professional_config.json']
        for file in required_files:
            if not Path(file).exists():
                log_message(f"❌ Archivo requerido no encontrado: {file}")
                return 1
            else:
                log_message(f"✅ Archivo encontrado: {file}")
        
        log_message("")
        
        # Importar y ejecutar bot
        log_message("📦 Importando módulos...")
        import argparse
        from trading_bot import TradingBot
        
        parser = argparse.ArgumentParser(description='IOL Quantum AI Trading Bot')
        parser.add_argument('--continuous', action='store_true', help='Run in continuous mode')
        parser.add_argument('--interval', type=int, default=60, help='Interval in minutes')
        parser.add_argument('--live', action='store_true', help='Enable LIVE trading with real money')
        args = parser.parse_args()
        
        log_message(f"⚙️  Argumentos: continuous={args.continuous}, interval={args.interval}, live={args.live}")
        log_message("")
        
        # Cargar configuración
        log_message("📋 Cargando configuración...")
        import json
        config_file = Path("professional_config.json")
        use_full_universe = False
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    use_full_universe = config.get('monitoring', {}).get('use_full_universe', False)
                log_message(f"✅ Configuración cargada. Universo completo: {use_full_universe}")
            except Exception as e:
                log_message(f"⚠️  Error cargando configuración: {e}")
        else:
            log_message("⚠️  professional_config.json no encontrado")
        
        log_message("")
        
        # Determinar símbolos
        if use_full_universe:
            log_message("🌍 Modo Universo Completo detectado en configuración")
            symbols_param = None
        else:
            default_symbols = ['AAPL', 'MSFT', 'GOOGL'] if not args.live else ['GGAL', 'PAMP', 'YPFD']
            symbols_param = default_symbols
            log_message(f"📊 Usando símbolos por defecto: {', '.join(symbols_param)}")
        
        log_message("")
        log_message("🤖 Inicializando TradingBot...")
        
        # Inicializar bot con manejo de errores detallado
        try:
            bot = TradingBot(
                symbols=symbols_param,
                initial_capital=None,
                paper_trading=not args.live
            )
            log_message("✅ TradingBot inicializado correctamente")
            
            # Verificar símbolos
            if hasattr(bot, 'symbols') and bot.symbols:
                log_message(f"✅ Símbolos cargados: {len(bot.symbols)} símbolos")
                log_message(f"   Primeros 10: {', '.join(bot.symbols[:10])}")
            else:
                log_message("⚠️  No se cargaron símbolos. Usando fallback...")
                default_fallback = ['GGAL', 'YPFD', 'PAMP'] if args.live else ['AAPL', 'MSFT', 'GOOGL']
                bot.symbols = default_fallback
                log_message(f"📌 Símbolos de fallback: {', '.join(bot.symbols)}")
            
            log_message("")
            log_message("="*70)
            log_message("✅ BOT INICIALIZADO CORRECTAMENTE")
            log_message("="*70)
            log_message("")
            
            # Ejecutar bot
            if args.continuous:
                log_message(f"🔄 Iniciando modo continuo (intervalo: {args.interval} minutos)")
                log_message("")
                bot.run_continuous(interval_minutes=args.interval)
            else:
                log_message("🔄 Ejecutando ciclo único de análisis")
                log_message("")
                bot.run_analysis_cycle()
                
        except KeyboardInterrupt:
            log_message("\n\n🛑 Bot detenido por el usuario")
            return 0
        except Exception as e:
            log_message(f"\n\n❌ ERROR CRÍTICO durante inicialización:")
            log_message(f"   Tipo: {type(e).__name__}")
            log_message(f"   Mensaje: {str(e)}")
            log_message(f"\n📋 Traceback completo:")
            traceback_str = traceback.format_exc()
            log_message(traceback_str)
            
            print("\n" + "="*70)
            print("❌ ERROR CRÍTICO")
            print("="*70)
            print(f"Tipo: {type(e).__name__}")
            print(f"Mensaje: {str(e)}")
            print(f"\n📋 Ver detalles completos en: {log_file}")
            print("="*70)
            
            if sys.platform == 'win32':
                try:
                    input("\n⚠️  Presiona Enter para cerrar esta ventana...")
                except:
                    pass
            return 1
            
    except Exception as e:
        log_message(f"\n\n❌ ERROR FATAL: {e}")
        traceback_str = traceback.format_exc()
        log_message(traceback_str)
        print(f"\n❌ ERROR FATAL: {e}")
        print(f"📋 Ver detalles en: {log_file}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


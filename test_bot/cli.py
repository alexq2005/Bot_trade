"""
CLI Principal del Proyecto
Interfaz de línea de comandos para gestionar el sistema de trading
"""
import argparse
import sys
from pathlib import Path

# Configurar path
sys.path.append(str(Path(__file__).parent))

from src.core.console_utils import setup_windows_console
from src.core.logger import setup_logging, get_logger
from src.core.config_manager import get_config, set_config, save_config
from src.core.health_check import get_health_status

setup_windows_console()
logger = setup_logging()


class TradingBotCLI:
    """CLI principal para gestionar el bot de trading"""
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='🚀 IOL Quantum AI Trading Bot - CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos de uso:
  python cli.py health                    # Verificar estado del sistema
  python cli.py config show               # Mostrar configuración
  python cli.py config set app.debug true  # Establecer configuración
  python cli.py bot start                 # Iniciar bot en modo paper trading
  python cli.py bot start --live          # Iniciar bot en modo live
  python cli.py train --symbol AAPL      # Entrenar modelo para AAPL
  python cli.py dashboard                 # Iniciar dashboard
            """
        )
        
        self.subparsers = self.parser.add_subparsers(dest='command', help='Comandos disponibles')
        self._setup_commands()
    
    def _setup_commands(self):
        """Configura todos los comandos"""
        
        # Comando: health
        health_parser = self.subparsers.add_parser('health', help='Verificar estado del sistema')
        health_parser.add_argument('--json', action='store_true', help='Salida en formato JSON')
        
        # Comando: config
        config_parser = self.subparsers.add_parser('config', help='Gestionar configuración')
        config_subparsers = config_parser.add_subparsers(dest='config_action')
        
        config_subparsers.add_parser('show', help='Mostrar configuración actual')
        config_subparsers.add_parser('reload', help='Recargar configuración desde archivos')
        
        config_set = config_subparsers.add_parser('set', help='Establecer valor de configuración')
        config_set.add_argument('key', help='Clave de configuración (ej: app.debug)')
        config_set.add_argument('value', help='Valor a establecer')
        
        # Comando: bot
        bot_parser = self.subparsers.add_parser('bot', help='Gestionar bot de trading')
        bot_subparsers = bot_parser.add_subparsers(dest='bot_action')
        
        bot_subparsers.add_parser('start', help='Iniciar bot').add_argument(
            '--live', action='store_true', help='Modo live trading (peligroso)'
        )
        bot_subparsers.add_parser('stop', help='Detener bot')
        bot_subparsers.add_parser('status', help='Estado del bot')
        
        # Comando: train
        train_parser = self.subparsers.add_parser('train', help='Entrenar modelos')
        train_parser.add_argument('--symbol', help='Símbolo a entrenar (ej: AAPL)')
        train_parser.add_argument('--epochs', type=int, default=30, help='Número de épocas')
        train_parser.add_argument('--all', action='store_true', help='Entrenar todos los símbolos')
        
        # Comando: dashboard
        self.subparsers.add_parser('dashboard', help='Iniciar dashboard web')
        
        # Comando: test
        test_parser = self.subparsers.add_parser('test', help='Ejecutar pruebas')
        test_parser.add_argument('--extreme', action='store_true', help='Pruebas extremas')
        test_parser.add_argument('--full', action='store_true', help='Modo completo')
        
        # Comando: data
        data_parser = self.subparsers.add_parser('data', help='Gestionar datos')
        data_subparsers = data_parser.add_subparsers(dest='data_action')
        data_subparsers.add_parser('ingest', help='Ingerir datos históricos')
        data_subparsers.add_parser('update', help='Actualizar datos')
        data_subparsers.add_parser('verify', help='Verificar integridad de datos')
    
    def run(self, args=None):
        """Ejecuta el CLI"""
        args = self.parser.parse_args(args)
        
        if not args.command:
            self.parser.print_help()
            return
        
        try:
            if args.command == 'health':
                self._cmd_health(args)
            elif args.command == 'config':
                self._cmd_config(args)
            elif args.command == 'bot':
                self._cmd_bot(args)
            elif args.command == 'train':
                self._cmd_train(args)
            elif args.command == 'dashboard':
                self._cmd_dashboard()
            elif args.command == 'test':
                self._cmd_test(args)
            elif args.command == 'data':
                self._cmd_data(args)
        except KeyboardInterrupt:
            logger.info("Operación cancelada por el usuario")
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}", exc_info=True)
            sys.exit(1)
    
    def _cmd_health(self, args):
        """Comando: health"""
        from src.core.console_utils import safe_print
        
        health = get_health_status()
        
        if args.json:
            import json
            print(json.dumps(health, indent=2))
            return
        
        # Mostrar resultados con formato visual
        status_colors = {
            'healthy': '✅',
            'degraded': '⚠️',
            'unhealthy': '❌',
            'warning': '⚠️',
            'critical': '🔴'
        }
        
        safe_print(f"\n{'='*70}")
        safe_print(f"🏥 Health Check - {health['timestamp']}")
        safe_print(f"{'='*70}\n")
        
        overall_icon = status_colors.get(health['overall_status'], '❓')
        safe_print(f"{overall_icon} Estado General: {health['overall_status'].upper()}\n")
        
        safe_print("Componentes:")
        for name, check in health['checks'].items():
            icon = status_colors.get(check['status'], '❓')
            safe_print(f"  {icon} {name.replace('_', ' ').title()}: {check['message']}")
        
        safe_print(f"\nResumen: {health['summary']['healthy']} saludables, "
                  f"{health['summary']['degraded']} degradados, "
                  f"{health['summary']['unhealthy']} no saludables")
        safe_print(f"{'='*70}\n")
    
    def _cmd_config(self, args):
        """Comando: config"""
        if args.config_action == 'show':
            import json
            config = get_config()
            print(json.dumps(config, indent=2, default=str))
        
        elif args.config_action == 'reload':
            from src.core.config_manager import _config_manager
            _config_manager.reload()
            logger.info("Configuración recargada")
        
        elif args.config_action == 'set':
            # Convertir valor a tipo apropiado
            value = args.value
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            elif value.replace('.', '', 1).isdigit():
                value = float(value)
            
            set_config(args.key, value)
            save_config()
            logger.info(f"Configuración actualizada: {args.key} = {value}")
    
    def _cmd_bot(self, args):
        """Comando: bot"""
        if args.bot_action == 'start':
            from trading_bot import TradingBot
            
            paper_trading = not args.live
            if args.live:
                logger.warning("⚠️  INICIANDO EN MODO LIVE TRADING - DINERO REAL")
                response = input("¿Estás seguro? (escribe 'SI' para confirmar): ")
                if response != 'SI':
                    logger.info("Operación cancelada")
                    return
            
            bot = TradingBot(paper_trading=paper_trading)
            logger.info("Bot iniciado. Presiona Ctrl+C para detener.")
            try:
                bot.run()
            except KeyboardInterrupt:
                logger.info("Bot detenido")
        
        elif args.bot_action == 'stop':
            # Implementar detención del bot
            logger.info("Deteniendo bot...")
            # TODO: Implementar detención de proceso
        
        elif args.bot_action == 'status':
            # Verificar si el bot está corriendo
            pid_file = Path("bot.pid")
            if pid_file.exists():
                logger.info("Bot está corriendo")
            else:
                logger.info("Bot no está corriendo")
    
    def _cmd_train(self, args):
        """Comando: train"""
        if args.all:
            from scripts.retrain_all_models import retrain_all_models
            retrain_all_models()
        elif args.symbol:
            import subprocess
            cmd = ['python', 'scripts/train_model.py', '--symbol', args.symbol, '--epochs', str(args.epochs)]
            subprocess.run(cmd)
        else:
            logger.error("Especifica --symbol o --all")
    
    def _cmd_dashboard(self):
        """Comando: dashboard"""
        import subprocess
        logger.info("Iniciando dashboard en http://localhost:8501")
        subprocess.run(['streamlit', 'run', 'dashboard.py'])
    
    def _cmd_test(self, args):
        """Comando: test"""
        if args.extreme:
            import subprocess
            cmd = ['python', 'test_extreme_bot.py']
            if args.full:
                cmd.append('--full')
            subprocess.run(cmd)
        else:
            logger.info("Ejecutando pruebas básicas...")
            # TODO: Implementar suite de pruebas básicas
    
    def _cmd_data(self, args):
        """Comando: data"""
        if args.data_action == 'ingest':
            from scripts.ingest_data import main
            main()
        elif args.data_action == 'update':
            logger.info("Actualizando datos...")
            # TODO: Implementar actualización de datos
        elif args.data_action == 'verify':
            from scripts.verify_db import main
            main()


def main():
    """Punto de entrada principal"""
    cli = TradingBotCLI()
    cli.run()


if __name__ == '__main__':
    main()


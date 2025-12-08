"""
IOL Quantum AI Trading Bot - Main Integration
Sistema de trading autónomo con gestión de riesgo adaptativa
"""
import sys
import os
from pathlib import Path
import numpy as np

# Configurar TensorFlow para suprimir mensajes antes de cualquier import
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Solo errores
import warnings
warnings.filterwarnings('ignore')

# Cargar variables de entorno desde .env ANTES de cualquier otra importación
try:
    from dotenv import load_dotenv
    # Cargar .env desde el directorio del proyecto
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Intentar cargar desde el directorio actual
        load_dotenv()
except ImportError:
    # Si python-dotenv no está instalado, intentar cargar manualmente
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import time
import threading
import json
from datetime import datetime, timedelta
from typing import Dict
from src.services.prediction_service import PredictionService
from src.services.technical_analysis import TechnicalAnalysisService
from src.services.portfolio_optimizer import PortfolioOptimizer
from src.services.alert_system import AlertSystem
from src.services.adaptive_risk_manager import AdaptiveRiskManager
from src.services.portfolio_persistence import sync_from_iol, load_portfolio
from src.core.logger import get_logger
from src.core.safe_logger import safe_log, safe_info, safe_error, safe_warning
from src.core.safe_print import safe_print as _safe_print
from src.services.continuous_learning import ContinuousLearning
from src.connectors.iol_client import IOLClient
from src.services.telegram_bot import TelegramAlertBot
from src.services.professional_trader import ProfessionalTrader
from src.services.advanced_learning import AdvancedLearningSystem

# Reemplazar print con safe_print para evitar errores de I/O
import builtins
_original_print = builtins.print
def safe_print(*args, **kwargs):
    try:
        _original_print(*args, **kwargs)
    except (ValueError, IOError, OSError, AttributeError):
        try:
            kwargs['file'] = sys.stderr
            _original_print(*args, **kwargs)
        except:
            pass
builtins.print = safe_print

from src.services.enhanced_learning_system import EnhancedLearningSystem
from src.services.operation_notifier import OperationNotifier
from src.services.realtime_alerts import RealtimeAlertSystem
from src.services.price_monitor import PriceMonitor
from src.services.enhanced_sentiment import EnhancedSentimentAnalysis
from src.services.daily_report_service import DailyReportService
from src.services.commission_calculator import CommissionCalculator
from src.services.candlestick_analyzer import CandlestickAnalyzer
from src.services.correlation_analyzer import CorrelationAnalyzer
from src.services.self_programming_engine import SelfProgrammingEngine
from src.services.reasoning_system import ReasoningSystem
from src.services.chat_interface import ChatInterface
from src.services.advanced_reasoning_agent import AdvancedReasoningAgent
from src.services.web_search_agent import WebSearchAgent
from src.services.unlimited_learning import UnlimitedLearning
from src.services.verified_learning import VerifiedLearning
from src.services.business_implementer import BusinessImplementer

logger = get_logger("trading_bot")

class TradingBot:
    """
    Bot de trading principal integrando todos los sistemas.
    Soporta modo Paper Trading y Live Trading con estrategias profesionales.
    """
    
    def __init__(self, symbols=None, initial_capital=None, paper_trading=True):
        """
        Args:
            symbols: Lista de símbolos a monitorear (opcional)
            initial_capital: Capital inicial (se obtiene de IOL si es None)
            paper_trading: True para simulación, False para dinero real
        """
        # Modo de operación
        self.paper_trading = paper_trading
        self.trades_file = "trades.json"
        
        # Flag para evitar ejecuciones simultáneas de análisis
        self._analysis_running = False
        self._analysis_lock = threading.Lock()
        
        # Control de estado del bot
        self._paused = False  # Para /pause y /resume
        self._silence_until = None  # Para /silence
        self._start_time = datetime.now()  # Para /uptime y /next
        self._last_analysis_time = None  # Para /next
        
        # Estrategia Dinámica (para Optimizador Genético)
        self.strategy_config = {}
        
        # Initialize IOL client
        self.iol_client = IOLClient()
        
        # Obtener capital inicial
        if initial_capital is None and not paper_trading:
            # Obtener saldo real de IOL
            self.capital = self.iol_client.get_available_balance()
            print(f"💰 Saldo obtenido de IOL: ${self.capital:.2f} ARS")
        else:
            self.capital = initial_capital or 100.0
        
        # Initialize services
        self.prediction_service = PredictionService()
        # Pass IOL client for real-time data
        self.technical_service = TechnicalAnalysisService(iol_client=self.iol_client)
        self.portfolio_optimizer = PortfolioOptimizer()
        
        # Initialize data service for historical data (used by advanced strategies)
        try:
            from src.connectors.multi_source_client import MultiSourceDataClient
            # Pasar IOL client para que pueda obtener datos de instrumentos argentinos (ONs, bonos, letras)
            self.data_service = MultiSourceDataClient(iol_client=self.iol_client)
        except Exception as e:
            print(f"⚠️  Error inicializando data_service: {e}")
            self.data_service = None
        
        # Initialize macroeconomic data service (APIs públicas y gratuitas)
        # Inicializar AlertSystem PRIMERO (se usa en otros servicios)
        self.alert_system = AlertSystem()
        
        # Sistema de datos macroeconómicos
        try:
            from src.services.macroeconomic_data_service import MacroeconomicDataService
            from src.services.macroeconomic_alert_service import MacroeconomicAlertService
            self.macroeconomic_service = MacroeconomicDataService()
            self.macroeconomic_alert_service = MacroeconomicAlertService(alert_system=self.alert_system)
            print("✅ Servicio de datos macroeconómicos inicializado (BCRA, MonedAPI, Argentina Gov)")
            print("✅ Servicio de alertas macroeconómicas inicializado")
        except Exception as e:
            print(f"⚠️  Error inicializando macroeconomic_service: {e}")
            self.macroeconomic_service = None
            self.macroeconomic_alert_service = None
        self.telegram_bot = TelegramAlertBot() # Telegram Integration
        
        # Telegram Command Handler (para recibir mensajes)
        from src.services.telegram_command_handler import TelegramCommandHandler
        self.telegram_command_handler = TelegramCommandHandler()
        # Registrar comandos personalizados del bot
        self._register_telegram_commands()
        
        self.risk_manager = AdaptiveRiskManager(initial_capital=self.capital)
        
        # Trailing Stop Loss
        from src.services.trailing_stop_loss import TrailingStopLoss
        self.trailing_stop_loss = TrailingStopLoss(
            iol_client=self.iol_client if not self.paper_trading else None,
            telegram_bot=self.telegram_bot
        )
        print("✅ Trailing Stop Loss inicializado")
        
        # Estrategias de Análisis Avanzadas
        try:
            from src.services.regime_detector import RegimeDetector
            from src.services.multi_timeframe_analyzer import MultiTimeframeAnalyzer
            from src.services.order_flow_analyzer import OrderFlowAnalyzer
            from src.services.seasonal_analyzer import SeasonalAnalyzer
            from src.services.fractal_analyzer import FractalAnalyzer
            from src.services.anomaly_detector import AnomalyDetector
            from src.services.volume_profile_analyzer import VolumeProfileAnalyzer
            from src.services.monte_carlo_simulator import MonteCarloSimulator
            from src.services.pattern_recognizer import PatternRecognizer
            from src.services.pairs_trader import PairsTrader
            from src.services.elliott_wave_analyzer import ElliottWaveAnalyzer
            from src.services.smart_money_analyzer import SmartMoneyAnalyzer
            from src.services.meta_learner import MetaLearner
            
            self.regime_detector = RegimeDetector()
            self.mtf_analyzer = MultiTimeframeAnalyzer()
            self.order_flow_analyzer = OrderFlowAnalyzer(self.iol_client)
            self.seasonal_analyzer = SeasonalAnalyzer()
            self.fractal_analyzer = FractalAnalyzer()
            self.anomaly_detector = AnomalyDetector()
            self.volume_profile = VolumeProfileAnalyzer()
            self.monte_carlo = MonteCarloSimulator()
            self.pattern_recognizer = PatternRecognizer()
            self.pairs_trader = PairsTrader()
            self.elliott_wave = ElliottWaveAnalyzer()
            self.smart_money = SmartMoneyAnalyzer()
            self.meta_learner = MetaLearner()
            
            # --- NUEVO: REDES NEURONALES COMPLETAS (Todas las mejoras implementadas) ---
            from src.services.neural_network_service_complete import NeuralNetworkServiceComplete
            self.neural_network = NeuralNetworkServiceComplete(data_dir=str(Path(self.trades_file).parent / "models"))
            print("🧠 Cerebro de Redes Neuronales COMPLETO inicializado (Ensemble + Multi-Features + Auto-Monitoreo)")
            
            print("✅ 14 Estrategias de análisis avanzadas inicializadas (incluyendo Deep Learning)")
            self.advanced_strategies_enabled = True
        except Exception as e:
            print(f"⚠️  Estrategias avanzadas no disponibles: {e}")
            self.advanced_strategies_enabled = False
        
        # Nuevos servicios de mejora
        try:
            self.commission_calculator = CommissionCalculator()
            self.candlestick_analyzer = CandlestickAnalyzer()
            self.correlation_analyzer = CorrelationAnalyzer()
            print("✅ Servicios de mejora inicializados (Comisiones, Velas, Correlación)")
        except Exception as e:
            print(f"⚠️  Error inicializando servicios de mejora: {e}")
            self.commission_calculator = None
            self.candlestick_analyzer = None
            self.correlation_analyzer = None
        
        # Sistema de Autoprogramación y Razonamiento - SIN LÍMITES
        try:
            bot_dir = Path(__file__).parent
            # Sin límite de cambios por ciclo - el bot puede mejorar sin restricciones
            self.self_programming = SelfProgrammingEngine(
                bot_directory=str(bot_dir),
                max_changes_per_cycle=None  # None = sin límite
            )
            self.reasoning_system = ReasoningSystem(bot_directory=str(bot_dir))
            print("✅ Sistema de Autoprogramación y Razonamiento inicializado")
            print("   🚀 MODO SIN LÍMITES ACTIVADO")
            print("   ⚠️  El bot puede ahora razonar y mejorarse a sí mismo SIN RESTRICCIONES")
            print("   🧠 Aprendizaje autónomo máximo - explorará todas las posibilidades")
        except Exception as e:
            print(f"⚠️  Error inicializando autoprogramación: {e}")
            self.self_programming = None
            self.reasoning_system = None
        
        # Sistema de Chat Interactivo con Razonamiento Espontáneo
        try:
            bot_dir = Path(__file__).parent
            self.chat_interface = ChatInterface(
                bot_directory=str(bot_dir),
                telegram_bot=self.telegram_bot,
                trading_bot=self  # Pasar referencia al bot de trading para retroalimentación
            )
            self.advanced_reasoning = AdvancedReasoningAgent(bot_directory=str(bot_dir))
            self.web_search = WebSearchAgent()
            print("✅ Sistema de Chat Interactivo inicializado")
            print("   💬 Puedes conversar con el bot de forma espontánea")
            print("   🔍 El bot puede buscar información en internet")
            print("   🧠 El bot razona y aprende de las conversaciones")
        except Exception as e:
            print(f"⚠️  Error inicializando chat: {e}")
            self.chat_interface = None
            self.advanced_reasoning = None
            self.web_search = None
        
        # Memoria compartida con el chat
        self.shared_learning_file = Path("data/shared_learning.json")
        self.shared_learning_file.parent.mkdir(parents=True, exist_ok=True)
        
        print("🔍 DEBUG: Después de inicializar shared_learning_file")
        
        # ============================================================
        # CONTINUACIÓN DEL __init__ - CÓDIGO DE CARGA DE SÍMBOLOS
        # ============================================================
        print("🔍 DEBUG: Continuando __init__ - Iniciando carga de símbolos")
        
        # Sistema de Aprendizaje Sin Límites
        try:
            bot_dir = Path(__file__).parent
            self.unlimited_learning = UnlimitedLearning(bot_directory=str(bot_dir))
            print("✅ Sistema de Aprendizaje Sin Límites inicializado")
            print("   🚀 Exploración agresiva activada")
            print("   🧠 Aprende de TODO sin restricciones")
            print("   💡 Genera mejoras ilimitadas")
        except Exception as e:
            print(f"⚠️  Error inicializando aprendizaje sin límites: {e}")
            self.unlimited_learning = None
        
        # Sistema de Aprendizaje Verificado
        try:
            bot_dir = Path(__file__).parent
            self.verified_learning = VerifiedLearning(bot_directory=str(bot_dir))
            print("✅ Sistema de Aprendizaje Verificado inicializado")
            print("   🔍 Verifica automáticamente todo lo que aprende")
            print("   ✅ Solo usa conocimiento verificado como correcto")
            print("   🔄 Corrige conocimiento incorrecto automáticamente")
        except Exception as e:
            print(f"⚠️  Error inicializando aprendizaje verificado: {e}")
            self.verified_learning = None
        
        # Sistema de Implementación de Negocios
        try:
            bot_dir = Path(__file__).parent
            self.business_implementer = BusinessImplementer(bot_directory=str(bot_dir))
            print("✅ Sistema de Implementación de Negocios inicializado")
            print("   💼 Puede identificar oportunidades de negocio")
            print("   📋 Puede crear planes de negocio")
            print("   🚀 Puede implementar negocios para generar ganancias")
        except Exception as e:
            print(f"⚠️  Error inicializando implementador de negocios: {e}")
            self.business_implementer = None
        
        # Asegurar que current_capital también se inicialice con el capital real
        self.risk_manager.current_capital = self.capital
        
        self.continuous_learning = ContinuousLearning()
        # Cargar configuración profesional desde professional_config.json si existe
        config_file = Path("professional_config.json")
        if config_file.exists():
            self.professional_trader = ProfessionalTrader(config_file="professional_config.json")
        else:
            self.professional_trader = ProfessionalTrader()  # Usar default si no existe
        self.advanced_learning = AdvancedLearningSystem()  # NEW: Advanced learning system
        # Inicializar enhanced learning con manejo de errores
        try:
            self.enhanced_learning = EnhancedLearningSystem()  # NEW: Enhanced learning (símbolos, horarios, condiciones)
        except Exception as e:
            try:
                safe_warning(logger, f"No se pudo inicializar EnhancedLearningSystem: {e}")
            except:
                pass
            self.enhanced_learning = None  # Continuar sin este sistema si falla
        self.operation_notifier = OperationNotifier(enable_telegram=True)  # NEW: Operation notifications
        self.realtime_alerts = RealtimeAlertSystem()  # NEW: Real-time alerts
        self.price_monitor = PriceMonitor()  # NEW: Price monitoring
        self.sentiment_analysis = EnhancedSentimentAnalysis()  # NEW: Sentiment analysis
        
        # Inicializar daily_report_service con manejo de errores
        try:
            self.daily_report_service = DailyReportService(telegram_bot=self.telegram_bot)  # NEW: Daily reports
            print("✅ Servicio de reportes diarios inicializado")
        except Exception as e:
            print(f"⚠️  Error inicializando daily_report_service: {e}")
            self.daily_report_service = None
        
        # ACTUALIZACIÓN INMEDIATA DEL SALDO al iniciar (solo en modo LIVE)
        if not self.paper_trading:
            try:
                print("\n" + "="*60)
                print("🔄 Actualizando saldo desde IOL al iniciar...")
                print("="*60)
                old_capital = self.capital
                new_balance = self.iol_client.get_available_balance()
                if new_balance != old_capital:
                    print(f"💰 Saldo actualizado: ${old_capital:,.2f} → ${new_balance:,.2f} ARS")
                else:
                    print(f"💰 Saldo confirmado: ${new_balance:,.2f} ARS")
                
                self.capital = new_balance
                # Actualizar Risk Manager con el saldo real
                self.risk_manager.initial_capital = new_balance
                self.risk_manager.current_capital = new_balance
                print(f"✅ Risk Manager inicializado con capital: ${new_balance:,.2f} ARS")
                print("="*60 + "\n")
            except Exception as e:
                try:
                    safe_warning(logger, f"⚠️  Error actualizando saldo al iniciar: {e}")
                except:
                    pass
                print(f"⚠️  Usando saldo inicial: ${self.capital:,.2f} ARS")
        
        # Inicializar auto_configurator con manejo de errores
        try:
            from src.services.auto_configurator import AutoConfigurator
            self.auto_configurator = AutoConfigurator()  # NEW: Auto-configuration system
            print("✅ Auto-configurador inicializado")
        except Exception as e:
            print(f"⚠️  Error inicializando auto_configurator: {e}")
            self.auto_configurator = None
        
        # ============================================================
        # GESTIÓN DUAL DE PORTAFOLIO: IOL + Tienda Broker o Solo IOL
        # ============================================================
        from src.services.portfolio_persistence import load_portfolio
        
        # Cargar configuración
        import json
        config_file = Path("professional_config.json")
        portfolio_mode = "COMPLETO"  # Default
        
        monitoring_config = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    monitoring_config = config_data.get('monitoring', {})
                    only_iol = monitoring_config.get('only_iol_portfolio', False)
                    portfolio_mode = "SOLO_IOL" if only_iol else "COMPLETO"
            except Exception as e:
                print(f"⚠️  Error leyendo config: {e}")
        
        print(f"\n{'='*60}")
        print(f"📊 MODO DE PORTAFOLIO: {portfolio_mode}")
        print(f"{'='*60}")
        
        print("🔍 DEBUG: ANTES de determinar símbolos")
        print(f"🔍 DEBUG: monitoring_config = {monitoring_config}")
        
        # Determinar símbolos según el modo
        # Si use_full_universe está activo, ignorar símbolos pasados y cargar universo completo
        try:
            use_full_universe = monitoring_config.get('use_full_universe', False)
            print(f"🔍 DEBUG: use_full_universe leído de config = {use_full_universe}")
            print(f"🔍 DEBUG: symbols recibido en constructor = {symbols}")
            print(f"🔍 DEBUG: type(symbols) = {type(symbols)}")
            
            print("🔍 DEBUG: Entrando al bloque de carga de símbolos...")
            if use_full_universe:
                # Forzar carga del universo completo incluso si se pasaron símbolos
                symbols = []
            
            print(f"DEBUG ANTES DEL IF: symbols={symbols}, type={type(symbols)}")
            if symbols is None or len(symbols) == 0:
                symbols = []
                
                # ============================================================
                # MODO UNIVERSO COMPLETO (NUEVO)
                # ============================================================
                print(f"DEBUG: use_full_universe = {use_full_universe}, symbols = {symbols}")
                if use_full_universe:
                    print("\n" + "="*70)
                    print("🌍 MODO UNIVERSO COMPLETO ACTIVADO")
                    print("="*70)
                    print("📊 Cargando TODOS los instrumentos disponibles en IOL...")
                    print("   Esto puede tomar unos minutos...")
                    print()
                    
                    try:
                        from src.services.iol_universe_loader import IOLUniverseLoader
                        
                        max_symbols = monitoring_config.get('max_symbols', 200)
                        categories = monitoring_config.get('universe_categories', ['acciones', 'cedears', 'bonos'])
                        
                        print(f"🔍 Configuración:")
                        print(f"   • Máximo de símbolos: {max_symbols}")
                        print(f"   • Categorías: {', '.join(categories)}")
                        print()
                        
                        loader = IOLUniverseLoader(self.iol_client)
                        universe_symbols = []
                        
                        # Intentar cargar universo completo con múltiples estrategias
                        try:
                            print("   🔄 Estrategia 1: Cargando universo completo...")
                            universe_symbols = loader.get_tradeable_universe(max_symbols=max_symbols, categories=categories)
                            if universe_symbols and len(universe_symbols) > 0:
                                print(f"   ✅ Cargados {len(universe_symbols)} símbolos con get_tradeable_universe")
                            else:
                                print(f"   ⚠️  get_tradeable_universe retornó lista vacía")
                        except Exception as e:
                            print(f"   ⚠️  Error con get_tradeable_universe: {e}")
                            import traceback
                            print(f"   📋 Detalles:")
                            traceback.print_exc()
                            universe_symbols = []
                        
                        # Si falló, intentar cargar por categorías
                        if not universe_symbols or len(universe_symbols) == 0:
                            try:
                                print("   🔄 Estrategia 2: Cargando por categorías...")
                                all_instruments = loader.get_all_instruments(categories=categories)
                                
                                # Combinar símbolos de todas las categorías
                                for cat, cat_symbols in all_instruments.items():
                                    if cat_symbols:
                                        universe_symbols.extend(cat_symbols)
                                        print(f"   ✅ {cat.upper()}: {len(cat_symbols)} símbolos")
                                
                                # Remover duplicados
                                universe_symbols = list(set(universe_symbols))
                                
                                # Limitar cantidad
                                if len(universe_symbols) > max_symbols:
                                    print(f"   ⚠️  Limitando a {max_symbols} símbolos (de {len(universe_symbols)} totales)")
                                    universe_symbols = universe_symbols[:max_symbols]
                                    
                            except Exception as e:
                                print(f"   ⚠️  Error cargando por categorías: {e}")
                                universe_symbols = []
                        
                        # Si aún no hay símbolos, usar fallback con símbolos conocidos
                        if not universe_symbols or len(universe_symbols) == 0:
                            print("   🔄 Estrategia 3: Usando símbolos conocidos como fallback...")
                            fallback_symbols = []
                            
                            # Agregar símbolos conocidos según categorías
                            if 'acciones' in categories:
                                fallback_symbols.extend([
                                    'GGAL', 'YPFD', 'PAMP', 'BMA', 'ALUA', 'LOMA', 'TGNO4', 'TGSU2',
                                    'COME', 'EDN', 'TXAR', 'CRES', 'VALO', 'MIRG', 'BYMA', 'TRAN',
                                    'CVBA', 'BOLT', 'METR', 'CEPU', 'DGCU2', 'HAVA', 'IRSA', 'BHIP'
                                ])
                            
                            if 'cedears' in categories:
                                fallback_symbols.extend([
                                    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                                    'DIS', 'KO', 'PEP', 'WMT', 'JPM', 'BAC', 'V', 'MA', 'PYPL',
                                    'TSM', 'INTC', 'AMD', 'QCOM', 'BA', 'CAT', 'GE', 'IBM'
                                ])
                            
                            if 'bonos' in categories:
                                fallback_symbols.extend([
                                    'GD30', 'GD35', 'GD38', 'GD41', 'GD46',
                                    'AL30', 'AL35', 'AL38', 'AL41', 'AE38'
                                ])
                            
                            if 'obligaciones' in categories:
                                fallback_symbols.extend([
                                    'PAMPY', 'PAMPO', 'TXARY', 'CRCCY', 'IRCP3',
                                    'YPF27', 'TGSU7', 'TGNO6'
                                ])
                            
                            universe_symbols = fallback_symbols[:max_symbols]
                            print(f"   ✅ Usando {len(universe_symbols)} símbolos de fallback")
                        
                        if universe_symbols and len(universe_symbols) > 0:
                            symbols = universe_symbols
                            print(f"\n✅ UNIVERSO COMPLETO CARGADO: {len(symbols)} instrumentos")
                            print(f"   Categorías incluidas: {', '.join(categories)}")
                            
                            print(f"\n📋 Primeros 20 símbolos:")
                            print(f"   {', '.join(symbols[:20])}")
                            if len(symbols) > 20:
                                print(f"   ... y {len(symbols) - 20} más")
                            print("="*70)
                            print()
                        else:
                            print("❌ No se pudieron cargar símbolos del universo con ninguna estrategia")
                            print("   Revertiendo a modo portafolio...")
                            use_full_universe = False
                            
                    except Exception as e:
                        print(f"❌ Error cargando universo completo: {e}")
                        import traceback
                        print(f"   📋 Detalles del error:")
                        traceback.print_exc()
                        print("   Revertiendo a modo portafolio...")
                        use_full_universe = False
                        # Asegurar que symbols tenga al menos valores por defecto
                        if not symbols or len(symbols) == 0:
                            symbols = ['GGAL', 'YPFD', 'PAMP']
                            print(f"   📌 Usando símbolos por defecto: {', '.join(symbols)}")
                
                # Si no se activó universo completo o falló, usar modo portafolio
                if not use_full_universe and (symbols is None or len(symbols) == 0):
                    if portfolio_mode == "SOLO_IOL":
                        # ============================================================
                        # MODO 1: SOLO IOL (para trading activo)
                        # ============================================================
                        print("📊 Obteniendo portafolio SOLO desde IOL...")
                        try:
                            from src.services.portfolio_persistence import sync_from_iol
                            if sync_from_iol(self.iol_client):
                                print("✅ Portafolio IOL sincronizado")
                                
                                # Cargar portafolio sincronizado
                                self.portfolio = load_portfolio()
                                
                                if self.portfolio and len(self.portfolio) > 0:
                                    for p in self.portfolio:
                                        symbol = p.get('symbol', '').strip()
                                        if symbol:
                                            symbols.append(symbol)
                                    
                                    print(f"✅ {len(symbols)} símbolos de IOL cargados:")
                                    print(f"   {', '.join(symbols[:15])}{'...' if len(symbols) > 15 else ''}")
                                else:
                                    print("⚠️  Portafolio IOL vacío")
                            else:
                                print("⚠️  No se pudo sincronizar con IOL")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                    
                    else:
                        # ============================================================
                        # MODO 2: COMPLETO (IOL + Tienda Broker + my_portfolio.json)
                        # ============================================================
                        print("📊 Obteniendo portafolio COMPLETO (IOL + Tienda Broker)...")
                        
                        # Cargar portafolio completo desde archivo
                        self.portfolio = load_portfolio()
                        
                        if self.portfolio and len(self.portfolio) > 0:
                            for p in self.portfolio:
                                symbol = p.get('symbol', '').strip()
                                if symbol:
                                    symbols.append(symbol)
                            
                            print(f"✅ {len(symbols)} símbolos del portafolio completo:")
                            print(f"   {', '.join(symbols[:15])}{'...' if len(symbols) > 15 else ''}")
                        else:
                            print("⚠️  Portafolio completo vacío")
            
            # Fallback si no hay símbolos
            if not symbols:
                print("\n⚠️  No se pudieron cargar símbolos")
                print("📌 Usando símbolos por defecto:")
                symbols = ['GGAL', 'YPFD', 'PAMP']
                print(f"   {', '.join(symbols)}")
            else:
                # Símbolos especificados por parámetro
                print(f"📊 Usando {len(symbols)} símbolos especificados: {', '.join(symbols[:10])}{'...' if len(symbols) > 10 else ''}")
        except Exception as e:
            print(f"❌ ERROR CRÍTICO en carga de símbolos: {e}")
            import traceback
            traceback.print_exc()
            # Fallback seguro
            symbols = ['GGAL', 'YPFD', 'PAMP']
            print(f"⚠️  Usando símbolos de fallback debido a error: {', '.join(symbols)}")
        
        # Asegurar que symbols siempre esté definido
        if 'symbols' not in locals() or not symbols:
            symbols = ['GGAL', 'YPFD', 'PAMP']
            print(f"⚠️  symbols no estaba definido, usando fallback: {', '.join(symbols)}")
        
        self.symbols = symbols if symbols else ['AAPL']  # Asegurar al menos un símbolo
        print(f"🔍 DEBUG: self.symbols asignado = {self.symbols}")
        print(f"🔍 DEBUG: len(self.symbols) = {len(self.symbols)}")
        
        # Verificar disponibilidad en IOL si no es paper trading
        if not self.paper_trading:
            from src.services.iol_availability_checker import IOLAvailabilityChecker
            availability_checker = IOLAvailabilityChecker(self.iol_client)
            
            # Verificar todos los símbolos
            print("\n🔍 Verificando disponibilidad de símbolos en IOL...")
            unavailable = availability_checker.get_unavailable_symbols(self.symbols)
            
            if unavailable:
                print(f"\n{'='*60}")
                print("⚠️  ALERTA: Algunos símbolos NO están disponibles en IOL")
                print(f"{'='*60}")
                for sym, err in unavailable:
                    print(f"  ❌ {sym}: {err}")
                print(f"{'='*60}\n")
                
                # Notificar al usuario
                unavailable_list = "\n".join([f"  • {sym}: {err}" for sym, err in unavailable])
                self.operation_notifier.notify_alert(
                    "Símbolos no disponibles en IOL",
                    f"Los siguientes símbolos no están disponibles en IOL y no se podrán operar:\n{unavailable_list}",
                    level="warning"
                )
                
                # Filtrar símbolos no disponibles (opcional - comentar si quieres mantenerlos)
                # self.symbols = [s for s in self.symbols if s not in [u[0] for u in unavailable]]
            else:
                print("✅ Todos los símbolos están disponibles en IOL")
        
        # Modo de operación
        mode_str = '🧪 PAPER TRADING' if self.paper_trading else '💰 LIVE TRADING'
        
        print("\n🚀 IOL Quantum AI Trading Bot Initialized")
        print(f"📊 Monitoring {len(self.symbols)} symbols: {', '.join(self.symbols[:5])}{'...' if len(self.symbols) > 5 else ''}")
        print(f"💰 Capital: ${self.capital:,.2f} ARS")
        print(f"🎯 Mode: {mode_str}")
        print(f"🎓 Professional Trading: ENABLED")
        
        if not self.paper_trading:
            print("\n⚠️  WARNING: LIVE TRADING MODE ACTIVE")
            print("⚠️  Real money will be used for operations")
            print(f"⚠️  Max position size: {self.risk_manager.base_position_size_pct*100}% (${self.capital * self.risk_manager.base_position_size_pct:.2f})")
            print(f"⚠️  Max daily trades: {self.risk_manager.max_daily_trades}")
            print(f"⚠️  Max daily loss: {self.risk_manager.max_daily_loss_pct*100}%\n")
        
    def _load_chat_learning(self) -> Dict:
        """Carga aprendizaje compartido del chat"""
        if self.shared_learning_file.exists():
            try:
                import json
                with open(self.shared_learning_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error cargando aprendizaje del chat: {e}")
                return {}
        return {}
    
    def _apply_chat_learning(self, chat_learning: Dict):
        """Aplica aprendizaje del chat a las decisiones del bot de trading"""
        try:
            # Aplicar insights del chat
            insights = chat_learning.get('insights', [])
            if insights:
                print(f"\n💡 Aplicando {len(insights)} insights del chat...")
                for insight in insights[-5:]:  # Últimos 5 insights
                    topic = insight.get('topic', '')
                    if 'estrategia' in topic.lower():
                        print(f"   📊 Insight sobre estrategias: {insight.get('message', '')[:100]}")
                    elif 'win rate' in topic.lower():
                        print(f"   📈 Insight sobre win rate: {insight.get('message', '')[:100]}")
            
            # Aplicar conocimiento de búsquedas web
            web_knowledge = chat_learning.get('chat_knowledge', [])
            if web_knowledge:
                print(f"\n🌐 Aplicando {len(web_knowledge)} conocimientos de búsquedas web...")
                # El bot puede usar esta información para mejorar sus decisiones
            
        except Exception as e:
            print(f"⚠️  Error aplicando aprendizaje del chat: {e}")
    
    def share_learning_with_chat(self, learning_data: Dict):
        """
        Comparte aprendizaje del bot de trading con el chat
        """
        try:
            import json
            current = self._load_chat_learning()
            
            # Agregar patrones aprendidos de trades
            if 'trading_patterns' not in current:
                current['trading_patterns'] = []
            if 'patterns' in learning_data:
                current['trading_patterns'].extend(learning_data['patterns'])
                current['trading_patterns'] = current['trading_patterns'][-50:]
            
            # Agregar insights de performance
            if 'trading_insights' not in current:
                current['trading_insights'] = []
            if 'insights' in learning_data:
                current['trading_insights'].extend(learning_data['insights'])
                current['trading_insights'] = current['trading_insights'][-100:]
            
            current['last_trading_bot_update'] = datetime.now().isoformat()
            
            # Guardar
            with open(self.shared_learning_file, 'w', encoding='utf-8') as f:
                json.dump(current, f, indent=2, ensure_ascii=False, default=str)
                
            print(f"📤 Compartiendo {len(learning_data.get('patterns', []))} patrones con el chat")
                
        except Exception as e:
            print(f"⚠️  Error compartiendo aprendizaje: {e}")
    
    def analyze_symbol(self, symbol):
        try:
            bot_dir = Path(__file__).parent
            self.unlimited_learning = UnlimitedLearning(bot_directory=str(bot_dir))
            print("✅ Sistema de Aprendizaje Sin Límites inicializado")
            print("   🚀 Exploración agresiva activada")
            print("   🧠 Aprende de TODO sin restricciones")
            print("   💡 Genera mejoras ilimitadas")
        except Exception as e:
            print(f"⚠️  Error inicializando aprendizaje sin límites: {e}")
            self.unlimited_learning = None
        
        # Sistema de Aprendizaje Verificado
        try:
            bot_dir = Path(__file__).parent
            self.verified_learning = VerifiedLearning(bot_directory=str(bot_dir))
            print("✅ Sistema de Aprendizaje Verificado inicializado")
            print("   🔍 Verifica automáticamente todo lo que aprende")
            print("   ✅ Solo usa conocimiento verificado como correcto")
            print("   🔄 Corrige conocimiento incorrecto automáticamente")
        except Exception as e:
            print(f"⚠️  Error inicializando aprendizaje verificado: {e}")
            self.verified_learning = None
        
        # Sistema de Implementación de Negocios
        try:
            bot_dir = Path(__file__).parent
            self.business_implementer = BusinessImplementer(bot_directory=str(bot_dir))
            print("✅ Sistema de Implementación de Negocios inicializado")
            print("   💼 Puede identificar oportunidades de negocio")
            print("   📋 Puede crear planes de negocio")
            print("   🚀 Puede implementar negocios para generar ganancias")
        except Exception as e:
            print(f"⚠️  Error inicializando implementador de negocios: {e}")
            self.business_implementer = None
        # Asegurar que current_capital también se inicialice con el capital real
        self.risk_manager.current_capital = self.capital
        
        self.continuous_learning = ContinuousLearning()
        # Cargar configuración profesional desde professional_config.json si existe
        config_file = Path("professional_config.json")
        if config_file.exists():
            self.professional_trader = ProfessionalTrader(config_file="professional_config.json")
        else:
            self.professional_trader = ProfessionalTrader()  # Usar default si no existe
        self.advanced_learning = AdvancedLearningSystem()  # NEW: Advanced learning system
        # Inicializar enhanced learning con manejo de errores
        try:
            self.enhanced_learning = EnhancedLearningSystem()  # NEW: Enhanced learning (símbolos, horarios, condiciones)
        except Exception as e:
            try:
                safe_warning(logger, f"No se pudo inicializar EnhancedLearningSystem: {e}")
            except:
                pass
            self.enhanced_learning = None  # Continuar sin este sistema si falla
        self.operation_notifier = OperationNotifier(enable_telegram=True)  # NEW: Operation notifications
        self.realtime_alerts = RealtimeAlertSystem()  # NEW: Real-time alerts
        self.price_monitor = PriceMonitor()  # NEW: Price monitoring
        self.sentiment_analysis = EnhancedSentimentAnalysis()  # NEW: Sentiment analysis
        
        # Inicializar daily_report_service con manejo de errores
        try:
            self.daily_report_service = DailyReportService(telegram_bot=self.telegram_bot)  # NEW: Daily reports
            print("✅ Servicio de reportes diarios inicializado")
        except Exception as e:
            print(f"⚠️  Error inicializando daily_report_service: {e}")
            self.daily_report_service = None
        
        # ACTUALIZACIÓN INMEDIATA DEL SALDO al iniciar (solo en modo LIVE)
        if not self.paper_trading:
            try:
                print("\n" + "="*60)
                print("🔄 Actualizando saldo desde IOL al iniciar...")
                print("="*60)
                old_capital = self.capital
                new_balance = self.iol_client.get_available_balance()
                if new_balance != old_capital:
                    print(f"💰 Saldo actualizado: ${old_capital:,.2f} → ${new_balance:,.2f} ARS")
                else:
                    print(f"💰 Saldo confirmado: ${new_balance:,.2f} ARS")
                
                self.capital = new_balance
                # Actualizar Risk Manager con el saldo real
                self.risk_manager.initial_capital = new_balance
                self.risk_manager.current_capital = new_balance
                print(f"✅ Risk Manager inicializado con capital: ${new_balance:,.2f} ARS")
                print("="*60 + "\n")
            except Exception as e:
                try:
                    safe_warning(logger, f"⚠️  Error actualizando saldo al iniciar: {e}")
                except:
                    pass
                print(f"⚠️  Usando saldo inicial: ${self.capital:,.2f} ARS")
        
        # Inicializar auto_configurator con manejo de errores
        try:
            from src.services.auto_configurator import AutoConfigurator
            self.auto_configurator = AutoConfigurator()  # NEW: Auto-configuration system
            print("✅ Auto-configurador inicializado")
        except Exception as e:
            print(f"⚠️  Error inicializando auto_configurator: {e}")
            self.auto_configurator = None
        
        # ============================================================
        # GESTIÓN DUAL DE PORTAFOLIO: IOL + Tienda Broker o Solo IOL
        # ============================================================
        from src.services.portfolio_persistence import load_portfolio
        
        # Cargar configuración
        import json
        config_file = Path("professional_config.json")
        portfolio_mode = "COMPLETO"  # Default
        
        monitoring_config = {}
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    monitoring_config = config_data.get('monitoring', {})
                    only_iol = monitoring_config.get('only_iol_portfolio', False)
                    portfolio_mode = "SOLO_IOL" if only_iol else "COMPLETO"
            except Exception as e:
                print(f"⚠️  Error leyendo config: {e}")
        
        print(f"\n{'='*60}")
        print(f"📊 MODO DE PORTAFOLIO: {portfolio_mode}")
        print(f"{'='*60}")
        
        print("🔍 DEBUG: ANTES de determinar símbolos")
        print(f"🔍 DEBUG: monitoring_config = {monitoring_config}")
        
        # Determinar símbolos según el modo
        # Si use_full_universe está activo, ignorar símbolos pasados y cargar universo completo
        try:
            use_full_universe = monitoring_config.get('use_full_universe', False)
            print(f"🔍 DEBUG: use_full_universe leído de config = {use_full_universe}")
            print(f"🔍 DEBUG: symbols recibido en constructor = {symbols}")
            print(f"🔍 DEBUG: type(symbols) = {type(symbols)}")
            
            print("🔍 DEBUG: Entrando al bloque de carga de símbolos...")
            if use_full_universe:
                # Forzar carga del universo completo incluso si se pasaron símbolos
                symbols = []
            
            print(f"DEBUG ANTES DEL IF: symbols={symbols}, type={type(symbols)}")
            if symbols is None or len(symbols) == 0:
                symbols = []
                
                # ============================================================
                # MODO UNIVERSO COMPLETO (NUEVO)
                # ============================================================
                print(f"DEBUG: use_full_universe = {use_full_universe}, symbols = {symbols}")
                if use_full_universe:
                    print("\n" + "="*70)
                    print("🌍 MODO UNIVERSO COMPLETO ACTIVADO")
                    print("="*70)
                print("📊 Cargando TODOS los instrumentos disponibles en IOL...")
                print("   Esto puede tomar unos minutos...")
                print()
                
                try:
                    from src.services.iol_universe_loader import IOLUniverseLoader
                    
                    max_symbols = monitoring_config.get('max_symbols', 200)
                    categories = monitoring_config.get('universe_categories', ['acciones', 'cedears', 'bonos'])
                    
                    print(f"🔍 Configuración:")
                    print(f"   • Máximo de símbolos: {max_symbols}")
                    print(f"   • Categorías: {', '.join(categories)}")
                    print()
                    
                    loader = IOLUniverseLoader(self.iol_client)
                    universe_symbols = []
                    
                    # Intentar cargar universo completo con múltiples estrategias
                    try:
                        print("   🔄 Estrategia 1: Cargando universo completo...")
                        universe_symbols = loader.get_tradeable_universe(max_symbols=max_symbols)
                        if universe_symbols and len(universe_symbols) > 0:
                            print(f"   ✅ Cargados {len(universe_symbols)} símbolos con get_tradeable_universe")
                        else:
                            print(f"   ⚠️  get_tradeable_universe retornó lista vacía")
                    except Exception as e:
                        print(f"   ⚠️  Error con get_tradeable_universe: {e}")
                        import traceback
                        print(f"   📋 Detalles:")
                        traceback.print_exc()
                        universe_symbols = []
                    
                    # Si falló, intentar cargar por categorías
                    if not universe_symbols or len(universe_symbols) == 0:
                        try:
                            print("   🔄 Estrategia 2: Cargando por categorías...")
                            all_instruments = loader.get_all_instruments(categories=categories)
                            
                            # Combinar símbolos de todas las categorías
                            for cat, cat_symbols in all_instruments.items():
                                if cat_symbols:
                                    universe_symbols.extend(cat_symbols)
                                    print(f"   ✅ {cat.upper()}: {len(cat_symbols)} símbolos")
                            
                            # Remover duplicados
                            universe_symbols = list(set(universe_symbols))
                            
                            # Limitar cantidad
                            if len(universe_symbols) > max_symbols:
                                print(f"   ⚠️  Limitando a {max_symbols} símbolos (de {len(universe_symbols)} totales)")
                                universe_symbols = universe_symbols[:max_symbols]
                                
                        except Exception as e:
                            print(f"   ⚠️  Error cargando por categorías: {e}")
                            universe_symbols = []
                    
                    # Si aún no hay símbolos, usar fallback con símbolos conocidos
                    if not universe_symbols or len(universe_symbols) == 0:
                        print("   🔄 Estrategia 3: Usando símbolos conocidos como fallback...")
                        fallback_symbols = []
                        
                        # Agregar símbolos conocidos según categorías
                        if 'acciones' in categories:
                            fallback_symbols.extend([
                                'GGAL', 'YPFD', 'PAMP', 'BMA', 'ALUA', 'LOMA', 'TGNO4', 'TGSU2',
                                'COME', 'EDN', 'TXAR', 'CRES', 'VALO', 'MIRG', 'BYMA', 'TRAN',
                                'CVBA', 'BOLT', 'METR', 'CEPU', 'DGCU2', 'HAVA', 'IRSA', 'BHIP'
                            ])
                        
                        if 'cedears' in categories:
                            fallback_symbols.extend([
                                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX',
                                'DIS', 'KO', 'PEP', 'WMT', 'JPM', 'BAC', 'V', 'MA', 'PYPL',
                                'TSM', 'INTC', 'AMD', 'QCOM', 'BA', 'CAT', 'GE', 'IBM'
                            ])
                        
                        if 'bonos' in categories:
                            fallback_symbols.extend([
                                'GD30', 'GD35', 'GD38', 'GD41', 'GD46',
                                'AL30', 'AL35', 'AL38', 'AL41', 'AE38'
                            ])
                        
                        if 'obligaciones' in categories:
                            fallback_symbols.extend([
                                'PAMPY', 'PAMPO', 'TXARY', 'CRCCY', 'IRCP3',
                                'YPF27', 'TGSU7', 'TGNO6'
                            ])
                        
                        universe_symbols = fallback_symbols[:max_symbols]
                        print(f"   ✅ Usando {len(universe_symbols)} símbolos de fallback")
                    
                    if universe_symbols and len(universe_symbols) > 0:
                        symbols = universe_symbols
                        print(f"\n✅ UNIVERSO COMPLETO CARGADO: {len(symbols)} instrumentos")
                        print(f"   Categorías incluidas: {', '.join(categories)}")
                        
                        print(f"\n📋 Primeros 20 símbolos:")
                        print(f"   {', '.join(symbols[:20])}")
                        if len(symbols) > 20:
                            print(f"   ... y {len(symbols) - 20} más")
                        print("="*70)
                        print()
                    else:
                        print("❌ No se pudieron cargar símbolos del universo con ninguna estrategia")
                        print("   Revertiendo a modo portafolio...")
                        use_full_universe = False
                        
                except Exception as e:
                    print(f"❌ Error cargando universo completo: {e}")
                    import traceback
                    print(f"   📋 Detalles del error:")
                    traceback.print_exc()
                    print("   Revertiendo a modo portafolio...")
                    use_full_universe = False
                    # Asegurar que symbols tenga al menos valores por defecto
                    if not symbols or len(symbols) == 0:
                        symbols = ['GGAL', 'YPFD', 'PAMP']
                        print(f"   📌 Usando símbolos por defecto: {', '.join(symbols)}")
                
                # Si no se activó universo completo o falló, usar modo portafolio
                if not use_full_universe and (symbols is None or len(symbols) == 0):
                    if portfolio_mode == "SOLO_IOL":
                        # ============================================================
                        # MODO 1: SOLO IOL (para trading activo)
                        # ============================================================
                        print("📊 Obteniendo portafolio SOLO desde IOL...")
                        try:
                            from src.services.portfolio_persistence import sync_from_iol
                            if sync_from_iol(self.iol_client):
                                print("✅ Portafolio IOL sincronizado")
                                
                                # Cargar portafolio sincronizado
                                self.portfolio = load_portfolio()
                                
                                if self.portfolio and len(self.portfolio) > 0:
                                    for p in self.portfolio:
                                        symbol = p.get('symbol', '').strip()
                                        if symbol:
                                            symbols.append(symbol)
                                    
                                    print(f"✅ {len(symbols)} símbolos de IOL cargados:")
                                    print(f"   {', '.join(symbols[:15])}{'...' if len(symbols) > 15 else ''}")
                                else:
                                    print("⚠️  Portafolio IOL vacío")
                            else:
                                print("⚠️  No se pudo sincronizar con IOL")
                        except Exception as e:
                            print(f"❌ Error: {e}")
                    
                    else:
                        # ============================================================
                        # MODO 2: COMPLETO (IOL + Tienda Broker + my_portfolio.json)
                        # ============================================================
                        print("📊 Obteniendo portafolio COMPLETO (IOL + Tienda Broker)...")
                        
                        # Cargar portafolio completo desde archivo
                        self.portfolio = load_portfolio()
                        
                        if self.portfolio and len(self.portfolio) > 0:
                            for p in self.portfolio:
                                symbol = p.get('symbol', '').strip()
                                if symbol:
                                    symbols.append(symbol)
                            
                            print(f"✅ {len(symbols)} símbolos del portafolio completo:")
                            print(f"   {', '.join(symbols[:15])}{'...' if len(symbols) > 15 else ''}")
                        else:
                            print("⚠️  Portafolio completo vacío")
            
            # Fallback si no hay símbolos
            if not symbols:
                print("\n⚠️  No se pudieron cargar símbolos")
                print("📌 Usando símbolos por defecto:")
                symbols = ['GGAL', 'YPFD', 'PAMP']
                print(f"   {', '.join(symbols)}")
            else:
                # Símbolos especificados por parámetro
                print(f"📊 Usando {len(symbols)} símbolos especificados: {', '.join(symbols[:10])}{'...' if len(symbols) > 10 else ''}")
        except Exception as e:
            print(f"❌ ERROR CRÍTICO en carga de símbolos: {e}")
            import traceback
            traceback.print_exc()
            # Fallback seguro
            symbols = ['GGAL', 'YPFD', 'PAMP']
            print(f"⚠️  Usando símbolos de fallback debido a error: {', '.join(symbols)}")
        
        # Asegurar que symbols siempre esté definido
        if 'symbols' not in locals() or not symbols:
            symbols = ['GGAL', 'YPFD', 'PAMP']
            print(f"⚠️  symbols no estaba definido, usando fallback: {', '.join(symbols)}")
        
        self.symbols = symbols if symbols else ['AAPL']  # Asegurar al menos un símbolo
        print(f"🔍 DEBUG: self.symbols asignado = {self.symbols}")
        print(f"🔍 DEBUG: len(self.symbols) = {len(self.symbols)}")
        
        # Verificar disponibilidad en IOL si no es paper trading
        if not self.paper_trading:
            from src.services.iol_availability_checker import IOLAvailabilityChecker
            availability_checker = IOLAvailabilityChecker(self.iol_client)
            
            # Verificar todos los símbolos
            print("\n🔍 Verificando disponibilidad de símbolos en IOL...")
            unavailable = availability_checker.get_unavailable_symbols(self.symbols)
            
            if unavailable:
                print(f"\n{'='*60}")
                print("⚠️  ALERTA: Algunos símbolos NO están disponibles en IOL")
                print(f"{'='*60}")
                for sym, err in unavailable:
                    print(f"  ❌ {sym}: {err}")
                print(f"{'='*60}\n")
                
                # Notificar al usuario
                unavailable_list = "\n".join([f"  • {sym}: {err}" for sym, err in unavailable])
                self.operation_notifier.notify_alert(
                    "Símbolos no disponibles en IOL",
                    f"Los siguientes símbolos no están disponibles en IOL y no se podrán operar:\n{unavailable_list}",
                    level="warning"
                )
                
                # Filtrar símbolos no disponibles (opcional - comentar si quieres mantenerlos)
                # self.symbols = [s for s in self.symbols if s not in [u[0] for u in unavailable]]
            else:
                print("✅ Todos los símbolos están disponibles en IOL")
        
        # Modo de operación
        mode_str = '🧪 PAPER TRADING' if self.paper_trading else '💰 LIVE TRADING'
        
        print("\n🚀 IOL Quantum AI Trading Bot Initialized")
        print(f"📊 Monitoring {len(self.symbols)} symbols: {', '.join(self.symbols[:5])}{'...' if len(self.symbols) > 5 else ''}")
        print(f"💰 Capital: ${self.capital:,.2f} ARS")
        print(f"🎯 Mode: {mode_str}")
        print(f"🎓 Professional Trading: ENABLED")
        
        if not self.paper_trading:
            print("\n⚠️  WARNING: LIVE TRADING MODE ACTIVE")
            print("⚠️  Real money will be used for operations")
            print(f"⚠️  Max position size: {self.risk_manager.base_position_size_pct*100}% (${self.capital * self.risk_manager.base_position_size_pct:.2f})")
            print(f"⚠️  Max daily trades: {self.risk_manager.max_daily_trades}")
            print(f"⚠️  Max daily loss: {self.risk_manager.max_daily_loss_pct*100}%\n")
    
    def analyze_symbol(self, symbol):
        """
        Perform complete analysis on a symbol.
        """
        print(f"\n{'='*60}")
        print(f"📊 Analyzing {symbol}")
        print(f"{'='*60}")
        
        analysis_result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'ai_signal': None,
            'technical_signal': None,
            'final_signal': None,
            'risk_metrics': None
        }
        
        # 1. Technical Analysis (obtener primero para usar como fallback)
        tech_analysis = None
        try:
            tech_analysis = self.technical_service.get_full_analysis(symbol, config=self.strategy_config)
            analysis_result['technical_signal'] = tech_analysis
            
            print(f"\n📈 Technical Analysis:")
            print(f"   RSI: {tech_analysis['momentum']['rsi']:.2f}" if tech_analysis.get('momentum', {}).get('rsi') else "   RSI: N/A")
            print(f"   ATR: {tech_analysis['volatility']['atr']:.2f}" if tech_analysis.get('volatility', {}).get('atr') else "   ATR: N/A")
            print(f"   Signal: {tech_analysis.get('signal', 'N/A')}")
        except (IndexError, ValueError) as e:
            # Error común cuando hay pocos datos históricos
            print(f"⚠️  Technical Analysis failed (datos insuficientes): {e}")
            print(f"   💡 Se necesitan al menos 14-20 registros históricos para análisis técnico completo")
            # Crear análisis técnico básico con datos disponibles
            tech_analysis = {
                'signal': 'HOLD',
                'momentum': {},
                'volatility': {},
                'trend': {}
            }
            analysis_result['technical_signal'] = tech_analysis
        except Exception as e:
            print(f"⚠️  Technical Analysis failed: {e}")
            # Crear análisis técnico básico como fallback
            tech_analysis = {
                'signal': 'HOLD',
                'momentum': {},
                'volatility': {},
                'trend': {}
            }
            analysis_result['technical_signal'] = tech_analysis
        
        # 2. AI Prediction (con fallback a análisis técnico)
        ai_pred = None
        try:
            # Intentar predicción IA, pasando análisis técnico como fallback
            ai_pred = self.prediction_service.generate_signal(
                symbol, 
                threshold=2.0,
                technical_analysis=tech_analysis
            )
            
            if ai_pred:
                analysis_result['ai_signal'] = ai_pred
                
                # Indicar si viene de IA o análisis técnico
                source = ai_pred.get('source', 'ai_model')
                source_icon = "🤖" if source == "ai_model" else "📊"
                source_text = "IA Model" if source == "ai_model" else "Análisis Técnico (Fallback)"
                
                print(f"\n{source_icon} Prediction ({source_text}):")
                print(f"   Current: ${ai_pred['current_price']:.2f}")
                print(f"   Predicted: ${ai_pred['predicted_price']:.2f}")
                print(f"   Change: {ai_pred['change_pct']:+.2f}%")
                print(f"   Signal: {ai_pred['signal']}")
                
                # 📢 NOTIFICACIÓN: Mostrar predicción al usuario
                self.operation_notifier.notify_prediction({
                    'symbol': symbol,
                    'current_price': ai_pred['current_price'],
                    'predicted_price': ai_pred['predicted_price'],
                    'change_pct': ai_pred['change_pct'],
                    'signal': ai_pred['signal'],
                    'source': source_text
                })
                
                # 🧠 APRENDIZAJE: Registrar predicción para feedback (solo si viene de IA)
                if source == "ai_model" and 'current_price' in ai_pred and 'predicted_price' in ai_pred:
                    try:
                        self.advanced_learning.learn_from_prediction(
                            symbol=symbol,
                            predicted_price=ai_pred['predicted_price'],
                            predicted_change=ai_pred['change_pct'],
                            current_price=ai_pred['current_price'],
                            confidence=abs(ai_pred['change_pct']) / 10.0,
                            features={
                                'rsi': tech_analysis.get('momentum', {}).get('rsi') if tech_analysis else None,
                                'macd': tech_analysis.get('momentum', {}).get('macd') if tech_analysis else None,
                            }
                        )
                    except Exception:
                        pass  # No interrumpir si el aprendizaje falla
            else:
                print(f"\n⚠️  AI Prediction no disponible - usando solo análisis técnico")
                analysis_result['ai_signal'] = None
        except Exception as e:
            print(f"⚠️  AI Prediction failed: {e}")
            analysis_result['ai_signal'] = None
        
        # 2.5. Sentiment Analysis (si está habilitado)
        try:
            # Verificar si está habilitado en la configuración
            from src.core.config_manager import get_config_manager
            config_mgr = get_config_manager()
            enable_sentiment = config_mgr.get_value('enable_sentiment_analysis', True)
            enable_news = config_mgr.get_value('enable_news_fetching', True)
            
            if enable_sentiment and hasattr(self, 'sentiment_analysis') and self.sentiment_analysis:
                try:
                    # Obtener sentimiento del mercado (obtiene noticias automáticamente si está habilitado)
                    sentiment_result = self.sentiment_analysis.get_market_sentiment(
                        symbol, 
                        auto_fetch_news=enable_news
                    )
                    analysis_result['sentiment'] = sentiment_result
                except Exception as e:
                    print(f"⚠️  Error en análisis de sentimiento: {e}")
                    analysis_result['sentiment'] = {}
                
                if sentiment_result.get('sample_size', 0) > 0:
                    print(f"\n💭 Sentiment Analysis:")
                    print(f"   Overall: {sentiment_result['overall_sentiment']}")
                    print(f"   Score: {sentiment_result['score']:.3f}")
                    print(f"   Sample Size: {sentiment_result['sample_size']} noticias")
                else:
                    print(f"\n💭 Sentiment Analysis: Sin datos recientes")
            else:
                print(f"\n💭 Sentiment Analysis: Deshabilitado en configuración")
                analysis_result['sentiment'] = None
        except Exception as e:
            print(f"⚠️  Sentiment Analysis failed: {e}")
            analysis_result['sentiment'] = None
        
        # 3. Determine final signal using Weighted Voting System (Score 0-100)
        # Previous consensus logic was too strict, leading to constant HOLD
        
        score = 0
        buy_factors = []
        sell_factors = []
        
        # A. AI Signal Impact (Max 30 pts) - con fallback a análisis técnico
        ai_signal = None
        ai_pred_change = 0.0
        ai_source = "none"
        
        if analysis_result.get('ai_signal'):
            ai_signal = analysis_result['ai_signal'].get('signal')
            ai_pred_change = analysis_result['ai_signal'].get('change_pct', 0.0)
            ai_source = analysis_result['ai_signal'].get('source', 'ai_model')
        
        if ai_signal == 'BUY':
            # Ajustar puntos según fuente: IA tiene más peso que análisis técnico
            base_points = 30 if ai_pred_change > 2.0 else 15
            points = base_points if ai_source == 'ai_model' else int(base_points * 0.7)
            score += points
            source_label = "IA" if ai_source == 'ai_model' else "Técnico"
            buy_factors.append(f"{source_label} Bullish (+{points})")
        elif ai_signal == 'SELL':
            base_points = 30 if ai_pred_change < -2.0 else 15
            points = base_points if ai_source == 'ai_model' else int(base_points * 0.7)
            score -= points
            source_label = "IA" if ai_source == 'ai_model' else "Técnico"
            sell_factors.append(f"{source_label} Bearish (-{points})")
            
        # B. Technical Signal Impact (Max 40 pts)
        # RSI Analysis
        rsi = None
        if (analysis_result.get('technical_signal') and 
            analysis_result['technical_signal'].get('momentum') and 
            'rsi' in analysis_result['technical_signal']['momentum']):
            rsi = analysis_result['technical_signal']['momentum']['rsi']
        
        if rsi:
            if rsi < 30: # Oversold
                score += 20
                buy_factors.append("RSI Oversold (+20)")
            elif rsi > 70: # Overbought
                score -= 20
                sell_factors.append("RSI Overbought (-20)")
            elif 50 < rsi < 70: # Bullish Trend
                score += 5
                buy_factors.append("RSI Uptrend (+5)")
            elif 30 < rsi < 50: # Bearish Trend
                score -= 5
                sell_factors.append("RSI Downtrend (-5)")
                
        # MACD Analysis
        macd = None
        macd_signal = None
        if (analysis_result.get('technical_signal') and 
            analysis_result['technical_signal'].get('momentum')):
            macd = analysis_result['technical_signal']['momentum'].get('macd')
            macd_signal = analysis_result['technical_signal']['momentum'].get('macd_signal')
        
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                score += 15
                buy_factors.append("MACD > Signal (+15)")
            else:
                score -= 15
                sell_factors.append("MACD < Signal (-15)")
        
        # C. Trend Analysis (Max 10 pts)
        current_price = None
        sma_20 = None
        if (analysis_result.get('technical_signal') and 
            analysis_result['technical_signal'].get('trend')):
            current_price = analysis_result['technical_signal']['trend'].get('current_price')
            sma_20 = analysis_result['technical_signal']['trend'].get('sma_20')
        
        if current_price and sma_20:
            if current_price > sma_20:
                score += 10
                buy_factors.append("Price > SMA20 (+10)")
            else:
                score -= 10
                sell_factors.append("Price < SMA20 (-10)")
        
        # D. Sentiment Analysis Impact (Max 20 pts)
        sentiment_result = analysis_result.get('sentiment')
        if sentiment_result and sentiment_result.get('sample_size', 0) > 0:
            sentiment_score = sentiment_result.get('score', 0)
            overall_sentiment = sentiment_result.get('overall_sentiment', 'NEUTRAL')
            
            if overall_sentiment == 'POSITIVE':
                # Score positivo: +10 a +20 puntos según intensidad
                points = 20 if sentiment_score > 0.3 else 15 if sentiment_score > 0.15 else 10
                score += points
                buy_factors.append(f"Sentiment Positive (+{points})")
            elif overall_sentiment == 'NEGATIVE':
                # Score negativo: -10 a -20 puntos según intensidad
                points = 20 if sentiment_score < -0.3 else 15 if sentiment_score < -0.15 else 10
                score -= points
                sell_factors.append(f"Sentiment Negative (-{points})")
            # NEUTRAL no afecta el score
        
        # E. NUEVAS ESTRATEGIAS AVANZADAS (Max 120 pts adicionales)
        if hasattr(self, 'advanced_strategies_enabled') and self.advanced_strategies_enabled:
            try:
                print(f"\n🧠 Análisis Avanzado:")
                advanced_scores = {}
                
                # 1. Regime Detection (detectar régimen de mercado)
                if hasattr(self, 'regime_detector') and tech_analysis:
                    try:
                        df = self.data_service.get_historical_data(symbol, period='3mo')
                        if df is not None and len(df) > 30:
                            regime, regime_info = self.regime_detector.detect_regime(df)
                            regime_score = regime_info.get('score', 0)
                            if regime != 'UNKNOWN':
                                score += regime_score
                                advanced_scores['regime'] = regime_score
                                print(f"   Regime: {regime} ({regime_score:+d})")
                                if regime_score > 0:
                                    buy_factors.append(f"Regime {regime} (+{regime_score})")
                                elif regime_score < 0:
                                    sell_factors.append(f"Regime {regime} ({regime_score})")
                    except Exception as e:
                        pass
                
                # 2. Multi-Timeframe Analysis
                if hasattr(self, 'mtf_analyzer'):
                    try:
                        mtf_result = self.mtf_analyzer.analyze_all_timeframes(symbol)
                        mtf_score = mtf_result.get('score', 0)
                        if abs(mtf_score) > 5:
                            score += int(mtf_score)
                            advanced_scores['multi_timeframe'] = int(mtf_score)
                            print(f"   Multi-TF: {mtf_result.get('signal', 'HOLD')} ({mtf_score:+.0f})")
                            if mtf_score > 0:
                                buy_factors.append(f"Multi-TF (+{int(mtf_score)})")
                            else:
                                sell_factors.append(f"Multi-TF ({int(mtf_score)})")
                    except Exception as e:
                        pass
                
                # 3. Seasonal Patterns
                if hasattr(self, 'seasonal_analyzer'):
                    try:
                        df = self.data_service.get_historical_data(symbol, period='1y')
                        if df is not None and len(df) > 250:
                            seasonal = self.seasonal_analyzer.analyze(symbol, df)
                            seasonal_score = seasonal.get('score', 0)
                            if abs(seasonal_score) > 0:
                                score += seasonal_score
                                advanced_scores['seasonal'] = seasonal_score
                                print(f"   Seasonal: ({seasonal_score:+d})")
                    except Exception as e:
                        pass
                
                # 4. Fractals (soportes/resistencias)
                if hasattr(self, 'fractal_analyzer'):
                    try:
                        df = self.data_service.get_historical_data(symbol, period='1mo')
                        if df is not None:
                            fractal = self.fractal_analyzer.analyze(df)
                            fractal_score = fractal.get('score', 0)
                            if abs(fractal_score) > 0:
                                score += fractal_score
                                advanced_scores['fractals'] = fractal_score
                                print(f"   Fractals: ({fractal_score:+d})")
                    except Exception as e:
                        pass
                
                # 5. Anomaly Detection
                if hasattr(self, 'anomaly_detector'):
                    try:
                        df = self.data_service.get_historical_data(symbol, period='1mo')
                        if df is not None:
                            anomaly = self.anomaly_detector.detect(df)
                            anomaly_score = anomaly.get('score', 0)
                            if abs(anomaly_score) > 5:
                                score += anomaly_score
                                advanced_scores['anomaly'] = anomaly_score
                                print(f"   Anomaly: {anomaly.get('count', 0)} detectadas ({anomaly_score:+d})")
                                if anomaly_score > 0:
                                    buy_factors.append(f"Anomaly (+{anomaly_score})")
                                else:
                                    sell_factors.append(f"Anomaly ({anomaly_score})")
                    except Exception as e:
                        pass
                
                # 6. Volume Profile
                if hasattr(self, 'volume_profile'):
                    try:
                        df = self.data_service.get_historical_data(symbol, period='2mo')
                        if df is not None:
                            vp = self.volume_profile.analyze(df)
                            vp_score = vp.get('score', 0)
                            if abs(vp_score) > 5:
                                score += vp_score
                                advanced_scores['volume_profile'] = vp_score
                                print(f"   Volume Profile: ({vp_score:+d})")
                    except Exception as e:
                        pass
                
                # 7. Monte Carlo Simulation
                if hasattr(self, 'monte_carlo') and current_price:
                    try:
                        df = self.data_service.get_historical_data(symbol, period='3mo')
                        if df is not None:
                            returns = df['close'].pct_change().dropna()
                            volatility = returns.std() * np.sqrt(252)
                            mc = self.monte_carlo.simulate_trade(symbol, current_price, volatility)
                            mc_score = mc.get('score', 0)
                            if abs(mc_score) > 5:
                                score += mc_score
                                advanced_scores['monte_carlo'] = mc_score
                                print(f"   Monte Carlo: Win {mc.get('win_rate', 0)}% ({mc_score:+d})")
                                if mc_score > 0:
                                    buy_factors.append(f"Monte Carlo (+{mc_score})")
                                else:
                                    sell_factors.append(f"Monte Carlo ({mc_score})")
                    except Exception as e:
                        pass
                
                        if df is not None:
                            patterns = self.pattern_recognizer.detect_all_patterns(df)
                            pattern_score = patterns.get('score', 0)
                            if abs(pattern_score) > 10:
                                score += pattern_score
                                advanced_scores['patterns'] = pattern_score
                                print(f"   Patterns: {patterns.get('count', 0)} detectados ({pattern_score:+d})")
                                if pattern_score > 0:
                                    buy_factors.append(f"Patterns (+{pattern_score})")
                                else:
                                    sell_factors.append(f"Patterns ({pattern_score})")
                    except Exception as e:
                        pass
                
                # 9. Neural Network (Deep Learning) - El "Cerebro" COMPLETO (Ensemble + Multi-Features)
                if hasattr(self, 'neural_network'):
                    try:
                        # Usar histórico largo para la red neuronal
                        df_long = self.data_service.get_historical_data(symbol, period='2y')
                        if df_long is not None and len(df_long) > 100:
                            # Nueva interfaz: retorna tupla (predicted_price, score, confidence)
                            nn_result = self.neural_network.predict(symbol, df_long)
                            if nn_result and len(nn_result) == 3:
                                pred_price, nn_score, confidence = nn_result
                                if pred_price is not None and abs(nn_score) > 0:
                                    score += nn_score
                                    advanced_scores['neural_network'] = nn_score
                                    
                                    # Calcular cambio porcentual
                                    current_price = df_long['Close'].iloc[-1] if 'Close' in df_long.columns else df_long['close'].iloc[-1]
                                    change = ((pred_price - current_price) / current_price) * 100
                                    
                                    icon = "🧠" if nn_score > 0 else "🛑"
                                    ensemble_info = "Ensemble" if hasattr(self.neural_network, 'ensemble_models') and symbol in self.neural_network.ensemble_models else "LSTM"
                                    
                                    print(f"   {icon} Neural Network ({ensemble_info}): Predice ${pred_price:.2f} ({change:+.2f}%) en 5 días ({nn_score:+d}, conf: {confidence:.2f})")
                                    
                                    if nn_score > 0:
                                        buy_factors.append(f"Neural Network Bullish (+{nn_score}, conf: {confidence:.2f})")
                                    else:
                                        sell_factors.append(f"Neural Network Bearish ({nn_score}, conf: {confidence:.2f})")
                    except Exception as e:
                        print(f"   ⚠️ Error Neural Network: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 9. Smart Money Concepts
                if hasattr(self, 'smart_money'):
                    try:
                        df = self.data_service.get_historical_data(symbol, period='2mo')
                        if df is not None:
                            smc = self.smart_money.analyze(df)
                            smc_score = smc.get('score', 0)
                            if abs(smc_score) > 10:
                                score += smc_score
                                advanced_scores['smart_money'] = smc_score
                                print(f"   Smart Money: ({smc_score:+d})")
                    except Exception as e:
                        pass
                
                # 10. Elliott Wave (simplificado)
                if hasattr(self, 'elliott_wave'):
                    try:
                        df = self.data_service.get_historical_data(symbol, period='3mo')
                        if df is not None:
                            wave = self.elliott_wave.detect_wave(df)
                            wave_score = wave.get('score', 0)
                            if abs(wave_score) > 0:
                                score += wave_score
                                advanced_scores['elliott_wave'] = wave_score
                                print(f"   Elliott Wave: {wave.get('wave', 'UNKNOWN')} ({wave_score:+d})")
                    except Exception as e:
                        pass
                
                # 14. Candlestick Patterns (Patrones de Velas)
                if hasattr(self, 'candlestick_analyzer'):
                    try:
                        df = self.data_service.get_historical_data(symbol, period='1mo')
                        if df is not None and len(df) > 5:
                            candles = self.candlestick_analyzer.analyze(df, lookback=5)
                            candle_score = candles.get('score', 0)
                            if abs(candle_score) > 5:
                                score += candle_score
                                advanced_scores['candlesticks'] = candle_score
                                patterns = candles.get('patterns_detected', [])
                                print(f"   Candlesticks: {candles.get('count', 0)} patrones ({candle_score:+d})")
                                if patterns:
                                    print(f"      Patrones: {', '.join(patterns[:3])}")
                                if candle_score > 0:
                                    buy_factors.append(f"Candlesticks (+{candle_score})")
                                elif candle_score < 0:
                                    sell_factors.append(f"Candlesticks ({candle_score})")
                    except Exception as e:
                        pass
                
                # 11. Meta-Learner - Combina TODAS las señales inteligentemente
                if hasattr(self, 'meta_learner') and len(advanced_scores) > 0:
                    try:
                        # Preparar condiciones del mercado
                        market_conditions = {
                            'regime': regime if 'regime' in locals() else 'UNKNOWN',
                            'volatility': volatility if 'volatility' in locals() else 0.20
                        }
                        
                        # Agregar scores existentes
                        all_scores = {
                            'technical': (score - sum(advanced_scores.values())),  # Score sin estrategias avanzadas
                            **advanced_scores
                        }
                        
                        # Meta-learner ajusta score final
                        meta_result = self.meta_learner.combine_signals(all_scores, market_conditions)
                        meta_adjustment = meta_result.get('final_score', 0) - score
                        
                        if abs(meta_adjustment) > 5:
                            score = int(meta_result.get('final_score', score))
                            print(f"   Meta-Learner: Ajuste {meta_adjustment:+.0f} → Score final: {score}")
                        
                    except Exception as e:
                        pass
                
                # 15. Análisis Macroeconómico - Ajustar score según contexto macro
                if hasattr(self, 'macroeconomic_service') and self.macroeconomic_service:
                    try:
                        indicators = self.macroeconomic_service.get_economic_indicators()
                        macro_score = 0
                        macro_factors = []
                        
                        # Ajuste por tipo de cambio USD
                        usd_blue = indicators.get('usd_blue')
                        usd_official = indicators.get('usd_official')
                        
                        if usd_blue and usd_official:
                            spread = usd_blue - usd_official
                            spread_pct = (spread / usd_official) * 100 if usd_official > 0 else 0
                            
                            # Si el spread es muy alto (>30%), puede indicar inestabilidad
                            if spread_pct > 30:
                                macro_score -= 10
                                macro_factors.append(f"Spread USD alto ({spread_pct:.1f}%)")
                            elif spread_pct < 10:
                                macro_score += 5
                                macro_factors.append(f"Spread USD normal ({spread_pct:.1f}%)")
                        
                        # Ajuste por inflación
                        inflation = indicators.get('inflation_rate')
                        if inflation:
                            # Inflación muy alta (>100% anual) es negativa
                            if inflation > 100:
                                macro_score -= 15
                                macro_factors.append(f"Inflación muy alta ({inflation:.1f}%)")
                            elif inflation > 50:
                                macro_score -= 8
                                macro_factors.append(f"Inflación alta ({inflation:.1f}%)")
                            elif inflation < 20:
                                macro_score += 5
                                macro_factors.append(f"Inflación moderada ({inflation:.1f}%)")
                        
                        # Aplicar ajuste macro al score
                        if abs(macro_score) > 0:
                            score += macro_score
                            advanced_scores['macroeconomic'] = macro_score
                            print(f"   📊 Macro: {', '.join(macro_factors) if macro_factors else 'Neutral'} ({macro_score:+d})")
                            if macro_score > 0:
                                buy_factors.append(f"Contexto Macro Favorable (+{macro_score})")
                            elif macro_score < 0:
                                sell_factors.append(f"Contexto Macro Desfavorable ({macro_score})")
                        
                    except Exception as e:
                        safe_warning(logger, f"Error en análisis macroeconómico: {e}")
                        pass
                
                print(f"   ✅ Análisis avanzado completado")
                
            except Exception as e:
                print(f"   ⚠️  Error en análisis avanzado: {e}")

        # Decision Thresholds (cargar desde professional_config.json)
        try:
            from pathlib import Path
            import json
            config_file = Path("professional_config.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    buy_threshold = config.get('buy_threshold', 30)
                    sell_threshold = config.get('sell_threshold', -30)
            else:
                # Fallback a parámetros adaptativos si no existe el archivo
                strategy_params = self.advanced_learning.adaptive_strategy.get_current_params()
                buy_threshold = strategy_params.get('buy_threshold', 25)
                sell_threshold = strategy_params.get('sell_threshold', -25)
        except Exception as e:
            # Fallback a parámetros adaptativos si hay error
            safe_warning(logger, f"Error cargando umbrales desde professional_config.json: {e}")
            strategy_params = self.advanced_learning.adaptive_strategy.get_current_params()
            buy_threshold = strategy_params.get('buy_threshold', 25)
            sell_threshold = strategy_params.get('sell_threshold', -25)
        
        final_signal = 'HOLD'
        confidence = 'LOW'
        
        if score >= buy_threshold:
            final_signal = 'BUY'
            confidence = 'HIGH' if score >= (buy_threshold + 25) else 'MEDIUM'
        elif score <= sell_threshold:
            final_signal = 'SELL'
            confidence = 'HIGH' if score <= (sell_threshold - 25) else 'MEDIUM'
            
        print(f"\n📊 Scoring Analysis (Score: {score}):")
        print(f"   Buy Factors: {', '.join(buy_factors) if buy_factors else 'None'}")
        print(f"   Sell Factors: {', '.join(sell_factors) if sell_factors else 'None'}")
        
        analysis_result['final_signal'] = final_signal
        analysis_result['confidence'] = confidence
        analysis_result['score'] = score
        
        print(f"\n🎯 Final Signal: {final_signal} (Confidence: {confidence})")
        
        # Sistema de Razonamiento Autónomo
        if hasattr(self, 'reasoning_system') and self.reasoning_system and final_signal != 'HOLD':
            try:
                trade_data = {
                    'symbol': symbol,
                    'signal': final_signal,
                    'score': score,
                    'confidence': confidence,
                    'current_price': current_price,
                    'market_conditions': {
                        'volatility': 'HIGH' if tech_analysis.get('volatility', {}).get('atr', 0) > 0.05 else 'MEDIUM',
                        'trend': tech_analysis.get('trend', {}).get('direction', 'NEUTRAL') if tech_analysis else 'NEUTRAL'
                    },
                    'current_positions': getattr(self, 'symbols', [])
                }
                
                reasoning = self.reasoning_system.reason_about_trade(trade_data)
                
                if reasoning.get('decision') == 'EXECUTE':
                    print(f"\n✅ Razonamiento: DECISIÓN DE EJECUTAR")
                    print(f"   Confianza del razonamiento: {reasoning.get('confidence', 0):.2f}")
                    for step in reasoning.get('reasoning_steps', [])[:3]:
                        print(f"   • {step}")
                elif reasoning.get('decision') == 'CONSIDER':
                    print(f"\n⚠️  Razonamiento: CONSIDERAR (confianza baja)")
                elif reasoning.get('decision') == 'HOLD':
                    print(f"\n⏸️  Razonamiento: MANTENER (señal no suficientemente fuerte)")
                    # Opcional: Sobrescribir señal si razonamiento es muy negativo
                    if reasoning.get('confidence', 0) < -0.3:
                        final_signal = 'HOLD'
                        analysis_result['final_signal'] = 'HOLD'
                        analysis_result['reasoning_override'] = True
            except Exception as e:
                print(f"   ⚠️  Error en razonamiento: {e}")
        
        # 📢 NOTIFICACIÓN: Mostrar análisis completo al usuario (mejorado)
        analysis_summary = {
            'symbol': symbol,
            'final_signal': final_signal,
            'confidence': confidence,
            'score': score,
            'buy_factors': buy_factors,
            'sell_factors': sell_factors,
            'current_price': current_price,
            'sentiment': analysis_result.get('sentiment', {}),
            'ai_prediction': analysis_result.get('ai_signal', {}),
            'technical': analysis_result.get('technical_signal', {}),
        }
        # Notificar análisis completo (si operation_notifier está disponible)
        if hasattr(self, 'operation_notifier') and self.operation_notifier:
            try:
                self.operation_notifier.notify_analysis_complete(analysis_summary)
            except Exception as e:
                print(f"⚠️  Error notificando análisis: {e}")
        
        # Send Telegram Alert if signal is generated (mejorado)
        # COMENTADO PARA ESTRATEGIA HÍBRIDA: Las señales se envían en el resumen consolidado
        # if final_signal != 'HOLD':
        #     emoji = "🟢" if final_signal == 'BUY' else "🔴"
        #     buy_factors_text = "\n".join([f"  ✅ {f}" for f in buy_factors]) if buy_factors else "  Ninguno"
        #     sell_factors_text = "\n".join([f"  ❌ {f}" for f in sell_factors]) if sell_factors else "  Ninguno"
            
        #     msg = f"""{emoji} *🚨 SEÑAL DE TRADING DETECTADA*

        # *Símbolo:* {symbol}
        # *Señal:* {final_signal}
        # *Confianza:* {confidence}
        # *Score:* {score}
        # *Precio Actual:* ${current_price:.2f}

        # *Factores de Compra:*
        # {buy_factors_text}

        # *Factores de Venta:*
        # {sell_factors_text}

        # *Sentimiento:* {(analysis_result.get('sentiment') or {}).get('overall_sentiment', 'N/A')}
        # *Score Sentimiento:* {(analysis_result.get('sentiment') or {}).get('score', 0):.3f}

        # ⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        # """
        #     try:
        #         self.telegram_bot.send_alert(msg)
        #     except Exception as e:
        #         safe_warning(logger, f"Error enviando alerta a Telegram: {e}")
        #         # No interrumpir el ciclo por errores de Telegram
        
        # 4. Professional Trading Filters
        if final_signal in ['BUY', 'SELL']:
            # Check time filters
            can_trade_time, time_reason = self.professional_trader.check_time_filters()
            if not can_trade_time:
                print(f"\n⏰ Filtro de Tiempo: {time_reason}")
                final_signal = 'HOLD'
                analysis_result['final_signal'] = 'HOLD'
                analysis_result['filter_reason'] = time_reason
                return analysis_result
            
            # Check entry filters
            if analysis_result.get('technical_signal'):
                can_enter, entry_reason = self.professional_trader.check_entry_filters(
                    analysis_result['technical_signal']
                )
                if not can_enter:
                    print(f"\n🎯 Filtro de Entrada: {entry_reason}")
                    final_signal = 'HOLD'
                    analysis_result['final_signal'] = 'HOLD'
                    analysis_result['filter_reason'] = entry_reason
                    return analysis_result
                else:
                    print(f"\n✅ Filtros Profesionales: {entry_reason}")
        
        # 4.5. Correlation Analysis (antes de ejecutar BUY)
        if final_signal == 'BUY' and hasattr(self, 'correlation_analyzer') and self.correlation_analyzer:
            try:
                # Obtener símbolos actuales del portafolio
                portfolio_symbols = []
                if hasattr(self, 'symbols') and self.symbols:
                    portfolio_symbols = [s for s in self.symbols if s != symbol]
                
                # Si hay símbolos en el portafolio, verificar correlación
                if portfolio_symbols:
                    corr_check = self.correlation_analyzer.should_add_symbol(
                        symbol, portfolio_symbols,
                        data_service=self.data_service,
                        max_correlation=0.8
                    )
                    
                    if not corr_check['should_add']:
                        print(f"\n⚠️  Análisis de Correlación: {corr_check['reason']}")
                        print(f"   Correlación máxima: {corr_check['max_correlation']:.2f}")
                        print(f"   ⚠️  Símbolo altamente correlacionado - Reduciendo score")
                        # Reducir score pero no bloquear completamente
                        score -= 10
                        if score < buy_threshold:
                            final_signal = 'HOLD'
                            analysis_result['final_signal'] = 'HOLD'
                            analysis_result['filter_reason'] = f"Alta correlación ({corr_check['max_correlation']:.2f})"
                            print(f"   ❌ Trade bloqueado por alta correlación")
                            return analysis_result
                    else:
                        print(f"\n✅ Análisis de Correlación: {corr_check['reason']}")
                        print(f"   Correlación máxima: {corr_check['max_correlation']:.2f} (OK)")
            except Exception as e:
                print(f"   ⚠️  Error en análisis de correlación: {e}")
                # Continuar sin bloquear si hay error
        
        # 5. Risk Management
        if final_signal in ['BUY', 'SELL'] and analysis_result.get('technical_signal'):
            tech_signal = analysis_result['technical_signal']
            atr = tech_signal.get('volatility', {}).get('atr') if tech_signal.get('volatility') else None
            current_price = tech_signal.get('trend', {}).get('current_price') if tech_signal.get('trend') else None
            
            if atr and current_price:
                stop_loss = self.risk_manager.calculate_stop_loss(current_price, atr)
                take_profit = self.risk_manager.calculate_take_profit(current_price, atr)
                position_size = self.risk_manager.calculate_position_size(
                    current_price, stop_loss
                )
                
                analysis_result['risk_metrics'] = {
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'position_size': position_size,
                    'risk_amount': position_size * (current_price - stop_loss)
                }
                
                print(f"\n🛡️  Risk Management:")
                print(f"   Stop Loss: ${stop_loss:.2f}")
                print(f"   Take Profit: ${take_profit:.2f}")
                print(f"   Position Size: {position_size} shares")
                print(f"   Risk Amount: ${analysis_result['risk_metrics']['risk_amount']:.2f}")
                
                # 6. EXECUTION LOGIC
                if position_size > 0:
                    print(f"\n🚀 Intentando ejecutar orden {final_signal} para {symbol}...")
                    result = self.execute_trade(symbol, final_signal, current_price, position_size, stop_loss, take_profit)
                    if result and result.get('status') in ['FAILED', 'BLOCKED']:
                        print(f"   ⚠️  Orden no ejecutada: {result.get('reason', 'Desconocido')}")
                        analysis_result['execution_status'] = result.get('status')
                        analysis_result['execution_reason'] = result.get('reason')
                else:
                    print(f"\n⚠️  Position size es 0 - Orden no ejecutada")
                    print(f"   💡 Posible causa: Capital insuficiente o riesgo demasiado alto")
                    analysis_result['execution_status'] = 'BLOCKED'
                    analysis_result['execution_reason'] = 'Position size is 0'
        
        # 6. Send alert if strong signal
        if final_signal in ['BUY', 'SELL'] and confidence in ['HIGH', 'MEDIUM']:
            self.alert_system.send_alert(
                final_signal,
                symbol,
                f"{confidence} confidence {final_signal} signal",
                data=analysis_result
            )
        
        return analysis_result

    def _get_buy_history_for_symbol(self, symbol):
        """Obtiene el historial de compras para un símbolo desde IOL"""
        from datetime import timedelta
        
        if self.paper_trading or not self.iol_client:
            return None
        
        try:
            # Buscar en últimos 365 días
            fecha_desde = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')
            
            history = self.iol_client.get_operation_history(fecha_desde, fecha_hasta)
            
            # Validar que history sea un diccionario
            if not isinstance(history, dict):
                print(f"⚠️  IOL devolvió formato inesperado: {type(history)}")
                return None
            
            if "error" in history:
                return None
            
            # Filtrar operaciones de compra para este símbolo
            buy_operations = []
            operaciones = history.get("operaciones", [])
            
            # Validar que operaciones sea una lista
            if not isinstance(operaciones, list):
                print(f"⚠️  'operaciones' no es una lista: {type(operaciones)}")
                return None
            
            for op in operaciones:
                if not isinstance(op, dict):
                    continue  # Saltar operaciones con formato inválido
                
                op_symbol = op.get('simbolo', '').upper()
                op_tipo = op.get('tipoOperacion', op.get('tipo', '')).upper()
                
                if op_symbol == symbol.upper() and ('COMPRA' in op_tipo or 'BUY' in op_tipo):
                    buy_operations.append(op)
            
            if not buy_operations:
                return None
            
            # Calcular precio promedio ponderado
            total_quantity = 0
            total_cost = 0
            buy_details = []
            
            for op in buy_operations:
                qty = op.get('cantidad', 0)
                price = op.get('precio', op.get('precioEjecutado', 0))
                fecha = op.get('fecha', op.get('fechaOperacion', 'N/A'))
                numero = op.get('numeroOperacion', 'N/A')
                
                if qty > 0 and price > 0:
                    total_quantity += qty
                    total_cost += qty * price
                    buy_details.append({
                        'operation_id': numero,
                        'date': fecha,
                        'quantity': qty,
                        'price': price,
                        'total': qty * price
                    })
            
            if total_quantity == 0:
                return None
            
            avg_price = total_cost / total_quantity
            
            return {
                'avg_price': avg_price,
                'total_quantity': total_quantity,
                'total_cost': total_cost,
                'buy_details': buy_details
            }
        except Exception as e:
            safe_warning(logger, f"Error obteniendo historial de compras para {symbol}: {e}")
            return None

    def _calculate_sale_pnl_with_history(self, symbol, sale_price, sale_quantity):
        """Calcula P&L de una venta usando historial de compras de IOL"""
        buy_history = self._get_buy_history_for_symbol(symbol)
        
        if not buy_history:
            return None
        
        avg_buy_price = buy_history['avg_price']
        sale_value = sale_quantity * sale_price
        cost_basis = sale_quantity * avg_buy_price
        pnl = sale_value - cost_basis
        pnl_pct = ((sale_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0
        
        return {
            'buy_price': avg_buy_price,
            'sale_price': sale_price,
            'quantity': sale_quantity,
            'cost_basis': cost_basis,
            'sale_value': sale_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'buy_history': buy_history
        }

    def _display_sale_comparison(self, symbol, sale_details):
        """Muestra visualización comparativa de venta con historial"""
        print("\n" + "="*70)
        print(f"📊 COMPARACIÓN: COMPRA vs VENTA - {symbol}")
        print("="*70)
        
        buy_history = sale_details.get('buy_history')
        
        # Mostrar historial de compras detallado
        if buy_history and buy_history.get('buy_details'):
            print(f"\n📜 HISTORIAL DE COMPRAS:")
            print("-"*70)
            print(f"{'#':<4} {'Fecha':<12} {'Operación':<12} {'Cantidad':<10} {'Precio':<15} {'Total':<15}")
            print("-"*70)
            
            for i, buy in enumerate(buy_history['buy_details'], 1):
                fecha_corta = buy['date'][:10] if len(buy['date']) > 10 else buy['date']
                print(f"{i:<4} {fecha_corta:<12} #{buy['operation_id']:<12} {buy['quantity']:<10} ${buy['price']:>12,.2f} ${buy['total']:>14,.2f}")
            
            print("-"*70)
            print(f"{'PROMEDIO':<40} {sale_details['quantity']:<10} {'PROMEDIO':<15} ${sale_details['buy_price']:>12,.2f} ${sale_details['cost_basis']:>14,.2f}")
            print("-"*70)
        
        # Tabla comparativa
        print(f"\n" + "="*70)
        print(f"📈 COMPARACIÓN LADO A LADO")
        print("="*70)
        print(f"{'Concepto':<30} {'Compra':<20} {'Venta':<20} {'Diferencia':<20}")
        print("-"*70)
        
        price_diff = sale_details['sale_price'] - sale_details['buy_price']
        price_diff_pct = sale_details['pnl_pct']
        
        compra_precio = f"${sale_details['buy_price']:,.2f} ARS"
        venta_precio = f"${sale_details['sale_price']:,.2f} ARS"
        diff_precio = f"${price_diff:,.2f} ({price_diff_pct:+.2f}%)"
        diff_precio_color = f"{'📈' if price_diff >= 0 else '📉'} {diff_precio}"
        print(f"{'Precio por acción':<30} {compra_precio:<20} {venta_precio:<20} {diff_precio_color:<20}")
        
        print(f"{'Cantidad':<30} {sale_details['quantity']:<20} {sale_details['quantity']:<20} {'-':<20}")
        
        compra_total = f"${sale_details['cost_basis']:,.2f} ARS"
        venta_total = f"${sale_details['sale_value']:,.2f} ARS"
        diff_total = f"${sale_details['pnl']:,.2f} ({sale_details['pnl_pct']:+.2f}%)"
        diff_total_color = f"{'📈' if sale_details['pnl'] >= 0 else '📉'} {diff_total}"
        print(f"{'Valor total':<30} {compra_total:<20} {venta_total:<20} {diff_total_color:<20}")
        
        print("="*70)
        
        # Resumen financiero destacado
        print(f"\n" + "="*70)
        print(f"💰 RESULTADO FINANCIERO")
        print("="*70)
        
        if sale_details['pnl'] >= 0:
            print(f"\n   ✅ GANANCIA REALIZADA")
            print(f"   💵 ${sale_details['pnl']:,.2f} ARS ({sale_details['pnl_pct']:+.2f}%)")
            print(f"\n   📊 Desglose:")
            print(f"      • Invertiste: ${sale_details['cost_basis']:,.2f} ARS")
            print(f"      • Recibirás: ${sale_details['sale_value']:,.2f} ARS")
            print(f"      • Ganancia: ${sale_details['pnl']:,.2f} ARS")
        else:
            print(f"\n   ❌ PÉRDIDA REALIZADA")
            print(f"   💸 ${abs(sale_details['pnl']):,.2f} ARS ({sale_details['pnl_pct']:+.2f}%)")
            print(f"\n   📊 Desglose:")
            print(f"      • Invertiste: ${sale_details['cost_basis']:,.2f} ARS")
            print(f"      • Recibirás: ${sale_details['sale_value']:,.2f} ARS")
            print(f"      • Pérdida: ${abs(sale_details['pnl']):,.2f} ARS")
        
        print("="*70)

    def execute_trade(self, symbol, signal, price, quantity, stop_loss, take_profit):
        """
        Execute trade (Paper or Live) with adaptive risk management.
        """
        # Check if trading is paused
        if self._paused:
            print(f"\n⏸️ Trading is PAUSED - Skipping trade execution for {symbol}")
            return {
                "status": "PAUSED",
                "symbol": symbol,
                "reason": "Trading is paused"
            }
        
        # Verificar disponibilidad en IOL antes de ejecutar (solo en live trading)
        if not self.paper_trading:
            from src.services.iol_availability_checker import IOLAvailabilityChecker
            availability_checker = IOLAvailabilityChecker(self.iol_client)
            is_available, error_msg = availability_checker.is_symbol_available(symbol)
            
            if not is_available:
                error_message = f"❌ No se puede operar {symbol}: {error_msg}"
                print(error_message)
                self.operation_notifier.notify_alert(
                    f"Operación cancelada: {symbol}",
                    error_message,
                    level="error"
                )
                return {
                    "status": "FAILED",
                    "error": error_msg,
                    "symbol": symbol,
                    "reason": "Symbol not available in IOL"
                }
        
        # Validación pre-operación
        can_trade, reason = self.risk_manager.can_trade()
        if not can_trade:
            print(f"\n⛔ Trade blocked by Risk Manager: {reason}")
            self.operation_notifier.notify_alert(
                f"Operación bloqueada: {symbol}",
                f"Risk Manager bloqueó la operación: {reason}",
                level="warning"
            )
            return {
                "status": "BLOCKED",
                "error": reason,
                "symbol": symbol,
                "reason": "Risk Manager blocked"
            }
        
        print(f"\n⚡ Executing {signal} Order:")
        print(f"   Symbol: {symbol}")
        print(f"   Quantity: {quantity}")
        print(f"   Price: ${price:.2f}")
        print(f"   Stop Loss: ${stop_loss:.2f}")
        print(f"   Take Profit: ${take_profit:.2f}")
        
        # Verificar rentabilidad después de comisiones (solo para BUY)
        if signal == 'BUY' and hasattr(self, 'commission_calculator') and self.commission_calculator:
            try:
                # Estimar precio de salida esperado (take_profit)
                expected_exit_price = take_profit if take_profit else price * 1.05  # 5% ganancia por defecto
                expected_profit_pct = ((expected_exit_price - price) / price) * 100
                
                commission_check = self.commission_calculator.should_execute_trade(
                    symbol, price, expected_exit_price, quantity, expected_profit_pct
                )
                
                if not commission_check['should_execute']:
                    print(f"\n⚠️  Trade no rentable después de comisiones:")
                    print(f"   Ganancia esperada: {expected_profit_pct:.2f}%")
                    print(f"   Costo total: {commission_check['total_cost_pct']:.2f}%")
                    print(f"   Ganancia neta: {commission_check['net_profit_pct']:.2f}%")
                    print(f"   Razón: {commission_check['reason']}")
                    
                    # Bloquear trade si ganancia neta es negativa o muy pequeña
                    if commission_check['net_profit_pct'] < 0:
                        return {
                            "status": "BLOCKED",
                            "error": commission_check['reason'],
                            "symbol": symbol,
                            "reason": "Trade no rentable después de comisiones"
                        }
                    else:
                        print(f"   ⚠️  Continuando con trade (ganancia pequeña pero positiva)")
                else:
                    print(f"\n✅ Análisis de Comisiones:")
                    print(f"   Ganancia esperada: {expected_profit_pct:.2f}%")
                    print(f"   Costo total: {commission_check['total_cost_pct']:.2f}%")
                    print(f"   Ganancia neta: {commission_check['net_profit_pct']:.2f}%")
            except Exception as e:
                print(f"   ⚠️  Error verificando comisiones: {e}")
                # Continuar sin bloquear si hay error
        
        # 📢 NOTIFICACIÓN: Mostrar ejecución de trade al usuario
        trade_data_for_notification = {
            'symbol': symbol,
            'signal': signal,
            'price': price,
            'quantity': quantity,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'mode': 'PAPER' if self.paper_trading else 'LIVE',
        }
        self.operation_notifier.notify_trade_execution(trade_data_for_notification)
        
        # 🚨 ALERTA EN TIEMPO REAL: Enviar alerta de trade ejecutado
        alert_level = 'CRITICAL' if not self.paper_trading else 'HIGH'
        self.realtime_alerts.alert_trade_execution(trade_data_for_notification, level=alert_level)
        
        # Agregar alertas de precio para stop loss y take profit
        if stop_loss:
            self.price_monitor.add_price_alert(symbol, stop_loss, 'below', 'HIGH')
        if take_profit:
            self.price_monitor.add_price_alert(symbol, take_profit, 'above', 'HIGH')
        
        # Crear registro de trade (inicialmente PENDING hasta confirmar ejecución)
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'signal': signal,
            'quantity': quantity,
            'price': price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'status': 'PENDING',  # PENDING hasta confirmar ejecución
            'mode': 'PAPER' if self.paper_trading else 'LIVE',
            'order_id': 'N/A'
        }
        
        # 🧠 APRENDIZAJE: Registrar trade para aprendizaje
        try:
            # Obtener información del análisis reciente
            recent_analysis = getattr(self, '_last_analysis', {})
            trade_data = {
                'symbol': symbol,
                'signal': signal,
                'entry_price': price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': quantity,
                'ai_prediction': recent_analysis.get('ai_signal', {}),
                'technical_score': recent_analysis.get('score', 0),
                'confidence': recent_analysis.get('confidence', 'LOW'),
                'market_conditions': {
                    'rsi': recent_analysis.get('technical_signal', {}).get('momentum', {}).get('rsi'),
                    'atr': recent_analysis.get('technical_signal', {}).get('volatility', {}).get('atr'),
                }
            }
            self.advanced_learning.learn_from_trade(trade_data)
            
            # 🧠 APRENDIZAJE MEJORADO: Aprender de entrada (sin P&L aún)
            # El P&L se registrará cuando se cierre la posición
        except Exception as e:
            print(f"⚠️  Error registrando trade para aprendizaje: {e}")
        
        if self.paper_trading:
            print("📝 [PAPER TRADING] Order simulated successfully")
            
            # Marcar como FILLED después de simular exitosamente
            trade_record['status'] = 'FILLED'
            
            # Si es una venta, calcular P&L simulado para aprendizaje
            if signal == 'SELL':
                # Buscar la compra correspondiente en trades.json
                try:
                    import json
                    trades = []
                    if os.path.exists(self.trades_file):
                        with open(self.trades_file, 'r') as f:
                            trades = json.load(f)
                    
                    # Buscar la última compra de este símbolo
                    buy_trade = None
                    for trade in reversed(trades):
                        if (trade.get('symbol') == symbol and 
                            trade.get('signal') == 'BUY' and 
                            trade.get('status') == 'FILLED'):
                            buy_trade = trade
                            break
                    
                    if buy_trade:
                        buy_price = buy_trade.get('price', price)
                        buy_quantity = buy_trade.get('quantity', quantity)
                        
                        # Calcular P&L simulado
                        cost_basis = buy_price * buy_quantity
                        sale_value = price * quantity
                        gross_pnl = sale_value - cost_basis
                        
                        # Calcular comisiones y P&L neto
                        commission_cost = 0.0
                        if hasattr(self, 'commission_calculator') and self.commission_calculator:
                            try:
                                round_trip = self.commission_calculator.calculate_round_trip_cost(
                                    symbol, buy_price, price, min(buy_quantity, quantity)
                                )
                                commission_cost = round_trip['total_commissions']
                                net_pnl = round_trip['net_pnl']
                                net_pnl_pct = (net_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                            except Exception as e:
                                print(f"   ⚠️  Error calculando comisiones: {e}")
                                net_pnl = gross_pnl
                                net_pnl_pct = (gross_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                        else:
                            net_pnl = gross_pnl
                            net_pnl_pct = (gross_pnl / cost_basis) * 100 if cost_basis > 0 else 0
                        
                        pnl = net_pnl  # Usar P&L neto
                        pnl_pct = net_pnl_pct
                        
                        trade_record['buy_price'] = buy_price
                        trade_record['pnl'] = pnl
                        trade_record['pnl_pct'] = pnl_pct
                        trade_record['cost_basis'] = cost_basis
                        trade_record['sale_value'] = sale_value
                        trade_record['commission'] = commission_cost
                        trade_record['gross_pnl'] = gross_pnl
                        trade_record['net_pnl'] = net_pnl
                        
                        print(f"📊 [PAPER TRADING] P&L Calculado:")
                        print(f"   Compra: ${buy_price:.2f} x {buy_quantity}")
                        print(f"   Venta: ${price:.2f} x {quantity}")
                        if commission_cost > 0:
                            print(f"   Comisiones: ${commission_cost:.2f}")
                            print(f"   P&L Bruto: ${gross_pnl:,.2f}")
                        pnl_str = f"${pnl:,.2f}" if pnl >= 0 else f"-${abs(pnl):,.2f}"
                        print(f"   P&L Neto: {pnl_str} ({pnl_pct:+.2f}%)")
                        
                        # Registrar P&L en risk manager (simulado)
                        self.risk_manager.record_trade(
                            symbol=symbol,
                            entry_price=buy_price,
                            exit_price=price,
                            quantity=min(buy_quantity, quantity),
                            side='SELL',
                            pnl=pnl
                        )
                        
                        # 🧠 APRENDIZAJE MEJORADO: Aprender del resultado del trade simulado
                        if hasattr(self, 'enhanced_learning') and self.enhanced_learning:
                            try:
                                recent_analysis = getattr(self, '_last_analysis', {})
                                market_conditions = {
                                    'volatility': 'HIGH' if recent_analysis.get('technical_signal', {}).get('volatility', {}).get('atr', 0) > 0.05 else 'MEDIUM',
                                    'trend': recent_analysis.get('technical_signal', {}).get('trend', {}).get('direction', 'NEUTRAL'),
                                    'rsi': recent_analysis.get('technical_signal', {}).get('momentum', {}).get('rsi', 50)
                                }
                                confidence = recent_analysis.get('confidence', 'MEDIUM')
                                
                                self.enhanced_learning.learn_from_trade(
                                    symbol=symbol,
                                    pnl=pnl,
                                    pnl_pct=pnl_pct,
                                    signal='SELL',
                                    confidence=confidence,
                                    market_conditions=market_conditions
                                )
                                print("✅ [PAPER TRADING] Aprendizaje registrado del P&L simulado")
                            except Exception as e:
                                safe_warning(logger, f"Error en aprendizaje mejorado (paper trading): {e}")
                except Exception as e:
                    safe_warning(logger, f"Error calculando P&L en paper trading: {e}")
            
            # Log simulated trade to JSON
            import json
            trades = []
            if os.path.exists(self.trades_file):
                try:
                    with open(self.trades_file, 'r') as f:
                        trades = json.load(f)
                except:
                    trades = []
            
            trades.append(trade_record)
            
            with open(self.trades_file, 'w') as f:
                json.dump(trades, f, indent=2)
            
            # Activar trailing stop si es compra exitosa
            if signal == 'BUY' and trade_record['status'] == 'FILLED':
                try:
                    self.trailing_stop_loss.add_position(
                        symbol=symbol,
                        entry_price=price,
                        quantity=quantity,
                        initial_stop_loss=stop_loss,
                        trail_pct=5.0,
                        activation_pct=3.0
                    )
                except Exception as e:
                    print(f"⚠️  Error activando trailing stop: {e}")
                
        else:
            # LIVE TRADING - Ejecutar en IOL REAL
            print("💸 [LIVE TRADING] Sending order to IOL...")
            print(f"   Symbol: {symbol}, Qty: {quantity}, Price: ${price:.2f}")
            
            try:
                # Verificar saldo disponible
                print("   📊 Verificando saldo disponible...")
                available_balance = self.iol_client.get_available_balance()
                required_capital = quantity * price
                
                print(f"   💰 Saldo disponible: ${available_balance:.2f}")
                print(f"   💵 Capital requerido: ${required_capital:.2f}")
                
                if required_capital > available_balance:
                    print(f"❌ Saldo insuficiente: ${available_balance:.2f} < ${required_capital:.2f}")
                    trade_record['status'] = 'FAILED'
                    trade_record['error'] = f'Insufficient balance (need ${required_capital:.2f}, have ${available_balance:.2f})'
                    
                    # Guardar el trade fallido para análisis
                    trades = self._load_trades()
                    trades.append(trade_record)
                    with open(self.trades_file, 'w') as f:
                        json.dump(trades, f, indent=2)
                    
                    return
                
                # Ejecutar orden en IOL
                print("   🚀 Enviando orden a IOL...")
                side = 'buy' if signal == 'BUY' else 'sell'
                response = self.iol_client.place_order(symbol, quantity, price, side)
                
                print(f"   📩 Respuesta de IOL: {response}")
                
                # Verificar respuesta
                if 'error' in response or response.get('success') == False:
                    error_msg = response.get('error', 'Unknown error')
                    print(f"❌ Orden rechazada por IOL: {error_msg}")
                    trade_record['status'] = 'FAILED'
                    trade_record['error'] = error_msg
                elif 'numeroOperacion' in response:
                    # Éxito - IOL devolvió número de operación
                    order_id = response.get('numeroOperacion')
                    print(f"✅ Orden ejecutada en IOL: ID {order_id}")
                    trade_record['order_id'] = order_id
                    trade_record['status'] = 'FILLED'
                else:
                    # Respuesta sin error pero sin numeroOperacion (raro)
                    print(f"⚠️  Respuesta inesperada de IOL (sin numeroOperacion): {response}")
                    trade_record['status'] = 'UNKNOWN'
                    trade_record['error'] = f'IOL response without numeroOperacion: {str(response)[:200]}'
                    trade_record['order_id'] = 'UNKNOWN'
                
                # Si es una venta y se ejecutó, calcular P&L usando historial de IOL
                if signal == 'SELL' and trade_record['status'] == 'FILLED':
                    try:
                        sale_pnl = self._calculate_sale_pnl_with_history(symbol, price, quantity)
                        if sale_pnl and isinstance(sale_pnl, dict):
                            trade_record['buy_price'] = sale_pnl['buy_price']
                            trade_record['pnl'] = sale_pnl['pnl']
                            trade_record['pnl_pct'] = sale_pnl['pnl_pct']
                            trade_record['cost_basis'] = sale_pnl['cost_basis']
                            trade_record['sale_value'] = sale_pnl['sale_value']
                            
                            # Mostrar visualización comparativa
                            self._display_sale_comparison(symbol, sale_pnl)
                            
                            # Registrar P&L en risk manager
                            self.risk_manager.record_trade(
                                symbol=symbol,
                                entry_price=sale_pnl['buy_price'],
                                exit_price=price,
                                quantity=quantity,
                                side='SELL',
                                pnl=sale_pnl['pnl']
                            )
                            
                            # 🧠 APRENDIZAJE MEJORADO: Aprender del resultado final del trade
                            if hasattr(self, 'enhanced_learning') and self.enhanced_learning:
                                try:
                                    recent_analysis = getattr(self, '_last_analysis', {})
                                    market_conditions = {
                                        'volatility': 'HIGH' if recent_analysis.get('technical_signal', {}).get('volatility', {}).get('atr', 0) > 0.05 else 'MEDIUM',
                                        'trend': recent_analysis.get('technical_signal', {}).get('trend', {}).get('direction', 'NEUTRAL'),
                                        'rsi': recent_analysis.get('technical_signal', {}).get('momentum', {}).get('rsi', 50)
                                    }
                                    confidence = recent_analysis.get('confidence', 'MEDIUM')
                                    
                                    self.enhanced_learning.learn_from_trade(
                                        symbol=symbol,
                                        pnl=sale_pnl['pnl'],
                                        pnl_pct=sale_pnl['pnl_pct'],
                                        signal='SELL',
                                        confidence=confidence,
                                        market_conditions=market_conditions
                                    )
                                except Exception as e:
                                    safe_warning(logger, f"Error en aprendizaje mejorado: {e}")
                    except Exception as e:
                        safe_warning(logger, f"Error calculando P&L de venta: {e}")
                    
                    # Registrar en risk manager
                    self.risk_manager.daily_trades_count += 1
                    
                    # Sincronizar portafolio automáticamente
                    self.sync_portfolio()
                
                # Log trade to JSON (con manejo robusto de errores)
                import json
                trades = []
                if os.path.exists(self.trades_file):
                    try:
                        with open(self.trades_file, 'r', encoding='utf-8') as f:
                            trades = json.load(f)
                        # Validar que trades es una lista
                        if not isinstance(trades, list):
                            trades = []
                    except (json.JSONDecodeError, IOError, OSError, ValueError) as e:
                        # Si hay error leyendo, empezar con lista vacía
                        trades = []
                        try:
                            safe_warning(logger, f"Error leyendo trades.json, iniciando nuevo: {e}")
                        except:
                            pass
                
                trades.append(trade_record)
                
                # Mantener solo últimas 1000 operaciones para evitar archivos muy grandes
                if len(trades) > 1000:
                    trades = trades[-1000:]
                
                try:
                    with open(self.trades_file, 'w', encoding='utf-8') as f:
                        json.dump(trades, f, indent=2, ensure_ascii=False)
                except (IOError, OSError, ValueError) as e:
                    # Si falla guardar, intentar guardar en archivo de respaldo
                    try:
                        backup_file = f"{self.trades_file}.backup"
                        with open(backup_file, 'w', encoding='utf-8') as f:
                            json.dump(trades, f, indent=2, ensure_ascii=False)
                        print(f"⚠️  Error guardando trades, guardado en backup: {backup_file}")
                    except:
                        print(f"⚠️  Error crítico guardando trades: {e}")

            except Exception as e:
                print(f"❌ Trade execution exception: {e}")
                trade_record['status'] = 'FAILED'
                trade_record['error'] = str(e)
                
                # Log failed trade (con manejo robusto)
                try:
                    import json
                    trades = []
                    if os.path.exists(self.trades_file):
                        try:
                            with open(self.trades_file, 'r', encoding='utf-8') as f:
                                trades = json.load(f)
                            if not isinstance(trades, list):
                                trades = []
                        except (json.JSONDecodeError, IOError, OSError):
                            trades = []
                    
                    trades.append(trade_record)
                    
                    # Mantener solo últimas 1000 operaciones
                    if len(trades) > 1000:
                        trades = trades[-1000:]
                    
                    with open(self.trades_file, 'w', encoding='utf-8') as f:
                        json.dump(trades, f, indent=2, ensure_ascii=False)
                except Exception as log_error:
                    print(f"⚠️  Error guardando trade fallido: {log_error}")
                    # Intentar guardar en backup
                    try:
                        backup_file = f"{self.trades_file}.backup"
                        with open(backup_file, 'a', encoding='utf-8') as f:
                            f.write(f"\n{datetime.now().isoformat()}: {json.dumps(trade_record, default=str)}\n")
                    except:
                        pass  # Si también falla el backup, continuar

    def _register_telegram_commands(self):
        """Registra comandos personalizados de Telegram"""
        import json
        if not self.telegram_command_handler:
            return
        
        # Comando para ver portafolio
        def handle_portfolio(chat_id, args):
            portfolio = load_portfolio()
            if not portfolio:
                self.telegram_command_handler._send_message(chat_id, "📊 *Portafolio*\n\nNo hay posiciones abiertas.")
                return
            
            total_value = sum(p.get('current_value', 0) for p in portfolio)
            total_cost = sum(p.get('cost_basis', 0) for p in portfolio)
            total_pnl = total_value - total_cost
            total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
            
            message = f"""📊 *Portafolio*

*Posiciones:* {len(portfolio)}
*Valor Total:* ${total_value:,.2f}
*Costo Total:* ${total_cost:,.2f}
*P&L:* ${total_pnl:,.2f} ({total_pnl_pct:+.2f}%)

*Posiciones:*
"""
            for pos in portfolio[:10]:  # Mostrar máximo 10
                symbol = pos.get('symbol', 'N/A')
                qty = pos.get('quantity', 0)
                price = pos.get('current_price', 0)
                pnl = pos.get('unrealized_pnl', 0)
                message += f"• {symbol}: {qty} @ ${price:.2f} (P&L: ${pnl:.2f})\n"
            
            if len(portfolio) > 10:
                message += f"\n... y {len(portfolio) - 10} más"
            
            self.telegram_command_handler._send_message(chat_id, message)
        
        # Comando para ver saldo
        def handle_balance(chat_id, args):
            if self.paper_trading:
                balance = self.capital
                message = f"💰 *Saldo (Paper Trading)*\n\n*Capital disponible:* ${balance:,.2f}"
            else:
                try:
                    balance = self.iol_client.get_available_balance()
                    # Actualizar capital interno si cambió
                    if balance != self.capital:
                        old_capital = self.capital
                        self.capital = balance
                        # Actualizar risk_manager
                        if hasattr(self.risk_manager, 'initial_capital'):
                            self.risk_manager.initial_capital = balance
                        if hasattr(self.risk_manager, 'current_capital'):
                            self.risk_manager.current_capital = balance
                        message = f"💰 *Saldo (Live Trading)*\n\n*Disponible:* ${balance:,.2f} ARS\n\n"
                        message += f"🔄 *Actualizado*\n"
                        message += f"Anterior: ${old_capital:,.2f}\n"
                        message += f"Nuevo: ${balance:,.2f}\n"
                        message += f"Diferencia: ${balance - old_capital:,.2f}"
                    else:
                        message = f"💰 *Saldo (Live Trading)*\n\n*Disponible:* ${balance:,.2f} ARS"
                except Exception as e:
                    message = f"❌ Error obteniendo saldo: {e}"
            
            self.telegram_command_handler._send_message(chat_id, message)
        
        # Comando para actualizar saldo manualmente
        def handle_update_balance(chat_id, args):
            """Actualiza el saldo desde IOL y actualiza el capital del bot"""
            if self.paper_trading:
                self.telegram_command_handler._send_message(
                    chat_id,
                    "ℹ️ En modo Paper Trading, el saldo no se actualiza desde IOL.\n"
                    "Usa /balance para ver el saldo simulado."
                )
                return
            
            try:
                self.telegram_command_handler._send_message(chat_id, "🔄 Actualizando saldo desde IOL...")
                old_capital = self.capital
                new_balance = self.iol_client.get_available_balance()
                
                if new_balance != old_capital:
                    self.capital = new_balance
                    # Actualizar risk_manager
                    if hasattr(self.risk_manager, 'initial_capital'):
                        self.risk_manager.initial_capital = new_balance
                    if hasattr(self.risk_manager, 'current_capital'):
                        self.risk_manager.current_capital = new_balance
                    if hasattr(self.risk_manager, 'config'):
                        # Recalcular tamaño de posición basado en nuevo capital
                        pass
                    
                    difference = new_balance - old_capital
                    message = f"""✅ *Saldo Actualizado*

*Anterior:* ${old_capital:,.2f} ARS
*Nuevo:* ${new_balance:,.2f} ARS
*Diferencia:* ${difference:,.2f} ARS

💡 El bot ahora usará este nuevo saldo para calcular posiciones.
"""
                    self.telegram_command_handler._send_message(chat_id, message)
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"ℹ️ El saldo no ha cambiado: ${new_balance:,.2f} ARS"
                    )
            except Exception as e:
                error_msg = f"❌ Error actualizando saldo: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
                print(error_msg)
        
        # Función helper para cargar/guardar professional_config.json
        def load_professional_config():
            """Carga professional_config.json"""
            config_file = Path("professional_config.json")
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    safe_error(logger, f"Error cargando professional_config.json: {e}")
            return {}
        
        def save_professional_config(config):
            """Guarda professional_config.json"""
            config_file = Path("professional_config.json")
            try:
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                return True
            except Exception as e:
                safe_error(logger, f"Error guardando professional_config.json: {e}")
                return False
        
        # Comando para ver configuración
        def handle_config(chat_id, args):
            try:
                from src.core.config_manager import get_config
                import json
                
                # Cargar professional_config.json
                prof_config = load_professional_config()
                
                # Obtener configuración de riesgo
                risk_config = self.risk_manager.config if hasattr(self.risk_manager, 'config') else {}
                max_position = prof_config.get('max_position_size_pct', risk_config.get('max_position_size_pct', 30))
                max_daily_trades = prof_config.get('max_daily_trades', risk_config.get('max_daily_trades', 10))
                max_daily_loss = prof_config.get('max_daily_loss_pct', risk_config.get('max_daily_loss_pct', 5))
                risk_per_trade = prof_config.get('risk_per_trade', 0.03)
                
                # Obtener configuración del bot
                symbols_count = len(self.symbols)
                mode = "💰 LIVE TRADING" if not self.paper_trading else "🧪 PAPER TRADING"
                capital = self.capital
                
                # Obtener configuración de autoconfiguración
                auto_config_enabled = prof_config.get('auto_configuration_enabled', True)
                config_mode = prof_config.get('configuration_mode', 'automatic')
                interval = prof_config.get('analysis_interval_minutes', 60)
                sentiment_enabled = prof_config.get('enable_sentiment_analysis', True)
                news_enabled = prof_config.get('enable_news_fetching', True)
                
                message = f"""⚙️ *Configuración del Bot*

*Modo:* {mode}
*Capital:* ${capital:,.2f}
*Símbolos monitoreados:* {symbols_count}
*Intervalo de análisis:* {interval} minutos

*📊 Gestión de Riesgo:*
• Riesgo por operación: {risk_per_trade*100:.1f}%
• Tamaño máximo de posición: {max_position}%
• Máximo de trades diarios: {max_daily_trades}
• Pérdida máxima diaria: {max_daily_loss}%

*⚙️ Autoconfiguración:*
• Estado: {'✅ Activada' if auto_config_enabled else '❌ Desactivada'}
• Modo: {config_mode.upper()}

*📰 Análisis:*
• Análisis de sentimiento: {'✅' if sentiment_enabled else '❌'}
• Obtención de noticias: {'✅' if news_enabled else '❌'}

*💡 Comandos de configuración:*
• `/set_risk <valor>` - Cambiar riesgo (ej: 0.03 = 3%)
• `/set_interval <min>` - Cambiar intervalo
• `/toggle_sentiment` - Activar/desactivar sentimiento
• `/toggle_news` - Activar/desactivar noticias
• `/toggle_autoconfig` - Activar/desactivar autoconfig
• `/set_mode <manual|automatic>` - Cambiar modo
"""
                self.telegram_command_handler._send_message(chat_id, message)
            except Exception as e:
                error_msg = f"❌ Error obteniendo configuración: {e}"
                print(error_msg)
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        # Comandos de configuración
        def handle_set_risk(chat_id, args):
            """Establece el riesgo por operación"""
            try:
                if not args or not args.strip():
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Uso: /set_risk <valor>\n"
                        "Ejemplo: /set_risk 0.03 (para 3%)\n"
                        "Valor actual: consulta con /config"
                    )
                    return
                
                value = float(args.strip())
                if value <= 0 or value > 1:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ El riesgo debe estar entre 0 y 1 (0.01 = 1%, 0.03 = 3%)"
                    )
                    return
                
                config = load_professional_config()
                config['risk_per_trade'] = value
                if save_professional_config(config):
                    # Actualizar risk_manager si es posible
                    if hasattr(self.risk_manager, 'config'):
                        self.risk_manager.config['risk_per_trade'] = value
                    
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"✅ Riesgo por operación actualizado a {value*100:.1f}%\n"
                        f"💡 Los cambios se aplicarán en el próximo ciclo"
                    )
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error guardando configuración"
                    )
            except ValueError:
                self.telegram_command_handler._send_message(
                    chat_id,
                    "❌ Valor inválido. Usa un número (ej: 0.03 para 3%)"
                )
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        def handle_set_interval(chat_id, args):
            """Establece el intervalo de análisis en minutos"""
            try:
                if not args or not args.strip():
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Uso: /set_interval <minutos>\n"
                        "Ejemplo: /set_interval 30 (para 30 minutos)\n"
                        "Valor actual: consulta con /config"
                    )
                    return
                
                minutes = int(args.strip())
                if minutes < 1 or minutes > 1440:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ El intervalo debe estar entre 1 y 1440 minutos (24 horas)"
                    )
                    return
                
                config = load_professional_config()
                config['analysis_interval_minutes'] = minutes
                if save_professional_config(config):
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"✅ Intervalo de análisis actualizado a {minutes} minutos\n"
                        f"💡 El cambio se aplicará en el próximo reinicio del bot"
                    )
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error guardando configuración"
                    )
            except ValueError:
                self.telegram_command_handler._send_message(
                    chat_id,
                    "❌ Valor inválido. Usa un número entero (ej: 60)"
                )
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        def handle_toggle_sentiment(chat_id, args):
            """Activa/desactiva el análisis de sentimiento"""
            try:
                config = load_professional_config()
                current = config.get('enable_sentiment_analysis', True)
                config['enable_sentiment_analysis'] = not current
                
                if save_professional_config(config):
                    status = "✅ Activado" if not current else "❌ Desactivado"
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"{status} análisis de sentimiento\n"
                        f"💡 El cambio se aplicará en el próximo ciclo"
                    )
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error guardando configuración"
                    )
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        def handle_toggle_news(chat_id, args):
            """Activa/desactiva la obtención de noticias"""
            try:
                config = load_professional_config()
                current = config.get('enable_news_fetching', True)
                config['enable_news_fetching'] = not current
                
                if save_professional_config(config):
                    status = "✅ Activado" if not current else "❌ Desactivado"
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"{status} obtención de noticias\n"
                        f"💡 El cambio se aplicará en el próximo ciclo"
                    )
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error guardando configuración"
                    )
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        def handle_toggle_autoconfig(chat_id, args):
            """Activa/desactiva la autoconfiguración"""
            try:
                config = load_professional_config()
                current = config.get('auto_configuration_enabled', True)
                config['auto_configuration_enabled'] = not current
                
                if save_professional_config(config):
                    status = "✅ Activada" if not current else "❌ Desactivada"
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"{status} autoconfiguración\n"
                        f"💡 El cambio se aplicará en el próximo ciclo"
                    )
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error guardando configuración"
                    )
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        def handle_set_mode(chat_id, args):
            """Cambia el modo de configuración (manual/automatic)"""
            try:
                if not args or not args.strip():
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Uso: /set_mode <manual|automatic>\n"
                        "Ejemplo: /set_mode manual"
                    )
                    return
                
                mode = args.strip().lower()
                if mode not in ['manual', 'automatic']:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Modo inválido. Usa 'manual' o 'automatic'"
                    )
                    return
                
                config = load_professional_config()
                config['configuration_mode'] = mode
                if save_professional_config(config):
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"✅ Modo de configuración cambiado a {mode.upper()}\n"
                        f"💡 El cambio se aplicará en el próximo ciclo"
                    )
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error guardando configuración"
                    )
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        # Comando para ajustar umbral de compra
        def handle_set_buy_threshold(chat_id, args):
            """Establece el umbral de compra (score mínimo para BUY)"""
            try:
                if not args or not args.strip():
                    config = load_professional_config()
                    current = config.get('buy_threshold', 30)
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"❌ Uso: /set_buy_threshold <valor>\n"
                        f"Ejemplo: /set_buy_threshold 25\n"
                        f"Valor actual: {current}\n"
                        f"💡 Valores más bajos = más operaciones (más riesgo)"
                    )
                    return
                
                value = int(args.strip())
                if value < 0 or value > 100:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ El umbral debe estar entre 0 y 100"
                    )
                    return
                
                config = load_professional_config()
                old_value = config.get('buy_threshold', 30)
                config['buy_threshold'] = value
                if save_professional_config(config):
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"✅ Umbral de compra actualizado: {old_value} → {value}\n"
                        f"💡 El bot operará cuando el score sea >= {value}\n"
                        f"⚠️  Valores más bajos aumentan operaciones pero también el riesgo"
                    )
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error guardando configuración"
                    )
            except ValueError:
                self.telegram_command_handler._send_message(
                    chat_id,
                    "❌ Valor inválido. Usa un número entero (ej: 25)"
                )
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        # Comando para ajustar umbral de venta
        def handle_set_sell_threshold(chat_id, args):
            """Establece el umbral de venta (score máximo para SELL)"""
            try:
                if not args or not args.strip():
                    config = load_professional_config()
                    current = config.get('sell_threshold', -30)
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"❌ Uso: /set_sell_threshold <valor>\n"
                        f"Ejemplo: /set_sell_threshold -25\n"
                        f"Valor actual: {current}\n"
                        f"💡 Valores más altos (menos negativos) = más ventas"
                    )
                    return
                
                value = int(args.strip())
                if value > 0 or value < -100:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ El umbral debe ser negativo (ej: -25, -30)"
                    )
                    return
                
                config = load_professional_config()
                old_value = config.get('sell_threshold', -30)
                config['sell_threshold'] = value
                if save_professional_config(config):
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"✅ Umbral de venta actualizado: {old_value} → {value}\n"
                        f"💡 El bot operará cuando el score sea <= {value}\n"
                        f"⚠️  Valores más altos (menos negativos) aumentan ventas"
                    )
                else:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error guardando configuración"
                    )
            except ValueError:
                self.telegram_command_handler._send_message(
                    chat_id,
                    "❌ Valor inválido. Usa un número entero negativo (ej: -25)"
                )
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        # Comando para ver scores recientes
        def handle_scores(chat_id, args):
            """Muestra los scores recientes de los análisis"""
            try:
                import json
                from datetime import datetime as dt
                
                # Leer desde operations_log.json
                operations_file = Path("data/operations_log.json")
                
                if not operations_file.exists():
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "ℹ️ No hay datos de análisis disponibles aún.\n"
                        "💡 Ejecuta /analyze para generar análisis y scores."
                    )
                    return
                
                # Leer y filtrar análisis recientes
                try:
                    with open(operations_file, 'r', encoding='utf-8') as f:
                        operations = json.load(f)
                    
                    # Filtrar solo análisis y ordenar por timestamp
                    analyses = [
                        op for op in operations 
                        if op.get('type') == 'ANALYSIS' and op.get('data', {}).get('score') is not None
                    ]
                    
                    # Ordenar por timestamp (más reciente primero)
                    analyses.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                    
                    if not analyses:
                        self.telegram_command_handler._send_message(
                            chat_id,
                            "ℹ️ No hay scores recientes disponibles.\n"
                            "💡 Ejecuta /analyze para generar análisis."
                        )
                        return
                    
                    # Tomar los últimos 10
                    recent_analyses = analyses[:10]
                    
                    message = "📊 *Scores Recientes:*\n\n"
                    config = load_professional_config()
                    buy_threshold = config.get('buy_threshold', 30)
                    sell_threshold = config.get('sell_threshold', -30)
                    
                    message += f"*Umbrales actuales:*\n"
                    message += f"• Compra: >= {buy_threshold}\n"
                    message += f"• Venta: <= {sell_threshold}\n\n"
                    message += "*Últimos análisis:*\n"
                    
                    for op in recent_analyses:
                        data = op.get('data', {})
                        symbol = data.get('symbol', 'N/A')
                        signal = data.get('final_signal', 'HOLD')
                        score = data.get('score', 0)
                        confidence = data.get('confidence', 'N/A')
                        timestamp = op.get('timestamp', '')
                        
                        # Formatear timestamp
                        try:
                            dt_obj = dt.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt_obj.strftime('%Y-%m-%d %H:%M')
                        except:
                            time_str = timestamp[:16] if len(timestamp) > 16 else timestamp
                        
                        emoji = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "🟡"
                        status = "✅ Operará" if (signal == 'BUY' and score >= buy_threshold) or (signal == 'SELL' and score <= sell_threshold) else "⏸️ No operará"
                        
                        message += f"{emoji} *{symbol}*: {signal}\n"
                        message += f"   Score: {score} | Conf: {confidence}\n"
                        message += f"   {status} | {time_str}\n\n"
                    
                    self.telegram_command_handler._send_message(chat_id, message)
                    
                except json.JSONDecodeError as e:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"❌ Error leyendo archivo de operaciones: {e}\n"
                        "💡 El archivo puede estar corrupto."
                    )
                except Exception as e:
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"❌ Error procesando scores: {e}"
                    )
                    print(f"Error en handle_scores: {e}")
                    import traceback
                    traceback.print_exc()
                    
            except Exception as e:
                error_msg = f"❌ Error obteniendo scores: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
                print(error_msg)
                import traceback
                traceback.print_exc()
        
        # Comando para ejecutar análisis manualmente
        def handle_analyze(chat_id, args):
            # Verificar si hay símbolos para analizar
            if not self.symbols or len(self.symbols) == 0:
                self.telegram_command_handler._send_message(
                    chat_id,
                    "⚠️ No hay símbolos configurados para analizar.\n\n"
                    "💡 Soluciones:\n"
                    "• Verifica tu portafolio en IOL\n"
                    "• Agrega símbolos manualmente en el dashboard\n"
                    "• Verifica la configuración de monitoreo con /config"
                )
                return
            
            self.telegram_command_handler._send_message(
                chat_id, 
                f"🔄 Iniciando análisis manual de {len(self.symbols)} símbolo(s)..."
            )
            try:
                # Ejecutar ciclo de análisis en un thread para no bloquear
                import threading
                def run_analysis():
                    try:
                        results = self.run_analysis_cycle()
                        
                        if not results or len(results) == 0:
                            self.telegram_command_handler._send_message(
                                chat_id,
                                "⚠️ No se generaron resultados de análisis.\n\n"
                                "💡 Posibles causas:\n"
                                "• Errores al obtener datos de los símbolos\n"
                                "• Símbolos no disponibles en IOL\n"
                                "• Problemas de conexión\n\n"
                                "💡 Revisa los logs del bot para más detalles."
                            )
                            return
                        
                        # Enviar resumen
                        signals = [r for r in results if r.get('final_signal') != 'HOLD']
                        summary = f"""✅ *Análisis Completado*

*Símbolos analizados:* {len(results)}
*Señales detectadas:* {len(signals)}
*Hora:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
                        if signals:
                            summary += "*Señales:*\n"
                            for result in signals[:10]:  # Limitar a 10
                                symbol = result.get('symbol', 'N/A')
                                signal = result.get('final_signal', 'N/A')
                                score = result.get('score', 0)
                                emoji = "🟢" if signal == 'BUY' else "🔴"
                                summary += f"{emoji} {symbol}: {signal} (Score: {score})\n"
                        else:
                            summary += "ℹ️ Todas las señales están en HOLD\n"
                            summary += "💡 Usa /scores para ver los scores detallados"
                        
                        self.telegram_command_handler._send_message(chat_id, summary)
                    except Exception as e:
                        error_msg = f"❌ Error en análisis: {e}"
                        print(error_msg)
                        import traceback
                        traceback.print_exc()
                        self.telegram_command_handler._send_message(chat_id, error_msg)
                
                thread = threading.Thread(target=run_analysis, daemon=True)
                thread.start()
            except Exception as e:
                error_msg = f"❌ Error iniciando análisis: {e}"
                print(error_msg)
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        # Comando para ver estado del bot
        def handle_status(chat_id, args):
            """Muestra el estado completo del bot incluyendo modo de trading"""
            try:
                from pathlib import Path
                import os
                
                # Verificar si el bot está corriendo
                pid_file = Path("bot.pid")
                bot_running = pid_file.exists()
                
                if bot_running:
                    try:
                        with open(pid_file, 'r') as f:
                            pid = int(f.read().strip())
                        # Verificar si el proceso realmente existe usando psutil si está disponible
                        try:
                            import psutil  # type: ignore
                            if psutil.pid_exists(pid):
                                try:
                                    process = psutil.Process(pid)
                                    if 'python' in process.name().lower() or 'run_bot' in ' '.join(process.cmdline()):
                                        bot_running = True
                                    else:
                                        bot_running = False
                                except:
                                    bot_running = False
                            else:
                                bot_running = False
                        except ImportError:
                            # psutil no disponible, confiar en el archivo PID
                            pass
                    except:
                        bot_running = False
                
                status_icon = "🟢" if bot_running else "🔴"
                status_text = "ACTIVO" if bot_running else "INACTIVO"
                
                # Obtener modo de trading
                mode = "💰 LIVE TRADING" if not self.paper_trading else "🧪 PAPER TRADING"
                mode_emoji = "💰" if not self.paper_trading else "🧪"
                mode_warning = "⚠️ OPERANDO CON DINERO REAL" if not self.paper_trading else "ℹ️ Modo simulación (no opera con dinero real)"
                
                # Obtener información adicional
                symbols_count = len(self.symbols) if self.symbols else 0
                capital = self.capital
                
                # Cargar configuración
                config = load_professional_config()
                buy_threshold = config.get('buy_threshold', 30)
                sell_threshold = config.get('sell_threshold', -30)
                interval = config.get('analysis_interval_minutes', 60)
                
                # Calcular P&L diario y posiciones
                daily_pnl = 0
                daily_trades = 0
                if hasattr(self, 'risk_manager'):
                    daily_pnl = self.risk_manager.daily_pnl
                    daily_trades = self.risk_manager.daily_trades_count
                
                # Cargar portfolio de forma segura
                try:
                    from src.services.portfolio_persistence import load_portfolio
                    portfolio = load_portfolio()
                    open_positions = len(portfolio) if portfolio else 0
                except Exception as e:
                    # Si no se puede cargar el portfolio, usar 0 o verificar si existe self.portfolio
                    if hasattr(self, 'portfolio') and self.portfolio:
                        open_positions = len(self.portfolio)
                    else:
                        open_positions = 0
                
                response = f"""{status_icon} *Estado del Bot*

*Estado:* {status_text}
*Modo:* {mode}
{mode_warning}

*📊 Hoy:*
• P&L: ${daily_pnl:+,.2f}
• Trades: {daily_trades}
• Posiciones: {open_positions}

*⚙️ Configuración:*
• Capital: ${capital:,.2f} ARS
• Símbolos monitoreados: {symbols_count}
• Intervalo de análisis: {interval} minutos

*🎯 Umbrales de Trading:*
• Compra: score >= {buy_threshold}
• Venta: score <= {sell_threshold}

*⏰ Última actualización:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                self.telegram_command_handler._send_message(chat_id, response)
            except Exception as e:
                error_msg = f"❌ Error obteniendo estado: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
                print(error_msg)
                import traceback
                traceback.print_exc()
        
        # Comando para iniciar el bot en modo LIVE
        def handle_start_live(chat_id, args):
            """Inicia el bot en modo LIVE trading desde Telegram"""
            try:
                from pathlib import Path
                import subprocess
                import sys
                import os
                
                # Verificar si el bot ya está corriendo
                pid_file = Path("bot.pid")
                bot_running = False
                
                if pid_file.exists():
                    try:
                        with open(pid_file, 'r') as f:
                            pid = int(f.read().strip())
                        try:
                            import psutil  # type: ignore
                            if psutil.pid_exists(pid):
                                try:
                                    process = psutil.Process(pid)
                                    cmdline = ' '.join(process.cmdline())
                                    if 'run_bot' in cmdline or 'trading_bot' in cmdline:
                                        bot_running = True
                                except:
                                    pass
                        except ImportError:
                            pass
                    except:
                        pass
                
                if bot_running:
                    # El bot ya está corriendo
                    current_mode = "💰 LIVE TRADING" if not self.paper_trading else "🧪 PAPER TRADING"
                    self.telegram_command_handler._send_message(
                        chat_id,
                        f"""⚠️ *El bot ya está corriendo*

*Modo actual:* {current_mode}

💡 Para cambiar a modo LIVE:
1. Detén el bot primero con /restart_full
2. O desde el dashboard presiona "Detener Bot"
3. Luego ejecuta este comando nuevamente

⚠️ *IMPORTANTE:* No puedes cambiar el modo mientras el bot está corriendo.
"""
                    )
                    return
                
                # El bot no está corriendo, intentar iniciarlo
                self.telegram_command_handler._send_message(
                    chat_id,
                    "🚀 Iniciando bot en modo LIVE TRADING...\n\n"
                    "⏳ Esto puede tomar unos segundos..."
                )
                
                # Obtener la ruta del script run_bot.py
                script_dir = Path(__file__).parent
                run_bot_script = script_dir / "run_bot.py"
                
                if not run_bot_script.exists():
                    self.telegram_command_handler._send_message(
                        chat_id,
                        "❌ Error: No se encontró run_bot.py\n\n"
                        "💡 Inicia el bot manualmente desde la terminal:\n"
                        "   python run_bot.py --live --continuous"
                    )
                    return
                
                # Determinar el comando según el sistema operativo
                python_cmd = sys.executable
                
                # Crear el comando para iniciar el bot
                cmd = [python_cmd, str(run_bot_script), "--live", "--continuous"]
                
                # En Windows, usar CREATE_NEW_CONSOLE para abrir una nueva ventana
                if sys.platform == 'win32':
                    try:
                        # Intentar iniciar en una nueva ventana de consola
                        subprocess.Popen(
                            cmd,
                            creationflags=subprocess.CREATE_NEW_CONSOLE,
                            cwd=str(script_dir)
                        )
                        
                        self.telegram_command_handler._send_message(
                            chat_id,
                            """✅ *Bot iniciado en modo LIVE TRADING*

💰 *MODO: LIVE TRADING*
⚠️ *OPERANDO CON DINERO REAL*

*El bot se está iniciando en una nueva ventana...*

💡 Verifica:
• Que la ventana del bot se haya abierto
• Que muestre "💰 LIVE TRADING" en los logs
• Usa /status para verificar el estado

⚠️ *ADVERTENCIA:* El bot ahora operará con dinero real.
"""
                        )
                    except Exception as e:
                        self.telegram_command_handler._send_message(
                            chat_id,
                            f"""❌ Error iniciando el bot: {e}

💡 Inicia el bot manualmente desde la terminal:
   cd financial_ai
   python run_bot.py --live --continuous

O desde PowerShell:
   cd financial_ai; python run_bot.py --live --continuous
"""
                        )
                else:
                    # En Linux/Mac, iniciar en background
                    try:
                        subprocess.Popen(
                            cmd,
                            cwd=str(script_dir),
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True
                        )
                        
                        self.telegram_command_handler._send_message(
                            chat_id,
                            """✅ *Bot iniciado en modo LIVE TRADING*

💰 *MODO: LIVE TRADING*
⚠️ *OPERANDO CON DINERO REAL*

*El bot se está ejecutando en segundo plano...*

💡 Usa /status para verificar el estado

⚠️ *ADVERTENCIA:* El bot ahora operará con dinero real.
"""
                        )
                    except Exception as e:
                        self.telegram_command_handler._send_message(
                            chat_id,
                            f"""❌ Error iniciando el bot: {e}

💡 Inicia el bot manualmente desde la terminal:
   cd financial_ai
   python run_bot.py --live --continuous &
"""
                        )
                        
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
                print(error_msg)
                import traceback
                traceback.print_exc()
        # Comando para reporte diario manual
        def handle_daily_report(chat_id, args):
            """Genera y envía el reporte diario manualmente"""
            try:
                if not hasattr(self, 'daily_report_service') or self.daily_report_service is None:
                    self.telegram_command_handler._send_message(chat_id, "⚠️ Servicio de reportes diarios no disponible")
                    return
                self.telegram_command_handler._send_message(chat_id, "📊 Generando reporte diario...")
                success = self.daily_report_service.send_daily_report()
                if success:
                    self.telegram_command_handler._send_message(chat_id, "✅ Reporte diario enviado correctamente")
                else:
                    self.telegram_command_handler._send_message(chat_id, "⚠️ Error generando reporte diario")
            except Exception as e:
                error_msg = f"❌ Error generando reporte: {str(e)}"
                self.telegram_command_handler._send_message(chat_id, error_msg)

        # Comando para resumen de mercado
        def handle_market_summary(chat_id, args):
            """Envía un resumen del mercado"""
            try:
                self.telegram_command_handler._send_message(chat_id, "🌎 Analizando mercado...")
                
                # Índices principales
                indices = {
                    'SPY': 'S&P 500',
                    'QQQ': 'Nasdaq 100',
                    'IWM': 'Russell 2000',
                    'BTC-USD': 'Bitcoin'
                }
                
                summary = "🌎 *Resumen de Mercado*\n\n"
                
                import yfinance as yf
                for ticker, name in indices.items():
                    try:
                        data = yf.Ticker(ticker).history(period="2d")
                        if len(data) >= 2:
                            current = data['Close'].iloc[-1]
                            prev = data['Close'].iloc[-2]
                            change_pct = ((current - prev) / prev) * 100
                            emoji = "🟢" if change_pct >= 0 else "🔴"
                            summary += f"{emoji} *{name}*: ${current:,.2f} ({change_pct:+.2f}%)\n"
                    except:
                        summary += f"⚪ *{name}*: N/A\n"
                
                # Sentimiento (si está disponible)
                if hasattr(self, 'sentiment_analysis'):
                    try:
                        sentiment = self.sentiment_analysis.get_market_sentiment()
                        score = sentiment.get('score', 0)
                        label = sentiment.get('label', 'NEUTRAL')
                        emoji = "🟢" if score > 0.2 else "🔴" if score < -0.2 else "🟡"
                        summary += f"\n*Sentimiento:* {emoji} {label} ({score:.2f})"
                    except:
                        pass
                
                summary += f"\n\n⏰ {datetime.now().strftime('%H:%M')}"
                self.telegram_command_handler._send_message(chat_id, summary)
            except Exception as e:
                self.telegram_command_handler._send_message(chat_id, f"❌ Error: {str(e)}")

        # Comando para gráfico simple (texto)
        def handle_chart(chat_id, args):
            """Envía datos recientes de un símbolo"""
            symbol = args.strip().upper()
            if not symbol:
                self.telegram_command_handler._send_message(chat_id, "⚠️ Debes especificar un símbolo. Ej: /chart AAPL")
                return
            
            try:
                import yfinance as yf
                data = yf.Ticker(symbol).history(period="5d")
                if data.empty:
                    self.telegram_command_handler._send_message(chat_id, f"⚠️ No hay datos para {symbol}")
                    return
                
                msg = f"📈 *{symbol} - Últimos 5 días*\n\n"
                for date, row in data.iterrows():
                    date_str = date.strftime('%m-%d')
                    close = row['Close']
                    msg += f"• {date_str}: ${close:,.2f}\n"
                
                current = data['Close'].iloc[-1]
                start = data['Close'].iloc[0]
                change = ((current - start) / start) * 100
                emoji = "🟢" if change >= 0 else "🔴"
                msg += f"\n*Cambio 5d:* {emoji} {change:+.2f}%"
                
                self.telegram_command_handler._send_message(chat_id, msg)
            except Exception as e:
                self.telegram_command_handler._send_message(chat_id, f"❌ Error: {str(e)}")

        # Comando para detener el bot
        def handle_stop(chat_id, args):
            """Detiene el bot de forma segura"""
            self.telegram_command_handler._send_message(chat_id, "🛑 Deteniendo bot... (Esto puede tomar unos segundos)")
            try:
                # Crear flag de parada
                with open("stop_flag.txt", "w") as f:
                    f.write("stop")
            except Exception as e:
                self.telegram_command_handler._send_message(chat_id, f"❌ Error intentando detener: {e}")

        # Comando para pausar trading
        def handle_pause(chat_id, args):
            """Pausa el trading (sigue analizando pero no ejecuta)"""
            self._paused = True
            self.telegram_command_handler._send_message(chat_id, "⏸️ Trading pausado. El bot seguirá analizando pero NO ejecutará trades.\n💡 Usa /resume para reanudar.")

        # Comando para reanudar trading
        def handle_resume(chat_id, args):
            """Reanuda el trading"""
            self._paused = False
            self.telegram_command_handler._send_message(chat_id, "▶️ Trading reanudado. El bot volverá a ejecutar trades.")

        # Comando para silenciar notificaciones
        def handle_silence(chat_id, args):
            """Silencia notificaciones por X minutos"""
            try:
                minutes = int(args.strip()) if args.strip() else 60
                self._silence_until = datetime.now() + timedelta(minutes=minutes)
                self.telegram_command_handler._send_message(chat_id, f"🔕 Notificaciones silenciadas por {minutes} minutos.\n⏰ Reanudarán a las {self._silence_until.strftime('%H:%M')}")
            except ValueError:
                self.telegram_command_handler._send_message(chat_id, "⚠️ Formato incorrecto. Uso: /silence <minutos>")

        # Comando para reactivar notificaciones
        def handle_unsilence(chat_id, args):
            """Reactiva notificaciones"""
            self._silence_until = None
            self.telegram_command_handler._send_message(chat_id, "🔔 Notificaciones reactivadas.")

        # Comando para ver próximo análisis
        def handle_next(chat_id, args):
            """Muestra cuándo será el próximo análisis"""
            try:
                import json
                config_file = Path("professional_config.json")
                interval = 60
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        interval = config.get('analysis_interval_minutes', 60)
                
                if self._last_analysis_time:
                    next_analysis = self._last_analysis_time + timedelta(minutes=interval)
                    remaining = next_analysis - datetime.now()
                    minutes_left = int(remaining.total_seconds() / 60)
                    msg = f"⏱️ Próximo análisis en: {minutes_left} minutos\n🕐 Hora estimada: {next_analysis.strftime('%H:%M:%S')}"
                else:
                    msg = f"⏱️ Próximo análisis: en curso o próximamente\n⚙️ Intervalo configurado: {interval} minutos"
                
                self.telegram_command_handler._send_message(chat_id, msg)
            except Exception as e:
                self.telegram_command_handler._send_message(chat_id, f"❌ Error: {e}")

        # Comando para analizar símbolo específico
        def handle_analyze(chat_id, args):
            """Analiza un símbolo específico bajo demanda"""
            symbol = args.strip().upper()
            if not symbol:
                self.telegram_command_handler._send_message(chat_id, "⚠️ Especifica un símbolo. Uso: /analyze AAPL")
                return
            
            self.telegram_command_handler._send_message(chat_id, f"🔍 Analizando {symbol}...")
            try:
                result = self.analyze_symbol(symbol)
                signal = result.get('final_signal', 'HOLD')
                confidence = result.get('confidence', 'LOW')
                score = result.get('score', 0)
                
                emoji = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "⚪"
                msg = f"""{emoji} *Análisis de {symbol}*

*Señal:* {signal}
*Confianza:* {confidence}
*Score:* {score}

⏰ {datetime.now().strftime('%H:%M:%S')}"""
                self.telegram_command_handler._send_message(chat_id, msg)
            except Exception as e:
                self.telegram_command_handler._send_message(chat_id, f"❌ Error analizando {symbol}: {e}")

        # Comando para ver posiciones
        def handle_positions(chat_id, args):
            """Muestra posiciones abiertas con P&L"""
            try:
                from src.services.portfolio_persistence import load_portfolio
                portfolio = load_portfolio()
                
                if not portfolio:
                    self.telegram_command_handler._send_message(chat_id, "📊 No hay posiciones abiertas.")
                    return
                
                msg = "📊 *Posiciones Abiertas*\n\n"
                total_value = 0
                total_pnl = 0
                
                for pos in portfolio:
                    symbol = pos.get('symbol', 'N/A')
                    quantity = pos.get('quantity', 0)
                    avg_price = pos.get('average_price', 0)
                    current_price = pos.get('current_price', avg_price)
                    
                    position_value = quantity * current_price
                    position_pnl = (current_price - avg_price) * quantity
                    pnl_pct = ((current_price / avg_price) - 1) * 100 if avg_price > 0 else 0
                    
                    total_value += position_value
                    total_pnl += position_pnl
                    
                    emoji = "🟢" if position_pnl > 0 else "🔴" if position_pnl < 0 else "⚪"
                    msg += f"{emoji} *{symbol}*\n"
                    msg += f"   Cantidad: {quantity}\n"
                    msg += f"   Precio Prom: ${avg_price:.2f}\n"
                    msg += f"   Precio Actual: ${current_price:.2f}\n"
                    msg += f"   P&L: ${position_pnl:+.2f} ({pnl_pct:+.2f}%)\n\n"
                
                msg += f"━━━━━━━━━━━━━━━━\n"
                msg += f"💰 Valor Total: ${total_value:.2f}\n"
                msg += f"📈 P&L Total: ${total_pnl:+.2f}"
                
                self.telegram_command_handler._send_message(chat_id, msg)
            except Exception as e:
                self.telegram_command_handler._send_message(chat_id, f"❌ Error obteniendo posiciones: {e}")

        # Comando para ver P&L
        def handle_pnl(chat_id, args):
            """Muestra resumen de P&L"""
            try:
                from src.services.portfolio_persistence import load_portfolio
                portfolio = load_portfolio()
                
                total_pnl = 0
                for pos in portfolio:
                    avg_price = pos.get('average_price', 0)
                    current_price = pos.get('current_price', avg_price)
                    quantity = pos.get('quantity', 0)
                    total_pnl += (current_price - avg_price) * quantity
                
                emoji = "📈" if total_pnl > 0 else "📉" if total_pnl < 0 else "➖"
                msg = f"""{emoji} *Resumen P&L*

💰 P&L Total: ${total_pnl:+.2f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
                
                self.telegram_command_handler._send_message(chat_id, msg)
            except Exception as e:
                self.telegram_command_handler._send_message(chat_id, f"❌ Error calculando P&L: {e}")

        # Comando para cambiar intervalo de análisis
        def handle_set_interval(chat_id, args):
            """Cambia el intervalo de análisis dinámicamente"""
            try:
                minutes = int(args.strip())
                if minutes < 1:
                    self.telegram_command_handler._send_message(chat_id, "⚠️ El intervalo debe ser mayor a 0 minutos.")
                    return
                
                # Actualizar configuración
                config = load_professional_config()
                config['analysis_interval_minutes'] = minutes
                save_professional_config(config)
                
                self.telegram_command_handler._send_message(chat_id, f"✅ Intervalo de análisis actualizado a {minutes} minutos.\n🔄 El cambio se aplicará en el próximo ciclo.")
            except ValueError:
                self.telegram_command_handler._send_message(chat_id, "⚠️ Formato incorrecto. Uso: /set_interval <minutos>")
            except Exception as e:
                self.telegram_command_handler._send_message(chat_id, f"❌ Error actualizando intervalo: {e}")

        # Registrar comandos (con alias en español)
        self.telegram_command_handler.register_command('/set_interval', handle_set_interval)
        self.telegram_command_handler.register_command('/intervalo', handle_set_interval)
        self.telegram_command_handler.register_command('/daily_report', handle_daily_report)
        self.telegram_command_handler.register_command('/reporte_diario', handle_daily_report)
        self.telegram_command_handler.register_command('/market', handle_market_summary)
        self.telegram_command_handler.register_command('/mercado', handle_market_summary)
        self.telegram_command_handler.register_command('/chart', handle_chart)
        self.telegram_command_handler.register_command('/grafico', handle_chart)
        self.telegram_command_handler.register_command('/status', handle_status)
        self.telegram_command_handler.register_command('/estado', handle_status)  # Alias en español
        self.telegram_command_handler.register_command('/start_live', handle_start_live)
        self.telegram_command_handler.register_command('/iniciar_live', handle_start_live)  # Alias en español
        self.telegram_command_handler.register_command('/iniciarlive', handle_start_live)  # Sin guión
        self.telegram_command_handler.register_command('/portfolio', handle_portfolio)
        self.telegram_command_handler.register_command('/portafolio', handle_portfolio)  # Alias en español
        self.telegram_command_handler.register_command('/balance', handle_balance)
        self.telegram_command_handler.register_command('/saldo', handle_balance)  # Alias en español
        self.telegram_command_handler.register_command('/analyze', handle_analyze)
        self.telegram_command_handler.register_command('/analizar', handle_analyze)  # Alias en español
        
        # Comandos para controlar el bot autónomo
        def handle_start_bot(chat_id, args):
            """Inicia el bot autónomo"""
            import subprocess
            import sys
            from pathlib import Path
            
            PID_FILE = Path("bot.pid")
            if PID_FILE.exists():
                try:
                    with open(PID_FILE, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Verificar si el proceso existe (psutil opcional)
                    pid_exists = False
                    try:
                        import psutil  # type: ignore
                        pid_exists = psutil.pid_exists(pid)
                    except ImportError:
                        # Si psutil no está disponible, usar método alternativo
                        try:
                            os.kill(pid, 0)  # Signal 0 solo verifica existencia
                            pid_exists = True
                        except (OSError, ProcessLookupError):
                            pid_exists = False
                    
                    if pid_exists:
                        self.telegram_command_handler._send_message(
                            chat_id,
                            "⚠️ El bot autónomo ya está activo.\n\n"
                            "💡 Usa /bot_estado para ver el estado actual."
                        )
                        return
                except:
                    pass
            
            # Parsear argumentos
            args_list = args.strip().split() if args.strip() else []
            paper_mode = True  # Por defecto Paper Trading
            interval = 60
            enable_chat = False
            use_full_universe = False
            
            # Procesar argumentos
            if 'live' in args_list or 'real' in args_list:
                paper_mode = False
            if 'paper' in args_list or 'sim' in args_list:
                paper_mode = True
            
            # Buscar intervalo
            for i, arg in enumerate(args_list):
                if arg in ['--interval', '-i', 'interval'] and i + 1 < len(args_list):
                    try:
                        interval = int(args_list[i + 1])
                    except:
                        pass
            
            if '--chat' in args_list or 'chat' in args_list:
                enable_chat = True
            if '--universo' in args_list or 'universo' in args_list or 'full' in args_list:
                use_full_universe = True
            
            # Construir comando
            cmd = [sys.executable, 'run_bot.py', '--continuous', '--interval', str(interval)]
            if paper_mode:
                cmd.append('--paper')
            else:
                cmd.append('--live')
            if enable_chat:
                cmd.append('--chat')
            
            # Configurar universo completo si está habilitado
            if use_full_universe:
                config_file = Path("professional_config.json")
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        config['use_full_universe'] = True
                        with open(config_file, 'w', encoding='utf-8') as f:
                            json.dump(config, f, indent=2, ensure_ascii=False)
                    except:
                        pass
            
            try:
                if sys.platform == 'win32':
                    proc = subprocess.Popen(
                        cmd,
                        cwd=os.getcwd(),
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    proc = subprocess.Popen(cmd, cwd=os.getcwd())
                
                with open(PID_FILE, 'w') as f:
                    f.write(str(proc.pid))
                
                mode_text = "🧪 Paper Trading (Simulación)" if paper_mode else "💰 LIVE TRADING (Dinero Real)"
                features = []
                if enable_chat:
                    features.append("Chat Interactivo")
                if use_full_universe:
                    features.append("Universo Completo")
                
                message = f"""✅ *Bot Autónomo Iniciado*

*Modo:* {mode_text}
*Intervalo:* {interval} minutos"""
                
                if features:
                    message += f"\n*Características:* {', '.join(features)}"
                
                message += "\n\n💡 El bot comenzará a analizar y operar automáticamente."
                
                if not paper_mode:
                    message += "\n\n⚠️ *ADVERTENCIA:* Modo LIVE TRADING activo - Usa dinero real."
                
                self.telegram_command_handler._send_message(chat_id, message)
            except Exception as e:
                error_msg = f"❌ Error iniciando bot: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        def handle_stop_bot(chat_id, args):
            """Detiene el bot autónomo"""
            from pathlib import Path
            try:
                import psutil  # type: ignore
            except ImportError:
                self.telegram_command_handler._send_message(
                    chat_id,
                    "❌ Error: psutil no disponible. No se puede detener el bot."
                )
                return
            
            PID_FILE = Path("bot.pid")
            if not PID_FILE.exists():
                self.telegram_command_handler._send_message(
                    chat_id,
                    "ℹ️ El bot autónomo no está activo."
                )
                return
            
            try:
                with open(PID_FILE, 'r') as f:
                    pid = int(f.read().strip())
                
                # Intentar detener el proceso
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        process.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # Limpiar PID
                if PID_FILE.exists():
                    PID_FILE.unlink()
                
                self.telegram_command_handler._send_message(
                    chat_id,
                    "✅ *Bot Autónomo Detenido*\n\n"
                    "💡 El bot ha dejado de operar."
                )
            except Exception as e:
                error_msg = f"❌ Error deteniendo bot: {e}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        def handle_bot_status(chat_id, args):
            """Muestra el estado del bot autónomo"""
            from pathlib import Path
            try:
                import psutil  # type: ignore
            except ImportError:
                psutil = None
            
            PID_FILE = Path("bot.pid")
            bot_running = False
            pid = None
            
            if PID_FILE.exists():
                try:
                    with open(PID_FILE, 'r') as f:
                        pid = int(f.read().strip())
                    if psutil:
                        try:
                            process = psutil.Process(pid)
                            bot_running = process.is_running()
                        except:
                            bot_running = False
                    else:
                        # Sin psutil, solo verificar que el archivo existe
                        bot_running = True
                except:
                    bot_running = False
            
            status_icon = "🟢" if bot_running else "🔴"
            status_text = "ACTIVO" if bot_running else "INACTIVO"
            
            # Obtener información adicional
            mode_text = "🧪 Paper Trading" if self.paper_trading else "💰 Live Trading"
            
            # Intentar leer configuración
            config_file = Path("professional_config.json")
            interval = 60
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        interval = config.get('analysis_interval_minutes', 60)
                except:
                    pass
            
            message = f"""{status_icon} *Estado del Bot Autónomo*

*Estado:* {status_text}"""
            
            if bot_running and pid:
                message += f"\n*PID:* {pid}"
            
            message += f"""
*Modo:* {mode_text}
*Intervalo:* {interval} minutos
*Símbolos:* {len(self.symbols)}"""
            
            if bot_running:
                message += "\n\n💡 El bot está operando automáticamente."
            else:
                message += "\n\n💡 Usa /iniciar_bot para activar el bot autónomo."
            
            self.telegram_command_handler._send_message(chat_id, message)
        
        # Registrar comandos del bot autónomo
        self.telegram_command_handler.register_command('/iniciar_bot', handle_start_bot)
        self.telegram_command_handler.register_command('/start_bot', handle_start_bot)
        self.telegram_command_handler.register_command('/detener_bot', handle_stop_bot)
        self.telegram_command_handler.register_command('/stop_bot', handle_stop_bot)
        self.telegram_command_handler.register_command('/bot_estado', handle_bot_status)
        self.telegram_command_handler.register_command('/bot_status', handle_bot_status)
        self.telegram_command_handler.register_command('/config', handle_config)
        self.telegram_command_handler.register_command('/configuracion', handle_config)  # Alias en español
        
        # Comandos de configuración
        self.telegram_command_handler.register_command('/set_risk', handle_set_risk)
        self.telegram_command_handler.register_command('/set_interval', handle_set_interval)
        self.telegram_command_handler.register_command('/toggle_sentiment', handle_toggle_sentiment)
        self.telegram_command_handler.register_command('/toggle_news', handle_toggle_news)
        self.telegram_command_handler.register_command('/toggle_autoconfig', handle_toggle_autoconfig)
        self.telegram_command_handler.register_command('/set_mode', handle_set_mode)
        self.telegram_command_handler.register_command('/set_buy_threshold', handle_set_buy_threshold)
        self.telegram_command_handler.register_command('/set_sell_threshold', handle_set_sell_threshold)
        self.telegram_command_handler.register_command('/scores', handle_scores)
        
        # Alias en español (con y sin guiones)
        self.telegram_command_handler.register_command('/establecer_riesgo', handle_set_risk)
        self.telegram_command_handler.register_command('/establecerriesgo', handle_set_risk)  # Sin guión
        self.telegram_command_handler.register_command('/establecer_intervalo', handle_set_interval)
        self.telegram_command_handler.register_command('/establecerintervalo', handle_set_interval)  # Sin guión
        self.telegram_command_handler.register_command('/alternar_sentimiento', handle_toggle_sentiment)
        self.telegram_command_handler.register_command('/alternarsentimiento', handle_toggle_sentiment)  # Sin guión
        self.telegram_command_handler.register_command('/alternar_noticias', handle_toggle_news)
        self.telegram_command_handler.register_command('/alternarnoticias', handle_toggle_news)  # Sin guión
        self.telegram_command_handler.register_command('/alternar_autoconfig', handle_toggle_autoconfig)
        self.telegram_command_handler.register_command('/alternarautoconfig', handle_toggle_autoconfig)  # Sin guión
        self.telegram_command_handler.register_command('/establecer_modo', handle_set_mode)
        self.telegram_command_handler.register_command('/establecermodo', handle_set_mode)  # Sin guión
        self.telegram_command_handler.register_command('/establecer_umbral_compra', handle_set_buy_threshold)
        self.telegram_command_handler.register_command('/establecerumbralcompra', handle_set_buy_threshold)  # Sin guión
        self.telegram_command_handler.register_command('/establecer_umbral_venta', handle_set_sell_threshold)
        self.telegram_command_handler.register_command('/establecerumbralventa', handle_set_sell_threshold)  # Sin guión
        self.telegram_command_handler.register_command('/puntuaciones', handle_scores)
        
        # Comando para reiniciar análisis
        def handle_restart(chat_id, args):
            """Reinicia el ciclo de análisis inmediatamente"""
            try:
                # Verificar si ya hay un análisis en ejecución
                if self._analysis_running:
                    self.telegram_command_handler._send_message(
                        chat_id, 
                        "⏳ Ya hay un ciclo de análisis en ejecución.\n"
                        "💡 Espera a que termine o el bot ejecutará el siguiente ciclo automáticamente."
                    )
                    return
                
                # Ejecutar análisis en un thread para no bloquear
                import threading
                def run_analysis():
                    try:
                        self.telegram_command_handler._send_message(chat_id, "🔄 Reiniciando ciclo de análisis...")
                        results = self.run_analysis_cycle()
                        # Enviar resumen
                        signals = [r for r in results if r.get('final_signal') != 'HOLD']
                        summary = f"""✅ *Análisis Reiniciado y Completado*

*Símbolos analizados:* {len(results)}
*Señales detectadas:* {len(signals)}
*Hora:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""
                        if signals:
                            summary += "*Señales:*\n"
                            for result in signals[:10]:  # Limitar a 10 señales
                                symbol = result.get('symbol', 'N/A')
                                signal = result.get('final_signal', 'N/A')
                                score = result.get('score', 0)
                                emoji = "🟢" if signal == 'BUY' else "🔴"
                                summary += f"{emoji} {symbol}: {signal} (Score: {score})\n"
                        else:
                            summary += "ℹ️ Todas las señales están en HOLD"
                        
                        self.telegram_command_handler._send_message(chat_id, summary)
                    except Exception as e:
                        error_msg = f"❌ Error en análisis: {e}"
                        print(error_msg)
                        self.telegram_command_handler._send_message(chat_id, error_msg)
                
                thread = threading.Thread(target=run_analysis, daemon=True)
                thread.start()
                self.telegram_command_handler._send_message(chat_id, "⏳ Reiniciando análisis... Te notificaré cuando termine.")
            except Exception as e:
                error_msg = f"❌ Error iniciando reinicio: {str(e)}"
                print(error_msg)
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        # Comando para reinicio completo (requiere flag file)
        def handle_restart_full(chat_id, args):
            """Prepara el bot para reinicio completo"""
            try:
                restart_flag = Path("restart_flag.txt")
                with open(restart_flag, 'w') as f:
                    f.write(f"{datetime.now().isoformat()}\n")
                self.telegram_command_handler._send_message(
                    chat_id, 
                    "🔄 Reinicio completo solicitado.\n"
                    "⚠️ El bot se detendrá en el próximo ciclo.\n"
                    "💡 Usa un script externo o el dashboard para reiniciarlo automáticamente."
                )
            except Exception as e:
                error_msg = f"❌ Error preparando reinicio: {str(e)}"
                self.telegram_command_handler._send_message(chat_id, error_msg)
        
        self.telegram_command_handler.register_command('/restart', handle_restart)
        self.telegram_command_handler.register_command('/reiniciar', handle_restart)  # Alias en español
        self.telegram_command_handler.register_command('/restart_full', handle_restart_full)
        self.telegram_command_handler.register_command('/restarfull', handle_restart_full) # Alias por typo común
        self.telegram_command_handler.register_command('/reiniciar_completo', handle_restart_full)  # Alias con guión
        self.telegram_command_handler.register_command('/reiniciarcompleto', handle_restart_full)  # Alias sin guión
        self.telegram_command_handler.register_command('/stop', handle_stop)
        self.telegram_command_handler.register_command('/detener', handle_stop)  # Alias en español
        self.telegram_command_handler.register_command('/pause', handle_pause)
        self.telegram_command_handler.register_command('/pausar', handle_pause)
        self.telegram_command_handler.register_command('/resume', handle_resume)
        self.telegram_command_handler.register_command('/reanudar', handle_resume)
        self.telegram_command_handler.register_command('/silence', handle_silence)
        self.telegram_command_handler.register_command('/silenciar', handle_silence)
        self.telegram_command_handler.register_command('/unsilence', handle_unsilence)
        self.telegram_command_handler.register_command('/next', handle_next)
        self.telegram_command_handler.register_command('/proximo', handle_next)
        self.telegram_command_handler.register_command('/analyze', handle_analyze)
        self.telegram_command_handler.register_command('/analizar', handle_analyze)
        self.telegram_command_handler.register_command('/positions', handle_positions)
        self.telegram_command_handler.register_command('/posiciones', handle_positions)
        self.telegram_command_handler.register_command('/pnl', handle_pnl)
        
        self.telegram_command_handler.set_paper_trading(self.paper_trading)
        
        # Enviar mensaje de inicio con configuración
        try:
            # Verificar que risk_manager existe antes de acceder a él
            if hasattr(self, 'risk_manager') and self.risk_manager is not None:
                risk_config = self.risk_manager.config if hasattr(self.risk_manager, 'config') else {}
                max_position = risk_config.get('max_position_size_pct', 30)
                max_daily_trades = risk_config.get('max_daily_trades', 10)
                max_daily_loss = risk_config.get('max_daily_loss_pct', 5)
            else:
                max_position = 30
                max_daily_trades = 10
                max_daily_loss = 5
            # Obtener configuración de autoconfiguración
            try:
                from src.core.config_manager import get_config_manager
                config_mgr = get_config_manager()
                # Cargar desde professional_config.json directamente
                import json
                config_file = Path("professional_config.json")
                if config_file.exists():
                    with open(config_file, 'r', encoding='utf-8') as f:
                        prof_config = json.load(f)
                        auto_config_enabled = prof_config.get('auto_configuration_enabled', True)
                else:
                    auto_config_enabled = True
            except Exception as e:
                print(f"⚠️  Error obteniendo configuración de autoconfiguración: {e}")
                auto_config_enabled = True
            
            mode = "💰 LIVE TRADING" if not self.paper_trading else "🧪 PAPER TRADING"
            symbols_count = len(self.symbols) if hasattr(self, 'symbols') and self.symbols else 0
            startup_msg = f"""🤖 *Bot Iniciado*

*Modo:* {mode}
*Capital:* ${self.capital:,.2f}
*Símbolos:* {symbols_count}

*⚙️ Configuración:*
• Riesgo por operación: {max_position}%
• Trades diarios máx: {max_daily_trades}
• Pérdida diaria máx: {max_daily_loss}%
• Autoconfiguración: {'✅' if auto_config_enabled else '❌'}

*📱 Alertas activas:*
✅ Señales BUY/SELL
✅ Trades ejecutados
✅ Resúmenes de análisis
✅ Optimización de portafolio

*💡 Comandos:*
/help - Ver todos los comandos
/config - Ver configuración completa

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            try:
                self.telegram_bot.send_alert(startup_msg)
            except Exception as e:
                print(f"⚠️  Error enviando mensaje de inicio: {e}")
                # No interrumpir el inicio del bot por errores de Telegram
        except Exception as e:
            print(f"⚠️  Error preparando mensaje de inicio: {e}")
    
    def sync_portfolio(self):
        """
        Synchronize local portfolio with IOL and update monitored symbols.
        """
        if not self.paper_trading and self.iol_client:
            print("🔄 Auto-syncing portfolio...")
            old_portfolio_count = len(self.portfolio) if self.portfolio else 0
            
            sync_from_iol(self.iol_client)
            
            # Recargar portafolio actualizado
            self.portfolio = load_portfolio()
            new_portfolio_count = len(self.portfolio) if self.portfolio else 0
            
            # Actualizar símbolos monitoreados si el portafolio cambió
            import json
            config_file = Path("professional_config.json")
            use_portfolio = True
            additional_symbols = []
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        monitoring = config_data.get('monitoring', {})
                        use_portfolio = monitoring.get('use_portfolio_symbols', True)
                        additional_symbols = monitoring.get('additional_symbols', [])
                except Exception:
                    pass
            
            if use_portfolio and self.portfolio:
                portfolio_symbols = [p.get('symbol', '').strip() for p in self.portfolio if p.get('symbol')]
                
                # Combinar portafolio + adicionales
                all_symbols = list(set(portfolio_symbols + additional_symbols))
                
                # Actualizar si hay cambios
                if set(all_symbols) != set(self.symbols):
                    old_count = len(self.symbols)
                    self.symbols = all_symbols
                    new_count = len(self.symbols)
                    print(f"🔄 Símbolos monitoreados actualizados: {old_count} → {new_count}")
                    
                    if new_portfolio_count != old_portfolio_count:
                        print(f"📊 Portafolio actualizado: {old_portfolio_count} → {new_portfolio_count} activos")
            
            # 📢 NOTIFICACIÓN: Mostrar actualización de portafolio
            try:
                portfolio = load_portfolio()
                if portfolio:
                    total_value = sum(p.get('current_value', 0) for p in portfolio)
                    total_cost = sum(p.get('cost_basis', 0) for p in portfolio)
                    total_pnl = total_value - total_cost
                    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0
                    
                    self.operation_notifier.notify_portfolio_update({
                        'total_value': total_value,
                        'total_pnl': total_pnl,
                        'total_pnl_pct': total_pnl_pct,
                        'positions_count': len(portfolio),
                    })
            except Exception as e:
                try:
                    safe_warning(logger, f"Error notificando actualización de portafolio: {e}")
                except:
                    pass

    def run_analysis_cycle(self):
        """
        Run one complete analysis cycle for all symbols.
        Protegido contra ejecuciones simultáneas.
        """
        # Verificar si ya hay un análisis en ejecución
        if self._analysis_running:
            print("⚠️  Ya hay un ciclo de análisis en ejecución. Omitiendo este ciclo.")
            return []
        
        # Adquirir lock para evitar ejecuciones simultáneas
        if not self._analysis_lock.acquire(blocking=False):
            print("⚠️  Análisis ya en ejecución (lock adquirido por otro thread)")
            return []
        
        try:
            self._analysis_running = True
            self._last_analysis_time = datetime.now()  # Track for /next command
            
            # Check if trading is paused
            if self._paused:
                print(f"\n{'#'*60}")
                print(f"⏸️ Trading PAUSED - Analysis will run but NO trades will execute")
                print(f"{'#'*60}")
            
            print(f"\n{'#'*60}")
            print(f"🔄 Starting Analysis Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'#'*60}")
            
            # Verificar que symbols esté inicializado ANTES de cualquier operación
            if not hasattr(self, 'symbols') or not self.symbols:
                print("⚠️  Error: self.symbols no está inicializado. Inicializando con valores por defecto...")
                self.symbols = ['GGAL', 'YPFD', 'PAMP']
                print(f"📌 Usando símbolos por defecto: {', '.join(self.symbols)}")
            
            # 📈 TRAILING STOP LOSS: Actualizar antes del análisis
            try:
                if hasattr(self, 'trailing_stop_loss') and not self.paper_trading:
                    current_prices = {}
                    for sym in self.trailing_stop_loss.get_all_positions().keys():
                        try:
                            quote = self.iol_client.get_quote(sym)
                            if 'ultimoPrecio' in quote:
                                current_prices[sym] = quote['ultimoPrecio']
                        except:
                            pass
                    
                    if current_prices:
                        sell_actions = self.trailing_stop_loss.update_all(current_prices)
                        for action in sell_actions:
                            print(f"\n🚨 Trailing Stop: {action['symbol']} (+{action['gain_pct']:.2f}%)")
                            position = self.trailing_stop_loss.get_all_positions().get(action['symbol'], {})
                            qty = position.get('quantity', 1) if position else 1
                            self.execute_trade(action['symbol'], 'SELL', action['current_price'], qty, None, None)
            except Exception as e:
                print(f"⚠️  Error trailing stops: {e}")
            
            results = []
            
            # 🧠 APRENDIZAJE: Ejecutar ciclo de aprendizaje antes de analizar
            if hasattr(self, 'advanced_learning') and self.advanced_learning:
                try:
                    learning_summary = self.advanced_learning.run_learning_cycle()
                    if learning_summary.get('lessons_learned'):
                        print(f"\n📚 Lecciones Aprendidas:")
                        for lesson in learning_summary['lessons_learned']:
                            print(f"   {lesson}")
                except Exception as e:
                    print(f"⚠️  Error en ciclo de aprendizaje: {e}")
            
            # 🔄 RETROALIMENTACIÓN: Leer aprendizaje del chat
            try:
                chat_learning = self._load_chat_learning()
                if chat_learning:
                    self._apply_chat_learning(chat_learning)
            except Exception as e:
                print(f"⚠️  Error leyendo aprendizaje del chat: {e}")
            
            # Verificar que symbols esté inicializado
            if not hasattr(self, 'symbols') or not self.symbols:
                print("⚠️  Error: self.symbols no está inicializado. Inicializando con valores por defecto...")
                self.symbols = ['GGAL', 'YPFD', 'PAMP']
                print(f"📌 Usando símbolos por defecto: {', '.join(self.symbols)}")
            
            # 🔄 RETROALIMENTACIÓN: Compartir aprendizaje del bot con el chat al final del ciclo
            try:
                # Extraer insights del ciclo de análisis
                learning_to_share = {
                    'patterns': [],
                    'insights': []
                }
                
                # Agregar patrones de los resultados
                for result in results:
                    if result.get('final_signal') != 'HOLD':
                        pattern = {
                            'type': 'analysis_pattern',
                            'symbol': result.get('symbol'),
                            'signal': result.get('final_signal'),
                            'score': result.get('score', 0),
                            'timestamp': datetime.now().isoformat()
                        }
                        learning_to_share['patterns'].append(pattern)
                
                # Compartir con el chat
                if learning_to_share['patterns']:
                    self.share_learning_with_chat(learning_to_share)
            except Exception as e:
                print(f"⚠️  Error compartiendo aprendizaje: {e}")
            
            for symbol in self.symbols:
                # Fetch latest data (Fallback to Yahoo if IOL fails)
                try:
                    from scripts.ingest_data import ingest_symbol
                    from src.core.database import SessionLocal
                    from src.models.market_data import MarketData
                    
                    # Verificar cuántos registros tiene el símbolo
                    db = SessionLocal()
                    try:
                        record_count = db.query(MarketData).filter(MarketData.symbol == symbol).count()
                    except:
                        record_count = 0
                    finally:
                        db.close()
                    
                    # Si tiene menos de 30 registros, descargar más historia
                    if record_count < 30:
                        print(f"📥 Descargando datos históricos para {symbol} (tiene {record_count} registros, necesitamos al menos 30)...")
                        ingest_symbol(symbol, period="1y")  # Descargar 1 año de datos
                    else:
                        print(f"📥 Actualizando datos recientes para {symbol} (tiene {record_count} registros)...")
                        ingest_symbol(symbol, period="5d")  # Solo actualizar últimos 5 días
                except Exception as e:
                    print(f"⚠️  Data fetch failed for {symbol}: {e}")

                result = self.analyze_symbol(symbol)
                results.append(result)
                time.sleep(1)  # Rate limiting
            
            # Portfolio optimization
            print(f"\n{'='*60}")
            print("💼 Portfolio Optimization")
            print(f"{'='*60}")
            
            try:
                returns_df = self.portfolio_optimizer.get_returns_data(self.symbols, days=252)
                
                # Validar que tenemos datos suficientes
                if returns_df.empty or len(returns_df.columns) < 2:
                    print("ℹ️  No hay suficientes datos para optimización de portafolio")
                    print("   💡 Se necesitan al menos 2 símbolos con datos históricos suficientes")
                    # No retornar aquí, continuar con el resto del ciclo
                else:
                    sharpe_result = self.portfolio_optimizer.optimize_sharpe_ratio(returns_df)
                    
                    if sharpe_result.get('success'):
                        print("\n🎯 Recommended Portfolio (Max Sharpe):")
                        portfolio_msg = "💼 *Optimización de Portafolio*\n\n*Recomendaciones (Max Sharpe):*\n"
                        has_recommendations = False
                        for symbol, weight in sharpe_result['weights'].items():
                            if weight > 0.01:  # Only show significant weights
                                print(f"   {symbol}: {weight*100:.2f}%")
                                portfolio_msg += f"• {symbol}: {weight*100:.2f}%\n"
                                has_recommendations = True
                        
                        # Enviar recomendación por Telegram si hay recomendaciones
                        if has_recommendations:
                            # NO ENVIAR ALERTAS INDIVIDUALES - Guardar para resumen
                            pass
            except Exception as e:
                print(f"⚠️  Portfolio optimization failed: {e}")
            
            # Enviar resumen CONSOLIDADO del ciclo de análisis por Telegram
            # Estrategia Híbrida: Solo un mensaje con todo (Insights + Portafolio + Señales)
            
            summary_msg = f"📊 *Resumen de Análisis* - {datetime.now().strftime('%H:%M')}\n\n"
            has_content = False
            
            # 1. Agregar Insights de Aprendizaje (si hay)
            if 'learning_summary' in locals() and learning_summary.get('lessons_learned'):
                summary_msg += "🧠 *Aprendizaje:*\n"
                for lesson in learning_summary['lessons_learned']:
                    summary_msg += f"• {lesson}\n"
                summary_msg += "\n"
                has_content = True
                
            # 2. Agregar Recomendaciones de Portafolio (si hay)
            if 'portfolio_msg' in locals() and portfolio_msg:
                # Extraer solo las líneas de recomendaciones del mensaje original
                lines = portfolio_msg.split('\n')
                rec_lines = [l for l in lines if l.startswith('•')]
                if rec_lines:
                    summary_msg += "💼 *Portafolio (Max Sharpe):*\n"
                    for line in rec_lines:
                        summary_msg += f"{line}\n"
                    summary_msg += "\n"
                    has_content = True
            
            # 3. Agregar Señales de Trading
            signals_summary = [r for r in results if r.get('final_signal') != 'HOLD']
            if signals_summary:
                summary_msg += f"🎯 *Señales ({len(signals_summary)}):*\n"
                for sig in signals_summary:
                    emoji = "🟢" if sig['final_signal'] == 'BUY' else "🔴"
                    summary_msg += f"{emoji} {sig['symbol']}: {sig['final_signal']} (Score: {sig.get('score', 0)})\n"
                has_content = True
            else:
                # No agregar nada si no hay señales, para no activar has_content
                pass
            
            # Enviar mensaje consolidado SOLO si hay contenido relevante
            if has_content:
                # Check if notifications are silenced
                if self._silence_until and datetime.now() < self._silence_until:
                    print(f"🔕 Notificaciones silenciadas hasta {self._silence_until.strftime('%H:%M')}")
                else:
                    try:
                        self.telegram_bot.send_alert(summary_msg)
                    except Exception as e:
                        safe_warning(logger, f"Error enviando resumen consolidado a Telegram: {e}")
            else:
                print("ℹ️ Ciclo sin novedades relevantes. Silenciando notificación.")
            
            return results
        except Exception as e:
            # Log del error pero no interrumpir el bot (con logging seguro)
            error_msg = f"Error en ciclo de análisis: {e}"
            print(f"❌ {error_msg}")
            try:
                safe_error(logger, error_msg, exc_info=True)
            except (ValueError, IOError, OSError):
                # Si el logging falla, solo imprimir
                print(f"   Tipo: {type(e).__name__}")
            return []
        finally:
            # Liberar el flag y el lock al finalizar (incluso si hay error)
            self._analysis_running = False
            self._analysis_lock.release()
    
    def run_continuous(self, interval_minutes=60):
        """
        Run bot continuously.
        
        Args:
            interval_minutes: Minutes between analysis cycles
        """
        print(f"\n🤖 Starting continuous mode (interval: {interval_minutes} min)")
        print("Press Ctrl+C to stop\n")
        
        # Iniciar polling de Telegram para recibir comandos (opcional, no crítico)
        if hasattr(self, 'telegram_command_handler') and self.telegram_command_handler:
            if self.telegram_command_handler.bot_token:
                try:
                    # Verificar si ya hay otra instancia haciendo polling
                    success = self.telegram_command_handler.start_polling()
                    if success:
                        print("✅ Telegram command handler iniciado - Puedes enviar comandos desde Telegram")
                        print("   💡 Envía /start a tu bot para probar")
                    else:
                        print("⚠️  No se pudo iniciar el polling de Telegram (puede haber otra instancia corriendo)")
                        print("   ℹ️  El bot continuará funcionando normalmente, solo sin comandos de Telegram")
                except Exception as e:
                    error_msg = str(e)
                    if "409" in error_msg or "Conflict" in error_msg:
                        print("⚠️  Otra instancia del bot está usando Telegram")
                        print("   ℹ️  El bot continuará funcionando normalmente, solo sin comandos de Telegram")
                    else:
                        print(f"⚠️  Error iniciando Telegram command handler: {e}")
                        print("   ℹ️  El bot continuará funcionando normalmente")
            else:
                print("ℹ️  Telegram bot_token no configurado - Comandos de Telegram deshabilitados")
        else:
            print("ℹ️  Telegram command handler no disponible - Comandos de Telegram deshabilitados")
        
        # Contador para autoconfiguración (cada 24 horas o cada 50 trades)
        last_auto_config = datetime.now()
        auto_config_interval = timedelta(hours=24)
        trades_since_config = 0
        
        # Contador para sincronización de portafolio (cada 6 horas)
        last_portfolio_sync = datetime.now()
        portfolio_sync_interval = timedelta(hours=6)
        
        # Contador para generación de insights (cada 24 horas)
        last_insights_generation = datetime.now()
        insights_interval = timedelta(hours=24)
        
        # Contador para reportes diarios (una vez al día, a las 23:00)
        last_daily_report = datetime.now()
        daily_report_sent = False
        
        # Contador para autoprogramación (cada 24 horas o cada 50 trades - más frecuente)
        # SIN LÍMITES - el bot puede mejorarse más frecuentemente
        last_self_programming = datetime.now()
        self_programming_interval = timedelta(hours=24)  # Más frecuente
        trades_since_programming = 0
        
        # Contador para alertas macroeconómicas (cada 1 hora)
        last_macro_alert_check = datetime.now()
        macro_alert_interval = timedelta(hours=1)
        
        # Contador de errores consecutivos para evitar loops infinitos
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        try:
            while True:
                # Verificar si hay solicitud de parada
                stop_flag = Path("stop_flag.txt")
                if stop_flag.exists():
                    print("\n" + "="*60)
                    print("🛑 Parada solicitada desde Telegram")
                    print("="*60)
                    print("⚠️  Deteniendo bot...")
                    try:
                        stop_flag.unlink()  # Eliminar flag
                    except:
                        pass
                    # Detener polling de Telegram
                    if hasattr(self, 'telegram_command_handler') and self.telegram_command_handler:
                        try:
                            self.telegram_command_handler.stop_polling()
                        except:
                            pass
                    # Enviar mensaje de confirmación
                    try:
                        self.telegram_bot.send_alert("✅ Bot detenido correctamente.")
                    except:
                        pass
                    print("✅ Bot detenido.")
                    break
                
                # Verificar si hay solicitud de reinicio completo
                restart_flag = Path("restart_flag.txt")
                if restart_flag.exists():
                    print("\n" + "="*60)
                    print("🔄 Reinicio completo solicitado desde Telegram")
                    print("="*60)
                    print("⚠️  Deteniendo bot para reinicio...")
                    try:
                        restart_flag.unlink()  # Eliminar flag
                    except:
                        pass
                    # Detener polling de Telegram
                    if hasattr(self, 'telegram_command_handler') and self.telegram_command_handler:
                        try:
                            self.telegram_command_handler.stop_polling()
                        except:
                            pass
                    # Salir del loop para permitir reinicio
                    print("✅ Bot detenido. Reinicia manualmente o usa un script de monitoreo.")
                    break
                
                # Sincronizar portafolio periódicamente si está habilitado
                import json
                config_file = Path("professional_config.json")
                auto_sync = True
                if config_file.exists():
                    try:
                        with open(config_file, 'r', encoding='utf-8') as f:
                            config_data = json.load(f)
                            monitoring = config_data.get('monitoring', {})
                            auto_sync = monitoring.get('auto_sync_portfolio', True)
                    except Exception:
                        pass
                if auto_sync and not self.paper_trading:
                    time_since_sync = datetime.now() - last_portfolio_sync
                    if time_since_sync >= portfolio_sync_interval:
                        try:
                            print(f"\n{'='*60}")
                            print("🔄 Sincronizando portafolio con IOL...")
                            print(f"{'='*60}")
                            self.sync_portfolio()
                            last_portfolio_sync = datetime.now()
                        except Exception as e:
                            safe_warning(logger, f"Error sincronizando portafolio: {e}")
                    
                    # Actualizar saldo periódicamente (cada hora)
                    if 'last_balance_update' not in locals():
                        last_balance_update = datetime.now()
                    time_since_balance = datetime.now() - last_balance_update
                    if time_since_balance >= timedelta(hours=1):
                        try:
                            old_capital = self.capital
                            new_balance = self.iol_client.get_available_balance()
                            if new_balance != old_capital:
                                print(f"💰 Saldo actualizado automáticamente: ${old_capital:,.2f} → ${new_balance:,.2f} ARS")
                                self.capital = new_balance
                                # Actualizar risk_manager
                                if hasattr(self.risk_manager, 'initial_capital'):
                                    self.risk_manager.initial_capital = new_balance
                                if hasattr(self.risk_manager, 'current_capital'):
                                    self.risk_manager.current_capital = new_balance
                                # Notificar por Telegram
                                try:
                                    self.telegram_bot.send_alert(
                                        f"💰 *Saldo Actualizado Automáticamente*\n\n"
                                        f"*Anterior:* ${old_capital:,.2f} ARS\n"
                                        f"*Nuevo:* ${new_balance:,.2f} ARS\n"
                                        f"*Diferencia:* ${new_balance - old_capital:,.2f} ARS"
                                    )
                                except:
                                    pass  # No interrumpir si falla Telegram
                            last_balance_update = datetime.now()
                        except Exception as e:
                            safe_warning(logger, f"Error actualizando saldo: {e}")
                
                # Generar insights de aprendizaje periódicamente
                if hasattr(self, 'enhanced_learning') and self.enhanced_learning:
                    time_since_insights = datetime.now() - last_insights_generation
                    if time_since_insights >= insights_interval:
                        try:
                            print(f"\n{'='*60}")
                            print("🧠 Generando insights de aprendizaje...")
                            print(f"{'='*60}")
                            insights = self.enhanced_learning.generate_insights()
                            if insights.get('recommendations'):
                                print("\n💡 Recomendaciones basadas en aprendizaje:")
                                for rec in insights['recommendations']:
                                    print(f"   {rec}")
                                # Enviar a Telegram si está configurado
                                if hasattr(self, 'telegram_bot') and self.telegram_bot.bot_token:
                                    insights_msg = "🧠 *Insights de Aprendizaje*\n\n"
                                    insights_msg += "\n".join([f"• {r}" for r in insights['recommendations'][:5]])
                                    try:
                                        self.telegram_bot.send_alert(insights_msg)
                                    except Exception as e:
                                        safe_warning(logger, f"Error enviando insights a Telegram: {e}")
                                        # No interrumpir el ciclo por errores de Telegram
                            last_insights_generation = datetime.now()
                        except Exception as e:
                            safe_warning(logger, f"Error generando insights: {e}")
                            # Continuar ejecutando aunque falle la generación de insights
                
                # Enviar reporte diario (una vez al día, a las 23:00)
                now = datetime.now()
                if now.hour == 23 and not daily_report_sent:
                    try:
                        if not hasattr(self, 'daily_report_service') or self.daily_report_service is None:
                            print("⚠️  Servicio de reportes diarios no disponible")
                        else:
                            print(f"\n{'='*60}")
                            print("📊 Generando reporte diario...")
                            print(f"{'='*60}")
                            success = self.daily_report_service.send_daily_report()
                            if success:
                                print("✅ Reporte diario enviado correctamente")
                                daily_report_sent = True
                            else:
                                print("⚠️  Error generando reporte diario")
                    except Exception as e:
                        safe_warning(logger, f"Error generando reporte diario: {e}")
                
                # Resetear flag de reporte diario a las 00:00
                if now.hour == 0 and daily_report_sent:
                    daily_report_sent = False
                
                # Verificar alertas macroeconómicas (cada hora)
                if hasattr(self, 'macroeconomic_alert_service') and self.macroeconomic_alert_service:
                    time_since_macro_check = datetime.now() - last_macro_alert_check
                    if time_since_macro_check >= macro_alert_interval:
                        try:
                            alerts = self.macroeconomic_alert_service.check_and_alert()
                            if alerts:
                                print(f"\n📊 {len(alerts)} alerta(s) macroeconómica(s) generada(s)")
                                for alert in alerts:
                                    print(f"   • {alert['indicator']}: {alert['message']}")
                            last_macro_alert_check = datetime.now()
                        except Exception as e:
                            safe_warning(logger, f"Error verificando alertas macroeconómicas: {e}")
                
                # Ejecutar ciclo de análisis con manejo robusto de errores
                try:
                    self.run_analysis_cycle()
                    # Si el ciclo se ejecutó correctamente, resetear contador de errores
                    consecutive_errors = 0
                except Exception as e:
                    error_msg = f"Error en ciclo de análisis: {type(e).__name__}: {str(e)}"
                    print(f"\n⚠️  {error_msg}")
                    # Usar logging seguro para evitar errores de I/O
                    try:
                        safe_error(logger, error_msg, exc_info=True)
                    except (ValueError, IOError, OSError):
                        # Si el logging falla, solo imprimir
                        print(f"   Detalles: {e}")
                    # Continuar ejecutando en lugar de cerrar
                    print("   🔄 Continuando con el siguiente ciclo...\n")
                
                # Ejecutar autoconfiguración si es necesario y está habilitada
                if not hasattr(self, 'auto_configurator') or self.auto_configurator is None:
                    print("⚠️  auto_configurator no está inicializado. Saltando autoconfiguración...")
                    auto_config_enabled = False
                else:
                    auto_config_enabled = self.auto_configurator.config.get('auto_configuration_enabled', True)
                if auto_config_enabled and hasattr(self, 'auto_configurator') and self.auto_configurator is not None:
                    time_since_config = datetime.now() - last_auto_config
                    if time_since_config >= auto_config_interval or trades_since_config >= 50:
                        try:
                            print(f"\n{'='*60}")
                            print("🔧 Ejecutando autoconfiguración...")
                            print(f"{'='*60}")
                            
                            result = self.auto_configurator.auto_configure(self.risk_manager)
                            
                            if result.get('success') and result.get('changes'):
                                print(f"\n✅ Autoconfiguración completada: {len(result['changes'])} cambios")
                                for change in result['changes']:
                                    print(f"   • {change}")
                                
                                # Notificar por Telegram
                                if result.get('changes'):
                                    changes_text = "\n".join([f"• {c}" for c in result['changes']])
                                    self.telegram_bot.send_alert(f"""
🔧 *AUTOCONFIGURACIÓN REALIZADA*

Se ajustaron {len(result['changes'])} parámetros:

{changes_text}

*Razón:* Optimización basada en rendimiento histórico
""")
                                
                                last_auto_config = datetime.now()
                                trades_since_config = 0
                            else:
                                print("ℹ️  Configuración óptima, no se requieren cambios")
                                last_auto_config = datetime.now()
                                trades_since_config = 0
                        except Exception as e:
                            print(f"⚠️  Error en autoconfiguración: {e}")
                
                # Contar trades para próxima autoconfiguración
                trades_since_config += len([s for s in self.symbols])  # Aproximación
                
                # Ejecutar ciclo de autoprogramación si está habilitado
                # SIN LÍMITES - más frecuente para aprendizaje continuo
                if hasattr(self, 'self_programming') and self.self_programming:
                    time_since_programming = datetime.now() - last_self_programming
                    if time_since_programming >= self_programming_interval or trades_since_programming >= 50:  # Más frecuente
                        try:
                            print(f"\n{'='*60}")
                            print("🧠 Ejecutando ciclo de autoprogramación...")
                            print(f"{'='*60}")
                            
                            result = self.self_programming.run_improvement_cycle()
                            
                            if result.get('success') and result.get('improvements_applied', 0) > 0:
                                print(f"\n✅ Autoprogramación completada: {result['improvements_applied']} mejoras aplicadas")
                                
                                # Notificar por Telegram
                                if hasattr(self, 'telegram_bot') and self.telegram_bot.bot_token:
                                    improvements_text = "\n".join([
                                        f"• {imp['improvement']['description']}" 
                                        for imp in result.get('applied_improvements', [])
                                    ])
                                    self.telegram_bot.send_alert(f"""
🧠 *AUTOPROGRAMACIÓN REALIZADA*

El bot se ha mejorado a sí mismo:

{improvements_text}

*Total:* {result['improvements_applied']} mejora(s) aplicada(s)

⚠️  El bot ahora tiene código modificado por sí mismo
""")
                                
                                last_self_programming = datetime.now()
                                trades_since_programming = 0
                            else:
                                print("ℹ️  No se requieren mejoras en este momento")
                                last_self_programming = datetime.now()
                                trades_since_programming = 0
                        except Exception as e:
                            print(f"⚠️  Error en autoprogramación: {e}")
                            safe_warning(logger, f"Error en autoprogramación: {e}")
                
                # Contar trades para próxima autoprogramación
                trades_since_programming += len([s for s in self.symbols])  # Aproximación
                
                print(f"\n⏸️  Waiting {interval_minutes} minutes until next cycle...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user")
            # Detener polling de Telegram
            if hasattr(self, 'telegram_command_handler') and self.telegram_command_handler:
                try:
                    self.telegram_command_handler.stop_polling()
                except:
                    pass
        except Exception as e:
            # Capturar cualquier error no esperado y continuar
            consecutive_errors += 1
            error_msg = f"Error crítico en loop principal ({consecutive_errors}/{max_consecutive_errors}): {type(e).__name__}: {str(e)}"
            print(f"\n❌ {error_msg}")
            try:
                safe_error(logger, error_msg, exc_info=True)
            except (ValueError, IOError, OSError):
                # Si el logging falla, solo imprimir
                print(f"   Detalles: {e}")
            
            # Si hay demasiados errores consecutivos, detener el bot
            if consecutive_errors >= max_consecutive_errors:
                print(f"\n⚠️  Demasiados errores consecutivos ({consecutive_errors}). Deteniendo bot por seguridad.")
                print("   💡 Revisa los logs y reinicia el bot manualmente.")
                # Detener polling de Telegram
                if hasattr(self, 'telegram_command_handler') and self.telegram_command_handler:
                    try:
                        self.telegram_command_handler.stop_polling()
                    except:
                        pass
                return  # Salir de la función en lugar de break
            
            print(f"   🔄 Reintentando en 60 segundos... ({consecutive_errors}/{max_consecutive_errors})\n")
            # Esperar antes de continuar el loop
            time.sleep(60)
            # Continuar el loop - reiniciar el while True
            self.run_continuous(interval_minutes=interval_minutes)
            return

# Example usage
if __name__ == "__main__":
    import argparse
    import traceback
    
    parser = argparse.ArgumentParser(description='IOL Quantum AI Trading Bot')
    parser.add_argument('--continuous', action='store_true', help='Run in continuous mode')
    parser.add_argument('--interval', type=int, default=60, help='Interval in minutes')
    parser.add_argument('--live', action='store_true', help='Enable LIVE trading with real money')
    args = parser.parse_args()

    try:
        # Initialize bot
        # Si use_full_universe está activo en la configuración, pasar None para que cargue el universo completo
        import json
        from pathlib import Path
        config_file = Path("professional_config.json")
        use_full_universe = False
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    use_full_universe = config.get('monitoring', {}).get('use_full_universe', False)
            except:
                pass
        
        # Si use_full_universe está activo, pasar None para cargar universo completo
        # Si no, usar símbolos por defecto
        if use_full_universe:
            print("🌍 Modo Universo Completo detectado en configuración")
            symbols_param = None  # None para que cargue el universo completo
        else:
            default_symbols = ['AAPL', 'MSFT', 'GOOGL'] if not args.live else ['GGAL', 'PAMP', 'YPFD']
            symbols_param = default_symbols
        
        try:
            bot = TradingBot(
                symbols=symbols_param,  # None si use_full_universe, sino símbolos por defecto
                initial_capital=None, # Will fetch from IOL if live
                paper_trading=not args.live
            )
            
            # Verificar que los símbolos se inicializaron correctamente
            if not hasattr(bot, 'symbols') or not bot.symbols:
                print("⚠️  No se pudieron inicializar símbolos. Usando símbolos por defecto...")
                default_fallback = ['GGAL', 'YPFD', 'PAMP'] if args.live else ['AAPL', 'MSFT', 'GOOGL']
                bot.symbols = default_symbols if 'default_symbols' in locals() else default_fallback
                print(f"📌 Símbolos de fallback: {', '.join(bot.symbols)}")
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO durante inicialización del bot:")
            print(f"   Tipo: {type(e).__name__}")
            print(f"   Mensaje: {str(e)}")
            print(f"\n📋 Traceback completo:")
            traceback.print_exc()
            print("\n⚠️  El bot no pudo inicializarse correctamente.")
            print("   💡 Revisa los errores arriba y corrige la configuración.")
            if sys.platform == 'win32':
                try:
                    input("\n⚠️  Presiona Enter para cerrar esta ventana...")
                except:
                    pass
            sys.exit(1)
        
        if args.continuous:
            bot.run_continuous(interval_minutes=args.interval)
        else:
            # Run single analysis cycle
            bot.run_analysis_cycle()
    except KeyboardInterrupt:
        print("\n\n🛑 Bot detenido por el usuario")
    except Exception as e:
        print(f"\n\n❌ ERROR CRÍTICO en el bot:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {str(e)}")
        print(f"\n📋 Traceback completo:")
        traceback.print_exc()
        print("\n⚠️  Presiona Enter para cerrar esta ventana...")
        if sys.platform == 'win32':
            try:
                input()  # Mantener ventana abierta en Windows
            except:
                pass
        raise  # Re-raise para que el sistema lo capture

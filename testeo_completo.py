"""
Testeo Completo del Sistema IOL Quantum AI Trading Bot
Verifica todos los componentes, configuraciones y funcionalidades
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, time
import traceback

# Configurar path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")

def test_1_archivos_esenciales():
    """Test 1: Verificar archivos esenciales"""
    print_header("TEST 1: ARCHIVOS ESENCIALES")
    
    archivos_requeridos = [
        "trading_bot.py",
        "run_bot.py",
        "dashboard.py",
        "professional_config.json",
        ".env",
        "requirements.txt"
    ]
    
    resultados = {}
    for archivo in archivos_requeridos:
        path = Path(archivo)
        if path.exists():
            print_success(f"{archivo} existe")
            resultados[archivo] = True
        else:
            print_error(f"{archivo} NO existe")
            resultados[archivo] = False
    
    return resultados

def test_2_configuracion():
    """Test 2: Verificar configuración"""
    print_header("TEST 2: CONFIGURACIÓN")
    
    resultados = {}
    
    # 2.1 professional_config.json
    print_info("Verificando professional_config.json...")
    config_file = Path("professional_config.json")
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Verificar horario de trading IOL (11:00 - 17:00)
            time_mgmt = config.get("time_management", {})
            start = time_mgmt.get("trading_hours_start", "")
            end = time_mgmt.get("trading_hours_end", "")
            
            if start == "11:00" and end == "17:00":
                print_success(f"Horario de trading IOL configurado: {start} - {end}")
                resultados["horario_iol"] = True
            else:
                print_warning(f"Horario de trading: {start} - {end} (debería ser 11:00 - 17:00)")
                resultados["horario_iol"] = False
            
            # Verificar otros parámetros importantes
            buy_threshold = config.get("buy_threshold", None)
            sell_threshold = config.get("sell_threshold", None)
            
            if buy_threshold is not None and sell_threshold is not None:
                print_success(f"Umbrales configurados: Compra={buy_threshold}, Venta={sell_threshold}")
                resultados["umbrales"] = True
            else:
                print_warning("Umbrales no configurados")
                resultados["umbrales"] = False
            
            resultados["config_file"] = True
        except Exception as e:
            print_error(f"Error leyendo professional_config.json: {e}")
            resultados["config_file"] = False
    else:
        print_error("professional_config.json no existe")
        resultados["config_file"] = False
    
    # 2.2 Variables de entorno
    print_info("Verificando variables de entorno...")
    env_file = Path(".env")
    if env_file.exists():
        print_success(".env existe")
        
        # Verificar variables críticas
        from dotenv import load_dotenv
        load_dotenv()
        
        iol_user = os.getenv("IOL_USERNAME")
        iol_pass = os.getenv("IOL_PASSWORD")
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
        
        if iol_user and iol_pass:
            print_success(f"IOL configurado: {iol_user}")
            resultados["iol_env"] = True
        else:
            print_warning("IOL no configurado en .env")
            resultados["iol_env"] = False
        
        if telegram_token and telegram_chat:
            print_success("Telegram configurado")
            resultados["telegram_env"] = True
        else:
            print_warning("Telegram no configurado en .env")
            resultados["telegram_env"] = False
    else:
        print_error(".env no existe")
        resultados["iol_env"] = False
        resultados["telegram_env"] = False
    
    return resultados

def test_3_dependencias():
    """Test 3: Verificar dependencias instaladas"""
    print_header("TEST 3: DEPENDENCIAS")
    
    resultados = {}
    
    dependencias_criticas = [
        "pandas",
        "numpy",
        "tensorflow",
        "scikit-learn",
        "requests",
        "streamlit",
        "sqlalchemy",
        "yfinance"
    ]
    
    for dep in dependencias_criticas:
        try:
            __import__(dep)
            print_success(f"{dep} instalado")
            resultados[dep] = True
        except ImportError:
            print_error(f"{dep} NO instalado")
            resultados[dep] = False
    
    return resultados

def test_4_servicios():
    """Test 4: Verificar servicios principales"""
    print_header("TEST 4: SERVICIOS PRINCIPALES")
    
    resultados = {}
    
    # 4.1 IOL Client
    print_info("Verificando IOL Client...")
    try:
        from src.connectors.iol_client import IOLClient
        iol = IOLClient()
        print_success("IOL Client importado correctamente")
        
        # Intentar autenticación
        try:
            login_result = iol._login()
            if login_result:
                print_success("Autenticación IOL exitosa")
                resultados["iol_auth"] = True
                
                # Verificar saldo
                try:
                    balance = iol.get_available_balance()
                    if balance and balance > 0:
                        print_success(f"Saldo IOL: ${balance:,.2f} ARS")
                        resultados["iol_balance"] = True
                    else:
                        print_warning("Saldo IOL no disponible o es 0")
                        resultados["iol_balance"] = False
                except Exception as e:
                    print_warning(f"Error obteniendo saldo: {e}")
                    resultados["iol_balance"] = False
            else:
                print_warning("Autenticación IOL no retornó True (puede ser un falso negativo)")
                # Verificar si realmente está autenticado intentando obtener saldo
                try:
                    balance = iol.get_available_balance()
                    if balance is not None:
                        print_success(f"Autenticación verificada - Saldo: ${balance:,.2f} ARS")
                        resultados["iol_auth"] = True
                        resultados["iol_balance"] = True
                    else:
                        resultados["iol_auth"] = False
                except:
                    resultados["iol_auth"] = False
        except Exception as e:
            print_warning(f"Error en autenticación IOL: {e}")
            resultados["iol_auth"] = False
        
        resultados["iol_client"] = True
    except Exception as e:
        print_error(f"Error importando IOL Client: {e}")
        resultados["iol_client"] = False
        resultados["iol_auth"] = False
    
    # 4.2 Telegram Bot
    print_info("Verificando Telegram Bot...")
    try:
        from src.services.telegram_bot import TelegramAlertBot
        telegram_bot = TelegramAlertBot()
        
        if telegram_bot.bot_token and telegram_bot.chat_id:
            print_success("Telegram Bot configurado")
            resultados["telegram_bot"] = True
        else:
            print_warning("Telegram Bot no configurado completamente")
            resultados["telegram_bot"] = False
    except Exception as e:
        print_error(f"Error con Telegram Bot: {e}")
        resultados["telegram_bot"] = False
    
    # 4.3 Professional Trader
    print_info("Verificando Professional Trader...")
    try:
        from src.services.professional_trader import ProfessionalTrader
        trader = ProfessionalTrader(config_file="professional_config.json")
        
        # Verificar horario
        can_trade, reason = trader.check_time_filters()
        now = datetime.now()
        current_time = now.time()
        
        print_info(f"Hora actual: {current_time.strftime('%H:%M:%S')}")
        print_info(f"Puede operar: {reason}")
        
        resultados["professional_trader"] = True
    except Exception as e:
        print_error(f"Error con Professional Trader: {e}")
        resultados["professional_trader"] = False
    
    # 4.4 Risk Manager
    print_info("Verificando Risk Manager...")
    try:
        from src.services.adaptive_risk_manager import AdaptiveRiskManager
        risk_manager = AdaptiveRiskManager(initial_capital=100000)
        print_success("Risk Manager inicializado")
        resultados["risk_manager"] = True
    except Exception as e:
        print_error(f"Error con Risk Manager: {e}")
        resultados["risk_manager"] = False
    
    return resultados

def test_5_base_datos():
    """Test 5: Verificar base de datos"""
    print_header("TEST 5: BASE DE DATOS")
    
    resultados = {}
    
    # 5.1 trading_bot.db
    print_info("Verificando trading_bot.db...")
    db_file = Path("trading_bot.db")
    if db_file.exists():
        print_success("trading_bot.db existe")
        
        try:
            from src.core.database import SessionLocal
            from src.models.market_data import MarketData
            
            db = SessionLocal()
            
            # Contar registros
            total_records = db.query(MarketData).count()
            print_info(f"Total de registros: {total_records:,}")
            
            # Contar símbolos únicos
            unique_symbols = db.query(MarketData.symbol).distinct().count()
            print_info(f"Símbolos únicos: {unique_symbols}")
            
            if total_records > 0:
                print_success("Base de datos tiene datos")
                resultados["db_data"] = True
            else:
                print_warning("Base de datos vacía")
                resultados["db_data"] = False
            
            db.close()
            resultados["db_connection"] = True
        except Exception as e:
            print_error(f"Error conectando a base de datos: {e}")
            resultados["db_connection"] = False
            resultados["db_data"] = False
    else:
        print_warning("trading_bot.db no existe (se creará automáticamente)")
        resultados["db_connection"] = True
        resultados["db_data"] = False
    
    return resultados

def test_6_modelos_entrenados():
    """Test 6: Verificar modelos entrenados"""
    print_header("TEST 6: MODELOS ENTRENADOS")
    
    resultados = {}
    
    models_dir = Path("models")
    if models_dir.exists():
        modelos = list(models_dir.glob("*.h5"))
        scalers = list(models_dir.glob("*_scaler.pkl"))
        
        print_info(f"Modelos encontrados: {len(modelos)}")
        print_info(f"Scalers encontrados: {len(scalers)}")
        
        if modelos:
            print_success(f"✅ {len(modelos)} modelo(s) entrenado(s)")
            for modelo in modelos[:5]:  # Mostrar primeros 5
                print_info(f"   • {modelo.name}")
            if len(modelos) > 5:
                print_info(f"   ... y {len(modelos) - 5} más")
            resultados["modelos"] = True
        else:
            print_warning("No hay modelos entrenados")
            resultados["modelos"] = False
        
        resultados["models_dir"] = True
    else:
        print_warning("Directorio models/ no existe")
        resultados["models_dir"] = False
        resultados["modelos"] = False
    
    return resultados

def test_7_horario_trading():
    """Test 7: Verificar horario de trading IOL"""
    print_header("TEST 7: HORARIO DE TRADING IOL")
    
    resultados = {}
    
    try:
        from src.services.professional_trader import ProfessionalTrader
        
        trader = ProfessionalTrader(config_file="professional_config.json")
        time_config = trader.config.get("time_management", {})
        
        start = time_config.get("trading_hours_start", "")
        end = time_config.get("trading_hours_end", "")
        
        print_info(f"Horario configurado: {start} - {end}")
        
        if start == "11:00" and end == "17:00":
            print_success("✅ Horario correcto para IOL (11:00 - 17:00)")
            resultados["horario_correcto"] = True
        else:
            print_error(f"❌ Horario incorrecto. Debería ser 11:00 - 17:00")
            resultados["horario_correcto"] = False
        
        # Verificar hora actual
        now = datetime.now()
        current_time = now.time()
        start_time = time(11, 0)
        end_time = time(17, 0)
        
        print_info(f"Hora actual: {current_time.strftime('%H:%M:%S')}")
        
        can_trade, reason = trader.check_time_filters()
        
        if start_time <= current_time <= end_time:
            if can_trade:
                print_success(f"✅ Dentro del horario de trading IOL - {reason}")
            else:
                print_warning(f"⚠️  Dentro del horario pero bloqueado: {reason}")
        else:
            if current_time < start_time:
                print_info(f"⏰ Mercado aún no abre (abre a las 11:00)")
            else:
                print_info(f"⏰ Mercado ya cerró (cerró a las 17:00)")
        
        resultados["validacion_horario"] = True
    except Exception as e:
        print_error(f"Error verificando horario: {e}")
        resultados["validacion_horario"] = False
    
    return resultados

def test_8_archivos_operacion():
    """Test 8: Verificar archivos de operación"""
    print_header("TEST 8: ARCHIVOS DE OPERACIÓN")
    
    resultados = {}
    
    archivos = {
        "trades.json": "Registro de operaciones",
        "data/operations_log.json": "Log de análisis",
        "bot.pid": "PID del bot (si está corriendo)"
    }
    
    for archivo, descripcion in archivos.items():
        path = Path(archivo)
        if path.exists():
            if archivo == "bot.pid":
                try:
                    pid = int(path.read_text().strip())
                    print_success(f"{archivo} existe (Bot corriendo con PID {pid})")
                except:
                    print_warning(f"{archivo} existe pero no es válido")
            else:
                try:
                    size = path.stat().st_size
                    print_success(f"{archivo} existe ({size:,} bytes)")
                except:
                    print_warning(f"{archivo} existe pero no se puede leer")
            resultados[archivo] = True
        else:
            if archivo != "bot.pid":
                print_warning(f"{archivo} no existe (se creará automáticamente)")
            resultados[archivo] = False
    
    return resultados

def test_9_importaciones():
    """Test 9: Verificar importaciones críticas"""
    print_header("TEST 9: IMPORTACIONES CRÍTICAS")
    
    resultados = {}
    
    modulos = [
        "src.services.prediction_service",
        "src.services.technical_analysis",
        "src.services.portfolio_optimizer",
        "src.services.adaptive_risk_manager",
        "src.services.enhanced_sentiment",
        "src.services.telegram_command_handler"
    ]
    
    for modulo in modulos:
        try:
            __import__(modulo)
            print_success(f"{modulo} importado correctamente")
            resultados[modulo] = True
        except Exception as e:
            print_error(f"{modulo} NO se puede importar: {e}")
            resultados[modulo] = False
    
    return resultados

def test_10_resumen_final():
    """Test 10: Resumen final y recomendaciones"""
    print_header("TEST 10: RESUMEN FINAL")
    
    # Recopilar todos los resultados
    todos_resultados = {}
    
    print_info("Ejecutando todos los tests...")
    
    todos_resultados.update(test_1_archivos_esenciales())
    todos_resultados.update(test_2_configuracion())
    todos_resultados.update(test_3_dependencias())
    todos_resultados.update(test_4_servicios())
    todos_resultados.update(test_5_base_datos())
    todos_resultados.update(test_6_modelos_entrenados())
    todos_resultados.update(test_7_horario_trading())
    todos_resultados.update(test_8_archivos_operacion())
    todos_resultados.update(test_9_importaciones())
    
    # Calcular estadísticas
    total_tests = len(todos_resultados)
    tests_exitosos = sum(1 for v in todos_resultados.values() if v)
    tests_fallidos = total_tests - tests_exitosos
    porcentaje = (tests_exitosos / total_tests * 100) if total_tests > 0 else 0
    
    print_header("RESUMEN DE RESULTADOS")
    
    print(f"{Colors.BOLD}Total de tests: {total_tests}{Colors.RESET}")
    print(f"{Colors.GREEN}✅ Exitosos: {tests_exitosos}{Colors.RESET}")
    print(f"{Colors.RED}❌ Fallidos: {tests_fallidos}{Colors.RESET}")
    print(f"{Colors.BOLD}Porcentaje de éxito: {porcentaje:.1f}%{Colors.RESET}")
    
    # Tests críticos
    print_header("TESTS CRÍTICOS")
    
    criticos = {
        "Configuración IOL": todos_resultados.get("iol_env", False),
        "Autenticación IOL": todos_resultados.get("iol_auth", False),
        "Horario IOL (11:00-17:00)": todos_resultados.get("horario_correcto", False),
        "Base de datos": todos_resultados.get("db_connection", False),
        "Risk Manager": todos_resultados.get("risk_manager", False)
    }
    
    for nombre, resultado in criticos.items():
        if resultado:
            print_success(f"{nombre}: OK")
        else:
            print_error(f"{nombre}: FALLO")
    
    # Recomendaciones
    print_header("RECOMENDACIONES")
    
    if not todos_resultados.get("horario_correcto", False):
        print_warning("⚠️  El horario de trading NO está configurado para IOL (11:00-17:00)")
        print_info("   Solución: Verificar professional_config.json")
    
    if not todos_resultados.get("iol_auth", False):
        print_warning("⚠️  No se pudo autenticar con IOL")
        print_info("   Solución: Verificar credenciales en .env")
    
    if not todos_resultados.get("modelos", False):
        print_warning("⚠️  No hay modelos entrenados")
        print_info("   Solución: Ejecutar entrenamiento desde el dashboard")
    
    if not todos_resultados.get("db_data", False):
        print_warning("⚠️  La base de datos está vacía")
        print_info("   Solución: Ejecutar recolección de datos desde el dashboard")
    
    if porcentaje >= 80:
        print_success("\n🎉 El sistema está en buen estado general")
    elif porcentaje >= 60:
        print_warning("\n⚠️  El sistema tiene algunos problemas menores")
    else:
        print_error("\n❌ El sistema tiene problemas críticos que deben resolverse")
    
    return todos_resultados

def main():
    """Función principal"""
    print_header("TESTEO COMPLETO DEL SISTEMA")
    print_info(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Directorio: {Path.cwd()}")
    
    try:
        resultados = test_10_resumen_final()
        
        print_header("TESTEO COMPLETADO")
        print_info("Revisa los resultados arriba para ver el estado del sistema")
        
    except KeyboardInterrupt:
        print_warning("\nTesteo interrumpido por el usuario")
    except Exception as e:
        print_error(f"\nError crítico durante el testeo: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()


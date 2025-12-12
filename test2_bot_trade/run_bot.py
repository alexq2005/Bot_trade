"""
Wrapper script para ejecutar el bot con mejor manejo de errores y ventana persistente
"""
import sys
import os
import traceback
import io
import threading
import time
from pathlib import Path

# Proteger sys.stderr ANTES de cualquier otra importación
# Esto previene errores cuando argparse intenta escribir a stderr
if hasattr(sys.stderr, 'closed') and sys.stderr.closed:
    # Si stderr está cerrado, crear un wrapper seguro
    class SafeStderr:
        def __init__(self):
            self._buffer = io.StringIO()
        
        def write(self, text):
            try:
                # Intentar escribir a un buffer
                self._buffer.write(text)
            except Exception:
                pass
        
        def flush(self):
            try:
                self._buffer.flush()
            except Exception:
                pass
        
        @property
        def closed(self):
            return False
    
    sys.stderr = SafeStderr()
else:
    # Si stderr no está cerrado, crear un wrapper que verifique antes de escribir
    _original_stderr = sys.stderr
    
    class SafeStderrWrapper:
        def __init__(self, original):
            self._original = original
            self._buffer = io.StringIO()
        
        def write(self, text):
            # Siempre intentar escribir, pero nunca fallar
            try:
                if not hasattr(self._original, 'closed') or not self._original.closed:
                    self._original.write(text)
                    return
            except (ValueError, IOError, OSError, AttributeError):
                pass
            
            # Si falla o está cerrado, usar buffer (nunca falla)
            try:
                self._buffer.write(text)
            except Exception:
                pass  # Si incluso el buffer falla, simplemente ignorar
        
        def flush(self):
            # Siempre intentar flush, pero nunca fallar
            try:
                if not hasattr(self._original, 'closed') or not self._original.closed:
                    self._original.flush()
            except (ValueError, IOError, OSError, AttributeError):
                pass
        
        @property
        def closed(self):
            # Siempre devolver False para que argparse no piense que está cerrado
            # Esto previene que argparse intente escribir y falle
            return False
        
        def __getattr__(self, name):
            # Delegar otros atributos al stderr original de forma segura
            try:
                return getattr(self._original, name)
            except (ValueError, IOError, OSError, AttributeError):
                return None
    
    sys.stderr = SafeStderrWrapper(_original_stderr)
    
# Asegurar que argparse use nuestro stderr protegido
# argparse importa sys internamente como _sys cuando se usa
# Necesitamos interceptar esa importación
import sys as _sys_module
# Guardar referencia al sys original para argparse
_sys_module.stderr = sys.stderr

# También proteger sys.stdout por si acaso
if hasattr(sys.stdout, 'closed') and sys.stdout.closed:
    class SafeStdout:
        def __init__(self):
            self._buffer = io.StringIO()
        
        def write(self, text):
            try:
                self._buffer.write(text)
            except Exception:
                pass
        
        def flush(self):
            try:
                self._buffer.flush()
            except Exception:
                pass
        
        @property
        def closed(self):
            return False
        
        def __getattr__(self, name):
            return None
    
    sys.stdout = SafeStdout()
else:
    _original_stdout = sys.stdout
    
    class SafeStdoutWrapper:
        def __init__(self, original):
            self._original = original
            self._buffer = io.StringIO()
        
        def write(self, text):
            try:
                if not hasattr(self._original, 'closed') or not self._original.closed:
                    self._original.write(text)
                else:
                    self._buffer.write(text)
            except (ValueError, IOError, OSError, AttributeError):
                try:
                    self._buffer.write(text)
                except Exception:
                    pass
        
        def flush(self):
            try:
                if not hasattr(self._original, 'closed') or not self._original.closed:
                    self._original.flush()
            except (ValueError, IOError, OSError, AttributeError):
                pass
        
        @property
        def closed(self):
            try:
                return getattr(self._original, 'closed', False)
            except (ValueError, IOError, OSError, AttributeError):
                return False
        
        def __getattr__(self, name):
            try:
                return getattr(self._original, name)
            except (ValueError, IOError, OSError, AttributeError):
                return None
    
    sys.stdout = SafeStdoutWrapper(_original_stdout)

# Configurar TensorFlow para suprimir mensajes
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
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

# Agregar el directorio actual al path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importar safe_print para evitar errores de I/O
try:
    from src.core.safe_print import safe_print
    # Reemplazar print con safe_print
    _original_print = __builtins__['print'] if isinstance(__builtins__, dict) else __builtins__.print
    def safe_print_wrapper(*args, **kwargs):
        try:
            safe_print(*args, **kwargs)
        except Exception:
            # Si safe_print falla, intentar directamente
            try:
                _original_print(*args, **kwargs)
            except (ValueError, IOError, OSError):
                # Si stdout está cerrado, intentar stderr
                try:
                    kwargs['file'] = sys.stderr
                    _original_print(*args, **kwargs)
                except Exception:
                    pass  # Si todo falla, ignorar
    print = safe_print_wrapper
except ImportError:
    # Si no está disponible, crear una versión básica
    _original_print = __builtins__['print'] if isinstance(__builtins__, dict) else __builtins__.print
    def safe_print(*args, **kwargs):
        try:
            _original_print(*args, **kwargs)
        except (ValueError, IOError, OSError):
            # Si stdout está cerrado, intentar stderr
            try:
                kwargs['file'] = sys.stderr
                _original_print(*args, **kwargs)
            except Exception:
                pass  # Si todo falla, ignorar
    print = safe_print

def main():
    """Ejecuta el bot con manejo robusto de errores"""
    try:
        from trading_bot import TradingBot
        import argparse
        # Asegurar que argparse use nuestro stderr protegido
        # argparse usa sys.stderr internamente, que ya está protegido
        
        parser = argparse.ArgumentParser(description='IOL Quantum AI Trading Bot')
        parser.add_argument('--continuous', action='store_true', help='Run in continuous mode')
        parser.add_argument('--interval', type=int, default=60, help='Interval in minutes')
        parser.add_argument('--live', action='store_true', help='Enable LIVE trading with real money')
        parser.add_argument('--paper', action='store_true', help='Enable PAPER trading (simulation mode) - this is the default')
        parser.add_argument('--symbols', type=str, default=None, 
                          help='Comma-separated list of symbols to monitor (e.g., "AAPL,MSFT,GOOGL,TSLA")')
        parser.add_argument('--chat', '--interactive-chat', action='store_true', 
                          help='Enable interactive chat console (allows chatting while trading)')
        args = parser.parse_args()
        
        # If both --live and --paper are specified, --live takes precedence
        # If neither is specified, default to paper trading
        is_live = args.live and not args.paper
        
        print("=" * 60)
        print("🚀 IOL QUANTUM AI TRADING BOT")
        print("=" * 60)
        print(f"Modo: {'LIVE TRADING' if is_live else 'PAPER TRADING'}")
        if not is_live:
            print(f"💰 Capital inicial: $100,000 ARS (modo prueba)")
        print(f"Ejecución: {'Continua' if args.continuous else 'Ciclo único'}")
        if args.continuous:
            print(f"Intervalo: {args.interval} minutos")
        print("=" * 60)
        print()
        
        # Parse symbols from command line if provided
        symbols = None
        if args.symbols:
            symbols = [s.strip().upper() for s in args.symbols.split(',') if s.strip()]
            print(f"📊 Símbolos especificados manualmente: {', '.join(symbols)}")
            print()
        else:
            # Si no se especifican símbolos, el bot usará automáticamente el portafolio guardado
            print("📂 El bot usará automáticamente los símbolos de tu portafolio guardado (my_portfolio.json)")
            print("   💡 Si quieres especificar símbolos manualmente, usa: --symbols SYMBOL1,SYMBOL2,...")
            print()
        
        # Initialize bot con manejo robusto de errores
        # Capital inicial de prueba: $100,000 ARS
        initial_capital = 100000.0 if not is_live else None  # $100,000 para paper trading, IOL para live
        
        try:
            bot = TradingBot(
                symbols=symbols,  # None = auto-detect from portfolio (my_portfolio.json), or use provided list
                initial_capital=initial_capital,  # $100,000 para pruebas en paper trading
                paper_trading=not is_live
            )
        except (ValueError, IOError, OSError) as io_error:
            # Si es un error de I/O, intentar continuar de todas formas
            if "I/O operation on closed file" in str(io_error) or "closed file" in str(io_error):
                print("⚠️  Advertencia: Error de I/O detectado pero continuando...")
                print("   El bot puede funcionar pero algunos logs pueden no mostrarse")
                # Intentar crear bot de nuevo (puede que el logger ya esté inicializado)
                try:
                    bot = TradingBot(
                        symbols=symbols,
                        initial_capital=initial_capital,  # $100,000 para pruebas
                        paper_trading=not is_live
                    )
                except Exception as e2:
                    print(f"❌ Error crítico inicializando bot: {e2}")
                    raise
            else:
                raise
        
        # Crear archivo PID para que el dashboard pueda detectar que el bot está corriendo
        # IMPORTANTE: Crear PID ANTES de inicializar el bot para que el dashboard lo detecte inmediatamente
        pid_file = Path("bot.pid")
        try:
            # Asegurar que el directorio existe
            pid_file.parent.mkdir(parents=True, exist_ok=True)
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
            print(f"📝 PID guardado en {pid_file} (PID: {os.getpid()})")
        except Exception as e:
            print(f"⚠️  No se pudo crear archivo PID: {e}")
            import traceback
            traceback.print_exc()
        
        # Iniciar chat interactivo si está habilitado
        chat_thread = None
        if args.chat:
            print("💬 Chat interactivo habilitado")
            print("   Puedes escribir mensajes mientras el bot opera\n")
            
            def start_chat():
                """Inicia chat interactivo en thread separado"""
                try:
                    if bot.chat_interface:
                        bot.chat_interface.interactive_chat()
                    else:
                        print("⚠️  Chat interface no disponible")
                except Exception as e:
                    print(f"⚠️  Error en chat: {e}")
            
            chat_thread = threading.Thread(target=start_chat, daemon=True)
            chat_thread.start()
            print("✅ Chat interactivo iniciado en segundo plano\n")
        
        if args.continuous:
            print("✅ Bot iniciado en modo continuo")
            if args.chat:
                print("💬 Chat interactivo activo - Escribe mensajes mientras el bot opera")
            print("   Presiona Ctrl+C para detener\n")
            try:
                bot.run_continuous(interval_minutes=args.interval)
            finally:
                # Eliminar archivo PID al detener
                try:
                    if pid_file.exists():
                        pid_file.unlink()
                        print("📝 Archivo PID eliminado")
                except:
                    pass
        else:
            print("✅ Ejecutando en modo manual")
            print("   El bot ejecutará un ciclo de análisis y mantendrá Telegram activo")
            if args.chat:
                print("💬 Chat interactivo activo - Escribe mensajes mientras el bot opera")
            print("   Presiona Ctrl+C para detener\n")
            
            # Iniciar chat interactivo si está habilitado (en modo manual también)
            if args.chat and not chat_thread:
                def start_chat():
                    """Inicia chat interactivo en thread separado"""
                    try:
                        if bot.chat_interface:
                            bot.chat_interface.interactive_chat()
                        else:
                            print("⚠️  Chat interface no disponible")
                    except Exception as e:
                        print(f"⚠️  Error en chat: {e}")
                
                chat_thread = threading.Thread(target=start_chat, daemon=True)
                chat_thread.start()
                print("✅ Chat interactivo iniciado\n")
            
            # Iniciar polling de Telegram también en modo manual
            if hasattr(bot, 'telegram_command_handler') and bot.telegram_command_handler:
                if bot.telegram_command_handler.bot_token:
                    try:
                        success = bot.telegram_command_handler.start_polling()
                        if success:
                            print("✅ Telegram command handler iniciado - Puedes enviar comandos desde Telegram")
                            print("   💡 Usa /analyze para ejecutar análisis manualmente")
                    except Exception as e:
                        print(f"⚠️  Error iniciando Telegram command handler: {e}")
            
            # Ejecutar un ciclo inicial
            print("\n🔄 Ejecutando ciclo inicial de análisis...\n")
            bot.run_analysis_cycle()
            
            # Mantener el bot corriendo para recibir comandos de Telegram y chat
            print("\n✅ Ciclo inicial completado")
            print("📱 Bot en modo manual - Telegram activo para recibir comandos")
            if args.chat:
                print("💬 Chat interactivo activo - Escribe mensajes en la consola")
            print("   💡 Envía /analyze desde Telegram para ejecutar más análisis")
            print("   💡 Presiona Ctrl+C para detener\n")
            
            # Mantener el bot corriendo
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 Bot detenido por el usuario")
        # Eliminar archivo PID
        pid_file = Path("bot.pid")
        try:
            if pid_file.exists():
                pid_file.unlink()
                print("📝 Archivo PID eliminado")
        except:
            pass
        
    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("🛑 Bot detenido por el usuario (Ctrl+C)")
        print("=" * 60)
        
        # Eliminar archivo PID
        pid_file = Path("bot.pid")
        try:
            if pid_file.exists():
                pid_file.unlink()
                print("📝 Archivo PID eliminado")
        except:
            pass
    except Exception as e:
        # Intentar escribir el error de forma segura
        error_msg = f"""
{'=' * 60}
ERROR CRÍTICO EN EL BOT
{'=' * 60}
Tipo: {type(e).__name__}
Mensaje: {str(e)}

Traceback completo:
{'-' * 60}
"""
        try:
            traceback_str = traceback.format_exc()
            error_msg += traceback_str
        except Exception:
            error_msg += "No se pudo obtener traceback completo\n"
        
        error_msg += f"{'-' * 60}\n"
        error_msg += "\nEsta ventana se cerrará en 30 segundos...\n"
        error_msg += "(O presiona Enter para cerrar ahora)\n"
        
        # Intentar imprimir de forma segura
        try:
            print(error_msg)
        except (ValueError, IOError, OSError):
            # Si print falla, intentar escribir a un archivo
            try:
                from datetime import datetime
                with open("error_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n{datetime.now()}: ERROR CRÍTICO\n")
                    f.write(error_msg)
            except Exception:
                # Si incluso escribir al archivo falla, intentar stderr
                try:
                    sys.stderr.write(error_msg)
                    sys.stderr.flush()
                except Exception:
                    pass  # Si todo falla, simplemente continuar
        
        # Eliminar archivo PID en caso de error
        pid_file = Path("bot.pid")
        try:
            if pid_file.exists():
                pid_file.unlink()
                print("📝 Archivo PID eliminado")
        except:
            pass
        
        if sys.platform == 'win32':
            try:
                import time
                import threading
                
                def wait_for_input():
                    input()
                    os._exit(1)
                
                def auto_close():
                    time.sleep(30)
                    os._exit(1)
                
                # Iniciar threads para input y auto-close
                input_thread = threading.Thread(target=wait_for_input, daemon=True)
                close_thread = threading.Thread(target=auto_close, daemon=True)
                input_thread.start()
                close_thread.start()
                
                # Esperar a que uno termine
                input_thread.join()
            except:
                import time
                time.sleep(5)
        
        sys.exit(1)

if __name__ == "__main__":
    main()


"""
Script para verificar que el bot está usando las nuevas mejoras
"""
import sys
from pathlib import Path

# Agregar el directorio al path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🔍 VERIFICACIÓN DE MEJORAS EN EL BOT")
print("=" * 70)
print()

# Verificar imports
print("📦 Verificando módulos de mejoras...")
try:
    from src.core.error_handler import RetryHandler, retry_on_network_error
    print("✅ error_handler.py - OK")
except ImportError as e:
    print(f"❌ error_handler.py - Error: {e}")

try:
    from src.core.rate_limiter import iol_rate_limiter, telegram_rate_limiter
    print("✅ rate_limiter.py - OK")
except ImportError as e:
    print(f"❌ rate_limiter.py - Error: {e}")

try:
    from src.core.validators import TradeRequest, SymbolValidator
    print("✅ validators.py - OK")
except ImportError as e:
    print(f"❌ validators.py - Error: {e}")

try:
    from src.core.cache_manager import get_cache, cached
    print("✅ cache_manager.py - OK")
except ImportError as e:
    print(f"❌ cache_manager.py - Error: {e}")

print()

# Verificar integraciones
print("🔗 Verificando integraciones...")
try:
    from src.connectors.iol_client import IOLClient
    import inspect
    
    # Verificar que iol_client tiene rate_limiter importado
    source = inspect.getsource(IOLClient)
    if 'iol_rate_limiter' in source or 'rate_limiter' in source:
        print("✅ IOL Client - Rate limiting integrado")
    else:
        print("⚠️  IOL Client - Rate limiting no detectado en código")
except Exception as e:
    print(f"⚠️  Error verificando IOL Client: {e}")

try:
    from src.services.telegram_bot import TelegramAlertBot
    import inspect
    
    source = inspect.getsource(TelegramAlertBot)
    if 'telegram_rate_limiter' in source or 'rate_limiter' in source:
        print("✅ Telegram Bot - Rate limiting integrado")
    else:
        print("⚠️  Telegram Bot - Rate limiting no detectado en código")
except Exception as e:
    print(f"⚠️  Error verificando Telegram Bot: {e}")

print()

# Verificar estado del bot
print("🤖 Verificando estado del bot...")
pid_file = Path("bot.pid")
if pid_file.exists():
    try:
        pid = int(pid_file.read_text().strip())
        print(f"✅ Bot PID file encontrado (PID: {pid})")
        
        # Intentar verificar con psutil si está disponible
        try:
            import psutil
            proc = psutil.Process(pid)
            print(f"   Estado: {proc.status()}")
            print(f"   CPU: {proc.cpu_percent():.1f}%")
            print(f"   Memoria: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
        except ImportError:
            print("   (psutil no disponible para detalles)")
        except psutil.NoSuchProcess:
            print(f"   ⚠️  Proceso no encontrado (puede haber terminado)")
        except Exception as e:
            print(f"   ⚠️  Error verificando proceso: {e}")
    except Exception as e:
        print(f"⚠️  Error leyendo PID: {e}")
else:
    print("❌ Bot NO está corriendo (no hay PID file)")

print()
print("=" * 70)
print("✅ Verificación completada")
print("=" * 70)


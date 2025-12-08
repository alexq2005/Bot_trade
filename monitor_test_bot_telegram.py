"""
Monitor Continuo del Test Bot con Alertas a Telegram
Monitorea el bot de test y envía notificaciones automáticas
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

if not TOKEN or not CHAT_ID:
    print("❌ Token o Chat ID no configurados")
    sys.exit(1)

def enviar_telegram(mensaje):
    """Envía mensaje a Telegram"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensaje,
            "parse_mode": None  # Sin Markdown para evitar errores
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error enviando a Telegram: {e}")
        return False

def verificar_bot_corriendo():
    """Verifica si el bot está corriendo"""
    pid_file = Path("bot.pid")
    if not pid_file.exists():
        return False, None
    
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Verificar proceso
        try:
            import psutil
            if psutil.pid_exists(pid):
                return True, pid
        except ImportError:
            # Sin psutil, usar os.kill
            try:
                os.kill(pid, 0)
                return True, pid
            except:
                return False, None
    except:
        return False, None
    
    return False, None

def leer_terminal():
    """Lee el contenido del terminal del bot"""
    terminal_files = list(Path("c:/Users/Lexus/.cursor/projects/c-Users-Lexus-gemini-antigravity-scratch/terminals").glob("*.txt"))
    
    if not terminal_files:
        return ""
    
    # Leer el más reciente
    latest = max(terminal_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        return ""

def leer_logs():
    """Lee los logs más recientes"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return ""
    
    log_files = list(log_dir.glob("*.log"))
    if not log_files:
        return ""
    
    latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return ''.join(lines[-200:])  # Últimas 200 líneas
    except:
        return ""

# Estado inicial
print("="*70)
print("🔍 MONITOR CONTINUO DEL TEST BOT")
print("="*70)
print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("📱 Notificaciones a Telegram configuradas")
print(f"   Chat ID: {CHAT_ID}")
print()
print("🎯 Monitoreando:")
print("  • Señales BUY/SELL")
print("  • Errores críticos")
print("  • Estado del bot")
print()
print("⏳ Presiona Ctrl+C para detener el monitor")
print("="*70)
print()

# Enviar mensaje de inicio
enviar_telegram(f"""🔍 MONITOR DEL TEST BOT INICIADO

Hora: {datetime.now().strftime('%H:%M:%S')}

Configuracion:
• Buy Threshold: 0 (ultra agresivo)
• Min Confidence: LOW
• Modo: PAPER TRADING

Te avisare cuando:
• Se ejecute una operacion BUY/SELL
• Ocurra un error critico
• El bot se detenga

Monitoreo activo...""")

# Variables de estado
last_analyzed_symbol = None
last_signal_time = datetime.now()
errors_detectados = []
operaciones_detectadas = []
check_count = 0

try:
    while True:
        check_count += 1
        hora_actual = datetime.now().strftime('%H:%M:%S')
        
        # 1. Verificar que el bot esté corriendo
        bot_running, pid = verificar_bot_corriendo()
        
        if not bot_running:
            mensaje = f"""⚠️ ALERTA - BOT DETENIDO

Hora: {hora_actual}
Check: #{check_count}

El bot de test se detuvo inesperadamente.

Verifica los logs para más detalles."""
            
            print(f"\n❌ [{hora_actual}] Bot detenido - Enviando alerta...")
            enviar_telegram(mensaje)
            print("⏸️  Monitor pausado - El bot no está corriendo")
            time.sleep(30)
            continue
        
        # 2. Leer terminal y logs
        terminal_content = leer_terminal()
        logs_content = leer_logs()
        
        # 3. Buscar señales BUY/SELL
        señales_buy = []
        señales_sell = []
        
        for line in terminal_content.split('\n')[-100:]:
            if 'Final Signal: BUY' in line or 'Señal Final: BUY' in line:
                if line not in operaciones_detectadas:
                    señales_buy.append(line)
                    operaciones_detectadas.append(line)
            elif 'Final Signal: SELL' in line or 'Señal Final: SELL' in line:
                if line not in operaciones_detectadas:
                    señales_sell.append(line)
                    operaciones_detectadas.append(line)
        
        # Notificar señales
        if señales_buy:
            # Buscar detalles del símbolo
            simbolo = "UNKNOWN"
            score = 0
            for line in terminal_content.split('\n')[-50:]:
                if 'Símbolo:' in line:
                    simbolo = line.split(':')[-1].strip()
                if 'Score:' in line and 'Scoring' not in line:
                    try:
                        score = int(line.split(':')[-1].strip())
                    except:
                        pass
            
            mensaje = f"""✅ SEÑAL DE COMPRA DETECTADA!

Hora: {hora_actual}
Simbolo: {simbolo}
Score: {score}
Threshold: 0

Modo: PAPER TRADING (simulado)

El bot ejecutara la compra en el proximo ciclo."""
            
            print(f"\n✅ [{hora_actual}] Señal BUY detectada - Enviando alerta...")
            enviar_telegram(mensaje)
        
        if señales_sell:
            mensaje = f"""❌ SEÑAL DE VENTA DETECTADA!

Hora: {hora_actual}
Señales: {len(señales_sell)}

Modo: PAPER TRADING (simulado)"""
            
            print(f"\n❌ [{hora_actual}] Señal SELL detectada - Enviando alerta...")
            enviar_telegram(mensaje)
        
        # 4. Buscar errores críticos
        errores_nuevos = []
        for line in logs_content.split('\n')[-100:]:
            if 'ERROR' in line and 'CRITICAL' in line.upper():
                if line not in errors_detectados:
                    errores_nuevos.append(line)
                    errors_detectados.append(line)
        
        if errores_nuevos:
            mensaje = f"""❌ ERROR CRITICO DETECTADO

Hora: {hora_actual}
Errores: {len(errores_nuevos)}

Primeros errores:
{errores_nuevos[0][:200]}

Revisa los logs para más detalles."""
            
            print(f"\n❌ [{hora_actual}] Error crítico - Enviando alerta...")
            enviar_telegram(mensaje)
        
        # 5. Mostrar progreso cada 10 checks
        if check_count % 10 == 1:
            print(f"[{hora_actual}] Check #{check_count} - Bot corriendo (PID: {pid}) - Monitoreando...")
        
        # Esperar antes del próximo check
        time.sleep(15)  # Check cada 15 segundos

except KeyboardInterrupt:
    print("\n\n🛑 Monitor detenido por usuario")
    
    mensaje = f"""🛑 MONITOR DETENIDO

Hora: {datetime.now().strftime('%H:%M:%S')}
Checks realizados: {check_count}

Monitor detenido manualmente.
El bot de test sigue corriendo."""
    
    enviar_telegram(mensaje)

except Exception as e:
    print(f"\n❌ Error en monitor: {e}")
    import traceback
    traceback.print_exc()
    
    enviar_telegram(f"""❌ ERROR EN MONITOR

El script de monitoreo tuvo un error:
{str(e)[:200]}

El bot de test puede seguir corriendo.""")

finally:
    print()
    print("="*70)
    print("🏁 Monitor Finalizado")
    print("="*70)
    print(f"Checks realizados: {check_count}")
    print(f"Operaciones detectadas: {len(operaciones_detectadas)}")
    print(f"Errores detectados: {len(errors_detectados)}")
    print()


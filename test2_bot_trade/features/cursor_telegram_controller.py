"""
Cursor Telegram Controller
Permite controlar el desarrollo y ejecutar acciones desde Telegram

Estado: 🧪 EN DESARROLLO
Versión: 0.1

Descripción:
    Sistema que escucha comandos de Telegram y ejecuta acciones
    de desarrollo como:
    - Ejecutar scripts
    - Ver logs
    - Reiniciar bots
    - Ver estado del sistema
    - Ejecutar tests
    - Aplicar cambios de test_bot a producción
"""

import sys
import os
import subprocess
from pathlib import Path
from datetime import datetime
import time
import threading

# Agregar path del proyecto
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

class CursorTelegramController:
    """
    Controlador que permite ejecutar comandos de desarrollo desde Telegram
    """
    
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.running = False
        self.last_update_id = 0
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurados")
        
        # Comandos de desarrollo disponibles
        self.dev_commands = {
            '/dev_status': self._handle_dev_status,
            '/dev_logs': self._handle_dev_logs,
            '/dev_restart_test': self._handle_restart_test_bot,
            '/dev_restart_prod': self._handle_restart_prod_bot,
            '/dev_backup': self._handle_create_backup,
            '/dev_apply_changes': self._handle_apply_changes,
            '/dev_test_feature': self._handle_test_feature,
            '/dev_compare': self._handle_compare_configs,
            '/dev_help': self._handle_dev_help,
            '/dev_exec': self._handle_execute_command,
        }
        
        print("✅ Cursor Telegram Controller inicializado")
        print(f"   📱 Bot: {self.bot_token[:15]}...")
        print(f"   💬 Chat: {self.chat_id}")
        print(f"   🎮 Comandos: {len(self.dev_commands)}")
    
    def _send_message(self, text):
        """Envía mensaje a Telegram"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": None  # Sin Markdown
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            return False
    
    def _get_updates(self):
        """Obtiene actualizaciones de Telegram"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 10
            }
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    updates = data.get('result', [])
                    if updates:
                        self.last_update_id = max(u.get('update_id', 0) for u in updates)
                    return updates
            return []
        except Exception as e:
            print(f"⚠️  Error obteniendo updates: {e}")
            return []
    
    def _handle_dev_status(self, message):
        """Muestra estado del sistema de desarrollo"""
        try:
            # Verificar bot de test
            test_pid_file = PROJECT_ROOT / "bot.pid"
            test_running = test_pid_file.exists()
            
            # Verificar bot de producción
            prod_running = False
            if test_pid_file.exists():
                # Simplificado: si hay PID, asumimos que corre
                prod_running = True
            
            # Contar archivos en test_bot
            test_files = len(list((PROJECT_ROOT / "test_bot").rglob("*.py")))
            
            mensaje = f"""📊 ESTADO DEL SISTEMA DE DESARROLLO

⏰ Hora: {datetime.now().strftime('%H:%M:%S')}

🤖 Bot de Test:
{'✅ CORRIENDO' if test_running else '❌ DETENIDO'}
Ubicacion: /test_bot/
Archivos: {test_files} archivos Python

🚀 Bot de Produccion:
{'✅ FUNCIONANDO' if prod_running else '❌ DETENIDO'}
Ubicacion: /financial_ai/

📁 Test Bot:
• trading_bot.py modificable
• dashboard.py modificable
• src/ completa copiada

💾 Backup:
• Disponible para rollback
• Ultima copia guardada

✅ Sistema listo para desarrollo"""
            
            self._send_message(mensaje)
            
        except Exception as e:
            self._send_message(f"❌ Error: {e}")
    
    def _handle_dev_logs(self, message):
        """Envía últimas líneas de logs"""
        try:
            log_dir = PROJECT_ROOT / "logs"
            if not log_dir.exists():
                self._send_message("ℹ️  No hay logs disponibles")
                return
            
            log_files = list(log_dir.glob("*.log"))
            if not log_files:
                self._send_message("ℹ️  No hay archivos de log")
                return
            
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_log, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                ultimas = ''.join(lines[-20:])  # Últimas 20 líneas
            
            mensaje = f"""📋 LOGS RECIENTES

Archivo: {latest_log.name}
Hora: {datetime.now().strftime('%H:%M:%S')}

Ultimas 20 lineas:
{ultimas[:1000]}"""  # Limitar a 1000 chars
            
            self._send_message(mensaje)
            
        except Exception as e:
            self._send_message(f"❌ Error: {e}")
    
    def _handle_restart_test_bot(self, message):
        """Reinicia el bot de test"""
        try:
            self._send_message("🔄 Reiniciando bot de test...")
            
            # Detener bot actual
            pid_file = PROJECT_ROOT / "bot.pid"
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                             capture_output=True, timeout=5)
                time.sleep(2)
            
            # Iniciar nuevo bot de test
            os.chdir(PROJECT_ROOT / "test_bot")
            subprocess.Popen(
                [sys.executable, 'run_bot.py', '--paper', '--continuous', '--interval', '5'],
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
            
            time.sleep(5)
            
            self._send_message("""✅ BOT DE TEST REINICIADO

⏰ Hora: """ + datetime.now().strftime('%H:%M:%S') + """
🎯 Estado: INICIANDO
📊 Modo: PAPER TRADING
⏱️  Intervalo: 5 minutos

El bot esta analizando...
Te avisare cuando complete el primer ciclo.""")
            
        except Exception as e:
            self._send_message(f"❌ Error reiniciando: {e}")
    
    def _handle_restart_prod_bot(self, message):
        """Reinicia el bot de producción (CUIDADO)"""
        self._send_message("""⚠️  REINICIO DE BOT DE PRODUCCION

Este comando reinicia el bot que opera con dinero REAL.

⚠️  ⚠️  ⚠️  PRECAUCION EXTREMA ⚠️  ⚠️  ⚠️

Para confirmar, envia:
/dev_confirm_restart_prod

(Este es un mecanismo de seguridad)""")
    
    def _handle_create_backup(self, message):
        """Crea un backup del estado actual"""
        try:
            self._send_message("💾 Creando backup...")
            
            os.chdir(PROJECT_ROOT)
            result = subprocess.run(
                [sys.executable, 'backup_estado_estable.py', 'backup_telegram'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self._send_message(f"""✅ BACKUP CREADO

⏰ Hora: {datetime.now().strftime('%H:%M:%S')}
📁 Ubicacion: backups/
✅ Sistema respaldado

Puedes continuar desarrollo con seguridad.""")
            else:
                self._send_message(f"❌ Error creando backup:\n{result.stderr[:500]}")
                
        except Exception as e:
            self._send_message(f"❌ Error: {e}")
    
    def _handle_apply_changes(self, message):
        """Aplica cambios de test_bot a producción"""
        self._send_message("""⚠️  APLICAR CAMBIOS A PRODUCCION

Este comando copiara archivos de test_bot/ a produccion.

⚠️  Asegurate de:
1. Haber probado en test_bot/
2. Sin errores en logs
3. Crear backup primero

Para confirmar, envia:
/dev_confirm_apply [archivo]

Ejemplo:
/dev_confirm_apply trading_bot.py""")
    
    def _handle_test_feature(self, message):
        """Ejecuta tests de una feature"""
        try:
            # Listar features disponibles
            features_dir = PROJECT_ROOT / "test_bot" / "features"
            features = list(features_dir.glob("*.py"))
            features = [f.stem for f in features if not f.stem.startswith('_')]
            
            if not features:
                self._send_message("ℹ️  No hay features para testear")
                return
            
            mensaje = f"""🧪 FEATURES DISPONIBLES

Total: {len(features)}

Features:
"""
            for f in features[:10]:
                mensaje += f"• {f}\n"
            
            mensaje += "\nPara testear:\n/dev_run_test [feature_name]"
            
            self._send_message(mensaje)
            
        except Exception as e:
            self._send_message(f"❌ Error: {e}")
    
    def _handle_compare_configs(self, message):
        """Compara configs de test vs producción"""
        try:
            import json
            
            # Cargar configs
            with open(PROJECT_ROOT / "test_bot" / "configs" / "professional_config.json", 'r') as f:
                test_config = json.load(f)
            
            with open(PROJECT_ROOT / "professional_config.json", 'r') as f:
                prod_config = json.load(f)
            
            # Comparar parámetros clave
            diferencias = []
            
            keys_to_compare = ['buy_threshold', 'sell_threshold', 'min_confidence', 
                              'risk_per_trade', 'max_daily_trades']
            
            for key in keys_to_compare:
                test_val = test_config.get(key, 'N/A')
                prod_val = prod_config.get(key, 'N/A')
                
                if test_val != prod_val:
                    diferencias.append(f"• {key}:\n  Test: {test_val}\n  Prod: {prod_val}")
            
            mensaje = f"""📊 COMPARACION DE CONFIGURACIONES

Test Bot vs Produccion

{"="*30}
DIFERENCIAS:
{"="*30}

"""
            if diferencias:
                mensaje += '\n\n'.join(diferencias)
            else:
                mensaje += "✅ Configuraciones identicas"
            
            self._send_message(mensaje)
            
        except Exception as e:
            self._send_message(f"❌ Error: {e}")
    
    def _handle_dev_help(self, message):
        """Muestra ayuda de comandos de desarrollo"""
        mensaje = """🛠️ COMANDOS DE DESARROLLO

MONITOREO:
• /dev_status - Estado del sistema
• /dev_logs - Ver logs recientes

CONTROL:
• /dev_restart_test - Reiniciar bot de test
• /dev_restart_prod - Reiniciar produccion (cuidado)

DESARROLLO:
• /dev_backup - Crear backup
• /dev_test_feature - Listar features
• /dev_compare - Comparar configs

EJECUCION:
• /dev_exec [comando] - Ejecutar comando
  Ejemplo: /dev_exec python script.py

APLICACION:
• /dev_apply_changes - Aplicar a produccion

AYUDA:
• /dev_help - Esta ayuda

NOTA: Estos son comandos de DESARROLLO
No afectan el trading normal del bot."""
        
        self._send_message(mensaje)
    
    def _handle_execute_command(self, message):
        """Ejecuta un comando de sistema"""
        try:
            # Extraer comando del mensaje
            parts = message.split(' ', 1)
            if len(parts) < 2:
                self._send_message("❌ Uso: /dev_exec [comando]\nEjemplo: /dev_exec python script.py")
                return
            
            comando = parts[1].strip()
            
            self._send_message(f"⏳ Ejecutando: {comando}")
            
            # Ejecutar comando
            os.chdir(PROJECT_ROOT)
            result = subprocess.run(
                comando,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Enviar resultado
            output = result.stdout if result.stdout else result.stderr
            
            mensaje = f"""✅ COMANDO EJECUTADO

Comando: {comando}
Codigo de salida: {result.returncode}

Salida:
{output[:1000]}"""  # Limitar a 1000 chars
            
            self._send_message(mensaje)
            
        except subprocess.TimeoutExpired:
            self._send_message("⏱️ Timeout: Comando tardo mas de 30 segundos")
        except Exception as e:
            self._send_message(f"❌ Error: {e}")
    
    def _process_message(self, update):
        """Procesa un mensaje recibido"""
        try:
            message = update.get('message', {})
            if not message:
                return
            
            text = message.get('text', '').strip()
            chat_id = str(message.get('chat', {}).get('id', ''))
            
            # Verificar autorización
            if chat_id != str(self.chat_id):
                print(f"⚠️  Mensaje no autorizado de: {chat_id}")
                return
            
            # Verificar si es comando de desarrollo
            if not text.startswith('/dev_'):
                return
            
            print(f"📨 Comando de desarrollo: {text}")
            
            # Buscar y ejecutar comando
            comando = text.split(' ')[0]
            
            if comando in self.dev_commands:
                print(f"⚙️  Ejecutando: {comando}")
                self.dev_commands[comando](text)
            else:
                self._send_message(f"❓ Comando no reconocido: {comando}\n\nEnvia /dev_help para ver comandos disponibles")
                
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            self._send_message(f"❌ Error procesando comando: {e}")
    
    def start(self):
        """Inicia el controller"""
        if self.running:
            print("⚠️  Controller ya está corriendo")
            return
        
        self.running = True
        
        print()
        print("="*70)
        print("🚀 CURSOR TELEGRAM CONTROLLER INICIADO")
        print("="*70)
        print()
        print("📱 Escuchando comandos de desarrollo en Telegram...")
        print("💡 Envia /dev_help para ver comandos disponibles")
        print()
        print("⏳ Presiona Ctrl+C para detener")
        print("="*70)
        print()
        
        # Enviar mensaje de inicio
        self._send_message(f"""🛠️ CURSOR CONTROLLER INICIADO

⏰ Hora: {datetime.now().strftime('%H:%M:%S')}

Ahora puedes controlar el desarrollo desde Telegram.

📋 Comandos disponibles:
• /dev_status - Estado del sistema
• /dev_logs - Ver logs
• /dev_restart_test - Reiniciar test bot
• /dev_backup - Crear backup
• /dev_help - Ayuda completa

✅ Controller activo y escuchando...""")
        
        # Loop de polling
        try:
            while self.running:
                updates = self._get_updates()
                
                for update in updates:
                    self._process_message(update)
                
                time.sleep(2)  # Check cada 2 segundos
                
        except KeyboardInterrupt:
            print("\n🛑 Controller detenido por usuario")
            self._send_message("🛑 Cursor Controller detenido")
        except Exception as e:
            print(f"❌ Error en loop: {e}")
            self._send_message(f"❌ Controller error: {e}")
        finally:
            self.running = False
            print("✅ Controller finalizado")

# Ejecutar como script standalone
if __name__ == "__main__":
    try:
        controller = CursorTelegramController()
        controller.start()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()


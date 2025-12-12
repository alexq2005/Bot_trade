"""
Telegram Command Handler
Recibe y procesa comandos desde Telegram
"""
import os
import sys
import time
import threading
from typing import Optional, Callable, Dict
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests no disponible, no se pueden recibir mensajes de Telegram")


class TelegramCommandHandler:
    """
    Maneja comandos recibidos desde Telegram usando polling
    """
    
    def __init__(self, bot_token=None, chat_id=None, command_callbacks=None):
        """
        Args:
            bot_token: Telegram bot token
            chat_id: Chat ID autorizado (None para aceptar cualquier chat)
            command_callbacks: Dict de comandos y sus funciones callback
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.command_callbacks = command_callbacks or {}
        self.running = False
        self.polling_thread = None
        self.last_update_id = 0
        
        # Inicializar siempre all_commands para evitar AttributeError
        self.all_commands = {}

        if not self.bot_token:
            print("⚠️  TELEGRAM_BOT_TOKEN no configurado")
            # No retornar aquí para permitir que el bot funcione sin Telegram
        
        # Comandos por defecto
        self.default_commands = {
            '/start': self._handle_start,
            '/help': self._handle_help,
            '/ayuda': self._handle_help,  # Alias en español
            '/status': self._handle_status,
            '/estado': self._handle_status,  # Alias en español
        }
        
        # Combinar comandos por defecto con los personalizados
        self.all_commands = {**self.default_commands, **self.command_callbacks}
    
    def _send_message(self, chat_id, message, parse_mode=None):
        """Envía un mensaje a Telegram"""
        if not REQUESTS_AVAILABLE or not self.bot_token:
            print(f"⚠️  No se puede enviar mensaje: requests={REQUESTS_AVAILABLE}, token={'✅' if self.bot_token else '❌'}")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": str(chat_id),
                "text": message
            }
            # Solo agregar parse_mode si no es None
            if parse_mode:
                payload["parse_mode"] = parse_mode
            
            print(f"📤 Enviando mensaje a chat_id {chat_id}...")
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            if result.get('ok'):
                print(f"✅ Mensaje enviado exitosamente")
                return True
            else:
                error_desc = result.get('description', 'Unknown error')
                print(f"❌ Error de API de Telegram: {error_desc}")
                print(f"   Payload: {payload}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión enviando mensaje: {e}")
            # Si es error 400, mostrar más detalles
            if hasattr(e, 'response') and e.response:
                try:
                    error_detail = e.response.json()
                    print(f"   Detalles del error: {error_detail}")
                except:
                    print(f"   Response text: {e.response.text[:200]}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado enviando mensaje: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_updates(self):
        """Obtiene actualizaciones de Telegram"""
        if not REQUESTS_AVAILABLE or not self.bot_token:
            return []
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": 10,
                "allowed_updates": ["message"]
            }
            # Aumentar timeout para conexiones lentas y manejar mejor los errores
            response = requests.get(url, params=params, timeout=30)
            
            # Manejar error 409 (Conflict) - múltiples instancias haciendo polling
            if response.status_code == 409:
                # NO imprimir aquí - el loop principal manejará el mensaje solo la primera vez
                # Solo resetear offset y retornar lista vacía
                self.last_update_id = 0
                # Lanzar excepción para que el loop la maneje (mostrará mensaje solo la primera vez)
                raise requests.exceptions.HTTPError(f"409 Conflict: {response.text}")
            
            response.raise_for_status()
            data = response.json()
            
            if data.get('ok'):
                updates = data.get('result', [])
                # Actualizar last_update_id al último update_id recibido
                if updates:
                    self.last_update_id = max(u.get('update_id', 0) for u in updates)
                return updates
            return []
        except requests.exceptions.Timeout as e:
            # Timeout - no es crítico, solo retornar lista vacía silenciosamente
            # No mostrar error repetitivo que llena los logs
            return []
        except requests.exceptions.ConnectionError as e:
            # Error de conexión - no es crítico, solo retornar lista vacía silenciosamente
            # No mostrar error repetitivo que llena los logs
            return []
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response and e.response.status_code == 409:
                # Error 409 - lanzar para que el loop principal lo maneje (solo mostrará mensaje la primera vez)
                raise
            else:
                # Otros errores HTTP - no críticos, solo retornar lista vacía
                return []
        except requests.exceptions.RequestException as e:
            # Otros errores de requests - no críticos, solo retornar lista vacía
            return []
        except Exception as e:
            # Otros errores - no críticos, solo retornar lista vacía
            return []
    
    def _handle_start(self, chat_id, message_text):
        """Maneja el comando /start"""
        response = """
🤖 *IOL Quantum AI Trading Bot*

¡Hola! Soy tu bot de trading.

*Comandos disponibles:*
/help o /ayuda - Ver esta ayuda
/status o /estado - Estado del bot
/portfolio o /portafolio - Ver portafolio
/balance o /saldo - Ver saldo disponible
/analyze o /analizar - Ejecutar análisis manual

Envía cualquier comando para interactuar conmigo.
"""
        self._send_message(chat_id, response, parse_mode=None)
    
    def _handle_help(self, chat_id, message_text):
        """Maneja el comando /help"""
        response = """📚 COMANDOS DEL BOT

🎮 CONTROL
• /start - Iniciar bot
• /detener - Detener bot
• /pausar - Pausar trading
• /reanudar - Reanudar trading
• /reiniciar - Reiniciar análisis
• /reiniciar_completo - Reinicio completo

📊 INFORMACIÓN
• /ayuda - Ver comandos
• /estado - Estado del bot
• /portafolio - Ver portafolio
• /posiciones - Posiciones con P&L
• /saldo - Ver saldo
• /pnl - Resumen P&L
• /proximo - Próximo análisis
• /puntuaciones - Ver scores

🔍 ANÁLISIS
• /analizar AAPL - Analizar símbolo
• /mercado - Resumen de mercado
• /reporte_diario - Reporte diario
• /grafico AAPL - Generar gráfico

⚙️ CONFIGURACIÓN
• /configuracion - Ver config
• /establecer_riesgo 0.03 - Riesgo (3%)
• /establecer_intervalo 30 - Intervalo
• /establecer_umbral_compra 25
• /establecer_umbral_venta -25
• /establecer_modo manual

🔔 NOTIFICACIONES
• /silenciar 60 - Mute temporal
• /unsilence - Reactivar
• /alternar_sentimiento - On/Off
• /alternar_noticias - On/Off
• /alternar_autoconfig - On/Off

💡 EJEMPLOS:
/analizar AAPL
/establecer_umbral_compra 20
/silenciar 60
/proximo

📝 Todos tienen alias en inglés
(help, status, portfolio, analyze, etc.)

✅ 27 comandos únicos disponibles"""
        # Enviar SIN parse_mode para evitar errores de formato
        self._send_message(chat_id, response, parse_mode=None)
    
    def _handle_status(self, chat_id, message_text):
        """Maneja el comando /status"""
        # Verificar si el bot está corriendo
        pid_file = Path("bot.pid")
        bot_running = pid_file.exists()
        
        status_icon = "🟢" if bot_running else "🔴"
        status_text = "ACTIVO" if bot_running else "INACTIVO"
        
        # Obtener modo de trading (puede no estar disponible)
        trading_mode = getattr(self, 'paper_trading', None)
        mode_text = 'PAPER TRADING' if trading_mode else 'LIVE TRADING' if trading_mode is False else 'DESCONOCIDO'
        
        response = f"""
{status_icon} *Estado del Bot*

*Estado:* {status_text}
*Modo:* {mode_text}

*Última actualización:* {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
        self._send_message(chat_id, response, parse_mode=None)
    
    def register_command(self, command: str, callback: Callable):
        """Registra un nuevo comando"""
        self.all_commands[command] = callback
    
    def _process_message(self, update):
        """Procesa un mensaje recibido"""
        try:
            print(f"   🔍 _process_message() llamado con update_id: {update.get('update_id', '?')}")
            
            message = update.get('message', {})
            if not message:
                print(f"   ⚠️  Update sin 'message' - ignorando")
                return
            
            chat = message.get('chat', {})
            chat_id = chat.get('id')
            text = message.get('text', '').strip()
            from_user = message.get('from', {})
            username = from_user.get('username', 'Unknown')
            first_name = from_user.get('first_name', 'Usuario')
            
            print(f"📨 Mensaje recibido de {first_name} (@{username}): '{text}'")
            print(f"   Chat ID del mensaje: {chat_id}")
            print(f"   Chat ID configurado: {self.chat_id}")
            
            # Verificar autorización si chat_id está configurado
            if self.chat_id and str(chat_id) != str(self.chat_id):
                print(f"⚠️  ❌ Mensaje RECHAZADO - Chat no autorizado: {chat_id} (esperado: {self.chat_id})")
                return
            else:
                print(f"   ✅ Chat autorizado - Procesando comando...")
            
            # Actualizar last_update_id
            self.last_update_id = max(self.last_update_id, update.get('update_id', 0))
            
            if not text:
                print("⚠️  Mensaje sin texto, ignorando")
                return
            
            # Buscar comando
            command = None
            args = ""
            
            if text.startswith('/'):
                parts = text.split(' ', 1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                print(f"🔍 Comando detectado: {command} (args: {args})")
            else:
                # Si no es un comando, tratar como mensaje libre
                command = 'message'
                args = text
                print(f"💬 Mensaje libre recibido")
            
            # Ejecutar comando si existe
            if command in self.all_commands:
                try:
                    print(f"⚙️  Ejecutando comando: {command}")
                    self.all_commands[command](chat_id, args)
                    print(f"✅ Comando {command} ejecutado exitosamente")
                except Exception as e:
                    error_msg = f"❌ Error ejecutando comando {command}: {e}"
                    print(error_msg)
                    import traceback
                    traceback.print_exc()
                    self._send_message(chat_id, error_msg)
            elif command == 'message':
                # Mensaje libre - responder con ayuda
                print("💡 Enviando mensaje de ayuda para mensaje libre")
                self._send_message(chat_id, "💡 Envía /help para ver los comandos disponibles.")
            else:
                # Comando no reconocido
                print(f"❓ Comando no reconocido: {command}")
                self._send_message(chat_id, f"❓ Comando '{command}' no reconocido. Envía /help para ver comandos disponibles.")
        
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")
            import traceback
            traceback.print_exc()
    
    def _polling_loop(self):
        """Loop principal de polling"""
        print("🔄 Iniciando polling de Telegram...")
        print(f"   Token: {'✅ Configurado' if self.bot_token else '❌ No configurado'}")
        print(f"   Chat ID: {'✅ Configurado' if self.chat_id else '❌ No configurado (acepta todos)'}")
        print(f"   💡 Loop de polling ACTIVO - Esperando mensajes...")
        
        consecutive_errors = 0
        max_errors = 10  # Aumentar antes de detener
        conflict_count = 0
        max_conflicts = 3
        connection_errors = 0
        last_connection_error_time = 0
        connection_error_cooldown = 300  # 5 minutos entre mensajes de error de conexión
        poll_count = 0
        
        while self.running:
            try:
                poll_count += 1
                # Mostrar actividad cada 50 polls para confirmar que está funcionando
                if poll_count % 50 == 1:
                    print(f"   🔄 Polling activo (check #{poll_count})...")
                
                updates = self._get_updates()
                
                if updates:
                    print(f"📨 ¡RECIBIDAS {len(updates)} ACTUALIZACIONES!")
                    # Resetear contadores si recibimos actualizaciones
                    conflict_count = 0
                    consecutive_errors = 0
                    connection_errors = 0
                    
                    # Procesar CADA update
                    for idx, update in enumerate(updates, 1):
                        print(f"   🔄 Procesando update {idx}/{len(updates)} (ID: {update.get('update_id', '?')})...")
                        try:
                            self._process_message(update)
                            print(f"   ✅ Update {idx} procesado correctamente")
                        except Exception as proc_error:
                            print(f"   ❌ ERROR procesando update {idx}: {proc_error}")
                            import traceback
                            traceback.print_exc()
                else:
                    # Sin updates - esto es normal en polling
                    pass
                
                # Resetear contador de errores si todo va bien
                consecutive_errors = 0
                connection_errors = 0
                
                # Pequeña pausa para no saturar la API
                time.sleep(1)
            
            except Exception as e:
                error_str = str(e)
                error_type = type(e).__name__
                
                # Detectar error 409 específicamente
                if "409" in error_str or "Conflict" in error_str:
                    conflict_count += 1
                    if conflict_count == 1:
                        # Solo mostrar el mensaje la primera vez
                        print(f"\n⚠️  Error 409: Conflicto de polling detectado")
                        print(f"   💡 Otra instancia del bot está usando Telegram")
                        print(f"   💡 El bot continuará funcionando, pero no recibirá comandos de Telegram")
                        print(f"   💡 Para solucionarlo, detén todas las instancias y reinicia solo una")
                        print(f"   💡 Deteniendo polling después de {max_conflicts} intentos...")
                        print(f"   💡 (Los siguientes errores 409 serán silenciosos)\n")
                    elif conflict_count >= max_conflicts:
                        # Detener polling silenciosamente después de varios conflictos
                        print(f"🛑 Polling de Telegram detenido (conflicto con otra instancia)")
                        print(f"   ℹ️  El bot continuará funcionando normalmente, solo sin comandos de Telegram")
                        self.running = False
                        break
                    # Esperar antes de reintentar (solo si aún no alcanzamos el límite)
                    # NO imprimir mensajes repetidos - solo esperar silenciosamente
                    if conflict_count < max_conflicts:
                        time.sleep(5)  # Reducir tiempo de espera
                    else:
                        # Ya alcanzamos el límite, detener
                        self.running = False
                        break
                # Detectar errores de conexión/timeout
                elif "Timeout" in error_type or "Connection" in error_type or "timeout" in error_str.lower() or "connection" in error_str.lower():
                    connection_errors += 1
                    consecutive_errors += 1
                    
                    # Solo mostrar mensaje de error de conexión cada 5 minutos
                    current_time = time.time()
                    if current_time - last_connection_error_time > connection_error_cooldown:
                        print(f"⚠️  Error de conexión con Telegram (intento {connection_errors})")
                        print(f"   💡 El bot continuará funcionando normalmente")
                        print(f"   💡 Los comandos de Telegram estarán temporalmente no disponibles")
                        print(f"   💡 Se reintentará automáticamente...")
                        last_connection_error_time = current_time
                    
                    # No detener el polling por errores de conexión temporales
                    # Solo esperar un poco más antes de reintentar
                    if connection_errors < 20:  # Permitir muchos errores de conexión
                        time.sleep(10)  # Esperar 10 segundos antes de reintentar
                    else:
                        time.sleep(30)  # Esperar más si hay muchos errores
                else:
                    consecutive_errors += 1
                    # Solo mostrar errores no críticos ocasionalmente
                    if consecutive_errors <= 3 or consecutive_errors % 5 == 0:
                        print(f"⚠️  Error en polling ({consecutive_errors}/{max_errors}): {error_type}")
                    
                    if consecutive_errors >= max_errors:
                        print(f"⚠️  Demasiados errores consecutivos. Deteniendo polling.")
                        print(f"   ℹ️  El bot continuará funcionando normalmente, solo sin comandos de Telegram")
                        self.running = False
                        break
                    
                    time.sleep(5)  # Esperar más tiempo si hay error
    
    def start_polling(self):
        """Inicia el polling en un thread separado"""
        if not self.bot_token:
            print("⚠️  No se puede iniciar polling: TELEGRAM_BOT_TOKEN no configurado")
            return False
        
        if not REQUESTS_AVAILABLE:
            print("⚠️  No se puede iniciar polling: requests no disponible")
            return False
        
        if self.running:
            print("⚠️  Polling ya está corriendo en esta instancia")
            return False
        
        # Verificar si hay otra instancia haciendo polling (verificar offset)
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            test_params = {"offset": -1, "timeout": 1, "allowed_updates": ["message"]}
            test_response = requests.get(url, params=test_params, timeout=5)
            if test_response.status_code == 409:
                print("⚠️  Error 409: Otra instancia del bot está haciendo polling")
                print("   💡 Detén otras instancias del bot antes de iniciar esta")
                print("   💡 O usa el script: reiniciar_bot_limpio.bat")
                print("   ⚠️  POLLING NO INICIADO - El bot NO recibirá comandos de Telegram")
                return False
        except Exception as e:
            # Si falla la verificación, intentar continuar de todas formas
            print(f"   ⚠️  No se pudo verificar estado de polling: {e}")
            print(f"   💡 Intentando iniciar polling de todas formas...")
        
        self.running = True
        self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.polling_thread.start()
        print("✅ Polling de Telegram iniciado - Escuchando mensajes...")
        print(f"   Token: ✅ Configurado")
        print(f"   Chat ID: ✅ Configurado" if self.chat_id else "   Chat ID: ⚠️  No configurado (acepta todos)")
        print(f"   💡 Envía /help a tu bot para probar")
        print(f"   💡 El bot está ACTIVAMENTE escuchando comandos")
        return True
    
    def stop_polling(self):
        """Detiene el polling"""
        self.running = False
        if self.polling_thread:
            self.polling_thread.join(timeout=5)
        print("🛑 Polling de Telegram detenido")
    
    def set_paper_trading(self, paper_trading: bool):
        """Establece el modo de trading"""
        self.paper_trading = paper_trading


# Ejemplo de uso
if __name__ == "__main__":
    handler = TelegramCommandHandler()
    
    # Registrar comandos personalizados
    def handle_portfolio(chat_id, args):
        handler._send_message(chat_id, "📊 Portafolio:\n\n(Implementar lógica aquí)")
    
    handler.register_command('/portfolio', handle_portfolio)
    
    # Iniciar polling
    handler.start_polling()
    
    try:
        # Mantener el script corriendo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handler.stop_polling()
        print("\n👋 Saliendo...")


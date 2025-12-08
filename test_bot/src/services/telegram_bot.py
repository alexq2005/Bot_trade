"""
Telegram Alert Bot
Send trading alerts via Telegram
Usa requests directamente para evitar problemas con python-telegram-bot v20+
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Intentar importar requests (requerido)
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests no disponible. Instala con: pip install requests")


class TelegramAlertBot:
    """
    Send trading alerts via Telegram.
    Usa requests directamente para evitar problemas con python-telegram-bot v20+
    """

    def __init__(self, bot_token=None, chat_id=None):
        """
        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Telegram chat ID to send messages to
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        # NO inicializar self.bot - siempre usar requests directamente
        # El objeto Bot de python-telegram-bot v20+ tiene problemas con weak references
        self._use_requests_fallback = True  # Siempre usar requests por defecto

        if not self.bot_token or not self.chat_id:
            if not self.bot_token:
                print("⚠️  TELEGRAM_BOT_TOKEN not configured")
            if not self.chat_id:
                print("⚠️  TELEGRAM_CHAT_ID not configured")
            return

        # Validar credenciales
        if not self.bot_token.strip() or not str(self.chat_id).strip():
            print("⚠️  Telegram credentials are empty")
            return

        # Usar requests directamente para evitar problemas con el objeto Bot
        if REQUESTS_AVAILABLE:
            print("✅ Telegram configurado (usando método directo vía requests)")
        else:
            print("⚠️  requests no disponible, Telegram no funcionará")
    
    @property
    def bot(self):
        """
        Propiedad para compatibilidad con código que verifica self.bot.
        Siempre retorna True si las credenciales están configuradas.
        """
        return self.bot_token and self.chat_id

    def _send_via_requests(self, message):
        """Envía mensaje usando requests directamente (método principal)
        NO BLOQUEA - Timeout corto y manejo silencioso de errores
        """
        if not REQUESTS_AVAILABLE:
            return False  # Fallback silencioso
        
        # Rate limiting para Telegram API
        try:
            from src.core.rate_limiter import telegram_rate_limiter
            telegram_rate_limiter.wait_if_needed('telegram_api', silent=True)
        except ImportError:
            pass  # Si no está disponible, continuar sin rate limiting
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": str(self.chat_id),  # Asegurar que sea string
                "text": message,
                "parse_mode": "Markdown"
            }
            # Timeout corto (3 segundos) para no bloquear el bot
            response = requests.post(url, json=payload, timeout=3)
            response.raise_for_status()
            
            # Verificar respuesta
            result = response.json()
            if result.get('ok'):
                return True
            else:
                # Error silencioso - no imprimir para no saturar logs
                return False
                
        except requests.exceptions.Timeout:
            # Timeout silencioso - no interrumpir el bot
            return False
        except requests.exceptions.RequestException:
            # Error de conexión silencioso
            return False
        except Exception:
            # Cualquier otro error silencioso
            return False

    def send_alert(self, message, parse_mode="Markdown"):
        """
        Send alert message via Telegram using requests directly.
        This avoids issues with the Bot object and weak references.

        Args:
            message: Message text (supports Markdown)
            parse_mode: 'Markdown' or 'HTML' (solo Markdown soportado con requests)
        """
        # Validaciones iniciales
        if not self.bot_token or not self.chat_id:
            print(f"📱 [Telegram] {message}")  # Fallback to console
            return False

        # Usar requests directamente (método más confiable)
        return self._send_via_requests(message)

    def send_trading_signal(self, symbol, signal, price, confidence, data=None):
        """
        Send formatted trading signal.
        """
        emoji = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}

        message = f"""
{emoji.get(signal, '⚪')} *TRADING SIGNAL*

*Symbol:* {symbol}
*Signal:* {signal}
*Price:* ${price:.2f}
*Confidence:* {confidence:.2%}
"""

        if data:
            message += "\n*Additional Data:*\n"
            for key, value in data.items():
                message += f"• {key}: {value}\n"

        return self.send_alert(message)


# Example usage
if __name__ == "__main__":
    # Initialize bot (requires environment variables or parameters)
    bot = TelegramAlertBot()

    # Send test alert
    bot.send_alert("🚀 *IOL Quantum AI Bot Started*\nMonitoring markets...")

    # Send trading signal
    bot.send_trading_signal(
        symbol="AAPL",
        signal="BUY",
        price=150.00,
        confidence=0.85,
        data={"RSI": 28.5, "MACD": "Bullish Crossover", "Target": "$165.00"},
    )

"""
Sistema de Alertas en Tiempo Real
Notificaciones push, sonidos, email y Telegram mejorado
"""
import os
import json
import smtplib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.core.logger import get_logger
from src.core.config_manager import get_config_manager
from src.services.telegram_bot import TelegramAlertBot

logger = get_logger("realtime_alerts")


class RealtimeAlertSystem:
    """Sistema completo de alertas en tiempo real"""
    
    def __init__(self):
        self.telegram_bot = TelegramAlertBot()
        self.alert_history = []
        self.alert_file = Path("data/alerts_history.json")
        self.alert_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_history()
        
        # Get config manager
        config_mgr = get_config_manager()
        
        # Configuración de email
        self.email_enabled = config_mgr.get_value('alerts.email_enabled', False)
        self.smtp_server = config_mgr.get_value('alerts.smtp_server', 'smtp.gmail.com')
        self.smtp_port = config_mgr.get_value('alerts.smtp_port', 587)
        self.email_user = config_mgr.get_value('alerts.email_user', '')
        self.email_password = config_mgr.get_value('alerts.email_password', '')
        self.email_to = config_mgr.get_value('alerts.email_to', '')
        
        # Configuración de sonidos
        self.sound_enabled = config_mgr.get_value('alerts.sound_enabled', True)
        
        # Niveles de alerta
        self.alert_levels = {
            'CRITICAL': {'priority': 1, 'sound': True, 'email': True, 'telegram': True},
            'HIGH': {'priority': 2, 'sound': True, 'email': False, 'telegram': True},
            'MEDIUM': {'priority': 3, 'sound': False, 'email': False, 'telegram': True},
            'LOW': {'priority': 4, 'sound': False, 'email': False, 'telegram': False},
        }
    
    def _load_history(self):
        """Carga historial de alertas"""
        if self.alert_file.exists():
            try:
                with open(self.alert_file, 'r', encoding='utf-8') as f:
                    self.alert_history = json.load(f)
            except:
                self.alert_history = []
    
    def _save_history(self):
        """Guarda historial de alertas"""
        # Mantener solo últimas 1000 alertas
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        try:
            with open(self.alert_file, 'w', encoding='utf-8') as f:
                json.dump(self.alert_history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando historial de alertas: {e}")
    
    def _play_sound(self, sound_type: str = 'notification'):
        """Reproduce sonido de alerta"""
        if not self.sound_enabled:
            return
        
        try:
            import winsound
            # Sonidos del sistema Windows
            if sound_type == 'critical':
                winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
            elif sound_type == 'success':
                winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            else:
                winsound.PlaySound("SystemDefault", winsound.SND_ALIAS)
        except Exception as e:
            logger.debug(f"No se pudo reproducir sonido: {e}")
    
    def _send_email(self, subject: str, body: str, html_body: Optional[str] = None):
        """Envía email de alerta"""
        if not self.email_enabled or not self.email_user or not self.email_password:
            return
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = self.email_to
            msg['Subject'] = subject
            
            # Texto plano
            msg.attach(MIMEText(body, 'plain'))
            
            # HTML si está disponible
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Enviar
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email enviado: {subject}")
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
    
    def alert_trade_execution(self, trade_data: Dict, level: str = 'HIGH'):
        """Alerta de ejecución de trade"""
        symbol = trade_data.get('symbol', 'UNKNOWN')
        signal = trade_data.get('signal', 'UNKNOWN')
        price = trade_data.get('price', 0)
        quantity = trade_data.get('quantity', 0)
        mode = trade_data.get('mode', 'PAPER')
        
        alert_config = self.alert_levels.get(level, self.alert_levels['MEDIUM'])
        
        # Mensaje
        emoji = '📈' if signal == 'BUY' else '📉'
        mode_text = '🧪 PAPER' if mode == 'PAPER' else '💰 LIVE'
        
        message = f"""
{emoji} *TRADE EJECUTADO*

*Símbolo:* {symbol}
*Señal:* {signal}
*Precio:* ${price:,.2f}
*Cantidad:* {quantity} acciones
*Capital:* ${price * quantity:,.2f}
*Modo:* {mode_text}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Telegram
        if alert_config['telegram']:
            self.telegram_bot.send_alert(message)
        
        # Email
        if alert_config['email']:
            subject = f"🚨 Trade Ejecutado: {symbol} {signal}"
            body = f"""
Trade Ejecutado

Símbolo: {symbol}
Señal: {signal}
Precio: ${price:,.2f}
Cantidad: {quantity} acciones
Capital: ${price * quantity:,.2f}
Modo: {mode_text}

Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self._send_email(subject, body)
        
        # Sonido
        if alert_config['sound']:
            self._play_sound('critical' if mode == 'LIVE' else 'notification')
        
        # Guardar
        alert = {
            'type': 'TRADE_EXECUTION',
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'data': trade_data,
            'message': message
        }
        self.alert_history.append(alert)
        self._save_history()
    
    def alert_price_alert(self, symbol: str, current_price: float, target_price: float, 
                         direction: str = 'above', level: str = 'MEDIUM'):
        """Alerta de precio alcanzado"""
        alert_config = self.alert_levels.get(level, self.alert_levels['MEDIUM'])
        
        direction_text = "superó" if direction == 'above' else "cayó por debajo de"
        emoji = '📈' if direction == 'above' else '📉'
        
        message = f"""
{emoji} *ALERTA DE PRECIO*

*Símbolo:* {symbol}
*Precio Actual:* ${current_price:,.2f}
*Precio Objetivo:* ${target_price:,.2f}

El precio {direction_text} ${target_price:,.2f}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Telegram
        if alert_config['telegram']:
            self.telegram_bot.send_alert(message)
        
        # Email
        if alert_config['email']:
            subject = f"💰 Alerta de Precio: {symbol}"
            body = f"""
Alerta de Precio

Símbolo: {symbol}
Precio Actual: ${current_price:,.2f}
Precio Objetivo: ${target_price:,.2f}
El precio {direction_text} ${target_price:,.2f}

Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self._send_email(subject, body)
        
        # Sonido
        if alert_config['sound']:
            self._play_sound('notification')
        
        # Guardar
        alert = {
            'type': 'PRICE_ALERT',
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'data': {
                'symbol': symbol,
                'current_price': current_price,
                'target_price': target_price,
                'direction': direction
            },
            'message': message
        }
        self.alert_history.append(alert)
        self._save_history()
    
    def alert_portfolio_change(self, portfolio_data: Dict, level: str = 'MEDIUM'):
        """Alerta de cambio significativo en portafolio"""
        total_value = portfolio_data.get('total_value', 0)
        total_pnl = portfolio_data.get('total_pnl', 0)
        total_pnl_pct = portfolio_data.get('total_pnl_pct', 0)
        
        # Solo alertar si cambio es significativo (>5%)
        if abs(total_pnl_pct) < 5:
            return
        
        alert_config = self.alert_levels.get(level, self.alert_levels['MEDIUM'])
        
        emoji = '📈' if total_pnl > 0 else '📉'
        
        message = f"""
{emoji} *CAMBIO EN PORTAFOLIO*

*Valor Total:* ${total_value:,.2f}
*P&L Total:* ${total_pnl:+,.2f}
*P&L %:* {total_pnl_pct:+.2f}%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Telegram
        if alert_config['telegram']:
            self.telegram_bot.send_alert(message)
        
        # Sonido
        if alert_config['sound']:
            self._play_sound('notification')
        
        # Guardar
        alert = {
            'type': 'PORTFOLIO_CHANGE',
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'data': portfolio_data,
            'message': message
        }
        self.alert_history.append(alert)
        self._save_history()
    
    def alert_system_status(self, status: str, message: str, level: str = 'HIGH'):
        """Alerta de estado del sistema"""
        alert_config = self.alert_levels.get(level, self.alert_levels['MEDIUM'])
        
        emoji = '✅' if status == 'OK' else '⚠️' if status == 'WARNING' else '❌'
        
        alert_message = f"""
{emoji} *ESTADO DEL SISTEMA*

*Estado:* {status}
*Mensaje:* {message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Telegram
        if alert_config['telegram']:
            self.telegram_bot.send_alert(alert_message)
        
        # Email para críticos
        if alert_config['email']:
            subject = f"🚨 Estado del Sistema: {status}"
            body = f"""
Estado del Sistema

Estado: {status}
Mensaje: {message}

Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self._send_email(subject, body)
        
        # Sonido
        if alert_config['sound']:
            self._play_sound('critical' if status != 'OK' else 'success')
        
        # Guardar
        alert = {
            'type': 'SYSTEM_STATUS',
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'data': {'status': status, 'message': message},
            'message': alert_message
        }
        self.alert_history.append(alert)
        self._save_history()
    
    def alert_prediction_accuracy(self, accuracy_data: Dict, level: str = 'MEDIUM'):
        """Alerta si precisión de predicciones baja"""
        accuracy = accuracy_data.get('direction_accuracy', 100)
        
        # Solo alertar si precisión es baja (<50%)
        if accuracy >= 50:
            return
        
        alert_config = self.alert_levels.get('HIGH', self.alert_levels['HIGH'])
        
        message = f"""
⚠️ *PRECISIÓN DE PREDICCIONES BAJA*

*Precisión Actual:* {accuracy:.1f}%
*Umbral Mínimo:* 50%

Se recomienda reentrenar los modelos.

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Telegram
        if alert_config['telegram']:
            self.telegram_bot.send_alert(message)
        
        # Email
        if alert_config['email']:
            subject = "⚠️ Precisión de Predicciones Baja"
            body = f"""
Precisión de Predicciones Baja

Precisión Actual: {accuracy:.1f}%
Umbral Mínimo: 50%

Se recomienda reentrenar los modelos.

Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self._send_email(subject, body)
        
        # Sonido
        if alert_config['sound']:
            self._play_sound('critical')
        
        # Guardar
        alert = {
            'type': 'PREDICTION_ACCURACY',
            'level': 'HIGH',
            'timestamp': datetime.now().isoformat(),
            'data': accuracy_data,
            'message': message
        }
        self.alert_history.append(alert)
        self._save_history()
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Obtiene alertas recientes"""
        return sorted(self.alert_history, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_alerts_by_type(self, alert_type: str, limit: int = 10) -> List[Dict]:
        """Obtiene alertas por tipo"""
        filtered = [a for a in self.alert_history if a['type'] == alert_type]
        return sorted(filtered, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_alerts_by_level(self, level: str, limit: int = 10) -> List[Dict]:
        """Obtiene alertas por nivel"""
        filtered = [a for a in self.alert_history if a['level'] == level]
        return sorted(filtered, key=lambda x: x['timestamp'], reverse=True)[:limit]


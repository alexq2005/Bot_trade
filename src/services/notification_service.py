"""
Sistema de Notificaciones Mejorado
Centraliza todas las notificaciones con priorización y múltiples canales
"""
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Literal
from enum import Enum
from dataclasses import dataclass

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.core.logger import get_logger
from src.services.telegram_bot import TelegramAlertBot

logger = get_logger("notification_service")


class NotificationPriority(Enum):
    """Prioridades de notificación"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Canales de notificación"""
    CONSOLE = "console"
    TELEGRAM = "telegram"
    FILE = "file"
    ALL = "all"


@dataclass
class Notification:
    """Estructura de una notificación"""
    title: str
    message: str
    priority: NotificationPriority
    channel: NotificationChannel
    timestamp: datetime
    metadata: Optional[Dict] = None
    category: Optional[str] = None


class NotificationService:
    """
    Servicio centralizado de notificaciones
    """
    
    def __init__(self, enable_telegram: bool = True):
        """
        Args:
            enable_telegram: Si habilitar notificaciones por Telegram
        """
        self.enable_telegram = enable_telegram
        self.telegram_bot = TelegramAlertBot() if enable_telegram else None
        self.notification_history: List[Notification] = []
        self.max_history = 1000
        self.logger = logger
        
        # Configuración de prioridades
        self.priority_config = {
            NotificationPriority.LOW: {"sound": False, "repeat": False},
            NotificationPriority.MEDIUM: {"sound": False, "repeat": False},
            NotificationPriority.HIGH: {"sound": True, "repeat": False},
            NotificationPriority.CRITICAL: {"sound": True, "repeat": True},
        }
    
    def notify(
        self,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        channel: NotificationChannel = NotificationChannel.ALL,
        category: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Envía una notificación
        
        Args:
            title: Título de la notificación
            message: Mensaje
            priority: Prioridad
            channel: Canal(es) a usar
            category: Categoría (trade, error, alert, etc.)
            metadata: Metadatos adicionales
        """
        notification = Notification(
            title=title,
            message=message,
            priority=priority,
            channel=channel,
            timestamp=datetime.now(),
            category=category,
            metadata=metadata or {}
        )
        
        # Agregar al historial
        self.notification_history.append(notification)
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[-self.max_history:]
        
        # Enviar según canal
        if channel == NotificationChannel.ALL or channel == NotificationChannel.CONSOLE:
            self._send_console(notification)
        
        if (channel == NotificationChannel.ALL or channel == NotificationChannel.TELEGRAM) and self.enable_telegram:
            self._send_telegram(notification)
        
        if channel == NotificationChannel.FILE:
            self._send_file(notification)
    
    def _send_console(self, notification: Notification):
        """Envía notificación a consola"""
        priority_icons = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "📢",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.CRITICAL: "🚨",
        }
        
        icon = priority_icons.get(notification.priority, "📢")
        print(f"\n{icon} {notification.title}")
        print(f"   {notification.message}")
        if notification.metadata:
            for key, value in notification.metadata.items():
                print(f"   {key}: {value}")
    
    def _send_telegram(self, notification: Notification):
        """Envía notificación por Telegram"""
        if not self.telegram_bot:
            return
        
        try:
            # Formatear mensaje según prioridad
            priority_icons = {
                NotificationPriority.LOW: "ℹ️",
                NotificationPriority.MEDIUM: "📢",
                NotificationPriority.HIGH: "⚠️",
                NotificationPriority.CRITICAL: "🚨",
            }
            
            icon = priority_icons.get(notification.priority, "📢")
            formatted_message = f"{icon} *{notification.title}*\n\n{notification.message}"
            
            if notification.metadata:
                formatted_message += "\n\n*Detalles:*"
                for key, value in notification.metadata.items():
                    formatted_message += f"\n• {key}: {value}"
            
            self.telegram_bot.send_alert(formatted_message)
        except Exception as e:
            self.logger.error(f"Error enviando notificación por Telegram: {e}")
    
    def _send_file(self, notification: Notification):
        """Guarda notificación en archivo"""
        from pathlib import Path
        
        log_file = Path("logs") / "notifications.log"
        log_file.parent.mkdir(exist_ok=True)
        
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{notification.timestamp.isoformat()}] [{notification.priority.value}] {notification.title}: {notification.message}\n")
        except Exception as e:
            self.logger.error(f"Error escribiendo notificación a archivo: {e}")
    
    # Métodos de conveniencia
    def notify_trade(
        self,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        order_id: Optional[str] = None
    ):
        """Notifica una operación de trading"""
        title = f"Trade {action.upper()}: {symbol}"
        message = f"{quantity} acciones de {symbol} a ${price:.2f}"
        
        metadata = {
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "price": price,
        }
        
        if order_id:
            metadata["order_id"] = order_id
        
        self.notify(
            title=title,
            message=message,
            priority=NotificationPriority.HIGH,
            category="trade",
            metadata=metadata
        )
    
    def notify_error(
        self,
        error: Exception,
        context: Optional[str] = None
    ):
        """Notifica un error"""
        title = f"Error: {type(error).__name__}"
        message = str(error)
        
        if context:
            message = f"{context}: {message}"
        
        metadata = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
        
        self.notify(
            title=title,
            message=message,
            priority=NotificationPriority.CRITICAL,
            category="error",
            metadata=metadata
        )
    
    def notify_alert(
        self,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM
    ):
        """Notifica una alerta genérica"""
        self.notify(
            title="Alerta",
            message=message,
            priority=priority,
            category="alert"
        )
    
    def notify_prediction(
        self,
        symbol: str,
        signal: str,
        confidence: float,
        predicted_price: float,
        current_price: float
    ):
        """Notifica una predicción"""
        change_pct = ((predicted_price - current_price) / current_price) * 100
        
        title = f"Predicción: {symbol} -> {signal}"
        message = f"Confianza: {confidence:.1%}, Cambio esperado: {change_pct:+.2f}%"
        
        metadata = {
            "symbol": symbol,
            "signal": signal,
            "confidence": confidence,
            "predicted_price": predicted_price,
            "current_price": current_price,
            "change_pct": change_pct,
        }
        
        priority = NotificationPriority.HIGH if confidence > 0.7 else NotificationPriority.MEDIUM
        
        self.notify(
            title=title,
            message=message,
            priority=priority,
            category="prediction",
            metadata=metadata
        )
    
    def get_history(
        self,
        category: Optional[str] = None,
        priority: Optional[NotificationPriority] = None,
        limit: int = 50
    ) -> List[Notification]:
        """
        Obtiene el historial de notificaciones
        
        Args:
            category: Filtrar por categoría
            priority: Filtrar por prioridad
            limit: Límite de resultados
        
        Returns:
            Lista de notificaciones
        """
        filtered = self.notification_history
        
        if category:
            filtered = [n for n in filtered if n.category == category]
        
        if priority:
            filtered = [n for n in filtered if n.priority == priority]
        
        return filtered[-limit:]
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas de notificaciones"""
        total = len(self.notification_history)
        
        by_priority = {}
        for priority in NotificationPriority:
            by_priority[priority.value] = sum(
                1 for n in self.notification_history if n.priority == priority
            )
        
        by_category = {}
        for notification in self.notification_history:
            cat = notification.category or "uncategorized"
            by_category[cat] = by_category.get(cat, 0) + 1
        
        return {
            "total": total,
            "by_priority": by_priority,
            "by_category": by_category,
        }


# Instancia global
_notification_service = None


def get_notification_service(enable_telegram: bool = True) -> NotificationService:
    """Obtiene la instancia global de NotificationService"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService(enable_telegram=enable_telegram)
    return _notification_service


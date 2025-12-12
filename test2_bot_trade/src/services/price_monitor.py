"""
Monitor de Precios en Tiempo Real
Monitorea precios y dispara alertas cuando se alcanzan objetivos
"""
import time
from datetime import datetime
from typing import Dict, List, Optional
from threading import Thread

from src.core.logger import get_logger
from src.connectors.iol_client import IOLClient
from src.services.realtime_alerts import RealtimeAlertSystem

logger = get_logger("price_monitor")


class PriceMonitor:
    """Monitor de precios con alertas automáticas"""
    
    def __init__(self):
        self.iol_client = IOLClient()
        self.alert_system = RealtimeAlertSystem()
        self.price_alerts = []  # Lista de alertas de precio configuradas
        self.monitoring = False
        self.monitor_thread = None
    
    def add_price_alert(self, symbol: str, target_price: float, direction: str = 'above',
                       alert_level: str = 'MEDIUM'):
        """
        Agrega una alerta de precio
        
        Args:
            symbol: Símbolo a monitorear
            target_price: Precio objetivo
            direction: 'above' o 'below'
            alert_level: Nivel de alerta
        """
        alert = {
            'symbol': symbol,
            'target_price': target_price,
            'direction': direction,
            'level': alert_level,
            'triggered': False,
            'created_at': datetime.now().isoformat()
        }
        
        self.price_alerts.append(alert)
        try:
            logger.info(f"Alerta de precio agregada: {symbol} {direction} ${target_price}")
        except (ValueError, IOError):
            pass  # Ignorar errores de logging si el archivo está cerrado
        
        return alert
    
    def remove_price_alert(self, symbol: str, target_price: Optional[float] = None):
        """Elimina alerta(s) de precio"""
        if target_price:
            self.price_alerts = [
                a for a in self.price_alerts
                if not (a['symbol'] == symbol and a['target_price'] == target_price)
            ]
        else:
            self.price_alerts = [a for a in self.price_alerts if a['symbol'] != symbol]
        
        try:
            logger.info(f"Alerta(s) de precio eliminada(s) para {symbol}")
        except (ValueError, IOError):
            pass  # Ignorar errores de logging si el archivo está cerrado
    
    def check_price_alerts(self):
        """Verifica todas las alertas de precio"""
        for alert in self.price_alerts:
            if alert['triggered']:
                continue
            
            try:
                quote = self.iol_client.get_quote(alert['symbol'])
                
                if 'error' in quote:
                    continue
                
                current_price = quote.get('ultimoPrecio', 0)
                
                if not current_price:
                    continue
                
                # Verificar si se alcanzó el precio objetivo
                triggered = False
                if alert['direction'] == 'above' and current_price >= alert['target_price']:
                    triggered = True
                elif alert['direction'] == 'below' and current_price <= alert['target_price']:
                    triggered = True
                
                if triggered:
                    alert['triggered'] = True
                    alert['triggered_at'] = datetime.now().isoformat()
                    alert['triggered_price'] = current_price
                    
                    # Enviar alerta
                    self.alert_system.alert_price_alert(
                        symbol=alert['symbol'],
                        current_price=current_price,
                        target_price=alert['target_price'],
                        direction=alert['direction'],
                        level=alert['level']
                    )
                    
                    try:
                        logger.info(f"Alerta de precio activada: {alert['symbol']} ${current_price}")
                    except (ValueError, IOError):
                        pass  # Ignorar errores de logging si el archivo está cerrado
            
            except Exception as e:
                try:
                    logger.error(f"Error verificando alerta de precio {alert['symbol']}: {e}")
                except (ValueError, IOError):
                    pass  # Ignorar errores de logging si el archivo está cerrado
    
    def start_monitoring(self, interval: int = 60):
        """Inicia monitoreo continuo de precios"""
        if self.monitoring:
            try:
                logger.warning("Monitor ya está corriendo")
            except (ValueError, IOError):
                pass  # Ignorar errores de logging si el archivo está cerrado
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    self.check_price_alerts()
                    time.sleep(interval)
                except Exception as e:
                    try:
                        logger.error(f"Error en loop de monitoreo: {e}")
                    except (ValueError, IOError):
                        pass  # Ignorar errores de logging si el archivo está cerrado
                    time.sleep(interval)
        
        self.monitor_thread = Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        try:
            logger.info(f"Monitor de precios iniciado (intervalo: {interval}s)")
        except (ValueError, IOError):
            pass  # Ignorar errores de logging si el archivo está cerrado
    
    def stop_monitoring(self):
        """Detiene monitoreo de precios"""
        self.monitoring = False
        try:
            logger.info("Monitor de precios detenido")
        except (ValueError, IOError):
            pass  # Ignorar errores de logging si el archivo está cerrado
    
    def get_active_alerts(self) -> List[Dict]:
        """Obtiene alertas activas (no disparadas)"""
        return [a for a in self.price_alerts if not a['triggered']]
    
    def get_triggered_alerts(self) -> List[Dict]:
        """Obtiene alertas que ya fueron disparadas"""
        return [a for a in self.price_alerts if a['triggered']]


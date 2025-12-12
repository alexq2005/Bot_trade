"""
Servicio de Alertas Macroeconómicas
Monitorea cambios en indicadores macro y envía alertas
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import json
from pathlib import Path

from src.services.macroeconomic_data_service import MacroeconomicDataService
from src.core.logger import get_logger

logger = get_logger("macroeconomic_alert_service")


class MacroeconomicAlertService:
    """
    Servicio para monitorear y alertar sobre cambios en indicadores macroeconómicos.
    """
    
    def __init__(self, alert_system=None):
        self.macroeconomic_service = MacroeconomicDataService()
        self.alert_system = alert_system
        self.history_file = Path("data/macroeconomic_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Umbrales para alertas
        self.thresholds = {
            'usd_blue_change_pct': 5.0,  # Cambio de 5% en dólar blue
            'usd_official_change_pct': 2.0,  # Cambio de 2% en dólar oficial
            'inflation_change_pct': 10.0,  # Cambio de 10% en inflación
            'spread_change_pct': 10.0  # Cambio de 10% en spread USD
        }
    
    def _load_history(self) -> Dict:
        """Carga historial de indicadores macro"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_history(self, history: Dict):
        """Guarda historial de indicadores macro"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando historial macro: {e}")
    
    def check_and_alert(self) -> list:
        """
        Verifica cambios en indicadores macro y envía alertas si es necesario.
        
        Returns:
            Lista de alertas generadas
        """
        alerts = []
        
        try:
            # Obtener indicadores actuales
            current_indicators = self.macroeconomic_service.get_economic_indicators()
            
            # Cargar historial
            history = self._load_history()
            last_check = history.get('last_check')
            last_indicators = history.get('indicators', {})
            
            # Verificar cambios
            if last_indicators:
                # Cambio en dólar blue
                last_blue = last_indicators.get('usd_blue')
                current_blue = current_indicators.get('usd_blue')
                
                if last_blue and current_blue:
                    change_pct = ((current_blue - last_blue) / last_blue) * 100
                    if abs(change_pct) >= self.thresholds['usd_blue_change_pct']:
                        alert = {
                            'type': 'WARNING' if abs(change_pct) > 10 else 'INFO',
                            'indicator': 'USD Blue',
                            'message': f"Dólar blue {'subió' if change_pct > 0 else 'bajó'} {abs(change_pct):.2f}%",
                            'previous': last_blue,
                            'current': current_blue,
                            'change_pct': change_pct,
                            'timestamp': datetime.now().isoformat()
                        }
                        alerts.append(alert)
                        
                        if self.alert_system:
                            self.alert_system.send_alert(
                                alert['type'],
                                'MACRO',
                                alert['message'],
                                alert
                            )
                
                # Cambio en dólar oficial
                last_official = last_indicators.get('usd_official')
                current_official = current_indicators.get('usd_official')
                
                if last_official and current_official:
                    change_pct = ((current_official - last_official) / last_official) * 100
                    if abs(change_pct) >= self.thresholds['usd_official_change_pct']:
                        alert = {
                            'type': 'WARNING' if abs(change_pct) > 5 else 'INFO',
                            'indicator': 'USD Oficial',
                            'message': f"Dólar oficial {'subió' if change_pct > 0 else 'bajó'} {abs(change_pct):.2f}%",
                            'previous': last_official,
                            'current': current_official,
                            'change_pct': change_pct,
                            'timestamp': datetime.now().isoformat()
                        }
                        alerts.append(alert)
                        
                        if self.alert_system:
                            self.alert_system.send_alert(
                                alert['type'],
                                'MACRO',
                                alert['message'],
                                alert
                            )
                
                # Cambio en inflación
                last_inflation = last_indicators.get('inflation_rate')
                current_inflation = current_indicators.get('inflation_rate')
                
                if last_inflation and current_inflation:
                    change_pct = ((current_inflation - last_inflation) / last_inflation) * 100
                    if abs(change_pct) >= self.thresholds['inflation_change_pct']:
                        alert = {
                            'type': 'WARNING',
                            'indicator': 'Inflación',
                            'message': f"Inflación {'subió' if change_pct > 0 else 'bajó'} {abs(change_pct):.2f}%",
                            'previous': last_inflation,
                            'current': current_inflation,
                            'change_pct': change_pct,
                            'timestamp': datetime.now().isoformat()
                        }
                        alerts.append(alert)
                        
                        if self.alert_system:
                            self.alert_system.send_alert(
                                'WARNING',
                                'MACRO',
                                alert['message'],
                                alert
                            )
                
                # Cambio en spread USD
                if last_blue and last_official and current_blue and current_official:
                    last_spread = last_blue - last_official
                    current_spread = current_blue - current_official
                    last_spread_pct = (last_spread / last_official) * 100 if last_official > 0 else 0
                    current_spread_pct = (current_spread / current_official) * 100 if current_official > 0 else 0
                    
                    spread_change = current_spread_pct - last_spread_pct
                    if abs(spread_change) >= self.thresholds['spread_change_pct']:
                        alert = {
                            'type': 'INFO',
                            'indicator': 'Spread USD',
                            'message': f"Spread USD {'aumentó' if spread_change > 0 else 'disminuyó'} {abs(spread_change):.2f}%",
                            'previous': last_spread_pct,
                            'current': current_spread_pct,
                            'change_pct': spread_change,
                            'timestamp': datetime.now().isoformat()
                        }
                        alerts.append(alert)
                        
                        if self.alert_system:
                            self.alert_system.send_alert(
                                'INFO',
                                'MACRO',
                                alert['message'],
                                alert
                            )
            
            # Guardar indicadores actuales
            history['last_check'] = datetime.now().isoformat()
            history['indicators'] = current_indicators
            self._save_history(history)
            
            if alerts:
                logger.info(f"✅ Generadas {len(alerts)} alertas macroeconómicas")
            else:
                logger.debug("No hay cambios significativos en indicadores macro")
            
            return alerts
        
        except Exception as e:
            logger.error(f"Error verificando alertas macroeconómicas: {e}")
            return []


if __name__ == "__main__":
    # Test del servicio
    from src.services.alert_system import AlertSystem
    
    alert_system = AlertSystem()
    service = MacroeconomicAlertService(alert_system=alert_system)
    
    print("Probando Servicio de Alertas Macroeconómicas...")
    
    # Primera verificación (no debería generar alertas)
    print("\n1. Primera verificación...")
    alerts = service.check_and_alert()
    print(f"Alertas generadas: {len(alerts)}")
    
    # Segunda verificación (después de un tiempo, debería comparar)
    print("\n2. Segunda verificación (después de guardar historial)...")
    alerts = service.check_and_alert()
    print(f"Alertas generadas: {len(alerts)}")
    for alert in alerts:
        print(f"   - {alert['indicator']}: {alert['message']}")


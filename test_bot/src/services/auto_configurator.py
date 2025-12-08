"""
Sistema de Autoconfiguración del Bot
Ajusta automáticamente parámetros basándose en rendimiento histórico
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from src.core.logger import get_logger
from src.services.adaptive_risk_manager import AdaptiveRiskManager

logger = get_logger("auto_configurator")


class AutoConfigurator:
    """
    Sistema que ajusta automáticamente los parámetros del bot
    basándose en rendimiento histórico y condiciones de mercado.
    """
    
    def __init__(self, config_file: str = "professional_config.json"):
        self.config_file = config_file
        self.config_history_file = "data/auto_config_history.json"
        self._ensure_data_dir()
        self.load_config()
    
    def _ensure_data_dir(self):
        """Asegura que el directorio de datos existe"""
        Path(self.config_history_file).parent.mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict:
        """Carga la configuración actual"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                return self.config
            except Exception as e:
                logger.error(f"Error cargando configuración: {e}")
                self.config = self._get_default_config()
                return self.config
        else:
            self.config = self._get_default_config()
            self.save_config()
            return self.config
    
    def _get_default_config(self) -> Dict:
        """Retorna configuración por defecto"""
        return {
            "risk_per_trade": 0.03,
            "max_position_size_pct": 18,
            "max_daily_trades": 10,
            "max_daily_loss_pct": 5,
            "stop_loss_atr_multiplier": 2.0,
            "take_profit_atr_multiplier": 3.0,
            "min_confidence": "MEDIUM",
            "buy_threshold": 25,
            "sell_threshold": -25,
            "analysis_interval_minutes": 60,
            "enable_sentiment_analysis": True,
            "enable_news_fetching": True,
            "auto_retrain_on_low_accuracy": True,
            "min_accuracy_for_retrain": 55
        }
    
    def save_config(self):
        """Guarda la configuración actual"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"✅ Configuración guardada en {self.config_file}")
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
    
    def analyze_performance(self, risk_manager: AdaptiveRiskManager, days: int = 30) -> Dict:
        """Analiza el rendimiento reciente"""
        metrics = risk_manager.get_performance_metrics(days=days)
        
        # Calcular métricas adicionales
        drawdown = risk_manager._calculate_drawdown()
        consecutive_losses = risk_manager.consecutive_losses
        daily_trades_avg = risk_manager.daily_trades_count / max(days, 1)
        
        return {
            **metrics,
            "drawdown": drawdown,
            "consecutive_losses": consecutive_losses,
            "daily_trades_avg": daily_trades_avg,
            "current_capital": risk_manager.current_capital,
            "initial_capital": risk_manager.initial_capital,
            "return_pct": ((risk_manager.current_capital - risk_manager.initial_capital) / risk_manager.initial_capital) * 100
        }
    
    def auto_configure(self, risk_manager: AdaptiveRiskManager, trades_data: Optional[List] = None) -> Dict:
        """
        Realiza autoconfiguración basada en rendimiento.
        
        Returns:
            Dict con los cambios realizados
        """
        # Verificar si la autoconfiguración está habilitada
        if not self.config.get('auto_configuration_enabled', True):
            logger.info("ℹ️  Autoconfiguración deshabilitada (modo manual)")
            return {
                "success": False,
                "changes": [],
                "message": "Autoconfiguración deshabilitada - Modo manual activo"
            }
        
        logger.info("🔄 Iniciando autoconfiguración...")
        
        # Analizar rendimiento
        performance = self.analyze_performance(risk_manager, days=30)
        
        changes = []
        old_config = self.config.copy()
        
        # 1. Ajustar riesgo por operación basado en win rate
        win_rate = performance.get('win_rate', 0.5)
        current_risk = self.config.get('risk_per_trade', 0.03)
        
        if win_rate < 0.4:  # Win rate bajo - reducir riesgo
            new_risk = max(0.01, current_risk * 0.8)  # Reducir 20%
            if abs(new_risk - current_risk) > 0.005:  # Solo cambiar si diferencia significativa
                self.config['risk_per_trade'] = round(new_risk, 3)
                changes.append(f"Riesgo por operación: {current_risk*100:.1f}% → {new_risk*100:.1f}% (win rate bajo: {win_rate*100:.1f}%)")
        elif win_rate > 0.6:  # Win rate alto - aumentar riesgo moderadamente
            new_risk = min(0.05, current_risk * 1.1)  # Aumentar 10%
            if abs(new_risk - current_risk) > 0.005:
                self.config['risk_per_trade'] = round(new_risk, 3)
                changes.append(f"Riesgo por operación: {current_risk*100:.1f}% → {new_risk*100:.1f}% (win rate alto: {win_rate*100:.1f}%)")
        
        # 2. Ajustar tamaño máximo de posición basado en drawdown
        drawdown = performance.get('drawdown', 0)
        current_position = self.config.get('max_position_size_pct', 18)
        
        if drawdown > 0.10:  # Drawdown > 10% - reducir posición
            new_position = max(10, current_position * 0.8)  # Reducir 20%
            if abs(new_position - current_position) > 2:
                self.config['max_position_size_pct'] = int(new_position)
                changes.append(f"Tamaño máximo posición: {current_position}% → {int(new_position)}% (drawdown: {drawdown*100:.1f}%)")
        elif drawdown < 0.02 and win_rate > 0.55:  # Drawdown bajo y buen win rate
            new_position = min(25, current_position * 1.1)  # Aumentar 10%
            if abs(new_position - current_position) > 2:
                self.config['max_position_size_pct'] = int(new_position)
                changes.append(f"Tamaño máximo posición: {current_position}% → {int(new_position)}% (rendimiento positivo)")
        
        # 3. Ajustar umbrales de compra/venta basado en win rate
        current_buy_threshold = self.config.get('buy_threshold', 25)
        current_sell_threshold = self.config.get('sell_threshold', -25)
        
        if win_rate < 0.45:  # Win rate bajo - ser más conservador
            new_buy = min(35, current_buy_threshold + 5)
            new_sell = max(-35, current_sell_threshold - 5)
            if new_buy != current_buy_threshold or new_sell != current_sell_threshold:
                self.config['buy_threshold'] = new_buy
                self.config['sell_threshold'] = new_sell
                changes.append(f"Umbrales: Compra {current_buy_threshold}→{new_buy}, Venta {current_sell_threshold}→{new_sell} (más conservador)")
        elif win_rate > 0.65:  # Win rate alto - ser más agresivo
            new_buy = max(15, current_buy_threshold - 5)
            new_sell = min(-15, current_sell_threshold + 5)
            if new_buy != current_buy_threshold or new_sell != current_sell_threshold:
                self.config['buy_threshold'] = new_buy
                self.config['sell_threshold'] = new_sell
                changes.append(f"Umbrales: Compra {current_buy_threshold}→{new_buy}, Venta {current_sell_threshold}→{new_sell} (más agresivo)")
        
        # 4. Ajustar stop loss/take profit basado en profit factor
        profit_factor = performance.get('profit_factor', 1.0)
        current_stop = self.config.get('stop_loss_atr_multiplier', 2.0)
        current_tp = self.config.get('take_profit_atr_multiplier', 3.0)
        
        if profit_factor < 1.0:  # Pérdidas mayores que ganancias
            # Ajustar stop loss más cerca y take profit más lejos
            new_stop = max(1.5, current_stop * 0.9)
            new_tp = min(4.0, current_tp * 1.1)
            if abs(new_stop - current_stop) > 0.1 or abs(new_tp - current_tp) > 0.1:
                self.config['stop_loss_atr_multiplier'] = round(new_stop, 1)
                self.config['take_profit_atr_multiplier'] = round(new_tp, 1)
                changes.append(f"Stop Loss: {current_stop}x→{new_stop}x, Take Profit: {current_tp}x→{new_tp}x (mejorar ratio)")
        
        # 5. Ajustar intervalo de análisis basado en volatilidad y trades
        daily_trades_avg = performance.get('daily_trades_avg', 0)
        current_interval = self.config.get('analysis_interval_minutes', 60)
        
        if daily_trades_avg > 8:  # Muchos trades - reducir frecuencia
            new_interval = min(120, current_interval * 1.2)
            if abs(new_interval - current_interval) > 10:
                self.config['analysis_interval_minutes'] = int(new_interval)
                changes.append(f"Intervalo análisis: {current_interval}min → {int(new_interval)}min (muchos trades)")
        elif daily_trades_avg < 2 and win_rate > 0.5:  # Pocos trades y buen rendimiento - aumentar frecuencia
            new_interval = max(30, current_interval * 0.9)
            if abs(new_interval - current_interval) > 10:
                self.config['analysis_interval_minutes'] = int(new_interval)
                changes.append(f"Intervalo análisis: {current_interval}min → {int(new_interval)}min (optimizar oportunidades)")
        
        # 6. Ajustar límite de trades diarios
        current_max_trades = self.config.get('max_daily_trades', 10)
        if daily_trades_avg > current_max_trades * 0.9:  # Casi alcanzando el límite
            new_max = min(20, int(current_max_trades * 1.2))
            if new_max != current_max_trades:
                self.config['max_daily_trades'] = new_max
                changes.append(f"Máximo trades/día: {current_max_trades} → {new_max} (alta actividad)")
        elif daily_trades_avg < current_max_trades * 0.3 and win_rate < 0.45:  # Pocos trades y mal rendimiento
            new_max = max(5, int(current_max_trades * 0.8))
            if new_max != current_max_trades:
                self.config['max_daily_trades'] = new_max
                changes.append(f"Máximo trades/día: {current_max_trades} → {new_max} (reducir actividad)")
        
        # Guardar cambios si hay alguno
        if changes:
            self.save_config()
            self._log_configuration_change(old_config, self.config, changes, performance)
            
            logger.info(f"✅ Autoconfiguración completada: {len(changes)} cambios realizados")
            return {
                "success": True,
                "changes": changes,
                "performance": performance,
                "old_config": old_config,
                "new_config": self.config.copy()
            }
        else:
            logger.info("ℹ️  No se requieren cambios en la configuración")
            return {
                "success": False,
                "changes": [],
                "performance": performance,
                "message": "Configuración óptima, no se requieren cambios"
            }
    
    def _log_configuration_change(self, old_config: Dict, new_config: Dict, changes: List[str], performance: Dict):
        """Registra el cambio de configuración en el historial"""
        try:
            history = []
            if os.path.exists(self.config_history_file):
                with open(self.config_history_file, 'r') as f:
                    history = json.load(f)
            
            history.append({
                "timestamp": datetime.now().isoformat(),
                "old_config": old_config,
                "new_config": new_config,
                "changes": changes,
                "performance": performance
            })
            
            # Mantener solo últimos 100 cambios
            history = history[-100:]
            
            with open(self.config_history_file, 'w') as f:
                json.dump(history, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando historial de configuración: {e}")
    
    def get_configuration_summary(self) -> Dict:
        """Retorna un resumen de la configuración actual"""
        return {
            "current_config": self.config.copy(),
            "last_change": self._get_last_change_date(),
            "total_changes": self._get_total_changes()
        }
    
    def _get_last_change_date(self) -> Optional[str]:
        """Obtiene la fecha del último cambio"""
        if os.path.exists(self.config_history_file):
            try:
                with open(self.config_history_file, 'r') as f:
                    history = json.load(f)
                    if history:
                        return history[-1].get('timestamp')
            except:
                pass
        return None
    
    def _get_total_changes(self) -> int:
        """Obtiene el total de cambios realizados"""
        if os.path.exists(self.config_history_file):
            try:
                with open(self.config_history_file, 'r') as f:
                    history = json.load(f)
                    return len(history)
            except:
                pass
        return 0


if __name__ == "__main__":
    # Test del autoconfigurador
    configurator = AutoConfigurator()
    risk_manager = AdaptiveRiskManager(initial_capital=10000.0)
    
    # Simular algunas métricas
    risk_manager.current_capital = 9500.0  # Drawdown del 5%
    risk_manager.daily_trades_count = 8
    
    # Simular algunos trades
    risk_manager.record_trade("AAPL", 150.0, 155.0, 10, "BUY", 50.0)
    risk_manager.record_trade("MSFT", 300.0, 295.0, 5, "BUY", -25.0)
    risk_manager.record_trade("GOOGL", 2500.0, 2550.0, 2, "BUY", 100.0)
    
    result = configurator.auto_configure(risk_manager)
    
    print("\n" + "="*70)
    print("RESULTADO DE AUTOCONFIGURACIÓN")
    print("="*70)
    print(f"Cambios realizados: {len(result.get('changes', []))}")
    for change in result.get('changes', []):
        print(f"  • {change}")
    print("\nConfiguración actual:")
    for key, value in configurator.config.items():
        print(f"  {key}: {value}")


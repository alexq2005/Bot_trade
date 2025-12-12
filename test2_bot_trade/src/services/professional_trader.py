"""
Professional Trader Module
Implementa estrategias de trading profesional con filtros avanzados
"""

import json
import os
from datetime import datetime, time, timedelta
from typing import Dict, Optional, Tuple

import numpy as np


class ProfessionalTrader:
    """
    Implementa lógica de trading profesional con filtros y gestión avanzada.
    """

    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.last_trade_time = None
        self.last_trade_result = None

    def _load_config(self) -> Dict:
        """Carga configuración profesional"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except:
                pass

        # Cargar template por defecto
        template_file = "professional_config_template.json"
        if os.path.exists(template_file):
            with open(template_file, "r") as f:
                config = json.load(f)
            # Guardar como config principal
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            return config

        return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Configuración por defecto si no existe archivo"""
        return {
            "risk_management": {
                "max_position_size_pct": 30,
                "max_daily_trades": 10,
                "max_daily_loss_pct": 5,
                "stop_loss_atr_multiplier": 2.0,
                "take_profit_atr_multiplier": 3.0,
            },
            "entry_filters": {
                "min_rsi": 30,
                "max_rsi": 70,
                "min_volume_ratio": 1.2,
                "require_trend_confirmation": True,
            },
            "time_management": {
                "trading_hours_start": "11:00",
                "trading_hours_end": "17:00",
                "trade_on_friday": False,
            },
        }

    def check_entry_filters(self, technical_data: Dict) -> Tuple[bool, str]:
        """
        Verifica filtros de entrada profesionales.

        Args:
            technical_data: Datos técnicos del activo

        Returns:
            (puede_entrar, razón)
        """
        filters = self.config.get("entry_filters", {})

        # 1. Filtro RSI
        rsi = technical_data.get("momentum", {}).get("rsi")
        if rsi:
            min_rsi = filters.get("min_rsi", 30)
            max_rsi = filters.get("max_rsi", 70)

            if rsi < min_rsi:
                return False, f"RSI muy bajo ({rsi:.1f} < {min_rsi}) - Sobreventa extrema"
            if rsi > max_rsi:
                return False, f"RSI muy alto ({rsi:.1f} > {max_rsi}) - Sobrecompra extrema"

        # 2. Filtro de Volumen
        volume_ratio = technical_data.get("volume", {}).get("volume_ratio", 1.0)
        min_volume = filters.get("min_volume_ratio", 1.0)
        if volume_ratio < min_volume:
            return False, f"Volumen insuficiente ({volume_ratio:.2f}x < {min_volume}x)"

        # 3. Confirmación de Tendencia
        if filters.get("require_trend_confirmation", True):
            trend = technical_data.get("trend", {})
            sma_20 = trend.get("sma_20")
            sma_50 = trend.get("sma_50")
            current_price = trend.get("current_price")

            if sma_20 and sma_50 and current_price:
                # Tendencia alcista: precio > SMA20 > SMA50
                if current_price < sma_20:
                    return False, "Precio por debajo de SMA20 - Sin confirmación alcista"
                if sma_20 < sma_50:
                    return False, "SMA20 < SMA50 - Tendencia bajista"

        # 4. Filtro de Volatilidad (ATR)
        atr = technical_data.get("volatility", {}).get("atr")
        current_price = technical_data.get("trend", {}).get("current_price", 1)
        if atr and current_price:
            atr_pct = (atr / current_price) * 100
            min_atr = filters.get("min_atr_pct", 0.5)
            max_atr = filters.get("max_atr_pct", 5.0)

            if atr_pct < min_atr:
                return False, f"Volatilidad muy baja (ATR {atr_pct:.2f}% < {min_atr}%)"
            if atr_pct > max_atr:
                return False, f"Volatilidad muy alta (ATR {atr_pct:.2f}% > {max_atr}%)"

        return True, "Todos los filtros pasados"

    def check_time_filters(self) -> Tuple[bool, str]:
        """
        Verifica filtros de tiempo.

        Returns:
            (puede_operar, razón)
        """
        time_config = self.config.get("time_management", {})
        now = datetime.now()

        # 1. Día de la semana
        weekday = now.strftime("%A").lower()
        if not time_config.get(f"trade_on_{weekday}", True):
            return False, f"No se opera los {weekday}s"

        # 2. Horario de operación (IOL: 11:00 - 17:00)
        start_time = time_config.get("trading_hours_start", "11:00")
        end_time = time_config.get("trading_hours_end", "17:00")

        start_hour, start_min = map(int, start_time.split(":"))
        end_hour, end_min = map(int, end_time.split(":"))

        trading_start = time(start_hour, start_min)
        trading_end = time(end_hour, end_min)
        current_time = now.time()

        if current_time < trading_start:
            return False, f"Antes del horario de trading ({start_time})"
        if current_time > trading_end:
            return False, f"Después del horario de trading ({end_time})"

        # 3. Evitar primeros/últimos minutos
        avoid_first = time_config.get("avoid_first_minutes", 30)
        avoid_last = time_config.get("avoid_last_minutes", 30)

        minutes_since_open = (current_time.hour - trading_start.hour) * 60 + (
            current_time.minute - trading_start.minute
        )
        minutes_to_close = (trading_end.hour - current_time.hour) * 60 + (
            trading_end.minute - current_time.minute
        )

        if minutes_since_open < avoid_first:
            return False, f"Primeros {avoid_first} minutos - Alta volatilidad"
        if minutes_to_close < avoid_last:
            return False, f"Últimos {avoid_last} minutos - Cierre de mercado"

        # 4. Cooldown después de operación
        if self.last_trade_time:
            if self.last_trade_result == "loss":
                cooldown = time_config.get("cooldown_after_loss_minutes", 60)
            else:
                cooldown = time_config.get("cooldown_after_win_minutes", 15)

            time_since_last = (now - self.last_trade_time).total_seconds() / 60
            if time_since_last < cooldown:
                return False, f"Cooldown activo ({int(cooldown - time_since_last)} min restantes)"

        return True, "Horario válido para operar"

    def calculate_position_size_with_conditions(
        self, base_size: int, market_condition: str = "neutral"
    ) -> int:
        """
        Ajusta tamaño de posición según condiciones de mercado.

        Args:
            base_size: Tamaño base calculado por risk manager
            market_condition: 'bull', 'bear', 'neutral', 'high_vol', 'low_vol'

        Returns:
            Tamaño ajustado
        """
        market_config = self.config.get("market_conditions", {})

        multiplier = 1.0
        if market_condition == "bull":
            multiplier = market_config.get("bull_market_position_multiplier", 1.2)
        elif market_condition == "bear":
            multiplier = market_config.get("bear_market_position_multiplier", 0.6)
        elif market_condition == "high_vol":
            multiplier = market_config.get("high_volatility_position_multiplier", 0.7)
        elif market_condition == "low_vol":
            multiplier = market_config.get("low_volatility_position_multiplier", 1.1)

        adjusted_size = int(base_size * multiplier)
        return max(1, adjusted_size)

    def should_use_trailing_stop(self) -> bool:
        """Verifica si debe usar trailing stop"""
        return self.config.get("risk_management", {}).get("trailing_stop_enabled", True)

    def get_trailing_stop_params(self) -> Dict:
        """Obtiene parámetros de trailing stop"""
        risk_config = self.config.get("risk_management", {})
        return {
            "activation_pct": risk_config.get("trailing_stop_activation_pct", 2.0),
            "distance_pct": risk_config.get("trailing_stop_distance_pct", 1.0),
        }

    def should_use_partial_tp(self) -> bool:
        """Verifica si debe usar take profit parcial"""
        return self.config.get("risk_management", {}).get("partial_tp_enabled", True)

    def get_partial_tp_params(self) -> Dict:
        """Obtiene parámetros de take profit parcial"""
        risk_config = self.config.get("risk_management", {})
        return {
            "first_target_pct": risk_config.get("partial_tp_first_target_pct", 1.5),
            "close_pct": risk_config.get("partial_tp_close_pct", 50),
        }

    def record_trade_outcome(self, result: str):
        """
        Registra resultado de operación para cooldown.

        Args:
            result: 'win' o 'loss'
        """
        self.last_trade_time = datetime.now()
        self.last_trade_result = result

    def get_config_summary(self) -> str:
        """Retorna resumen de configuración actual"""
        summary = []
        summary.append("=== CONFIGURACIÓN PROFESIONAL ===\n")

        # Risk Management
        risk = self.config.get("risk_management", {})
        summary.append("📊 Gestión de Riesgo:")
        summary.append(f"  • Posición máx: {risk.get('max_position_size_pct', 30)}%")
        summary.append(f"  • Operaciones/día: {risk.get('max_daily_trades', 10)}")
        summary.append(f"  • Pérdida diaria máx: {risk.get('max_daily_loss_pct', 5)}%")
        summary.append(f"  • Trailing Stop: {'✅' if risk.get('trailing_stop_enabled') else '❌'}")
        summary.append(
            f"  • Take Profit Parcial: {'✅' if risk.get('partial_tp_enabled') else '❌'}\n"
        )

        # Entry Filters
        filters = self.config.get("entry_filters", {})
        summary.append("🎯 Filtros de Entrada:")
        summary.append(f"  • RSI: {filters.get('min_rsi', 30)}-{filters.get('max_rsi', 70)}")
        summary.append(f"  • Volumen mín: {filters.get('min_volume_ratio', 1.2)}x")
        summary.append(
            f"  • Confirmación tendencia: {'✅' if filters.get('require_trend_confirmation') else '❌'}\n"
        )

        # Time Management
        time_mgmt = self.config.get("time_management", {})
        summary.append("⏰ Gestión de Tiempo:")
        summary.append(
            f"  • Horario: {time_mgmt.get('trading_hours_start', '10:00')} - {time_mgmt.get('trading_hours_end', '16:00')}"
        )
        summary.append(f"  • Opera viernes: {'✅' if time_mgmt.get('trade_on_friday') else '❌'}")
        summary.append(
            f"  • Cooldown pérdida: {time_mgmt.get('cooldown_after_loss_minutes', 60)} min"
        )

        return "\n".join(summary)


# Test
if __name__ == "__main__":
    trader = ProfessionalTrader()
    print(trader.get_config_summary())

    # Test filtros
    test_data = {
        "momentum": {"rsi": 45},
        "volume": {"volume_ratio": 1.5},
        "trend": {"current_price": 100, "sma_20": 98, "sma_50": 95},
        "volatility": {"atr": 2.0},
    }

    can_enter, reason = trader.check_entry_filters(test_data)
    print(f"\n¿Puede entrar? {can_enter} - {reason}")

    can_trade, reason = trader.check_time_filters()
    print(f"¿Puede operar ahora? {can_trade} - {reason}")

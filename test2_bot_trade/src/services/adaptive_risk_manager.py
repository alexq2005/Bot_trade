"""
Adaptive Risk Manager
Gestión de riesgo dinámica basada en volatilidad, rendimiento y condiciones de mercado
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import numpy as np


class AdaptiveRiskManager:
    """
    Gestor de riesgo adaptativo que ajusta parámetros dinámicamente.
    """

    def __init__(self, initial_capital: float = 100.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Load configuration from file if exists
        config_file = "professional_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)

                # Parámetros desde configuración
                self.base_position_size_pct = config.get("max_position_size_pct", 18) / 100
                self.max_daily_trades = config.get("max_daily_trades", 10)
                self.max_daily_loss_pct = config.get("max_daily_loss_pct", 5) / 100
                stop_loss_mult = config.get("stop_loss_atr_multiplier", 2.0)
                take_profit_mult = config.get("take_profit_atr_multiplier", 3.0)

                # Convertir multiplicadores ATR a porcentajes base
                self.base_stop_loss_pct = 0.01 * stop_loss_mult  # Aproximación
                self.base_take_profit_pct = 0.01 * take_profit_mult

                print(f"✅ Configuración cargada desde {config_file}")
            except Exception as e:
                print(f"⚠️ Error cargando configuración: {e}. Usando valores por defecto.")
                self._set_default_params()
        else:
            self._set_default_params()

        self.min_confidence = 0.70  # 70%
        self.max_consecutive_losses = 3

        # Seguimiento de rendimiento
        self.trades_history = []
        self.daily_trades_count = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.last_trade_date = None

        # Archivo de persistencia
        self.history_file = "risk_manager_history.json"
        self._load_history()

    def _set_default_params(self):
        """Establece parámetros por defecto"""
        self.base_position_size_pct = 0.30  # 30% del capital
        self.base_stop_loss_pct = 0.02  # 2%
        self.base_take_profit_pct = 0.03  # 3%
        self.max_daily_trades = 10
        self.max_daily_loss_pct = 0.05  # 5% del capital

    def _load_history(self):
        """Carga historial de operaciones desde archivo"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    self.trades_history = data.get("trades", [])
                    self.current_capital = data.get("current_capital", self.initial_capital)
            except:
                pass

    def _save_history(self):
        """Guarda historial de operaciones"""
        data = {
            "trades": self.trades_history[-100:],  # Últimas 100 operaciones
            "current_capital": self.current_capital,
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.history_file, "w") as f:
            json.dump(data, f, indent=2)

    def _reset_daily_counters(self):
        """Resetea contadores diarios si es un nuevo día"""
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.daily_trades_count = 0
            self.daily_pnl = 0.0
            self.last_trade_date = today

    def calculate_position_size(
        self, current_price: float, stop_loss_price: float, win_rate: Optional[float] = None
    ) -> int:
        """
        Calcula tamaño de posición usando Kelly Criterion adaptado.

        Args:
            current_price: Precio actual del activo
            stop_loss_price: Precio de stop loss
            win_rate: Tasa de aciertos histórica (opcional)

        Returns:
            Cantidad de acciones a comprar (0 si no es viable)
        """
        # Validar precios
        if current_price <= 0:
            return 0
        
        # Si stop loss es igual o mayor al precio actual, no es viable
        if stop_loss_price >= current_price:
            return 0
        
        # Calcular riesgo por acción
        risk_per_share = current_price - stop_loss_price
        if risk_per_share <= 0:
            return 0
        
        # Ajustar por drawdown
        drawdown = self._calculate_drawdown()
        drawdown_multiplier = 1.0
        if drawdown > 0.10:  # Si drawdown > 10%
            drawdown_multiplier = 0.5  # Reducir a la mitad
        elif drawdown > 0.05:  # Si drawdown > 5%
            drawdown_multiplier = 0.75

        # Calcular capital disponible para esta operación
        available_capital = self.current_capital * self.base_position_size_pct * drawdown_multiplier

        # Ajustar por win rate si está disponible
        if win_rate is not None and win_rate > 0.5:
            # Kelly Criterion simplificado: f = (p * b - q) / b
            # donde p = win_rate, q = 1 - win_rate, b = avg_win / avg_loss
            kelly_multiplier = min(1.5, 1.0 + (win_rate - 0.5))
            available_capital *= kelly_multiplier

        # Calcular cantidad de acciones basada en capital disponible
        quantity = int(available_capital / current_price)
        
        # Asegurar que el riesgo total no exceda el límite diario
        max_risk = self.current_capital * self.max_daily_loss_pct
        max_shares_by_risk = int(max_risk / risk_per_share) if risk_per_share > 0 else 0
        
        # Tomar el mínimo entre cantidad por capital y cantidad por riesgo
        quantity = min(quantity, max_shares_by_risk)

        return max(0, quantity)  # Retornar 0 si no es viable

    def calculate_stop_loss(self, current_price: float, atr: Optional[float] = None) -> float:
        """
        Calcula precio de stop loss ajustado por volatilidad.

        Args:
            current_price: Precio actual
            atr: Average True Range (volatilidad)

        Returns:
            Precio de stop loss (siempre menor que current_price)
        """
        if current_price <= 0:
            return 0.0
        
        base_stop_pct = self.base_stop_loss_pct

        # Ajustar por volatilidad
        if atr is not None and atr > 0 and current_price > 0:
            volatility_ratio = atr / current_price
            if volatility_ratio > 0.03:  # Alta volatilidad
                base_stop_pct *= 1.5  # Ampliar stop loss
            elif volatility_ratio < 0.01:  # Baja volatilidad
                base_stop_pct *= 0.8  # Estrechar stop loss
        elif atr is not None and atr <= 0:
            # Si ATR es 0 o negativo, usar stop loss mínimo
            base_stop_pct = max(0.005, base_stop_pct * 0.5)  # Mínimo 0.5%

        # Asegurar que el stop loss sea al menos 0.5% y máximo 10%
        base_stop_pct = max(0.005, min(0.10, base_stop_pct))

        stop_loss_price = current_price * (1 - base_stop_pct)
        
        # Asegurar que siempre sea menor que el precio actual
        stop_loss_price = min(stop_loss_price, current_price * 0.99)
        
        return round(stop_loss_price, 2)

    def calculate_take_profit(self, current_price: float, atr: Optional[float] = None) -> float:
        """
        Calcula precio de take profit ajustado por volatilidad.

        Args:
            current_price: Precio actual
            atr: Average True Range (volatilidad)

        Returns:
            Precio de take profit
        """
        base_tp_pct = self.base_take_profit_pct

        # Ajustar por volatilidad
        if atr is not None:
            volatility_ratio = atr / current_price
            if volatility_ratio > 0.03:  # Alta volatilidad
                base_tp_pct *= 1.5  # Ampliar take profit
            elif volatility_ratio < 0.01:  # Baja volatilidad
                base_tp_pct *= 0.8

        take_profit_price = current_price * (1 + base_tp_pct)
        return round(take_profit_price, 2)

    def can_trade(self) -> tuple[bool, str]:
        """
        Verifica si se puede realizar una nueva operación.

        Returns:
            (puede_operar, razón)
        """
        self._reset_daily_counters()

        # Verificar límite de operaciones diarias
        if self.daily_trades_count >= self.max_daily_trades:
            return False, f"Límite diario de operaciones alcanzado ({self.max_daily_trades})"

        # Verificar pérdida diaria máxima
        if self.daily_pnl < -(self.current_capital * self.max_daily_loss_pct):
            return False, f"Pérdida diaria máxima alcanzada ({self.max_daily_loss_pct*100}%)"

        # Verificar pérdidas consecutivas
        if self.consecutive_losses >= self.max_consecutive_losses:
            return (
                False,
                f"Límite de pérdidas consecutivas alcanzado ({self.max_consecutive_losses})",
            )

        # Verificar capital mínimo
        if self.current_capital < self.initial_capital * 0.5:
            return False, "Capital por debajo del 50% del inicial - Trading pausado"

        return True, "OK"

    def record_trade(
        self,
        symbol: str,
        entry_price: float,
        exit_price: float,
        quantity: int,
        side: str,
        pnl: float,
    ):
        """
        Registra una operación completada.

        Args:
            symbol: Símbolo operado
            entry_price: Precio de entrada
            exit_price: Precio de salida
            quantity: Cantidad
            side: 'BUY' o 'SELL'
            pnl: Profit & Loss
        """
        trade = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "quantity": quantity,
            "side": side,
            "pnl": pnl,
            "pnl_pct": (pnl / (entry_price * quantity)) * 100,
        }

        self.trades_history.append(trade)
        self.daily_trades_count += 1
        self.daily_pnl += pnl
        self.current_capital += pnl

        # Actualizar racha de pérdidas
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0

        self._save_history()

    def get_performance_metrics(self, days: int = 7) -> Dict:
        """
        Calcula métricas de rendimiento.

        Args:
            days: Días a considerar

        Returns:
            Diccionario con métricas
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_trades = [
            t for t in self.trades_history if datetime.fromisoformat(t["timestamp"]) > cutoff_date
        ]

        if not recent_trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
            }

        wins = [t for t in recent_trades if t["pnl"] > 0]
        losses = [t for t in recent_trades if t["pnl"] < 0]

        total_wins = sum(t["pnl"] for t in wins)
        total_losses = abs(sum(t["pnl"] for t in losses))

        return {
            "total_trades": len(recent_trades),
            "win_rate": len(wins) / len(recent_trades) if recent_trades else 0.0,
            "profit_factor": total_wins / total_losses if total_losses > 0 else float("inf"),
            "total_pnl": sum(t["pnl"] for t in recent_trades),
            "avg_win": total_wins / len(wins) if wins else 0.0,
            "avg_loss": total_losses / len(losses) if losses else 0.0,
            "current_capital": self.current_capital,
            "return_pct": ((self.current_capital - self.initial_capital) / self.initial_capital)
            * 100,
        }

    def _calculate_drawdown(self) -> float:
        """Calcula el drawdown actual"""
        if self.current_capital >= self.initial_capital:
            return 0.0
        return (self.initial_capital - self.current_capital) / self.initial_capital

    def get_current_parameters(self) -> Dict:
        """Retorna los parámetros actuales de riesgo"""
        return {
            "position_size_pct": self.base_position_size_pct,
            "stop_loss_pct": self.base_stop_loss_pct,
            "take_profit_pct": self.base_take_profit_pct,
            "min_confidence": self.min_confidence,
            "max_daily_trades": self.max_daily_trades,
            "current_capital": self.current_capital,
            "daily_trades_count": self.daily_trades_count,
            "consecutive_losses": self.consecutive_losses,
            "drawdown": self._calculate_drawdown(),
        }


# Test
if __name__ == "__main__":
    risk_manager = AdaptiveRiskManager(initial_capital=100.0)

    print("=== Adaptive Risk Manager Test ===\n")

    # Test 1: Calcular tamaño de posición
    current_price = 7860.0
    stop_loss = risk_manager.calculate_stop_loss(current_price, atr=150.0)
    take_profit = risk_manager.calculate_take_profit(current_price, atr=150.0)
    position_size = risk_manager.calculate_position_size(current_price, stop_loss)

    print(f"Precio actual: ${current_price}")
    print(f"Stop Loss: ${stop_loss} ({((stop_loss - current_price) / current_price * 100):.2f}%)")
    print(
        f"Take Profit: ${take_profit} ({((take_profit - current_price) / current_price * 100):.2f}%)"
    )
    print(f"Tamaño de posición: {position_size} acciones")
    print(f"Capital requerido: ${position_size * current_price:.2f}")

    # Test 2: Verificar si puede operar
    can_trade, reason = risk_manager.can_trade()
    print(f"\n¿Puede operar? {can_trade} - {reason}")

    # Test 3: Simular operación ganadora
    print("\n=== Simulando operación ganadora ===")
    risk_manager.record_trade(
        symbol="GGAL", entry_price=7860.0, exit_price=8100.0, quantity=1, side="BUY", pnl=240.0
    )

    # Test 4: Métricas de rendimiento
    metrics = risk_manager.get_performance_metrics()
    print(f"\nMétricas de rendimiento:")
    print(f"  Total operaciones: {metrics['total_trades']}")
    print(f"  Win Rate: {metrics['win_rate']*100:.1f}%")
    print(f"  P&L Total: ${metrics['total_pnl']:.2f}")
    print(f"  Capital actual: ${metrics['current_capital']:.2f}")
    print(f"  Retorno: {metrics['return_pct']:.2f}%")

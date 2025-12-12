"""
Sistema de Notificación de Operaciones
Muestra todas las operaciones al usuario de forma clara y visual
"""
import os
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

from src.core.logger import get_logger
from src.core.console_utils import setup_windows_console, safe_print
from src.services.telegram_bot import TelegramAlertBot

setup_windows_console()
logger = get_logger("operation_notifier")


class OperationNotifier:
    """Sistema de notificación visual de operaciones"""
    
    # Códigos de color ANSI
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    def __init__(self, enable_telegram: bool = True):
        self.telegram_bot = TelegramAlertBot() if enable_telegram else None
        self.operations_log = []
        self.operations_file = Path("data/operations_log.json")
        self.operations_file.parent.mkdir(parents=True, exist_ok=True)
    
    def notify_trade_execution(self, trade_data: Dict):
        """Notifica ejecución de un trade"""
        symbol = trade_data.get('symbol', 'UNKNOWN')
        signal = trade_data.get('signal', 'UNKNOWN')
        price = trade_data.get('price', 0)
        quantity = trade_data.get('quantity', 0)
        stop_loss = trade_data.get('stop_loss', 0)
        take_profit = trade_data.get('take_profit', 0)
        mode = trade_data.get('mode', 'PAPER')
        
        # Color según señal
        signal_color = self.GREEN if signal == 'BUY' else self.RED
        mode_icon = '🧪' if mode == 'PAPER' else '💰'
        
        # Banner visual
        safe_print(f"\n{self.CYAN}{self.BOLD}{'='*80}{self.RESET}")
        safe_print(f"{self.CYAN}{self.BOLD}{' '*25}⚡ OPERACIÓN EJECUTADA{self.RESET}")
        safe_print(f"{self.CYAN}{self.BOLD}{'='*80}{self.RESET}\n")
        
        # Información principal
        safe_print(f"{self.BOLD}📊 Símbolo:{self.RESET} {self.BOLD}{symbol}{self.RESET}")
        safe_print(f"{self.BOLD}🎯 Señal:{self.RESET} {signal_color}{self.BOLD}{signal}{self.RESET}")
        safe_print(f"{self.BOLD}💵 Precio:{self.RESET} ${price:,.2f}")
        safe_print(f"{self.BOLD}📦 Cantidad:{self.RESET} {quantity} acciones")
        safe_print(f"{self.BOLD}💼 Capital Total:{self.RESET} ${price * quantity:,.2f}")
        safe_print(f"{self.BOLD}🛡️  Stop Loss:{self.RESET} ${stop_loss:,.2f}")
        safe_print(f"{self.BOLD}🎯 Take Profit:{self.RESET} ${take_profit:,.2f}")
        safe_print(f"{self.BOLD}⏰ Hora:{self.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        safe_print(f"{self.BOLD}🔧 Modo:{self.RESET} {mode_icon} {mode} TRADING")
        
        # Cálculo de riesgo/beneficio
        if stop_loss and take_profit:
            risk = abs(price - stop_loss) * quantity
            reward = abs(take_profit - price) * quantity
            risk_reward = reward / risk if risk > 0 else 0
            
            safe_print(f"\n{self.BOLD}📈 Análisis de Riesgo/Beneficio:{self.RESET}")
            safe_print(f"   Riesgo: ${risk:,.2f}")
            safe_print(f"   Beneficio Potencial: ${reward:,.2f}")
            safe_print(f"   Ratio R/R: {risk_reward:.2f}:1")
        
        safe_print(f"\n{self.CYAN}{self.BOLD}{'='*80}{self.RESET}\n")
        
        # Guardar en log
        operation = {
            'type': 'TRADE_EXECUTION',
            'timestamp': datetime.now().isoformat(),
            'data': trade_data
        }
        self._save_operation(operation)
        
        # Notificar por Telegram
        if self.telegram_bot:
            self._send_telegram_trade_notification(trade_data)
    
    def notify_prediction(self, prediction_data: Dict):
        """Notifica una predicción realizada"""
        symbol = prediction_data.get('symbol', 'UNKNOWN')
        current_price = prediction_data.get('current_price', 0)
        predicted_price = prediction_data.get('predicted_price', 0)
        change_pct = prediction_data.get('change_pct', 0)
        signal = prediction_data.get('signal', 'HOLD')
        
        # Color según señal
        if signal == 'BUY':
            signal_color = self.GREEN
            signal_icon = '📈'
        elif signal == 'SELL':
            signal_color = self.RED
            signal_icon = '📉'
        else:
            signal_color = self.YELLOW
            signal_icon = '➡️'
        
        safe_print(f"\n{self.BLUE}{self.BOLD}{'='*80}{self.RESET}")
        safe_print(f"{self.BLUE}{self.BOLD}{' '*28}🤖 PREDICCIÓN IA{self.RESET}")
        safe_print(f"{self.BLUE}{self.BOLD}{'='*80}{self.RESET}\n")
        
        safe_print(f"{self.BOLD}📊 Símbolo:{self.RESET} {self.BOLD}{symbol}{self.RESET}")
        safe_print(f"{self.BOLD}💵 Precio Actual:{self.RESET} ${current_price:,.2f}")
        safe_print(f"{self.BOLD}🔮 Precio Predicho:{self.RESET} ${predicted_price:,.2f}")
        safe_print(f"{self.BOLD}📊 Cambio Esperado:{self.RESET} {signal_color}{change_pct:+.2f}%{self.RESET}")
        safe_print(f"{self.BOLD}🎯 Señal:{self.RESET} {signal_color}{signal_icon} {signal}{self.RESET}")
        safe_print(f"{self.BOLD}⏰ Hora:{self.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        safe_print(f"\n{self.BLUE}{self.BOLD}{'='*80}{self.RESET}\n")
        
        # Guardar en log
        operation = {
            'type': 'PREDICTION',
            'timestamp': datetime.now().isoformat(),
            'data': prediction_data
        }
        self._save_operation(operation)
    
    def notify_analysis_complete(self, analysis_data: Dict):
        """Notifica análisis completo de un símbolo"""
        symbol = analysis_data.get('symbol', 'UNKNOWN')
        final_signal = analysis_data.get('final_signal', 'HOLD')
        confidence = analysis_data.get('confidence', 'LOW')
        score = analysis_data.get('score', 0)
        
        # Color según señal
        if final_signal == 'BUY':
            signal_color = self.GREEN
        elif final_signal == 'SELL':
            signal_color = self.RED
        else:
            signal_color = self.YELLOW
        
        # Color según confianza
        if confidence == 'HIGH':
            conf_color = self.GREEN
        elif confidence == 'MEDIUM':
            conf_color = self.YELLOW
        else:
            conf_color = self.CYAN
        
        safe_print(f"\n{self.MAGENTA}{self.BOLD}{'='*80}{self.RESET}")
        safe_print(f"{self.MAGENTA}{self.BOLD}{' '*25}📊 ANÁLISIS COMPLETO{self.RESET}")
        safe_print(f"{self.MAGENTA}{self.BOLD}{'='*80}{self.RESET}\n")
        
        safe_print(f"{self.BOLD}📊 Símbolo:{self.RESET} {self.BOLD}{symbol}{self.RESET}")
        safe_print(f"{self.BOLD}🎯 Señal Final:{self.RESET} {signal_color}{self.BOLD}{final_signal}{self.RESET}")
        safe_print(f"{self.BOLD}📈 Score:{self.RESET} {score}")
        safe_print(f"{self.BOLD}🎯 Confianza:{self.RESET} {conf_color}{confidence}{self.RESET}")
        safe_print(f"{self.BOLD}⏰ Hora:{self.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Mostrar factores si están disponibles
        if 'buy_factors' in analysis_data or 'sell_factors' in analysis_data:
            safe_print(f"\n{self.BOLD}📋 Factores de Decisión:{self.RESET}")
            buy_factors = analysis_data.get('buy_factors', [])
            sell_factors = analysis_data.get('sell_factors', [])
            
            if buy_factors:
                safe_print(f"   {self.GREEN}✅ Factores de Compra:{self.RESET}")
                for factor in buy_factors:
                    safe_print(f"      • {factor}")
            
            if sell_factors:
                safe_print(f"   {self.RED}❌ Factores de Venta:{self.RESET}")
                for factor in sell_factors:
                    safe_print(f"      • {factor}")
        
        safe_print(f"\n{self.MAGENTA}{self.BOLD}{'='*80}{self.RESET}\n")
        
        # Guardar en log
        operation = {
            'type': 'ANALYSIS',
            'timestamp': datetime.now().isoformat(),
            'data': analysis_data
        }
        self._save_operation(operation)
    
    def notify_trade_update(self, update_data: Dict):
        """Notifica actualización de un trade (cierre, stop loss, etc.)"""
        symbol = update_data.get('symbol', 'UNKNOWN')
        status = update_data.get('status', 'UNKNOWN')
        pnl = update_data.get('pnl', 0)
        pnl_pct = update_data.get('pnl_pct', 0)
        
        # Color según resultado
        if pnl > 0:
            result_color = self.GREEN
            result_icon = '✅'
        elif pnl < 0:
            result_color = self.RED
            result_icon = '❌'
        else:
            result_color = self.YELLOW
            result_icon = '➡️'
        
        safe_print(f"\n{self.YELLOW}{self.BOLD}{'='*80}{self.RESET}")
        safe_print(f"{self.YELLOW}{self.BOLD}{' '*25}🔄 ACTUALIZACIÓN DE TRADE{self.RESET}")
        safe_print(f"{self.YELLOW}{self.BOLD}{'='*80}{self.RESET}\n")
        
        safe_print(f"{self.BOLD}📊 Símbolo:{self.RESET} {self.BOLD}{symbol}{self.RESET}")
        safe_print(f"{self.BOLD}📋 Estado:{self.RESET} {status}")
        safe_print(f"{self.BOLD}💰 P&L:{self.RESET} {result_color}{pnl:+,.2f}{self.RESET}")
        safe_print(f"{self.BOLD}📈 P&L %:{self.RESET} {result_color}{pnl_pct:+.2f}%{self.RESET}")
        safe_print(f"{self.BOLD}⏰ Hora:{self.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        safe_print(f"\n{result_icon} {result_color}{self.BOLD}Resultado: {status}{self.RESET}")
        safe_print(f"\n{self.YELLOW}{self.BOLD}{'='*80}{self.RESET}\n")
        
        # Guardar en log
        operation = {
            'type': 'TRADE_UPDATE',
            'timestamp': datetime.now().isoformat(),
            'data': update_data
        }
        self._save_operation(operation)
        
        # Notificar por Telegram
        if self.telegram_bot and abs(pnl) > 0:
            self._send_telegram_update_notification(update_data)
    
    def notify_portfolio_update(self, portfolio_data: Dict):
        """Notifica actualización del portafolio"""
        total_value = portfolio_data.get('total_value', 0)
        total_pnl = portfolio_data.get('total_pnl', 0)
        total_pnl_pct = portfolio_data.get('total_pnl_pct', 0)
        positions_count = portfolio_data.get('positions_count', 0)
        
        # Color según resultado
        if total_pnl > 0:
            result_color = self.GREEN
        elif total_pnl < 0:
            result_color = self.RED
        else:
            result_color = self.YELLOW
        
        safe_print(f"\n{self.CYAN}{self.BOLD}{'='*80}{self.RESET}")
        safe_print(f"{self.CYAN}{self.BOLD}{' '*25}💼 ACTUALIZACIÓN DE PORTAFOLIO{self.RESET}")
        safe_print(f"{self.CYAN}{self.BOLD}{'='*80}{self.RESET}\n")
        
        safe_print(f"{self.BOLD}💰 Valor Total:{self.RESET} ${total_value:,.2f}")
        safe_print(f"{self.BOLD}📊 P&L Total:{self.RESET} {result_color}{total_pnl:+,.2f}{self.RESET}")
        safe_print(f"{self.BOLD}📈 P&L %:{self.RESET} {result_color}{total_pnl_pct:+.2f}%{self.RESET}")
        safe_print(f"{self.BOLD}📦 Posiciones:{self.RESET} {positions_count}")
        safe_print(f"{self.BOLD}⏰ Hora:{self.RESET} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        safe_print(f"\n{self.CYAN}{self.BOLD}{'='*80}{self.RESET}\n")
        
        # Guardar en log
        operation = {
            'type': 'PORTFOLIO_UPDATE',
            'timestamp': datetime.now().isoformat(),
            'data': portfolio_data
        }
        self._save_operation(operation)
    
    def _save_operation(self, operation: Dict):
        """Guarda operación en archivo"""
        import json
        
        self.operations_log.append(operation)
        
        # Mantener solo últimas 1000 operaciones
        if len(self.operations_log) > 1000:
            self.operations_log = self.operations_log[-1000:]
        
        try:
            with open(self.operations_file, 'w', encoding='utf-8') as f:
                json.dump(self.operations_log, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error guardando operación: {e}")
    
    def _send_telegram_trade_notification(self, trade_data: Dict):
        """Envía notificación de trade por Telegram con detalles mejorados"""
        if not self.telegram_bot:
            return
        
        symbol = trade_data.get('symbol', 'UNKNOWN')
        signal = trade_data.get('signal', 'UNKNOWN')
        price = trade_data.get('price', 0)
        quantity = trade_data.get('quantity', 0)
        mode = trade_data.get('mode', 'PAPER')
        stop_loss = trade_data.get('stop_loss', 0)
        take_profit = trade_data.get('take_profit', 0)
        score = trade_data.get('score', 0)
        pnl = trade_data.get('pnl')
        
        emoji = '📈' if signal == 'BUY' else '📉'
        mode_text = '🧪 PAPER' if mode == 'PAPER' else '💰 LIVE'
        
        # Calcular porcentajes de stop loss y take profit
        stop_loss_pct = ((price - stop_loss) / price * 100) if stop_loss > 0 else 0
        take_profit_pct = ((take_profit - price) / price * 100) if take_profit > 0 else 0
        
        message = f"""
{emoji} *OPERACIÓN EJECUTADA*

*Símbolo:* {symbol}
*Señal:* {signal}
*Precio:* ${price:,.2f}
*Cantidad:* {quantity} acciones
*Capital:* ${price * quantity:,.2f}
*Modo:* {mode_text}

*📊 Análisis:*
• Score: {score:.1f}/100
• Stop Loss: ${stop_loss:,.2f} ({stop_loss_pct:.1f}%)
• Take Profit: ${take_profit:,.2f} ({take_profit_pct:.1f}%)
"""
        
        # Agregar P&L si está disponible
        if pnl is not None:
            pnl_emoji = '✅' if pnl > 0 else '❌'
            message += f"\n*{pnl_emoji} P&L:* ${pnl:,.2f}"
        
        message += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.telegram_bot.send_alert(message)
    
    def _send_telegram_update_notification(self, update_data: Dict):
        """Envía notificación de actualización por Telegram"""
        if not self.telegram_bot:
            return
        
        symbol = update_data.get('symbol', 'UNKNOWN')
        status = update_data.get('status', 'UNKNOWN')
        pnl = update_data.get('pnl', 0)
        pnl_pct = update_data.get('pnl_pct', 0)
        
        emoji = '✅' if pnl > 0 else '❌' if pnl < 0 else '➡️'
        
        message = f"""
{emoji} *ACTUALIZACIÓN DE TRADE*

*Símbolo:* {symbol}
*Estado:* {status}
*P&L:* ${pnl:+,.2f}
*P&L %:* {pnl_pct:+.2f}%

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        self.telegram_bot.send_alert(message)
    
    def notify_alert(self, title: str, message: str, level: str = "info"):
        """Notifica una alerta genérica"""
        # Color según nivel
        if level == "error":
            color = self.RED
            icon = "❌"
        elif level == "warning":
            color = self.YELLOW
            icon = "⚠️"
        elif level == "success":
            color = self.GREEN
            icon = "✅"
        else:
            color = self.BLUE
            icon = "ℹ️"
        
        safe_print(f"\n{color}{self.BOLD}{'='*80}{self.RESET}")
        safe_print(f"{color}{self.BOLD}{' '*30}{icon} {title}{self.RESET}")
        safe_print(f"{color}{self.BOLD}{'='*80}{self.RESET}\n")
        safe_print(f"{message}\n")
        safe_print(f"{color}{self.BOLD}{'='*80}{self.RESET}\n")
        
        # Guardar en log
        operation = {
            'type': 'ALERT',
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'title': title,
            'message': message
        }
        self._save_operation(operation)
        
        # Notificar por Telegram si es error o warning
        if self.telegram_bot and level in ["error", "warning"]:
            emoji = "❌" if level == "error" else "⚠️"
            telegram_message = f"""
{emoji} *{title}*

{message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.telegram_bot.send_alert(telegram_message)
    
    def get_recent_operations(self, limit: int = 10) -> list:
        """Obtiene operaciones recientes"""
        return self.operations_log[-limit:]
    
    def show_operations_summary(self, hours: int = 24):
        """Muestra resumen de operaciones de las últimas horas"""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            op for op in self.operations_log
            if datetime.fromisoformat(op['timestamp']) >= cutoff
        ]
        
        safe_print(f"\n{self.BOLD}📊 Resumen de Operaciones (últimas {hours}h):{self.RESET}\n")
        
        trades = [op for op in recent if op['type'] == 'TRADE_EXECUTION']
        predictions = [op for op in recent if op['type'] == 'PREDICTION']
        analyses = [op for op in recent if op['type'] == 'ANALYSIS']
        
        safe_print(f"   ⚡ Trades ejecutados: {len(trades)}")
        safe_print(f"   🤖 Predicciones: {len(predictions)}")
        safe_print(f"   📊 Análisis: {len(analyses)}")
        safe_print(f"   📋 Total: {len(recent)} operaciones\n")


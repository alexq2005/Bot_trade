"""
Trading Assistant Service
Generates trading recommendations based on AI predictions and technical analysis
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Dict, List

from src.connectors.iol_client import IOLClient
from src.services.prediction_service import PredictionService
from src.services.technical_analysis import TechnicalAnalysisService


class TradingAssistant:
    """
    Provides trading recommendations for manual execution.
    Combines AI predictions with technical analysis.
    """

    def __init__(self, iol_client=None):
        """
        Args:
            iol_client: Optional IOLClient for real-time prices
        """
        self.prediction_service = PredictionService()
        self.technical_service = TechnicalAnalysisService(iol_client=iol_client)
        self.iol_client = iol_client

    def get_recommendations(self, symbols: List[str]) -> List[Dict]:
        """
        Analyze symbols and return trading recommendations.

        Args:
            symbols: List of symbols to analyze

        Returns:
            List of recommendation dicts with structure:
            {
                'symbol': 'GGAL.BA',
                'action': 'BUY' | 'SELL' | 'HOLD',
                'confidence': 0.85,  # 0-1
                'current_price': 7860.0,
                'target_price': 8200.0,
                'stop_loss': 7500.0,
                'reasoning': {
                    'ai_signal': 'BUY (+4.3%)',
                    'ai_confidence': 'MEDIUM',
                    'technical': 'RSI: 45 (Neutral)',
                    'trend': 'Alcista',
                    'summary': 'Señal mixta...'
                },
                'urgency': 'HIGH' | 'MEDIUM' | 'LOW'
            }
        """
        recommendations = []

        for symbol in symbols:
            try:
                rec = self._analyze_symbol(symbol)
                if rec:
                    recommendations.append(rec)
            except Exception as e:
                print(f"Error analyzing {symbol}: {e}")
                continue

        # Sort by confidence (descending)
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)

        return recommendations

    def _analyze_symbol(self, symbol: str) -> Dict:
        """Analyze a single symbol and generate recommendation."""

        # 1. Get AI Prediction
        try:
            ai_pred = self.prediction_service.generate_signal(symbol, threshold=2.0)
            ai_signal = ai_pred["signal"]
            ai_change = ai_pred["change_pct"]
            current_price = ai_pred["current_price"]
            predicted_price = ai_pred["predicted_price"]
        except Exception as e:
            print(f"AI prediction failed for {symbol}: {e}")
            return None

        # 2. Get Technical Analysis
        try:
            tech = self.technical_service.get_full_analysis(symbol)
            tech_signal = tech["signal"]
            rsi = tech["momentum"].get("rsi")
            trend_direction = (
                "Alcista" if tech["trend"]["current_price"] > tech["trend"]["sma_20"] else "Bajista"
            )
        except Exception as e:
            print(f"Technical analysis failed for {symbol}: {e}")
            return None

        # 3. Determine Final Action & Confidence
        action, confidence = self._determine_action(ai_signal, tech_signal, ai_change, rsi)

        # 4. Calculate Targets
        target_price, stop_loss = self._calculate_targets(current_price, action, ai_change, tech)

        # 5. Determine Urgency
        urgency = self._determine_urgency(confidence, abs(ai_change))

        # 6. Build Reasoning
        reasoning = {
            "ai_signal": f"{ai_signal} ({ai_change:+.1f}%)",
            "ai_confidence": self._confidence_label(abs(ai_change)),
            "technical": f"RSI: {rsi:.0f}" if rsi else "RSI: N/A",
            "trend": trend_direction,
            "summary": self._build_summary(action, ai_signal, tech_signal, confidence),
        }

        return {
            "symbol": symbol,
            "action": action,
            "confidence": confidence,
            "current_price": current_price,
            "target_price": target_price,
            "stop_loss": stop_loss,
            "reasoning": reasoning,
            "urgency": urgency,
        }

    def _determine_action(self, ai_signal, tech_signal, ai_change, rsi):
        """Determine final action and confidence based on signals."""

        # Both agree
        if ai_signal == tech_signal:
            if ai_signal == "BUY":
                confidence = min(0.85, 0.6 + abs(ai_change) / 20)
                return "BUY", confidence
            elif ai_signal == "SELL":
                confidence = min(0.85, 0.6 + abs(ai_change) / 20)
                return "SELL", confidence
            else:
                return "HOLD", 0.5

        # Signals conflict
        else:
            # Use RSI as tiebreaker
            if rsi:
                if rsi < 30:  # Oversold
                    return "BUY", 0.6
                elif rsi > 70:  # Overbought
                    return "SELL", 0.6

            # Default to HOLD on conflict
            return "HOLD", 0.4

    def _calculate_targets(self, current_price, action, ai_change, tech):
        """Calculate target price and stop loss."""

        if action == "BUY":
            # Target: AI predicted price or +5%
            target_price = current_price * (1 + max(abs(ai_change) / 100, 0.05))
            # Stop loss: -3% or based on ATR
            atr = tech["volatility"].get("atr", current_price * 0.03)
            stop_loss = current_price - (atr * 1.5)

        elif action == "SELL":
            # Target: AI predicted price or -5%
            target_price = current_price * (1 - max(abs(ai_change) / 100, 0.05))
            # Stop loss: +3% or based on ATR
            atr = tech["volatility"].get("atr", current_price * 0.03)
            stop_loss = current_price + (atr * 1.5)

        else:  # HOLD
            target_price = current_price
            stop_loss = current_price * 0.97

        return round(target_price, 2), round(stop_loss, 2)

    def _determine_urgency(self, confidence, change_magnitude):
        """Determine urgency level."""

        if confidence >= 0.75 and change_magnitude >= 5:
            return "HIGH"
        elif confidence >= 0.6 or change_magnitude >= 3:
            return "MEDIUM"
        else:
            return "LOW"

    def _confidence_label(self, change_pct):
        """Convert change percentage to confidence label."""
        if change_pct >= 5:
            return "ALTA"
        elif change_pct >= 2:
            return "MEDIA"
        else:
            return "BAJA"

    def _build_summary(self, action, ai_signal, tech_signal, confidence):
        """Build human-readable summary."""

        if ai_signal == tech_signal:
            return f"Señal clara de {action}. IA y análisis técnico coinciden."
        else:
            return f"Señal mixta. IA sugiere {ai_signal}, técnico sugiere {tech_signal}. Confianza: {confidence:.0%}"


# Test
if __name__ == "__main__":
    from src.connectors.iol_client import IOLClient

    client = IOLClient()
    assistant = TradingAssistant(iol_client=client)

    symbols = ["GGAL.BA", "YPFD.BA"]

    print("=== Trading Recommendations ===\n")
    recommendations = assistant.get_recommendations(symbols)

    for rec in recommendations:
        print(f"\n{rec['symbol']} - {rec['action']} (Confianza: {rec['confidence']:.0%})")
        print(f"  Precio Actual: ${rec['current_price']:.2f}")
        print(f"  Target: ${rec['target_price']:.2f}")
        print(f"  Stop Loss: ${rec['stop_loss']:.2f}")
        print(f"  Urgencia: {rec['urgency']}")
        print(f"  Razón: {rec['reasoning']['summary']}")

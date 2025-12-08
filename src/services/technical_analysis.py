"""
Technical Analysis and Volatility Service
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import ta

from src.core.database import SessionLocal
from src.models.market_data import MarketData


class TechnicalAnalysisService:
    """
    Service for calculating technical indicators and volatility metrics.
    Now integrates real-time prices from IOL.
    """

    def __init__(self, iol_client=None):
        """
        Args:
            iol_client: Optional IOLClient instance for real-time quotes
        """
        self.iol_client = iol_client

    def get_historical_data(self, symbol, days=100):
        """Load historical data from database as DataFrame."""
        db = SessionLocal()
        try:
            records = (
                db.query(MarketData)
                .filter(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp)
                .limit(days)
                .all()
            )

            data = {
                "timestamp": [r.timestamp for r in records],
                "open": [r.open for r in records],
                "high": [r.high for r in records],
                "low": [r.low for r in records],
                "close": [r.close for r in records],
                "volume": [r.volume for r in records],
            }

            df = pd.DataFrame(data)
            df.set_index("timestamp", inplace=True)
            return df
        finally:
            db.close()

    def get_realtime_price(self, symbol):
        """
        Get real-time price from IOL. Falls back to latest DB price if IOL unavailable.

        Returns:
            dict with 'price', 'source', 'volume', 'timestamp'
        """
        # Try IOL first if client available
        if self.iol_client:
            try:
                quote = self.iol_client.get_quote(symbol)

                if quote and "error" not in quote:
                    # IOL successful
                    price = quote.get("ultimoPrecio") or quote.get("puntas", {}).get(
                        "compradorPrecio"
                    )
                    if price:
                        print(f"   📡 Real-time price from IOL: ${price:.2f}")
                        return {
                            "price": float(price),
                            "source": "IOL",
                            "volume": quote.get("volumen", 0),
                            "timestamp": quote.get("fecha", "N/A"),
                        }
            except Exception as e:
                print(f"   ⚠️  IOL quote failed for {symbol}: {e}")

        # Fallback to database
        db = SessionLocal()
        try:
            record = (
                db.query(MarketData)
                .filter(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp.desc())
                .first()
            )

            if record:
                print(f"   💾 Using DB price (latest): ${record.close:.2f}")
                return {
                    "price": float(record.close),
                    "source": "DATABASE",
                    "volume": record.volume,
                    "timestamp": record.timestamp.isoformat() if record.timestamp else "N/A",
                }
            else:
                raise ValueError(f"No data found for {symbol}")
        finally:
            db.close()

    def calculate_volatility_indicators(self, df):
        """
        Calculate volatility indicators.
        Returns dict with ATR, Bollinger Bands, etc.
        """
        # ATR (Average True Range)
        atr_indicator = ta.volatility.AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        )
        atr = atr_indicator.average_true_range()

        # Bollinger Bands
        bb_indicator = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)

        # Historical Volatility (Standard Deviation of Returns)
        returns = df["close"].pct_change()
        hist_vol = returns.std() * np.sqrt(252)  # Annualized

        latest_atr = atr.iloc[-1] if len(atr) > 0 else None

        return {
            "atr": (
                float(latest_atr) if latest_atr is not None and not np.isnan(latest_atr) else None
            ),
            "historical_volatility": float(hist_vol),
            "bb_upper": float(bb_indicator.bollinger_hband().iloc[-1]),
            "bb_middle": float(bb_indicator.bollinger_mavg().iloc[-1]),
            "bb_lower": float(bb_indicator.bollinger_lband().iloc[-1]),
            "current_price": float(df["close"].iloc[-1]),
        }

    def calculate_momentum_indicators(self, df):
        """
        Calculate momentum indicators (RSI, MACD, Stochastic).
        """
        # RSI
        rsi_indicator = ta.momentum.RSIIndicator(df["close"], window=14)
        rsi = rsi_indicator.rsi()

        # MACD
        macd_indicator = ta.trend.MACD(df["close"])

        # Stochastic
        stoch_indicator = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])

        return {
            "rsi": float(rsi.iloc[-1]) if len(rsi) > 0 and not np.isnan(rsi.iloc[-1]) else None,
            "macd": float(macd_indicator.macd().iloc[-1]),
            "macd_signal": float(macd_indicator.macd_signal().iloc[-1]),
            "macd_histogram": float(macd_indicator.macd_diff().iloc[-1]),
            "stoch_k": float(stoch_indicator.stoch().iloc[-1]),
            "stoch_d": float(stoch_indicator.stoch_signal().iloc[-1]),
        }

    def calculate_trend_indicators(self, df):
        """
        Calculate trend indicators (SMA, EMA, ADX).
        """
        # Moving Averages
        sma_20 = ta.trend.SMAIndicator(df["close"], window=20).sma_indicator()
        sma_50 = ta.trend.SMAIndicator(df["close"], window=50).sma_indicator()
        ema_12 = ta.trend.EMAIndicator(df["close"], window=12).ema_indicator()

        # ADX (Average Directional Index)
        adx_indicator = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=14)

        current_price = df["close"].iloc[-1]

        return {
            "sma_20": (
                float(sma_20.iloc[-1])
                if len(sma_20) > 0 and not np.isnan(sma_20.iloc[-1])
                else None
            ),
            "sma_50": (
                float(sma_50.iloc[-1])
                if len(sma_50) > 0 and not np.isnan(sma_50.iloc[-1])
                else None
            ),
            "ema_12": (
                float(ema_12.iloc[-1])
                if len(ema_12) > 0 and not np.isnan(ema_12.iloc[-1])
                else None
            ),
            "adx": float(adx_indicator.adx().iloc[-1]),
            "current_price": float(current_price),
        }

    def get_full_analysis(self, symbol):
        """
        Get complete technical analysis for a symbol.
        Integrates real-time data from IOL if available.
        """
        df = self.get_historical_data(symbol, days=100)

        if df.empty:
            raise ValueError(f"No data found for {symbol}")

        # Integrate Real-Time Data
        try:
            rt_data = self.get_realtime_price(symbol)

            # Only update DataFrame if we got fresh data from IOL
            if rt_data["source"] == "IOL":
                current_price = rt_data["price"]

                # Append as new latest row to ensure indicators use live price
                # We use current price for O/H/L/C to approximate the latest candle
                new_ts = pd.Timestamp.now()

                new_row = pd.DataFrame(
                    {
                        "open": [current_price],
                        "high": [current_price],
                        "low": [current_price],
                        "close": [current_price],
                        "volume": [rt_data["volume"]],
                    },
                    index=[new_ts],
                )

                df = pd.concat([df, new_row])
                print(f"   📊 Live data integrated: ${current_price:.2f}")

        except Exception as e:
            print(f"   ⚠️ Live data integration error: {e}")

        volatility = self.calculate_volatility_indicators(df)
        momentum = self.calculate_momentum_indicators(df)
        trend = self.calculate_trend_indicators(df)

        # Generate trading signal based on indicators
        signal = self._generate_signal(volatility, momentum, trend)

        return {
            "symbol": symbol,
            "volatility": volatility,
            "momentum": momentum,
            "trend": trend,
            "signal": signal,
        }

    def _generate_signal(self, volatility, momentum, trend):
        """
        Generate trading signal based on technical indicators.
        """
        signals = []

        # RSI Signal
        if momentum["rsi"] is not None:
            if momentum["rsi"] < 30:
                signals.append("BUY")  # Oversold
            elif momentum["rsi"] > 70:
                signals.append("SELL")  # Overbought

        # MACD Signal
        if momentum["macd"] is not None and momentum["macd_signal"] is not None:
            if momentum["macd"] > momentum["macd_signal"]:
                signals.append("BUY")
            else:
                signals.append("SELL")

        # Trend Signal (Price vs SMA)
        if trend["sma_20"] is not None and trend["current_price"] is not None:
            if trend["current_price"] > trend["sma_20"]:
                signals.append("BUY")
            else:
                signals.append("SELL")

        # Count signals
        buy_count = signals.count("BUY")
        sell_count = signals.count("SELL")

        if buy_count > sell_count:
            return "BUY"
        elif sell_count > buy_count:
            return "SELL"
        else:
            return "HOLD"


# Test
if __name__ == "__main__":
    service = TechnicalAnalysisService()

    symbols = ["AAPL", "GGAL.BA"]

    print("=== Technical Analysis ===\n")
    for symbol in symbols:
        try:
            analysis = service.get_full_analysis(symbol)
            print(f"{symbol}:")
            print(f"  Price: ${analysis['trend']['current_price']:.2f}")
            print(
                f"  RSI: {analysis['momentum']['rsi']:.2f}"
                if analysis["momentum"]["rsi"]
                else "  RSI: N/A"
            )
            print(
                f"  ATR: {analysis['volatility']['atr']:.2f}"
                if analysis["volatility"]["atr"]
                else "  ATR: N/A"
            )
            print(f"  Signal: {analysis['signal']}")
            print()
        except Exception as e:
            print(f"{symbol}: Error - {e}\n")

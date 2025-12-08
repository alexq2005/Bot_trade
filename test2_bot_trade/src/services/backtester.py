"""
Backtesting Engine for Trading Strategies
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime

import numpy as np
import pandas as pd

from src.core.database import SessionLocal
from src.models.market_data import MarketData


class Backtester:
    """
    Backtesting engine for trading strategies.
    """

    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []

    def get_historical_data(self, symbol, days=252):
        """Load historical data from database."""
        db = SessionLocal()
        try:
            records = (
                db.query(MarketData)
                .filter(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp)
                .limit(days)
                .all()
            )

            df = pd.DataFrame(
                [
                    {
                        "timestamp": r.timestamp,
                        "open": r.open,
                        "high": r.high,
                        "low": r.low,
                        "close": r.close,
                        "volume": r.volume,
                    }
                    for r in records
                ]
            )

            return df
        finally:
            db.close()

    def execute_trade(self, symbol, action, price, quantity, timestamp):
        """Execute a trade (BUY or SELL)."""
        if action == "BUY":
            cost = price * quantity
            if cost <= self.capital:
                self.capital -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity

                self.trades.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "BUY",
                        "price": price,
                        "quantity": quantity,
                        "cost": cost,
                    }
                )
                return True

        elif action == "SELL":
            if symbol in self.positions and self.positions[symbol] >= quantity:
                proceeds = price * quantity
                self.capital += proceeds
                self.positions[symbol] -= quantity

                self.trades.append(
                    {
                        "timestamp": timestamp,
                        "symbol": symbol,
                        "action": "SELL",
                        "price": price,
                        "quantity": quantity,
                        "proceeds": proceeds,
                    }
                )
                return True

        return False

    def calculate_portfolio_value(self, current_prices):
        """Calculate total portfolio value."""
        portfolio_value = self.capital

        for symbol, quantity in self.positions.items():
            if symbol in current_prices:
                portfolio_value += quantity * current_prices[symbol]

        return portfolio_value

    def run_simple_ma_strategy(self, symbol, short_window=20, long_window=50):
        """
        Run a simple Moving Average crossover strategy.
        BUY when short MA crosses above long MA.
        SELL when short MA crosses below long MA.
        """
        df = self.get_historical_data(symbol, days=252)

        if len(df) < long_window:
            return {"error": "Not enough data"}

        # Calculate moving averages
        df["SMA_short"] = df["close"].rolling(window=short_window).mean()
        df["SMA_long"] = df["close"].rolling(window=long_window).mean()

        # Generate signals
        df["signal"] = 0
        df.loc[df["SMA_short"] > df["SMA_long"], "signal"] = 1  # BUY
        df.loc[df["SMA_short"] < df["SMA_long"], "signal"] = -1  # SELL

        # Detect crossovers
        df["position"] = df["signal"].diff()

        # Execute trades
        position_size = 10  # Number of shares per trade

        for idx, row in df.iterrows():
            if pd.notna(row["position"]):
                if row["position"] == 2:  # Crossover up (BUY signal)
                    self.execute_trade(symbol, "BUY", row["close"], position_size, row["timestamp"])

                elif row["position"] == -2:  # Crossover down (SELL signal)
                    if symbol in self.positions and self.positions[symbol] > 0:
                        self.execute_trade(
                            symbol, "SELL", row["close"], position_size, row["timestamp"]
                        )

            # Record equity curve
            current_prices = {symbol: row["close"]}
            portfolio_value = self.calculate_portfolio_value(current_prices)
            self.equity_curve.append(
                {"timestamp": row["timestamp"], "portfolio_value": portfolio_value}
            )

        return self.get_performance_metrics()

    def get_performance_metrics(self):
        """Calculate performance metrics."""
        if not self.equity_curve:
            return {"error": "No trades executed"}

        equity_df = pd.DataFrame(self.equity_curve)

        final_value = equity_df["portfolio_value"].iloc[-1]
        total_return = ((final_value - self.initial_capital) / self.initial_capital) * 100

        # Calculate returns
        equity_df["returns"] = equity_df["portfolio_value"].pct_change()

        # Sharpe ratio (annualized)
        mean_return = equity_df["returns"].mean() * 252
        std_return = equity_df["returns"].std() * np.sqrt(252)
        sharpe_ratio = mean_return / std_return if std_return > 0 else 0

        # Max drawdown
        equity_df["cummax"] = equity_df["portfolio_value"].cummax()
        equity_df["drawdown"] = (equity_df["portfolio_value"] - equity_df["cummax"]) / equity_df[
            "cummax"
        ]
        max_drawdown = equity_df["drawdown"].min() * 100

        # Win rate
        winning_trades = sum(
            1
            for t in self.trades
            if t["action"] == "SELL"
            and any(
                b["action"] == "BUY" and b["price"] < t["price"]
                for b in self.trades
                if b["timestamp"] < t["timestamp"]
            )
        )
        total_sell_trades = sum(1 for t in self.trades if t["action"] == "SELL")
        win_rate = (winning_trades / total_sell_trades * 100) if total_sell_trades > 0 else 0

        return {
            "initial_capital": self.initial_capital,
            "final_value": final_value,
            "total_return": total_return,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_trades": len(self.trades),
            "win_rate": win_rate,
            "equity_curve": equity_df[["timestamp", "portfolio_value"]].to_dict("records"),
        }


# Test
if __name__ == "__main__":
    backtester = Backtester(initial_capital=10000)

    print("=== Backtesting Simple MA Strategy ===\n")
    print("Symbol: AAPL")
    print("Strategy: MA Crossover (20/50)")
    print("Initial Capital: $10,000\n")

    results = backtester.run_simple_ma_strategy("AAPL", short_window=20, long_window=50)

    if "error" not in results:
        print(f"Final Portfolio Value: ${results['final_value']:.2f}")
        print(f"Total Return: {results['total_return']:.2f}%")
        print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {results['max_drawdown']:.2f}%")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Win Rate: {results['win_rate']:.2f}%")
    else:
        print(f"Error: {results['error']}")

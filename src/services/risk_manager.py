"""
Risk Management System
"""

import numpy as np


class AdaptiveRiskManager:
    """
    Risk management for trading strategies.
    """

    def __init__(self, max_position_size=0.1, max_portfolio_risk=0.02):
        """
        Args:
            max_position_size: Maximum % of portfolio per position (default 10%)
            max_portfolio_risk: Maximum % of portfolio to risk per trade (default 2%)
        """
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk

    def calculate_position_size(self, portfolio_value, entry_price, stop_loss_price):
        """
        Calculate position size based on risk management rules.

        Args:
            portfolio_value: Current portfolio value
            entry_price: Entry price for the trade
            stop_loss_price: Stop loss price

        Returns:
            Number of shares to buy
        """
        # Maximum capital to allocate
        max_capital = portfolio_value * self.max_position_size

        # Risk per share
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share == 0:
            return 0

        # Maximum risk amount
        max_risk = portfolio_value * self.max_portfolio_risk

        # Position size based on risk
        position_size = int(max_risk / risk_per_share)

        # Ensure we don't exceed max position size
        max_shares = int(max_capital / entry_price)

        return min(position_size, max_shares)

    def calculate_stop_loss(self, entry_price, atr, multiplier=2.0):
        """
        Calculate stop loss using ATR (Average True Range).

        Args:
            entry_price: Entry price
            atr: Average True Range
            multiplier: ATR multiplier (default 2.0)

        Returns:
            Stop loss price
        """
        return entry_price - (atr * multiplier)

    def calculate_take_profit(self, entry_price, atr, risk_reward_ratio=2.0):
        """
        Calculate take profit based on risk-reward ratio.

        Args:
            entry_price: Entry price
            atr: Average True Range
            risk_reward_ratio: Desired risk-reward ratio (default 2:1)

        Returns:
            Take profit price
        """
        stop_loss = self.calculate_stop_loss(entry_price, atr)
        risk = entry_price - stop_loss

        return entry_price + (risk * risk_reward_ratio)

    def check_portfolio_heat(self, open_positions, portfolio_value):
        """
        Check if total portfolio risk is within limits.

        Args:
            open_positions: List of open positions with risk amounts
            portfolio_value: Current portfolio value

        Returns:
            True if within limits, False otherwise
        """
        total_risk = sum(pos.get("risk_amount", 0) for pos in open_positions)
        portfolio_heat = total_risk / portfolio_value

        # Maximum 6% total portfolio risk (3 positions at 2% each)
        return portfolio_heat <= 0.06

    def should_close_position(self, current_price, entry_price, stop_loss, take_profit):
        """
        Determine if a position should be closed.

        Returns:
            'STOP_LOSS', 'TAKE_PROFIT', or None
        """
        if current_price <= stop_loss:
            return "STOP_LOSS"
        elif current_price >= take_profit:
            return "TAKE_PROFIT"
        return None

    def calculate_kelly_criterion(self, win_rate, avg_win, avg_loss):
        """
        Calculate optimal position size using Kelly Criterion.

        Args:
            win_rate: Probability of winning (0-1)
            avg_win: Average win amount
            avg_loss: Average loss amount

        Returns:
            Optimal fraction of capital to risk
        """
        if avg_loss == 0:
            return 0

        win_loss_ratio = avg_win / avg_loss
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio

        # Use half-Kelly for safety
        return max(0, min(kelly * 0.5, 0.25))  # Cap at 25%


# Example usage
if __name__ == "__main__":
    rm = AdaptiveRiskManager(max_position_size=0.1, max_portfolio_risk=0.02)

    portfolio_value = 10000
    entry_price = 150.00
    atr = 5.00

    print("=== Risk Management Example ===\n")
    print(f"Portfolio Value: ${portfolio_value:,.2f}")
    print(f"Entry Price: ${entry_price:.2f}")
    print(f"ATR: ${atr:.2f}\n")

    # Calculate stop loss and take profit
    stop_loss = rm.calculate_stop_loss(entry_price, atr, multiplier=2.0)
    take_profit = rm.calculate_take_profit(entry_price, atr, risk_reward_ratio=2.0)

    print(f"Stop Loss: ${stop_loss:.2f}")
    print(f"Take Profit: ${take_profit:.2f}\n")

    # Calculate position size
    position_size = rm.calculate_position_size(portfolio_value, entry_price, stop_loss)

    print(f"Recommended Position Size: {position_size} shares")
    print(f"Total Investment: ${position_size * entry_price:,.2f}")
    print(f"Risk Amount: ${position_size * (entry_price - stop_loss):,.2f}")
    print(f"Risk %: {(position_size * (entry_price - stop_loss) / portfolio_value * 100):.2f}%\n")

    # Kelly Criterion
    kelly = rm.calculate_kelly_criterion(win_rate=0.55, avg_win=100, avg_loss=50)
    print(f"Kelly Criterion (Half): {kelly*100:.2f}% of capital")

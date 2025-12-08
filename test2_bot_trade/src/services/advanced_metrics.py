"""
Advanced Performance Metrics
"""

import numpy as np
import pandas as pd


class AdvancedMetrics:
    """
    Calculate advanced performance metrics for trading strategies.
    """

    @staticmethod
    def sortino_ratio(returns, target_return=0, periods=252):
        """
        Calculate Sortino Ratio (focuses on downside deviation).

        Args:
            returns: Series of returns
            target_return: Minimum acceptable return (default 0)
            periods: Number of periods per year (default 252 for daily)
        """
        excess_returns = returns - target_return
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return np.inf

        downside_std = np.sqrt(np.mean(downside_returns**2))

        if downside_std == 0:
            return np.inf

        return np.sqrt(periods) * excess_returns.mean() / downside_std

    @staticmethod
    def calmar_ratio(returns, periods=252):
        """
        Calculate Calmar Ratio (return / max drawdown).
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_dd = abs(drawdown.min())

        if max_dd == 0:
            return np.inf

        annual_return = (cumulative.iloc[-1] ** (periods / len(returns))) - 1

        return annual_return / max_dd

    @staticmethod
    def profit_factor(returns):
        """
        Calculate Profit Factor (gross profit / gross loss).
        """
        gains = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())

        if losses == 0:
            return np.inf

        return gains / losses

    @staticmethod
    def omega_ratio(returns, threshold=0):
        """
        Calculate Omega Ratio.
        """
        excess = returns - threshold
        gains = excess[excess > 0].sum()
        losses = abs(excess[excess < 0].sum())

        if losses == 0:
            return np.inf

        return gains / losses

    @staticmethod
    def value_at_risk(returns, confidence=0.95):
        """
        Calculate Value at Risk (VaR).
        """
        return np.percentile(returns, (1 - confidence) * 100)

    @staticmethod
    def conditional_var(returns, confidence=0.95):
        """
        Calculate Conditional Value at Risk (CVaR / Expected Shortfall).
        """
        var = AdvancedMetrics.value_at_risk(returns, confidence)
        return returns[returns <= var].mean()

    @staticmethod
    def calculate_all_metrics(returns, benchmark_returns=None):
        """
        Calculate all advanced metrics.

        Args:
            returns: Series of strategy returns
            benchmark_returns: Optional series of benchmark returns

        Returns:
            Dict with all metrics
        """
        metrics = {
            "total_return": (1 + returns).prod() - 1,
            "annual_return": (1 + returns).mean() * 252,
            "volatility": returns.std() * np.sqrt(252),
            "sharpe_ratio": (
                (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
            ),
            "sortino_ratio": AdvancedMetrics.sortino_ratio(returns),
            "calmar_ratio": AdvancedMetrics.calmar_ratio(returns),
            "profit_factor": AdvancedMetrics.profit_factor(returns),
            "omega_ratio": AdvancedMetrics.omega_ratio(returns),
            "var_95": AdvancedMetrics.value_at_risk(returns, 0.95),
            "cvar_95": AdvancedMetrics.conditional_var(returns, 0.95),
            "max_drawdown": AdvancedMetrics._max_drawdown(returns),
            "win_rate": len(returns[returns > 0]) / len(returns) if len(returns) > 0 else 0,
        }

        # Alpha and Beta if benchmark provided
        if benchmark_returns is not None and len(benchmark_returns) == len(returns):
            metrics["alpha"], metrics["beta"] = AdvancedMetrics._alpha_beta(
                returns, benchmark_returns
            )

        return metrics

    @staticmethod
    def _max_drawdown(returns):
        """Calculate maximum drawdown."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    @staticmethod
    def _alpha_beta(returns, benchmark_returns):
        """Calculate alpha and beta vs benchmark."""
        # Align returns
        df = pd.DataFrame({"strategy": returns, "benchmark": benchmark_returns}).dropna()

        if len(df) < 2:
            return 0, 0

        # Calculate beta
        covariance = df["strategy"].cov(df["benchmark"])
        benchmark_var = df["benchmark"].var()

        if benchmark_var == 0:
            return 0, 0

        beta = covariance / benchmark_var

        # Calculate alpha (annualized)
        alpha = (df["strategy"].mean() - beta * df["benchmark"].mean()) * 252

        return alpha, beta


# Example usage
if __name__ == "__main__":
    # Generate sample returns
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0.001, 0.02, 252))  # Daily returns

    print("=== Advanced Performance Metrics ===\n")

    metrics = AdvancedMetrics.calculate_all_metrics(returns)

    print(f"Total Return: {metrics['total_return']*100:.2f}%")
    print(f"Annual Return: {metrics['annual_return']*100:.2f}%")
    print(f"Volatility: {metrics['volatility']*100:.2f}%")
    print(f"\nRisk-Adjusted Returns:")
    print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"  Sortino Ratio: {metrics['sortino_ratio']:.2f}")
    print(f"  Calmar Ratio: {metrics['calmar_ratio']:.2f}")
    print(f"\nProfit Metrics:")
    print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"  Omega Ratio: {metrics['omega_ratio']:.2f}")
    print(f"  Win Rate: {metrics['win_rate']*100:.2f}%")
    print(f"\nRisk Metrics:")
    print(f"  VaR (95%): {metrics['var_95']*100:.2f}%")
    print(f"  CVaR (95%): {metrics['cvar_95']*100:.2f}%")
    print(f"  Max Drawdown: {metrics['max_drawdown']*100:.2f}%")

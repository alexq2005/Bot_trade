"""
Portfolio Optimization Service
Implements Markowitz Mean-Variance Optimization and Risk Parity
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from src.core.database import SessionLocal
from src.models.market_data import MarketData


class PortfolioOptimizer:
    """
    Portfolio optimization using Modern Portfolio Theory.
    """

    def __init__(self):
        self.risk_free_rate = 0.02  # 2% annual risk-free rate

    def get_returns_data(self, symbols, days=252):
        """
        Get historical returns for multiple symbols.
        Returns empty DataFrame if not enough data or symbols have different lengths.
        """
        db = SessionLocal()
        try:
            returns_dict = {}
            min_required_days = 30  # Mínimo de días requeridos para optimización

            for symbol in symbols:
                records = (
                    db.query(MarketData)
                    .filter(MarketData.symbol == symbol)
                    .order_by(MarketData.timestamp)
                    .limit(days)
                    .all()
                )

                if not records or len(records) < min_required_days:
                    continue

                prices = np.array([r.close for r in records])
                # Validar que haya precios válidos
                if len(prices) < 2 or np.any(prices <= 0):
                    continue
                
                returns = np.diff(prices) / prices[:-1]
                # Validar que los returns sean válidos (no infinitos ni NaN)
                if np.any(np.isinf(returns)) or np.any(np.isnan(returns)):
                    continue
                
                returns_dict[symbol] = returns

            # Validar que tengamos al menos 2 símbolos con datos
            if len(returns_dict) < 2:
                return pd.DataFrame()

            # Create DataFrame with aligned returns
            # Alinear todos los arrays a la misma longitud (la mínima)
            min_length = min(len(r) for r in returns_dict.values())
            
            # Validar que la longitud mínima sea razonable
            if min_length < min_required_days:
                return pd.DataFrame()
            
            aligned_returns = {k: v[-min_length:] for k, v in returns_dict.items()}
            
            # Crear DataFrame y validar que todas las columnas tengan la misma longitud
            returns_df = pd.DataFrame(aligned_returns)
            
            # Verificar que todas las columnas tengan la misma longitud
            if not returns_df.empty:
                lengths = [len(returns_df[col]) for col in returns_df.columns]
                if len(set(lengths)) > 1:
                    # Si hay diferentes longitudes, recortar a la mínima
                    min_len = min(lengths)
                    returns_df = returns_df.iloc[-min_len:]
            
            return returns_df
        except Exception as e:
            # Si hay cualquier error, retornar DataFrame vacío
            return pd.DataFrame()
        finally:
            db.close()

    def calculate_portfolio_metrics(self, weights, returns_df):
        """
        Calculate portfolio return and risk.
        """
        # Annualized returns
        mean_returns = returns_df.mean() * 252

        # Covariance matrix (annualized)
        cov_matrix = returns_df.cov() * 252

        # Portfolio return
        portfolio_return = np.dot(weights, mean_returns)

        # Portfolio volatility (risk)
        portfolio_std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        # Sharpe ratio
        sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_std

        return {
            "return": portfolio_return,
            "volatility": portfolio_std,
            "sharpe_ratio": sharpe_ratio,
        }

    def optimize_sharpe_ratio(self, returns_df):
        """
        Optimize portfolio to maximize Sharpe ratio (Markowitz).
        """
        n_assets = len(returns_df.columns)

        # Objective function: negative Sharpe ratio (we minimize)
        def neg_sharpe(weights):
            metrics = self.calculate_portfolio_metrics(weights, returns_df)
            return -metrics["sharpe_ratio"]

        # Constraints: weights sum to 1
        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}

        # Bounds: 0 <= weight <= 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess: equal weights
        initial_weights = np.array([1 / n_assets] * n_assets)

        # Optimize
        result = minimize(
            neg_sharpe, initial_weights, method="SLSQP", bounds=bounds, constraints=constraints
        )

        if result.success:
            optimal_weights = result.x
            metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)

            return {
                "weights": dict(zip(returns_df.columns, optimal_weights)),
                "metrics": metrics,
                "success": True,
            }
        else:
            return {"success": False, "message": result.message}

    def optimize_min_variance(self, returns_df):
        """
        Optimize portfolio to minimize variance.
        """
        n_assets = len(returns_df.columns)
        cov_matrix = returns_df.cov() * 252

        # Objective: minimize variance
        def portfolio_variance(weights):
            return np.dot(weights.T, np.dot(cov_matrix, weights))

        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_weights = np.array([1 / n_assets] * n_assets)

        result = minimize(
            portfolio_variance,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if result.success:
            optimal_weights = result.x
            metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)

            return {
                "weights": dict(zip(returns_df.columns, optimal_weights)),
                "metrics": metrics,
                "success": True,
            }
        else:
            return {"success": False, "message": result.message}

    def risk_parity_weights(self, returns_df):
        """
        Calculate Risk Parity portfolio weights.
        Each asset contributes equally to portfolio risk.
        """
        cov_matrix = returns_df.cov() * 252
        n_assets = len(returns_df.columns)

        # Objective: minimize difference in risk contributions
        def risk_parity_objective(weights):
            portfolio_var = np.dot(weights.T, np.dot(cov_matrix, weights))
            marginal_contrib = np.dot(cov_matrix, weights)
            risk_contrib = weights * marginal_contrib

            # We want equal risk contributions
            target_risk = portfolio_var / n_assets
            return np.sum((risk_contrib - target_risk) ** 2)

        constraints = {"type": "eq", "fun": lambda w: np.sum(w) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))
        initial_weights = np.array([1 / n_assets] * n_assets)

        result = minimize(
            risk_parity_objective,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
        )

        if result.success:
            optimal_weights = result.x
            metrics = self.calculate_portfolio_metrics(optimal_weights, returns_df)

            return {
                "weights": dict(zip(returns_df.columns, optimal_weights)),
                "metrics": metrics,
                "success": True,
            }
        else:
            return {"success": False, "message": result.message}


# Test
if __name__ == "__main__":
    optimizer = PortfolioOptimizer()

    symbols = ["AAPL", "MSFT", "GOOGL", "SPY"]

    print("=== Portfolio Optimization ===\n")

    # Get returns data
    returns_df = optimizer.get_returns_data(symbols, days=252)
    print(f"Analyzing {len(returns_df.columns)} assets with {len(returns_df)} days of data\n")

    # Max Sharpe Ratio
    print("1. Maximum Sharpe Ratio Portfolio (Markowitz):")
    sharpe_result = optimizer.optimize_sharpe_ratio(returns_df)
    if sharpe_result["success"]:
        print(f"   Expected Return: {sharpe_result['metrics']['return']*100:.2f}%")
        print(f"   Volatility: {sharpe_result['metrics']['volatility']*100:.2f}%")
        print(f"   Sharpe Ratio: {sharpe_result['metrics']['sharpe_ratio']:.2f}")
        print("   Weights:")
        for symbol, weight in sharpe_result["weights"].items():
            print(f"     {symbol}: {weight*100:.2f}%")
    print()

    # Min Variance
    print("2. Minimum Variance Portfolio:")
    minvar_result = optimizer.optimize_min_variance(returns_df)
    if minvar_result["success"]:
        print(f"   Expected Return: {minvar_result['metrics']['return']*100:.2f}%")
        print(f"   Volatility: {minvar_result['metrics']['volatility']*100:.2f}%")
        print(f"   Sharpe Ratio: {minvar_result['metrics']['sharpe_ratio']:.2f}")
        print("   Weights:")
        for symbol, weight in minvar_result["weights"].items():
            print(f"     {symbol}: {weight*100:.2f}%")
    print()

    # Risk Parity
    print("3. Risk Parity Portfolio:")
    rp_result = optimizer.risk_parity_weights(returns_df)
    if rp_result["success"]:
        print(f"   Expected Return: {rp_result['metrics']['return']*100:.2f}%")
        print(f"   Volatility: {rp_result['metrics']['volatility']*100:.2f}%")
        print(f"   Sharpe Ratio: {rp_result['metrics']['sharpe_ratio']:.2f}")
        print("   Weights:")
        for symbol, weight in rp_result["weights"].items():
            print(f"     {symbol}: {weight*100:.2f}%")

"""
Continuous Learning System
Automatic model retraining and performance monitoring
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import ta

from src.core.database import SessionLocal
from src.models.market_data import MarketData
from src.models.price_predictor import LSTMPricePredictor


class ContinuousLearning:
    """
    Continuous learning system for model retraining.
    """

    def __init__(self, model_path="models", performance_threshold=0.02):
        """
        Args:
            model_path: Path to save/load models
            performance_threshold: MAE threshold for retraining (default 2%)
        """
        self.model_path = model_path
        self.performance_threshold = performance_threshold
        self.performance_log = []

    def prepare_features(self, df):
        """
        Generate technical indicators for machine learning features.
        Target column (Close) MUST be first.
        """
        df = df.copy()
        
        # 1. Momentum: RSI
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        
        # 2. Trend: MACD
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        
        # 3. Volatility: Bollinger Band Width
        bb = ta.volatility.BollingerBands(df['close'], window=20)
        bb_upper = bb.bollinger_hband()
        bb_lower = bb.bollinger_lband()
        bb_middle = bb.bollinger_mavg()
        # Evitar división por cero
        df['bb_width'] = np.where(
            bb_middle != 0,
            (bb_upper - bb_lower) / bb_middle,
            0
        )
        
        # 4. Trend strength: Distance from SMA 20
        sma = ta.trend.SMAIndicator(df['close'], window=20)
        sma_values = sma.sma_indicator()
        # Evitar división por cero
        df['sma_dist'] = np.where(
            sma_values != 0,
            (df['close'] - sma_values) / sma_values,
            0
        )
        
        # 5. Volume: ROC
        df['vol_roc'] = df['volume'].pct_change()
        
        # Reemplazar infinitos y NaN
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        
        # Verificar que no queden infinitos
        if not np.isfinite(df.select_dtypes(include=[np.number]).values).all():
            # Si aún hay infinitos, reemplazarlos con 0
            df.replace([np.inf, -np.inf], 0, inplace=True)
        
        # Select and order columns: Close MUST be first for the predictor to identify target
        feature_cols = ['close', 'rsi', 'macd', 'bb_width', 'sma_dist', 'vol_roc']
        return df[feature_cols]

    def evaluate_model_performance(self, symbol, days=30):
        """
        Evaluate model performance on recent data.

        Returns:
            Dict with MAE, accuracy, and should_retrain flag
        """
        # Load model
        predictor = LSTMPricePredictor()
        model_file = os.path.join(self.model_path, symbol)

        try:
            predictor.load(model_file)
        except Exception:
            # If model doesn't exist or shapes changed (upgrade), force retrain
            return {"error": "Model not found or incompatible", "should_retrain": True}

        # Get recent data
        db = SessionLocal()
        try:
            # Fetch enough data for indicators (60 seq + 30 eval + 50 buffer for indicators)
            records = (
                db.query(MarketData)
                .filter(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp.desc())
                .limit(days + 60 + 50) 
                .all()
            )

            if len(records) < days + 60 + 20:
                return {"error": "Not enough data", "should_retrain": False}

            # Convert to DataFrame for feature engineering
            records = list(reversed(records))
            df = pd.DataFrame([{'close': r.close, 'volume': r.volume} for r in records])
            
            # Generate Features
            df_features = self.prepare_features(df)
            
            if len(df_features) < days + 60:
                 return {"error": "Not enough data after feature engineering", "should_retrain": False}
            
            feature_data = df_features.values

            # Evaluate on last 'days' days
            predictions = []
            actuals = []
            
            # Sliding window evaluation
            # We need 60 days (sequence_length) prior to target day
            
            start_idx = len(feature_data) - days
            
            for i in range(start_idx, len(feature_data)):
                # Get sequence of 60 days BEFORE i
                seq_start = i - 60
                if seq_start < 0: continue
                
                recent_features = feature_data[seq_start:i]
                actual = feature_data[i, 0] # 0 is close price
                
                prediction = predictor.predict(recent_features)
                
                predictions.append(prediction)
                actuals.append(actual)

            if not predictions:
                return {"error": "Evaluation failed", "should_retrain": True}

            # Calculate metrics
            predictions = np.array(predictions)
            actuals = np.array(actuals)

            mae = np.mean(np.abs(predictions - actuals))
            mape = np.mean(np.abs((predictions - actuals) / actuals)) * 100

            # Direction accuracy
            if len(predictions) > 1:
                pred_direction = np.diff(predictions) > 0
                actual_direction = np.diff(actuals) > 0
                direction_accuracy = np.mean(pred_direction == actual_direction) * 100
            else:
                direction_accuracy = 0.0

            # Determine if retraining is needed
            should_retrain = mape > self.performance_threshold

            performance = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "mae": float(mae),
                "mape": float(mape),
                "direction_accuracy": float(direction_accuracy),
                "should_retrain": should_retrain,
                "days_evaluated": len(predictions),
            }

            self.performance_log.append(performance)

            return performance

        finally:
            db.close()

    def retrain_model(self, symbol, epochs=30):
        """
        Retrain model with latest data.
        """
        print(f"🔄 Retraining model for {symbol}...")

        # Load data
        db = SessionLocal()
        try:
            records = (
                db.query(MarketData)
                .filter(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp)
                .all()
            )

            if len(records) < 100:
                return {"error": "Not enough data for training"}

            # Prepare DataFrame
            df = pd.DataFrame([{'close': r.close, 'volume': r.volume} for r in records])
            
            # Feature Engineering
            df_features = self.prepare_features(df)
            print(f"   Features generated: {df_features.shape[1]} columns ({', '.join(df_features.columns)})")
            
            feature_data = df_features.values

            # Create and train model
            predictor = LSTMPricePredictor(sequence_length=60, prediction_days=1)
            
            # Pass full feature matrix
            history = predictor.train(feature_data, epochs=epochs, batch_size=32, validation_split=0.2)

            # Save model
            os.makedirs(self.model_path, exist_ok=True)
            model_file = os.path.join(self.model_path, symbol)
            predictor.save(model_file)

            # Get final metrics
            final_loss = history.history["loss"][-1]
            final_val_loss = history.history["val_loss"][-1]

            print(f"✅ Model retrained successfully")
            print(f"   Training Loss: {final_loss:.6f}")
            print(f"   Validation Loss: {final_val_loss:.6f}")

            return {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "training_loss": float(final_loss),
                "validation_loss": float(final_val_loss),
                "epochs": epochs,
                "success": True,
            }

        finally:
            db.close()

    def auto_retrain_if_needed(self, symbols, evaluation_days=30, epochs=30):
        """
        Automatically evaluate and retrain models if needed.

        Args:
            symbols: List of symbols to check
            evaluation_days: Days to evaluate performance
            epochs: Training epochs if retraining needed

        Returns:
            Summary of actions taken
        """
        summary = {"evaluated": [], "retrained": [], "skipped": []}

        for symbol in symbols:
            print(f"\n📊 Evaluating {symbol}...")

            # Evaluate performance
            performance = self.evaluate_model_performance(symbol, days=evaluation_days)
            summary["evaluated"].append(performance)

            if "error" in performance:
                print(f"⚠️  {performance['error']}")
                summary["skipped"].append(symbol)
                continue

            print(f"   MAE: {performance['mae']:.2f}")
            print(f"   MAPE: {performance['mape']:.2f}%")
            print(f"   Direction Accuracy: {performance['direction_accuracy']:.2f}%")

            # Retrain if needed
            if performance["should_retrain"]:
                print(f"🔴 Performance below threshold - retraining...")
                result = self.retrain_model(symbol, epochs=epochs)

                if result.get("success"):
                    summary["retrained"].append(symbol)
                else:
                    summary["skipped"].append(symbol)
            else:
                print(f"✅ Performance acceptable - no retraining needed")

        return summary

    def get_performance_history(self, symbol=None):
        """Get performance history."""
        if symbol:
            return [p for p in self.performance_log if p["symbol"] == symbol]
        return self.performance_log


# Example usage
if __name__ == "__main__":
    cl = ContinuousLearning(performance_threshold=5.0)  # 5% MAPE threshold

    symbols = ["AAPL"]

    print("=== Continuous Learning System ===\n")

    # Auto-evaluate and retrain if needed
    summary = cl.auto_retrain_if_needed(symbols, evaluation_days=30, epochs=20)

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Evaluated: {len(summary['evaluated'])} models")
    print(f"Retrained: {len(summary['retrained'])} models")
    print(f"Skipped: {len(summary['skipped'])} models")

    if summary["retrained"]:
        print(f"\nRetrained models: {', '.join(summary['retrained'])}")

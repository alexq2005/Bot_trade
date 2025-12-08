"""
Prediction Service for generating trading signals.
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import ta

from src.core.database import SessionLocal
from src.models.market_data import MarketData
from src.models.price_predictor import LSTMPricePredictor


class PredictionService:
    """
    Service to generate predictions and trading signals.
    """

    def __init__(self, model_path="models"):
        self.model_path = model_path
        self.models = {}

    def load_model(self, symbol):
        """
        Load trained model for a symbol, with fallback to generic model.
        Returns None if model cannot be loaded (for graceful fallback).
        """
        if symbol not in self.models:
            predictor = LSTMPricePredictor()

            # Try specific model first: models/SYMBOL_model.h5
            specific_model_path = os.path.join(self.model_path, symbol)

            # Try generic model: models/lstm_model.h5
            generic_model_path = os.path.join(self.model_path, "lstm")

            try:
                # Check if specific model exists (predictor.load appends _model.h5)
                if os.path.exists(f"{specific_model_path}_model.h5"):
                    try:
                        predictor.load(specific_model_path)
                        self.models[symbol] = predictor
                        return predictor
                    except Exception as e:
                        # Si falla cargar modelo específico, intentar genérico
                        pass
                
                # Try generic model
                if os.path.exists(f"{generic_model_path}_model.h5"):
                    try:
                        print(f"Using generic model for {symbol}")
                        predictor.load(generic_model_path)
                        self.models[symbol] = predictor
                        return predictor
                    except Exception as e:
                        # Si también falla el genérico, retornar None
                        pass
                
                # Si no se encontró ningún modelo, retornar None
                return None
                
            except Exception as e:
                # Cualquier otro error, retornar None para fallback
                return None

        return self.models.get(symbol)

    def prepare_features(self, df):
        """
        Generate technical indicators for machine learning features.
        Target column (Close) MUST be first.
        Match logic with ContinuousLearning.
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
        
        # Select and order columns: Close MUST be first
        feature_cols = ['close', 'rsi', 'macd', 'bb_width', 'sma_dist', 'vol_roc']
        return df[feature_cols]

    def get_recent_data(self, symbol, days=150):
        """
        Get recent data from database for feature engineering.
        Need more days than sequence length to calculate indicators.
        """
        db = SessionLocal()
        try:
            records = (
                db.query(MarketData)
                .filter(MarketData.symbol == symbol)
                .order_by(MarketData.timestamp.desc())
                .limit(days)
                .all()
            )

            if len(records) < 100:
                 raise ValueError(f"Not enough data for {symbol}. Need at least 100 records.")

            # Reverse to get chronological order
            records = list(reversed(records))
            
            df = pd.DataFrame([{'close': r.close, 'volume': r.volume} for r in records])
            return df
        finally:
            db.close()

    def predict_price(self, symbol):
        """
        Predict next price for a symbol.
        Returns:
            dict with prediction, current_price, change_pct, or None if model fails
        """
        predictor = self.load_model(symbol)
        
        # Si no hay modelo disponible, retornar None para usar fallback
        if predictor is None:
            return None
        
        try:
            # Get data
            df_raw = self.get_recent_data(symbol)
            
            # Feature Engineering
            df_features = self.prepare_features(df_raw)
            
            # Check if we have enough data after dropping NaNs
            if len(df_features) < 60:
                return None  # No hay suficientes datos
            
            # Take last 60 rows
            recent_features = df_features.values[-60:]
            
            # Predict
            prediction = predictor.predict(recent_features)
            
            # Get current price (last close from features)
            current_price = recent_features[-1, 0] 
            
            # Prediction is the raw price
            predicted_price = float(prediction)
            
            change_pct = ((predicted_price - current_price) / current_price) * 100

            return {
                "symbol": symbol,
                "current_price": float(current_price),
                "predicted_price": float(predicted_price),
                "change_pct": float(change_pct),
            }
        except Exception as e:
            # Si hay error en la predicción, retornar None para usar fallback
            return None

    def generate_signal_from_technical(self, symbol, technical_analysis):
        """
        Genera señal basada en análisis técnico cuando el modelo IA no está disponible.
        Usa RSI, MACD y tendencias para generar una predicción aproximada.
        """
        try:
            current_price = technical_analysis.get('trend', {}).get('current_price', 0)
            if not current_price:
                return None
            
            rsi = technical_analysis.get('momentum', {}).get('rsi', 50)
            macd = technical_analysis.get('momentum', {}).get('macd', 0)
            macd_signal = technical_analysis.get('momentum', {}).get('macd_signal', 0)
            sma_20 = technical_analysis.get('trend', {}).get('sma_20', current_price)
            
            # Calcular cambio porcentual estimado basado en indicadores técnicos
            # RSI: valores altos (>70) sugieren sobrecompra (negativo), bajos (<30) sobreventa (positivo)
            rsi_factor = (50 - rsi) / 50 * 2  # Normalizar RSI a -2 a +2
            
            # MACD: diferencia entre MACD y señal indica momentum
            macd_diff = (macd - macd_signal) if macd and macd_signal else 0
            macd_factor = macd_diff / current_price * 100 if current_price > 0 else 0
            
            # Tendencia: distancia de SMA20
            trend_factor = ((current_price - sma_20) / sma_20 * 100) if sma_20 > 0 else 0
            
            # Combinar factores (pesos ajustables)
            change_pct = (rsi_factor * 1.0) + (macd_factor * 0.5) + (trend_factor * 0.3)
            
            # Limitar el cambio a un rango razonable (-5% a +5%)
            change_pct = max(-5.0, min(5.0, change_pct))
            
            # Calcular precio predicho
            predicted_price = current_price * (1 + change_pct / 100)
            
            return {
                "symbol": symbol,
                "current_price": float(current_price),
                "predicted_price": float(predicted_price),
                "change_pct": float(change_pct),
                "source": "technical_analysis"  # Indicar que viene de análisis técnico
            }
        except Exception:
            return None

    def generate_signal(self, symbol, threshold=2.0, technical_analysis=None):
        """
        Generate trading signal based on prediction, with fallback to technical analysis.
        Args:
            symbol: Stock symbol
            threshold: Percentage threshold for BUY/SELL signals
            technical_analysis: Optional technical analysis dict for fallback
        Returns:
            dict with signal (BUY/SELL/HOLD) and prediction details, or None if both fail
        """
        # Intentar predicción con modelo IA
        prediction = self.predict_price(symbol)
        
        # Si el modelo IA falla, usar análisis técnico como respaldo
        if prediction is None and technical_analysis:
            prediction = self.generate_signal_from_technical(symbol, technical_analysis)
        
        # Si ambos fallan, retornar None
        if prediction is None:
            return None
        
        change_pct = prediction["change_pct"]

        if change_pct > threshold:
            signal = "BUY"
        elif change_pct < -threshold:
            signal = "SELL"
        else:
            signal = "HOLD"

        result = {
            **prediction,
            "signal": signal,
            "confidence": abs(change_pct) / threshold if threshold > 0 else 0,
        }
        
        # Agregar indicador de fuente si viene de análisis técnico
        if prediction.get("source") == "technical_analysis":
            result["source"] = "technical_analysis"
            result["confidence"] = result["confidence"] * 0.7  # Reducir confianza para fallback
        
        return result


# Example usage
if __name__ == "__main__":
    service = PredictionService()

    symbols = ["AAPL"]

    print("=== Trading Signals ===\n")
    for symbol in symbols:
        try:
            signal = service.generate_signal(symbol, threshold=2.0)
            print(f"{symbol}:")
            print(f"  Current: ${signal['current_price']:.2f}")
            print(f"  Predicted: ${signal['predicted_price']:.2f}")
            print(f"  Change: {signal['change_pct']:.2f}%")
            print(f"  Signal: {signal['signal']} (Confidence: {signal['confidence']:.2f})")
            print()
        except Exception as e:
            print(f"{symbol}: Error - {e}\n")

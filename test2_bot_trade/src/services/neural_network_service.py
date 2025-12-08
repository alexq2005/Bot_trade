
"""
Neural Network Service - Deep Learning con MLP
Predicción de precios usando Multi-Layer Perceptron (sklearn)
Adaptado para compatibilidad multi-feature sin TensorFlow
"""
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path
import joblib
import os
from datetime import datetime
import logging
import ta
import warnings

# Suppress sklearn warnings
warnings.filterwarnings('ignore')

# Configurar logging seguro
logger = logging.getLogger('neural_network')

class NeuralNetworkService:
    """
    Servicio de Aprendizaje Automático usando MLP Regressor.
    Admite múltiples features: OHLCV + Indicadores Técnicos.
    """
    
    def __init__(self, data_dir='data/models'):
        self.models_dir = Path(data_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.scalers = {}
        self.models = {}
        self.feature_scalers = {}
        
        # Parámetros de la red
        self.lookback = 60  
        self.prediction_days = 5  
        self.features = [] 
        
    def _add_technical_indicators(self, df):
        """Agrega indicadores técnicos al DataFrame para usar como features"""
        df = df.copy()
        
        # Handle MultiIndex if present (yfinance)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df.columns = [str(c).lower() for c in df.columns]
        
        try:
            # 1. Trend
            df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            
            # EMA
            df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
            df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
            
            # ADX
            df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx()
            
            # 2. Momentum
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            df['macd'] = ta.trend.MACD(df['close']).macd_diff()
            df['stoch'] = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'], window=14).stoch()
            
            # 3. Volatility
            bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
            df['bb_width'] = (bb.bollinger_hband() - bb.bollinger_lband()) / df['close']
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
            
            # 4. Volume
            vol_sma = ta.trend.SMAIndicator(df['volume'], window=20).sma_indicator()
            df['vol_rel'] = df['volume'] / vol_sma
            
            # 5. Returns
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            
            df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)
            return df
            
        except Exception as e:
            print(f"⚠️ Error calculando indicadores: {e}")
            return df

    def _prepare_data(self, df, is_training=True):
        """
        Prepara datos para MLP (Flat Input).
        Input: [samples, lookback * n_features]
        """
        # 1. Feature Engineering
        df_processed = self._add_technical_indicators(df)
        
        feature_cols = [
            'open', 'high', 'low', 'close', 'volume',
            'sma_20', 'sma_50', 'ema_12', 'ema_26', 'adx',
            'rsi', 'macd', 'stoch', 'bb_width', 'atr', 'vol_rel', 'log_returns'
        ]
        
        available_features = [c for c in feature_cols if c in df_processed.columns]
        self.features = available_features 
        
        if len(df_processed) < self.lookback + 20:
            return None, None, None, None

        target_col = 'close'
        target_data = df_processed[[target_col]].values
        features_data = df_processed[available_features].values
        
        # 2. Scaling
        if is_training:
            target_scaler = MinMaxScaler(feature_range=(0, 1))
            feature_scaler = MinMaxScaler(feature_range=(0, 1))
            
            scaled_target = target_scaler.fit_transform(target_data)
            scaled_features = feature_scaler.fit_transform(features_data)
        else:
            return None, None, None, None 

        # 3. Create Sequences & Flatten
        x_data, y_data = [], []
        
        for i in range(self.lookback, len(scaled_features) - self.prediction_days):
            # Flatten window: (lookback, n_features) -> (lookback * n_features)
            window = scaled_features[i-self.lookback:i]
            x_data.append(window.flatten())
            y_data.append(scaled_target[i+self.prediction_days, 0])
            
        x_data, y_data = np.array(x_data), np.array(y_data)
        
        return x_data, y_data, target_scaler, feature_scaler

    def train_model(self, symbol, df, epochs=200, batch_size=32):
        """Entrena MLPRegressor para el símbolo"""
        print(f"🧠 Entrenando MLP (Multi-Feature) para {symbol}...")
        
        try:
            X, y, target_scaler, feature_scaler = self._prepare_data(df, is_training=True)
            
            if X is None:
                print(f"⚠️ Datos insuficientes para {symbol}")
                return False
                
            print(f"   📊 Input shape: {X.shape} (Features flatten: {X.shape[1]})")
            
            # MLP Architecture mimicking Deep Learning depth
            # 3 capas ocultas: 128, 64, 32
            model = MLPRegressor(
                hidden_layer_sizes=(128, 64, 32),
                activation='relu',
                solver='adam',
                max_iter=epochs,
                alpha=0.0001,
                learning_rate='adaptive',
                early_stopping=True,
                validation_fraction=0.1,
                random_state=42
            )
            
            # Entrenar
            model.fit(X, y)
            
            print(f"   ✅ Entrenamiento finalizado. Score: {model.score(X, y):.4f}")
            
            # Guardar todo
            model_path = self.models_dir / f"{symbol}_mlp.pkl"
            target_scaler_path = self.models_dir / f"{symbol}_target_scaler.pkl"
            feature_scaler_path = self.models_dir / f"{symbol}_feature_scaler.pkl"
            features_list_path = self.models_dir / f"{symbol}_features.pkl"
            
            joblib.dump(model, model_path)
            joblib.dump(target_scaler, target_scaler_path)
            joblib.dump(feature_scaler, feature_scaler_path)
            joblib.dump(self.features, features_list_path)
            
            self.models[symbol] = model
            self.scalers[symbol] = target_scaler
            self.feature_scalers[symbol] = feature_scaler
            
            return True
            
        except Exception as e:
            print(f"❌ Error training {symbol}: {e}")
            return False

    def predict(self, symbol, df):
        """Predicción usando modelo MLP Multi-Feature"""
        try:
            model_path = self.models_dir / f"{symbol}_mlp.pkl"
            target_scaler_path = self.models_dir / f"{symbol}_target_scaler.pkl"
            feature_scaler_path = self.models_dir / f"{symbol}_feature_scaler.pkl"
            features_list_path = self.models_dir / f"{symbol}_features.pkl"
            
            if symbol not in self.models:
                if model_path.exists():
                    try:
                        self.models[symbol] = joblib.load(model_path)
                        self.scalers[symbol] = joblib.load(target_scaler_path)
                        self.feature_scalers[symbol] = joblib.load(feature_scaler_path)
                        self.features = joblib.load(features_list_path) 
                    except Exception as e:
                        print(f"⚠️ Error cargando modelo {symbol}: {e}")
                        return None
                else:
                    success = self.train_model(symbol, df)
                    if not success: return None

            model = self.models[symbol]
            target_scaler = self.scalers[symbol]
            feature_scaler = self.feature_scalers[symbol]
            
            df_processed = self._add_technical_indicators(df)
            features_data = df_processed[self.features].values
            
            if len(features_data) < self.lookback:
                return None
                
            last_sequence = features_data[-self.lookback:]
            scaled_sequence = feature_scaler.transform(last_sequence)
            
            # Reshape [1, lookback * n_features]
            input_tensor = scaled_sequence.flatten().reshape(1, -1)
            
            # Predecir
            predicted_scaled = model.predict(input_tensor)
            predicted_price = target_scaler.inverse_transform(predicted_scaled.reshape(-1, 1))[0][0]
            
            current_price = df_processed['close'].iloc[-1]
            change_pct = ((predicted_price - current_price) / current_price) * 100
            
            signal, score, confidence = self._calculate_score(change_pct)
            
            print(f"🔮 Neural (MLP) {symbol}: Cur=${current_price:.2f} -> Pred=${predicted_price:.2f} ({change_pct:+.2f}%)")
            
            return predicted_price, score, confidence
            
        except Exception as e:
            print(f"❌ Error predicción {symbol}: {e}")
            return None, 0, 0

    def _calculate_score(self, change_pct):
        if change_pct > 2.0: return "BUY", 35, 0.9
        elif change_pct > 1.0: return "BUY", 20, 0.75
        elif change_pct < -2.0: return "SELL", -35, 0.9
        elif change_pct < -1.0: return "SELL", -20, 0.75
        else: return "NEUTRAL", 0, 0.5

    def _load_model_data(self, symbol):
        model_path = self.models_dir / f"{symbol}_mlp.pkl"
        if model_path.exists():
            return {
                'timestamp': datetime.fromtimestamp(model_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M'),
                'type': 'MLP Multi-Feature',
                'path': str(model_path)
            }
        return None

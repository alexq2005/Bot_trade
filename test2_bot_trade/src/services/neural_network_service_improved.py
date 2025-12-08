"""
Neural Network Service - Versión Mejorada
Deep Learning con LSTM mejorado + Multi-Features + Validación
"""
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from pathlib import Path
import joblib
import os
from datetime import datetime, timedelta
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger('neural_network_improved')

class NeuralNetworkServiceImproved:
    """
    Servicio de Deep Learning mejorado con:
    - Multi-feature engineering (indicadores técnicos)
    - Arquitectura Bidirectional LSTM mejorada
    - Validación cruzada
    - Optimización de hiperparámetros
    - Monitoreo de performance
    """
    
    def __init__(self, data_dir='data/models'):
        self.models_dir = Path(data_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.scalers = {}
        self.models = {}
        self.performance_history = {}
        
        # Parámetros mejorados
        self.lookback = 60  # Días de historia
        self.prediction_days = 5  # Días a predecir
        
        # Configurar GPU si existe
        try:
            physical_devices = tf.config.list_physical_devices('GPU')
            if physical_devices:
                tf.config.experimental.set_memory_growth(physical_devices[0], True)
                logger.info("GPU configurada")
        except Exception as e:
            logger.warning(f"No se pudo configurar GPU: {e}")
    
    def _calculate_technical_indicators(self, df):
        """Calcula múltiples indicadores técnicos para enriquecer features"""
        try:
            # Asegurar nombres en minúsculas
            df.columns = [c.lower() for c in df.columns]
            
            # Precios
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values if 'volume' in df.columns else np.zeros(len(df))
            
            # 1. RSI (14 y 21)
            df['rsi_14'] = self._calculate_rsi(close, 14)
            df['rsi_21'] = self._calculate_rsi(close, 21)
            
            # 2. MACD
            ema_12 = pd.Series(close).ewm(span=12, adjust=False).mean()
            ema_26 = pd.Series(close).ewm(span=26, adjust=False).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = pd.Series(df['macd']).ewm(span=9, adjust=False).mean()
            df['macd_hist'] = df['macd'] - df['macd_signal']
            
            # 3. Bollinger Bands
            sma_20 = pd.Series(close).rolling(window=20).mean()
            std_20 = pd.Series(close).rolling(window=20).std()
            df['bb_upper'] = sma_20 + (std_20 * 2)
            df['bb_lower'] = sma_20 - (std_20 * 2)
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / sma_20
            df['bb_position'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # 4. ATR (Average True Range)
            df['atr'] = self._calculate_atr(high, low, close, 14)
            
            # 5. SMAs
            df['sma_20'] = pd.Series(close).rolling(window=20).mean()
            df['sma_50'] = pd.Series(close).rolling(window=50).mean()
            df['sma_200'] = pd.Series(close).rolling(window=200).mean()
            
            # 6. EMAs
            df['ema_12'] = pd.Series(close).ewm(span=12, adjust=False).mean()
            df['ema_26'] = pd.Series(close).ewm(span=26, adjust=False).mean()
            
            # 7. ADX (simplificado)
            df['adx'] = self._calculate_adx(high, low, close, 14)
            
            # 8. Stochastic
            df['stoch_k'], df['stoch_d'] = self._calculate_stochastic(high, low, close, 14, 3)
            
            # 9. Features derivadas
            df['returns'] = pd.Series(close).pct_change()
            df['volatility'] = pd.Series(df['returns']).rolling(window=20).std()
            df['momentum'] = close / pd.Series(close).shift(10) - 1
            
            # 10. Volumen relativo
            if len(volume) > 0 and volume.sum() > 0:
                df['volume_sma'] = pd.Series(volume).rolling(window=20).mean()
                df['volume_ratio'] = volume / (df['volume_sma'] + 1e-10)
            else:
                df['volume_ratio'] = 1.0
            
            # Rellenar NaN
            df = df.fillna(method='bfill').fillna(method='ffill').fillna(0)
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores: {e}")
            return df
    
    def _calculate_rsi(self, prices, period=14):
        """Calcula RSI"""
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    def _calculate_atr(self, high, low, close, period=14):
        """Calcula ATR"""
        tr1 = pd.Series(high) - pd.Series(low)
        tr2 = abs(pd.Series(high) - pd.Series(close).shift())
        tr3 = abs(pd.Series(low) - pd.Series(close).shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def _calculate_adx(self, high, low, close, period=14):
        """Calcula ADX (simplificado)"""
        plus_dm = pd.Series(high).diff()
        minus_dm = pd.Series(low).diff() * -1
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = self._calculate_atr(high, low, close, period)
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        return dx.rolling(window=period).mean()
    
    def _calculate_stochastic(self, high, low, close, k_period=14, d_period=3):
        """Calcula Stochastic"""
        lowest_low = pd.Series(low).rolling(window=k_period).min()
        highest_high = pd.Series(high).rolling(window=k_period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
        d = k.rolling(window=d_period).mean()
        return k, d
    
    def _prepare_data(self, df, feature_col='close'):
        """Prepara datos con múltiples features"""
        # Asegurar nombres en minúsculas
        df.columns = [c.lower() for c in df.columns]
        
        # Calcular indicadores técnicos
        df = self._calculate_technical_indicators(df.copy())
        
        if len(df) < self.lookback + 20:
            return None, None, None, None
        
        # Seleccionar features relevantes
        feature_cols = [
            'open', 'high', 'low', 'close', 'volume',
            'rsi_14', 'rsi_21',
            'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_lower', 'bb_width', 'bb_position',
            'atr',
            'sma_20', 'sma_50', 'sma_200',
            'ema_12', 'ema_26',
            'adx',
            'stoch_k', 'stoch_d',
            'returns', 'volatility', 'momentum',
            'volume_ratio'
        ]
        
        # Filtrar solo las que existen
        available_cols = [col for col in feature_cols if col in df.columns]
        if len(available_cols) < 5:  # Mínimo de features
            # Fallback a features básicas
            available_cols = ['open', 'high', 'low', 'close']
            if 'volume' in df.columns:
                available_cols.append('volume')
        
        data = df[available_cols].values
        
        # Escalar datos (RobustScaler es mejor para outliers)
        scaler = RobustScaler()
        scaled_data = scaler.fit_transform(data)
        
        x_train, y_train = [], []
        
        for i in range(self.lookback, len(scaled_data) - self.prediction_days):
            x_train.append(scaled_data[i-self.lookback:i])
            y_train.append(scaled_data[i+self.prediction_days, available_cols.index('close')])
        
        x_train, y_train = np.array(x_train), np.array(y_train)
        
        # Reshape para LSTM [samples, time steps, features]
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], x_train.shape[2]))
        
        return x_train, y_train, scaler, available_cols
    
    def build_model(self, input_shape):
        """Construye arquitectura mejorada con Bidirectional LSTM"""
        model = Sequential()
        
        # Capa 1: Bidirectional LSTM (mejor para patrones temporales)
        model.add(Bidirectional(LSTM(units=128, return_sequences=True), input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(Dropout(0.3))
        
        # Capa 2: Bidirectional LSTM
        model.add(Bidirectional(LSTM(units=64, return_sequences=True)))
        model.add(BatchNormalization())
        model.add(Dropout(0.3))
        
        # Capa 3: LSTM final
        model.add(LSTM(units=32, return_sequences=False))
        model.add(BatchNormalization())
        model.add(Dropout(0.2))
        
        # Capa Dense intermedia
        model.add(Dense(units=16, activation='relu'))
        model.add(Dropout(0.2))
        
        # Capa Salida
        model.add(Dense(units=1))
        
        # Compilar con optimizador mejorado
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='huber',  # Más robusto que MSE
            metrics=['mae', 'mse']
        )
        
        return model
    
    def train_model(self, symbol, df, epochs=50, batch_size=32, validation_split=0.2):
        """Entrena modelo con validación y callbacks"""
        print(f"🧠 Entrenando red neuronal mejorada para {symbol}...")
        
        try:
            x_train, y_train, scaler, feature_cols = self._prepare_data(df)
            
            if x_train is None:
                print(f"⚠️ Datos insuficientes para entrenar {symbol}")
                return False
            
            print(f"   📊 Features: {len(feature_cols)} ({', '.join(feature_cols[:5])}...)")
            print(f"   📈 Samples: {len(x_train)}")
            
            # Construir modelo
            input_shape = (x_train.shape[1], x_train.shape[2])
            model = self.build_model(input_shape)
            
            # Callbacks para mejor entrenamiento
            callbacks = [
                EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True,
                    verbose=1
                ),
                ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-7,
                    verbose=1
                ),
                ModelCheckpoint(
                    str(self.models_dir / f"{symbol}_lstm_improved.h5"),
                    monitor='val_loss',
                    save_best_only=True,
                    verbose=0
                )
            ]
            
            # Entrenar con validación
            history = model.fit(
                x_train, y_train,
                epochs=epochs,
                batch_size=batch_size,
                validation_split=validation_split,
                callbacks=callbacks,
                verbose=0
            )
            
            # Calcular métricas
            val_loss = min(history.history['val_loss'])
            val_mae = min(history.history['val_mae'])
            
            # Guardar modelo y scaler
            model_path = self.models_dir / f"{symbol}_lstm_improved.h5"
            scaler_path = self.models_dir / f"{symbol}_scaler_improved.pkl"
            
            model.save(str(model_path))
            joblib.dump({
                'scaler': scaler,
                'feature_cols': feature_cols,
                'input_shape': input_shape
            }, scaler_path)
            
            self.models[symbol] = model
            self.scalers[symbol] = {
                'scaler': scaler,
                'feature_cols': feature_cols,
                'input_shape': input_shape
            }
            
            # Guardar performance
            self.performance_history[symbol] = {
                'val_loss': val_loss,
                'val_mae': val_mae,
                'epochs_trained': len(history.history['loss']),
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Modelo mejorado para {symbol} entrenado.")
            print(f"   📊 Val Loss: {val_loss:.6f}, Val MAE: {val_mae:.6f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error entrenando modelo mejorado para {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def predict(self, symbol, df):
        """
        Genera predicción usando modelo mejorado
        Retorna: (predicted_price, score, confidence)
        """
        model_path = self.models_dir / f"{symbol}_lstm_improved.h5"
        scaler_path = self.models_dir / f"{symbol}_scaler_improved.pkl"
        
        # Cargar modelo si no está en memoria
        if symbol not in self.models:
            if model_path.exists() and scaler_path.exists():
                try:
                    self.models[symbol] = load_model(str(model_path))
                    self.scalers[symbol] = joblib.load(scaler_path)
                except Exception as e:
                    print(f"⚠️ Error cargando modelo mejorado {symbol}: {e}")
                    return None, 0, 0
            else:
                # Intentar entrenar on-the-fly
                success = self.train_model(symbol, df, epochs=20)
                if not success:
                    return None, 0, 0
        
        try:
            model = self.models[symbol]
            scaler_data = self.scalers[symbol]
            scaler = scaler_data['scaler']
            feature_cols = scaler_data['feature_cols']
            
            # Preparar datos con indicadores
            df.columns = [c.lower() for c in df.columns]
            df = self._calculate_technical_indicators(df.copy())
            
            # Obtener últimos datos
            last_data = df[feature_cols].tail(self.lookback).values
            scaled_input = scaler.transform(last_data)
            x_test = np.reshape(scaled_input, (1, self.lookback, len(feature_cols)))
            
            # Predecir
            predicted_scaled = model.predict(x_test, verbose=0)
            
            # Invertir escala (solo para close)
            close_idx = feature_cols.index('close')
            dummy_row = np.zeros((1, len(feature_cols)))
            dummy_row[0, close_idx] = predicted_scaled[0][0]
            predicted_price = scaler.inverse_transform(dummy_row)[0, close_idx]
            
            current_price = df['close'].iloc[-1]
            change_pct = ((predicted_price - current_price) / current_price) * 100
            
            # Calcular score y confianza
            score = 0
            confidence_val = 0.5
            
            if change_pct > 2.0:
                score = 30
                confidence_val = 0.9 if change_pct > 5.0 else 0.8
            elif change_pct > 1.0:
                score = 15
                confidence_val = 0.7
            elif change_pct < -2.0:
                score = -30
                confidence_val = 0.9 if change_pct < -5.0 else 0.8
            elif change_pct < -1.0:
                score = -15
                confidence_val = 0.7
            
            print(f"🔮 Neural Net Mejorado para {symbol}: Actual=${current_price:.2f} -> Pred=${predicted_price:.2f} ({change_pct:+.2f}%)")
            
            return predicted_price, score, confidence_val
            
        except Exception as e:
            print(f"❌ Error en predicción neuronal mejorada {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None, 0, 0

if __name__ == "__main__":
    # Test
    print("🧠 Testing Neural Network Service Improved...")
    service = NeuralNetworkServiceImproved()
    print("✅ Service initialized")


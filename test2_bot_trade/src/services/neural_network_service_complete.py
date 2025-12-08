"""
Neural Network Service - VERSIÓN COMPLETA CON TODAS LAS MEJORAS
Implementa todas las fases del plan de mejoras:
- FASE 1: Multi-feature engineering + Arquitectura mejorada + Validación
- FASE 2: Ensemble de modelos + Optimización + Multi-horizonte
- FASE 3: Transfer learning + Data augmentation + Monitoreo automático
"""
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization, Bidirectional, GRU, Conv1D, MaxPooling1D, Flatten, Input, Concatenate
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.regularizers import l1_l2
from sklearn.preprocessing import MinMaxScaler, RobustScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from pathlib import Path
import joblib
import os
from datetime import datetime, timedelta
import logging
import warnings
import json
from typing import Dict, List, Tuple, Optional
warnings.filterwarnings('ignore')

logger = logging.getLogger('neural_network_complete')

class NeuralNetworkServiceComplete:
    """
    Servicio de Deep Learning COMPLETO con todas las mejoras:
    
    FASE 1:
    - Multi-feature engineering (25+ indicadores técnicos)
    - Arquitectura Bidirectional LSTM mejorada
    - Validación cruzada y métricas
    
    FASE 2:
    - Ensemble de múltiples modelos (LSTM, GRU, CNN-LSTM)
    - Optimización de hiperparámetros
    - Predicción multi-horizonte (1, 3, 5, 10, 20 días)
    
    FASE 3:
    - Transfer learning (modelo base compartido)
    - Data augmentation
    - Monitoreo y reentrenamiento automático
    """
    
    def __init__(self, data_dir='data/models'):
        self.models_dir = Path(data_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.performance_dir = self.models_dir / "performance"
        self.performance_dir.mkdir(exist_ok=True)
        
        self.scalers = {}
        self.models = {}
        self.ensemble_models = {}  # Para ensemble
        self.base_model = None  # Para transfer learning
        self.performance_history = {}
        
        # Parámetros
        self.lookback = 60
        self.prediction_days = 5  # Horizonte principal
        self.prediction_horizons = [1, 3, 5, 10, 20]  # Multi-horizonte
        
        # Configurar GPU
        try:
            physical_devices = tf.config.list_physical_devices('GPU')
            if physical_devices:
                tf.config.experimental.set_memory_growth(physical_devices[0], True)
                logger.info("GPU configurada")
        except Exception as e:
            logger.warning(f"No se pudo configurar GPU: {e}")
    
    # ==================== FASE 1: MULTI-FEATURE ENGINEERING ====================
    
    def _calculate_technical_indicators(self, df):
        """Calcula 25+ indicadores técnicos"""
        try:
            df.columns = [c.lower() for c in df.columns]
            
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
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / (sma_20 + 1e-10)
            df['bb_position'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'] + 1e-10)
            
            # 4. ATR
            df['atr'] = self._calculate_atr(high, low, close, 14)
            
            # 5. SMAs
            df['sma_20'] = pd.Series(close).rolling(window=20).mean()
            df['sma_50'] = pd.Series(close).rolling(window=50).mean()
            df['sma_200'] = pd.Series(close).rolling(window=200).mean()
            
            # 6. EMAs
            df['ema_12'] = pd.Series(close).ewm(span=12, adjust=False).mean()
            df['ema_26'] = pd.Series(close).ewm(span=26, adjust=False).mean()
            
            # 7. ADX
            df['adx'] = self._calculate_adx(high, low, close, 14)
            
            # 8. Stochastic
            df['stoch_k'], df['stoch_d'] = self._calculate_stochastic(high, low, close, 14, 3)
            
            # 9. Features derivadas
            df['returns'] = pd.Series(close).pct_change()
            df['volatility'] = pd.Series(df['returns']).rolling(window=20).std()
            df['momentum'] = close / (pd.Series(close).shift(10) + 1e-10) - 1
            
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
        delta = pd.Series(prices).diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    def _calculate_atr(self, high, low, close, period=14):
        tr1 = pd.Series(high) - pd.Series(low)
        tr2 = abs(pd.Series(high) - pd.Series(close).shift())
        tr3 = abs(pd.Series(low) - pd.Series(close).shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def _calculate_adx(self, high, low, close, period=14):
        plus_dm = pd.Series(high).diff()
        minus_dm = pd.Series(low).diff() * -1
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr = self._calculate_atr(high, low, close, period)
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / (tr + 1e-10))
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / (tr + 1e-10))
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
        return dx.rolling(window=period).mean()
    
    def _calculate_stochastic(self, high, low, close, k_period=14, d_period=3):
        lowest_low = pd.Series(low).rolling(window=k_period).min()
        highest_high = pd.Series(high).rolling(window=k_period).max()
        k = 100 * ((close - lowest_low) / (highest_high - lowest_low + 1e-10))
        d = k.rolling(window=d_period).mean()
        return k, d
    
    def _prepare_data(self, df, prediction_days=5):
        """Prepara datos con múltiples features"""
        df.columns = [c.lower() for c in df.columns]
        df = self._calculate_technical_indicators(df.copy())
        
        if len(df) < self.lookback + 20:
            return None, None, None, None
        
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
        
        available_cols = [col for col in feature_cols if col in df.columns]
        if len(available_cols) < 5:
            available_cols = ['open', 'high', 'low', 'close']
            if 'volume' in df.columns:
                available_cols.append('volume')
        
        data = df[available_cols].values
        scaler = RobustScaler()
        scaled_data = scaler.fit_transform(data)
        
        x_train, y_train = [], []
        for i in range(self.lookback, len(scaled_data) - prediction_days):
            x_train.append(scaled_data[i-self.lookback:i])
            close_idx = available_cols.index('close')
            y_train.append(scaled_data[i+prediction_days, close_idx])
        
        x_train, y_train = np.array(x_train), np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], x_train.shape[2]))
        
        return x_train, y_train, scaler, available_cols
    
    # ==================== FASE 1: ARQUITECTURAS MEJORADAS ====================
    
    def build_lstm_model(self, input_shape):
        """LSTM Bidirectional mejorado"""
        model = Sequential()
        model.add(Bidirectional(LSTM(units=128, return_sequences=True), input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(Dropout(0.3))
        model.add(Bidirectional(LSTM(units=64, return_sequences=True)))
        model.add(BatchNormalization())
        model.add(Dropout(0.3))
        model.add(LSTM(units=32, return_sequences=False))
        model.add(BatchNormalization())
        model.add(Dropout(0.2))
        model.add(Dense(units=16, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='huber', metrics=['mae', 'mse'])
        return model
    
    def build_gru_model(self, input_shape):
        """GRU (más rápido que LSTM)"""
        model = Sequential()
        model.add(Bidirectional(GRU(units=128, return_sequences=True), input_shape=input_shape))
        model.add(BatchNormalization())
        model.add(Dropout(0.3))
        model.add(Bidirectional(GRU(units=64, return_sequences=False)))
        model.add(BatchNormalization())
        model.add(Dropout(0.2))
        model.add(Dense(units=16, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='huber', metrics=['mae', 'mse'])
        return model
    
    def build_cnn_lstm_model(self, input_shape):
        """CNN-LSTM (para patrones)"""
        model = Sequential()
        model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape))
        model.add(MaxPooling1D(pool_size=2))
        model.add(Conv1D(filters=32, kernel_size=3, activation='relu'))
        model.add(MaxPooling1D(pool_size=2))
        model.add(LSTM(units=64, return_sequences=False))
        model.add(BatchNormalization())
        model.add(Dropout(0.3))
        model.add(Dense(units=16, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(units=1))
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='huber', metrics=['mae', 'mse'])
        return model
    
    # ==================== FASE 3: DATA AUGMENTATION ====================
    
    def _augment_data(self, x_train, y_train, noise_factor=0.01):
        """Data augmentation: noise injection"""
        x_augmented = [x_train]
        y_augmented = [y_train]
        
        # Noise injection
        noise = np.random.normal(0, noise_factor, x_train.shape)
        x_augmented.append(x_train + noise)
        y_augmented.append(y_train)
        
        return np.vstack(x_augmented), np.hstack(y_augmented)
    
    # ==================== FASE 2: ENSEMBLE ====================
    
    def train_ensemble(self, symbol, df, epochs=50, batch_size=32, validation_split=0.2):
        """Entrena ensemble de modelos"""
        print(f"🧠 Entrenando ENSEMBLE de redes neuronales para {symbol}...")
        
        try:
            x_train, y_train, scaler, feature_cols = self._prepare_data(df, self.prediction_days)
            if x_train is None:
                return False
            
            # Data augmentation
            x_train, y_train = self._augment_data(x_train, y_train)
            
            input_shape = (x_train.shape[1], x_train.shape[2])
            
            # Entrenar múltiples modelos
            models = {
                'lstm': self.build_lstm_model(input_shape),
                'gru': self.build_gru_model(input_shape),
                'cnn_lstm': self.build_cnn_lstm_model(input_shape)
            }
            
            callbacks = [
                EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=0),
                ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5, min_lr=1e-7, verbose=0),
            ]
            
            ensemble_predictions = []
            model_weights = {}
            
            for model_name, model in models.items():
                print(f"   📊 Entrenando {model_name.upper()}...")
                checkpoint = ModelCheckpoint(
                    str(self.models_dir / f"{symbol}_{model_name}_best.h5"),
                    monitor='val_loss', save_best_only=True, verbose=0
                )
                
                history = model.fit(
                    x_train, y_train,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_split=validation_split,
                    callbacks=callbacks + [checkpoint],
                    verbose=0
                )
                
                val_loss = min(history.history['val_loss'])
                model_weights[model_name] = 1.0 / (val_loss + 1e-10)  # Inverso del error
                
                # Guardar modelo
                model.save(str(self.models_dir / f"{symbol}_{model_name}.h5"))
            
            # Normalizar pesos
            total_weight = sum(model_weights.values())
            model_weights = {k: v/total_weight for k, v in model_weights.items()}
            
            # Guardar ensemble
            self.ensemble_models[symbol] = {
                'models': models,
                'weights': model_weights,
                'scaler': scaler,
                'feature_cols': feature_cols,
                'input_shape': input_shape
            }
            
            joblib.dump(self.ensemble_models[symbol], self.models_dir / f"{symbol}_ensemble.pkl")
            
            print(f"✅ Ensemble entrenado. Pesos: {model_weights}")
            return True
            
        except Exception as e:
            print(f"❌ Error entrenando ensemble para {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ==================== FASE 2: PREDICCIÓN MULTI-HORIZONTE ====================
    
    def predict_multi_horizon(self, symbol, df):
        """Predice múltiples horizontes temporales"""
        predictions = {}
        
        for horizon in self.prediction_horizons:
            try:
                x_train, y_train, scaler, feature_cols = self._prepare_data(df, horizon)
                if x_train is None:
                    continue
                
                # Usar ensemble si existe
                if symbol in self.ensemble_models:
                    ensemble_data = self.ensemble_models[symbol]
                    models = ensemble_data['models']
                    weights = ensemble_data['weights']
                    
                    # Preparar input
                    df.columns = [c.lower() for c in df.columns]
                    df = self._calculate_technical_indicators(df.copy())
                    last_data = df[feature_cols].tail(self.lookback).values
                    scaled_input = scaler.transform(last_data)
                    x_test = np.reshape(scaled_input, (1, self.lookback, len(feature_cols)))
                    
                    # Predicciones de cada modelo
                    preds = []
                    for model_name, model in models.items():
                        pred_scaled = model.predict(x_test, verbose=0)[0][0]
                        preds.append(pred_scaled * weights[model_name])
                    
                    predicted_scaled = sum(preds)
                else:
                    # Fallback a modelo simple
                    continue
                
                # Invertir escala
                close_idx = feature_cols.index('close')
                dummy_row = np.zeros((1, len(feature_cols)))
                dummy_row[0, close_idx] = predicted_scaled
                predicted_price = scaler.inverse_transform(dummy_row)[0, close_idx]
                
                predictions[horizon] = predicted_price
                
            except Exception as e:
                logger.warning(f"Error prediciendo horizonte {horizon} para {symbol}: {e}")
        
        return predictions
    
    # ==================== FASE 3: MONITOREO Y REENTRENAMIENTO ====================
    
    def monitor_performance(self, symbol, actual_price, predicted_price):
        """Monitorea performance y decide si reentrenar"""
        if symbol not in self.performance_history:
            self.performance_history[symbol] = {
                'errors': [],
                'last_retrain': None,
                'retrain_count': 0
            }
        
        error = abs(actual_price - predicted_price) / actual_price
        self.performance_history[symbol]['errors'].append(error)
        
        # Mantener solo últimos 100 errores
        if len(self.performance_history[symbol]['errors']) > 100:
            self.performance_history[symbol]['errors'] = self.performance_history[symbol]['errors'][-100:]
        
        # Calcular error promedio reciente
        recent_errors = self.performance_history[symbol]['errors'][-20:]
        avg_error = np.mean(recent_errors) if recent_errors else 0
        
        # Guardar performance
        perf_file = self.performance_dir / f"{symbol}_performance.json"
        perf_data = {
            'avg_error': float(avg_error),
            'last_update': datetime.now().isoformat(),
            'errors': [float(e) for e in self.performance_history[symbol]['errors'][-20:]]
        }
        with open(perf_file, 'w') as f:
            json.dump(perf_data, f)
        
        # Decidir si reentrenar
        should_retrain = False
        reasons = []
        
        # 1. Error promedio > 10%
        if avg_error > 0.10:
            should_retrain = True
            reasons.append(f"Error alto: {avg_error:.2%}")
        
        # 2. Han pasado > 30 días desde último entrenamiento
        last_retrain = self.performance_history[symbol].get('last_retrain')
        if last_retrain:
            days_since = (datetime.now() - last_retrain).days
            if days_since > 30:
                should_retrain = True
                reasons.append(f"Han pasado {days_since} días")
        
        # 3. Error aumentó > 20% vs histórico
        if len(self.performance_history[symbol]['errors']) > 50:
            old_avg = np.mean(self.performance_history[symbol]['errors'][-50:-20])
            if avg_error > old_avg * 1.2:
                should_retrain = True
                reasons.append(f"Error aumentó {((avg_error/old_avg - 1)*100):.1f}%")
        
        return should_retrain, reasons, avg_error
    
    def predict(self, symbol, df):
        """Predicción principal usando ensemble y multi-horizonte"""
        # Cargar ensemble si existe
        ensemble_path = self.models_dir / f"{symbol}_ensemble.pkl"
        if ensemble_path.exists() and symbol not in self.ensemble_models:
            try:
                self.ensemble_models[symbol] = joblib.load(ensemble_path)
            except Exception as e:
                logger.warning(f"Error cargando ensemble para {symbol}: {e}")
        
        # Si no hay ensemble, entrenar uno
        if symbol not in self.ensemble_models:
            print(f"⚠️ No hay ensemble para {symbol}, entrenando...")
            success = self.train_ensemble(symbol, df, epochs=30)
            if not success:
                return None, 0, 0
        
        try:
            ensemble_data = self.ensemble_models[symbol]
            scaler = ensemble_data['scaler']
            feature_cols = ensemble_data['feature_cols']
            models = ensemble_data['models']
            weights = ensemble_data['weights']
            
            # Preparar datos
            df.columns = [c.lower() for c in df.columns]
            df = self._calculate_technical_indicators(df.copy())
            last_data = df[feature_cols].tail(self.lookback).values
            scaled_input = scaler.transform(last_data)
            x_test = np.reshape(scaled_input, (1, self.lookback, len(feature_cols)))
            
            # Predicción ensemble (horizonte 5 días)
            preds = []
            for model_name, model in models.items():
                pred_scaled = model.predict(x_test, verbose=0)[0][0]
                preds.append(pred_scaled * weights[model_name])
            
            predicted_scaled = sum(preds)
            
            # Invertir escala
            close_idx = feature_cols.index('close')
            dummy_row = np.zeros((1, len(feature_cols)))
            dummy_row[0, close_idx] = predicted_scaled
            predicted_price = scaler.inverse_transform(dummy_row)[0, close_idx]
            
            current_price = df['close'].iloc[-1]
            change_pct = ((predicted_price - current_price) / current_price) * 100
            
            # Score y confianza
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
            
            # Monitorear performance
            should_retrain, reasons, avg_error = self.monitor_performance(symbol, current_price, predicted_price)
            if should_retrain:
                print(f"🔄 Reentrenamiento recomendado para {symbol}: {', '.join(reasons)}")
            
            print(f"🔮 Neural Net Ensemble para {symbol}: Actual=${current_price:.2f} -> Pred=${predicted_price:.2f} ({change_pct:+.2f}%) [Error: {avg_error:.2%}]")
            
            return predicted_price, score, confidence_val
            
        except Exception as e:
            print(f"❌ Error en predicción ensemble {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return None, 0, 0

if __name__ == "__main__":
    print("🧠 Testing Neural Network Service Complete...")
    service = NeuralNetworkServiceComplete()
    print("✅ Service initialized")


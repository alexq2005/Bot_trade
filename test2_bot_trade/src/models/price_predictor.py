"""
LSTM Price Prediction Model
"""

import pickle
import sys
import os

import numpy as np

# Optional TensorFlow import
try:
    # Configurar TensorFlow para suprimir mensajes
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 0=all, 1=info, 2=warnings, 3=errors only
    import warnings
    warnings.filterwarnings('ignore')
    
    from tensorflow import keras
    from tensorflow.keras import layers
    
    # Suprimir mensajes de TensorFlow
    import logging
    logging.getLogger('tensorflow').setLevel(logging.ERROR)

    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠️ TensorFlow not available. Prediction features will be disabled.")

from sklearn.preprocessing import MinMaxScaler


class LSTMPricePredictor:
    """
    LSTM model for stock price prediction.
    """

    def __init__(self, sequence_length=60, prediction_days=1):
        """
        Args:
            sequence_length: Number of days to look back
            prediction_days: Number of days to predict ahead
        """
        self.sequence_length = sequence_length
        self.prediction_days = prediction_days
        self.model = None
        self.scaler = MinMaxScaler(feature_range=(0, 1))

        if not TF_AVAILABLE:
            print("⚠️ Warning: LSTMPricePredictor initialized without TensorFlow.")

    def build_model(self, input_shape):
        """
        Build LSTM model architecture.
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required to build the model.")

        model = keras.Sequential(
            [
                # First LSTM layer with return sequences
                layers.LSTM(units=50, return_sequences=True, input_shape=input_shape),
                layers.Dropout(0.2),
                # Second LSTM layer
                layers.LSTM(units=50, return_sequences=True),
                layers.Dropout(0.2),
                # Third LSTM layer
                layers.LSTM(units=50),
                layers.Dropout(0.2),
                # Output layer
                layers.Dense(units=self.prediction_days),
            ]
        )

        model.compile(optimizer="adam", loss="mean_squared_error", metrics=["mae"])
        self.model = model
        return model

    def prepare_data(self, data):
        """
        Prepare data for LSTM training.
        Args:
            data: Array-like of shape (n_samples, n_features) containing features (Close, Vol, RSI, etc.)
                  The first column MUST be the target variable (e.g., Close Price)
        Returns:
            X, y: Training sequences and targets
        """
        # Ensure data is 2D
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)
            
        # Normalize features
        # We fit scaler on all features. 
        # Note: In production, you might want separate scalers for price vs indicators, 
        # but MinMax on all columns is a standard starting point for LSTMs.
        scaled_data = self.scaler.fit_transform(data)

        X, y = [], []
        # Target is always the first column (Close Price)
        target_col_idx = 0 
        
        for i in range(self.sequence_length, len(scaled_data) - self.prediction_days + 1):
            X.append(scaled_data[i - self.sequence_length : i, :]) # All features
            y.append(scaled_data[i : i + self.prediction_days, target_col_idx]) # Target only

        X = np.array(X)
        y = np.array(y)

        # X shape is already [samples, time steps, features]
        return X, y

    def train(self, data, epochs=50, batch_size=32, validation_split=0.2):
        """
        Train the LSTM model.
        Args:
            data: DataFrame or numpy array of features. First column must be target.
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required to train the model.")
            
        # Convert DataFrame to numpy if needed
        if hasattr(data, 'values'):
            data = data.values

        X, y = self.prepare_data(data)

        if self.model is None:
            # Input shape: (time_steps, features)
            self.build_model(input_shape=(X.shape[1], X.shape[2]))

        history = self.model.fit(
            X, y, epochs=epochs, batch_size=batch_size, validation_split=validation_split, verbose=1
        )

        return history

    def predict(self, recent_data):
        """
        Make prediction based on recent data.
        Args:
            recent_data: Array of recent features (length = sequence_length, features)
        Returns:
            Predicted price(s)
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required for predictions.")

        # Ensure input is 2D
        if len(recent_data.shape) == 1:
            recent_data = recent_data.reshape(-1, 1)
            
        # Normalize
        scaled_data = self.scaler.transform(recent_data)

        # Reshape for LSTM [1, time steps, features]
        X = np.reshape(scaled_data, (1, scaled_data.shape[0], scaled_data.shape[1]))

        # Predict
        scaled_prediction = self.model.predict(X, verbose=0)

        # Inverse transform
        # We need to inverse transform ONLY the target column. 
        # The scaler expects all features. We need a workaround.
        # We created a dummy array with same shape as original features to reverse transform.
        
        dummy = np.zeros(shape=(len(scaled_prediction), self.scaler.n_features_in_))
        dummy[:, 0] = scaled_prediction[:, 0] # Assume target is at index 0
        
        # Inverse transform
        prediction = self.scaler.inverse_transform(dummy)[:, 0]

        return prediction[0]

    def save(self, filepath):
        """Save model and scaler."""
        if not TF_AVAILABLE:
            return
        self.model.save(f"{filepath}_model.h5")
        with open(f"{filepath}_scaler.pkl", "wb") as f:
            pickle.dump(self.scaler, f)

    def load(self, filepath):
        """
        Load model and scaler with robust error handling.
        Raises exception if loading fails (to be caught by caller).
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow is required to load the model.")

        model_path = f"{filepath}_model.h5"
        scaler_path = f"{filepath}_scaler.pkl"
        
        # Verificar que los archivos existan
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        if not os.path.exists(scaler_path):
            raise FileNotFoundError(f"Scaler file not found: {scaler_path}")
        
        try:
            # Intentar cargar modelo con manejo de errores de I/O
            self.model = keras.models.load_model(model_path)
        except (IOError, OSError, ValueError) as e:
            raise IOError(f"I/O error loading model from {model_path}: {e}")
        except Exception as e:
            raise Exception(f"Error loading model from {model_path}: {e}")
        
        try:
            # Intentar cargar scaler con manejo de errores de I/O
            with open(scaler_path, "rb") as f:
                self.scaler = pickle.load(f)
        except (IOError, OSError, ValueError, pickle.UnpicklingError) as e:
            raise IOError(f"I/O error loading scaler from {scaler_path}: {e}")
        except Exception as e:
            raise Exception(f"Error loading scaler from {scaler_path}: {e}")

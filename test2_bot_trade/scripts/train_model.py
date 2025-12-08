"""
Train LSTM model for price prediction.
"""
import sys
import os

# Configurar TensorFlow para suprimir mensajes antes de cualquier import
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Solo errores
import warnings
warnings.filterwarnings('ignore')

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import argparse
import json
from datetime import datetime
from src.core.database import SessionLocal
from src.models.market_data import MarketData
from src.models.price_predictor import LSTMPricePredictor
from src.services.training_analytics import TrainingAnalytics, TrainingProgressCallback
from src.services.continuous_learning import ContinuousLearning

def load_prices_from_db(symbol):
    """
    Load historical prices from database.
    """
    db = SessionLocal()
    try:
        records = db.query(MarketData).filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.timestamp).all()
        
        if not records:
            print(f"\n❌ ERROR: No se encontraron datos para {symbol} en la base de datos.")
            print(f"   Este símbolo necesita ser monitoreado primero para generar datos históricos.")
            print(f"   Solución: Usa el bot de trading para comenzar a recopilar datos, o importa datos históricos.")
            sys.exit(1)  # Exit with code 1 to indicate error
        
        prices = np.array([r.close for r in records])
        return prices
    finally:
        db.close()

def train_model(symbol, epochs=50, save_path="models", enable_analytics=True):
    """
    Train LSTM model for a given symbol with advanced analytics.
    """
    print(f"=== Training LSTM Model for {symbol} ===\n")
    
    # Initialize analytics
    analytics = TrainingAnalytics() if enable_analytics else None
    
    # Load data with feature engineering (multivariate)
    print("Loading data from database...")
    db = SessionLocal()
    try:
        records = db.query(MarketData).filter(
            MarketData.symbol == symbol
        ).order_by(MarketData.timestamp).all()
        
        if not records:
            print(f"\n❌ ERROR: No se encontraron datos para {symbol} en la base de datos.")
            print(f"   Este símbolo necesita ser monitoreado primero para generar datos históricos.")
            print(f"   Solución: Usa el bot de trading para comenzar a recopilar datos, o importa datos históricos.")
            sys.exit(1)  # Exit with code 1 to indicate error
        
        # Prepare DataFrame for multivariate analysis
        df = pd.DataFrame([{'close': r.close, 'volume': r.volume} for r in records])
        
        # Use ContinuousLearning to prepare features
        cl = ContinuousLearning()
        df_features = cl.prepare_features(df)
        
        print(f"Loaded {len(df_features)} records with {len(df_features.columns)} features")
        print(f"Features: {', '.join(df_features.columns)}")
        
        # Data quality analysis
        if analytics:
            analytics.analyze_data_quality(df_features, symbol)
            analytics.plot_data_distribution(df_features, symbol)
            analytics.plot_correlation_matrix(df_features, symbol)
        
        feature_data = df_features.values
        
    finally:
        db.close()
    
    # Create and train model
    print("\nBuilding LSTM model...")
    predictor = LSTMPricePredictor(sequence_length=60, prediction_days=1)
    
    # Training with progress callback
    print("Training model...")
    callbacks = [TrainingProgressCallback(verbose=1)] if enable_analytics else []
    
    history = predictor.train(
        feature_data, 
        epochs=epochs, 
        batch_size=32, 
        validation_split=0.2
    )
    
    # Plot training history
    if analytics:
        analytics.plot_training_history(history, symbol)
    
    # Evaluate
    final_loss = history.history['loss'][-1]
    final_val_loss = history.history['val_loss'][-1]
    final_mae = history.history['mae'][-1]
    final_val_mae = history.history['val_mae'][-1]
    
    print(f"\n=== Training Complete ===")
    print(f"Final Training Loss: {final_loss:.6f}")
    print(f"Final Validation Loss: {final_val_loss:.6f}")
    print(f"Final Training MAE: {final_mae:.6f}")
    print(f"Final Validation MAE: {final_val_mae:.6f}")
    
    # Save model to fixed path for dashboard
    os.makedirs(save_path, exist_ok=True)
    # Force save to lstm_model.h5 so dashboard finds it
    # Note: price_predictor.save appends _model.h5, so we pass just "lstm"
    model_path = os.path.join(save_path, "lstm")
    predictor.save(model_path)
    print(f"\nModel saved to: {model_path}_model.h5")
    
    # Save metrics for dashboard
    metrics = {
        'loss': final_loss,
        'val_loss': final_val_loss,
        'mae': final_mae,
        'val_mae': final_val_mae,
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol,
        'epochs': epochs
    }
    
    with open('training_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Model evaluation with test set
    if analytics and predictor.model is not None:
        print(f"\n=== Model Evaluation ===")
        try:
            # Split data for evaluation
            split_idx = int(len(feature_data) * 0.8)
            if split_idx < 60:
                print("   ⚠️  Not enough data for evaluation")
            else:
                # Prepare test sequences
                X_test_seq = []
                y_test = []
                
                # Create sequences from test data
                for i in range(split_idx, len(feature_data) - 1):
                    if i >= 60:
                        X_test_seq.append(feature_data[i-60:i])
                        y_test.append(feature_data[i, 0])  # Close price (first column)
                
                if len(X_test_seq) > 0:
                    X_test_seq = np.array(X_test_seq)
                    y_test = np.array(y_test)
                    
                    # Get predictions using the predictor
                    test_predictions = []
                    for seq in X_test_seq:
                        try:
                            pred = predictor.predict(seq)
                            test_predictions.append(pred)
                        except:
                            continue
                    
                    if len(test_predictions) > 0:
                        test_predictions = np.array(test_predictions).flatten()
                        # Align lengths
                        min_len = min(len(test_predictions), len(y_test))
                        test_predictions = test_predictions[:min_len]
                        y_test = y_test[:min_len]
                        
                        # Evaluate using model directly for metrics
                        X_eval = X_test_seq[:min_len]
                        y_eval = y_test.reshape(-1, 1)
                        
                        perf = analytics.evaluate_model_performance(
                            predictor.model, 
                            X_eval, 
                            y_eval,
                            symbol
                        )
                        
                        # Visualizations
                        analytics.plot_predictions_vs_actuals(test_predictions, y_test, symbol)
                        analytics.plot_residuals(test_predictions, y_test, symbol)
                
        except Exception as e:
            print(f"   ⚠️  Error during evaluation: {e}")
        
        # Generate complete report
        analytics.generate_report(symbol)
    
    # Test prediction
    print(f"\n=== Test Prediction ===")
    recent_features = feature_data[-60:]  # Last 60 sequences
    prediction = predictor.predict(recent_features)
    current_price = feature_data[-1, 0]  # Close price
    
    print(f"Current price: ${current_price:.2f}")
    print(f"Predicted next price: ${prediction:.2f}")
    print(f"Change: {((prediction - current_price) / current_price * 100):.2f}%")
    
    return predictor

def main():
    parser = argparse.ArgumentParser(description='Train LSTM price prediction model')
    parser.add_argument('--symbol', type=str, default=None, help='Stock symbol to train on')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--save-path', type=str, default='models', help='Path to save model')
    parser.add_argument('--no-analytics', action='store_true', help='Disable analytics and visualizations')
    
    args = parser.parse_args()
    
    # If no symbol provided, try to load from local portfolio first
    symbol = args.symbol
    if not symbol:
        # 1. Try to load from local portfolio (my_portfolio.json)
        try:
            from src.services.portfolio_persistence import load_portfolio
            portfolio = load_portfolio()
            if portfolio:
                # Get first symbol from portfolio
                portfolio_symbols = [p.get('symbol') for p in portfolio if p.get('symbol')]
                if portfolio_symbols:
                    symbol = portfolio_symbols[0]
                    print(f"📂 Cargado símbolo del portafolio local: {symbol}")
                    print(f"   (Portafolio tiene {len(portfolio_symbols)} símbolos disponibles)")
        except Exception as e:
            print(f"⚠️  No se pudo cargar portafolio local: {e}")
        
        # 2. If no portfolio, try to find one in DB
        if not symbol:
            try:
                db = SessionLocal()
                # Get first symbol with data
                first_data = db.query(MarketData).first()
                if first_data:
                    symbol = first_data.symbol
                    print(f"📊 Auto-detectado símbolo de la base de datos: {symbol}")
                else:
                    symbol = 'AAPL' # Fallback
                    print(f"⚠️  No se encontraron datos en DB, usando por defecto: {symbol}")
                db.close()
            except Exception as e:
                print(f"⚠️  Error accediendo a la base de datos: {e}")
                symbol = 'AAPL'
            
    train_model(
        symbol, 
        epochs=args.epochs, 
        save_path=args.save_path,
        enable_analytics=not args.no_analytics
    )

if __name__ == "__main__":
    main()

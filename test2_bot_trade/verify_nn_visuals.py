
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.services.neural_network_service import NeuralNetworkService
import pandas as pd
import numpy as np

def test_service_initialization():
    print("Testing NeuralNetworkService initialization (LSTM)...")
    try:
        service = NeuralNetworkService()
        print("✅ Service initialized successfully")
        return service
    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        return None

def test_model_loading(service):
    print("\nTesting model loading...")
    models_dir = Path("data/models")
    if not models_dir.exists():
        print("⚠️ Models directory does not exist yet (expected if no training happened)")
        return
    
    models = list(models_dir.glob("*.h5"))
    if not models:
        print("⚠️ No models found (expected if no training happened)")
        return

    print(f"Found {len(models)} models.")
    for model_path in models[:1]:
        symbol = model_path.stem.replace('_lstm_model', '')
        print(f"Attempting to load model for {symbol}...")
        try:
            model = service._load_model(symbol)
            if model:
                print(f"✅ Model for {symbol} loaded successfully")
            else:
                print(f"❌ Failed to load model for {symbol}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")

if __name__ == "__main__":
    service = test_service_initialization()
    if service:
        test_model_loading(service)


import sys
import os
import yfinance as yf
from pathlib import Path

# Agregar root al path
sys.path.append(os.getcwd())

from src.services.neural_network_service import NeuralNetworkService

def verify_improved_nn():
    print("🚀 Iniciando Verificación de Red Neuronal Mejorada (Fase 1)...")
    
    # 1. Inicialización
    try:
        service = NeuralNetworkService(data_dir='data/models_v2_test')
        print("✅ Servicio inicializado correctamente.")
    except Exception as e:
        print(f"❌ Error al inicializar servicio: {e}")
        return

    # 2. Descarga de Datos
    symbol = "AAPL"
    print(f"\n📥 Descargando datos para {symbol} (2 años)...")
    try:
        df = yf.download(symbol, period="2y", interval="1d")
        if len(df) == 0:
            print("❌ No se descargaron datos.")
            return
        print(f"✅ Datos descargados: {len(df)} filas.")
    except Exception as e:
        print(f"❌ Error descargando datos: {e}")
        return

    # 3. Feature Engineering e Input Shapes
    print("\n🛠️ Verificando Feature Engineering...")
    try:
        # Usamos _add_technical_indicators directamente para ver las features
        df_feats = service._add_technical_indicators(df)
        print("   Columnas generadas:", df_feats.columns.tolist())
        
        expected_cols = ['rsi', 'macd', 'bollinger_hband', 'sma_20']
        # Check simple
        if 'rsi' in df_feats.columns:
             print("✅ Indicadores calculados correctamente (RSI presente).")
        else:
             print("❌ Faltan indicadores técnicos.")
             
        # Check shapes
        X, y, _, _ = service._prepare_data(df, is_training=True)
        if X is None:
            print("❌ Error preparando datos (X es None).")
            return
            
        print(f"✅ Tensores generados: X shape={X.shape}, y shape={y.shape}")
        
        # Check MLP shape (Samples, FeaturesFlattened)
        if len(X.shape) == 2:
            n_features_flat = X.shape[1]
            print(f"✅ Input flattened correctamente para MLP ({n_features_flat} dimensiones).")
            # Approximation check: n_features_flat should be lookback * n_raw_features
            # lookback=60. 
        elif len(X.shape) == 3:
             print(f"✅ Multi-Feature LSTM confirmado ({X.shape[2]} features).")
        else:
            print(f"❌ Shape inesperado: {X.shape}")
            
    except Exception as e:
        print(f"❌ Error en preparación de datos: {e}")
        import traceback
        traceback.print_exc()
        return


    # 4. Construcción y Entrenamiento del Modelo
    print("\n🧠 Verificando Entrenamiento (MLP Multi-Feature)...")
    try:
        success = service.train_model(symbol, df, epochs=10, batch_size=32)
        if success:
            print("✅ Entrenamiento Dummy completado exitosamente.")
            
            # Verificar archivos generados
            files = list(Path('data/models_v2_test').glob(f"{symbol}*"))
            print(f"   Archivos generados: {[f.name for f in files]}")
            if len(files) >= 4:
                print("✅ Persistencia correcta (.pkl model, scalers y features).")
            else:
                print("⚠️ Faltan archivos de persistencia.")
        else:
            print("❌ Falló el entrenamiento.")
            return
    except Exception as e:
        print(f"❌ Excepción durante entrenamiento: {e}")
        return

    # 5. Predicción
    print("\n🔮 Verificando Predicción...")
    try:
        pred_price, score, conf = service.predict(symbol, df)
        if pred_price is not None:
            print(f"✅ Predicción exitosa: ${pred_price:.2f} (Score: {score}, Conf: {conf})")
        else:
            print("❌ Predicción retornó None.")
    except Exception as e:
        print(f"❌ Error en predicción: {e}")

if __name__ == "__main__":
    verify_improved_nn()

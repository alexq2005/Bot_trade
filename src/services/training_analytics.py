"""
Training Analytics and Analysis Tools
Herramientas avanzadas de análisis para el entrenamiento de modelos
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    # Configurar TensorFlow para suprimir mensajes
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Solo errores
    import logging
    logging.getLogger('tensorflow').setLevel(logging.ERROR)
    
    from tensorflow import keras
    from tensorflow.keras.callbacks import Callback
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    # Don't print warning here, let it be handled by the caller

try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


class TrainingAnalytics:
    """
    Herramientas de análisis para el entrenamiento de modelos.
    """
    
    def __init__(self, output_dir="training_analytics"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.analysis_results = {}
        
    def analyze_data_quality(self, df: pd.DataFrame, symbol: str) -> Dict:
        """
        Análisis de calidad de datos antes del entrenamiento.
        
        Returns:
            Dict con métricas de calidad
        """
        print("\n" + "="*60)
        print("📊 ANÁLISIS DE CALIDAD DE DATOS")
        print("="*60)
        
        results = {
            'symbol': symbol,
            'total_records': len(df),
            'missing_values': df.isnull().sum().to_dict(),
            'duplicates': df.duplicated().sum(),
            'date_range': None,
            'outliers': {},
            'statistics': {}
        }
        
        # Estadísticas básicas
        print(f"\n📈 Estadísticas Básicas:")
        print(f"   Total de registros: {len(df)}")
        print(f"   Columnas: {', '.join(df.columns)}")
        
        # Valores faltantes
        missing = df.isnull().sum()
        if missing.sum() > 0:
            print(f"\n⚠️  Valores Faltantes:")
            for col, count in missing[missing > 0].items():
                pct = (count / len(df)) * 100
                print(f"   {col}: {count} ({pct:.2f}%)")
        else:
            print(f"\n✅ Sin valores faltantes")
        
        # Duplicados
        if results['duplicates'] > 0:
            print(f"\n⚠️  Registros duplicados: {results['duplicates']}")
        else:
            print(f"\n✅ Sin duplicados")
        
        # Estadísticas por columna
        print(f"\n📊 Estadísticas Descriptivas:")
        stats = df.describe()
        results['statistics'] = stats.to_dict()
        
        for col in df.select_dtypes(include=[np.number]).columns:
            print(f"\n   {col}:")
            print(f"      Media: {df[col].mean():.2f}")
            print(f"      Mediana: {df[col].median():.2f}")
            print(f"      Std: {df[col].std():.2f}")
            print(f"      Min: {df[col].min():.2f}")
            print(f"      Max: {df[col].max():.2f}")
            
            # Detectar outliers usando IQR
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
            if len(outliers) > 0:
                results['outliers'][col] = {
                    'count': len(outliers),
                    'percentage': (len(outliers) / len(df)) * 100,
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                }
                print(f"      ⚠️  Outliers: {len(outliers)} ({(len(outliers)/len(df)*100):.2f}%)")
        
        self.analysis_results['data_quality'] = results
        return results
    
    def plot_data_distribution(self, df: pd.DataFrame, symbol: str, save=True):
        """
        Visualizar distribución de datos.
        """
        print(f"\n📈 Generando gráficos de distribución...")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) == 0:
            print("   ⚠️  No hay columnas numéricas para graficar")
            return
        
        n_cols = min(3, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
        if n_rows == 1:
            axes = axes.reshape(1, -1) if len(numeric_cols) > 1 else [axes]
        axes = axes.flatten()
        
        for idx, col in enumerate(numeric_cols):
            ax = axes[idx]
            # Filtrar valores infinitos y NaN antes de graficar
            col_data = df[col].replace([np.inf, -np.inf], np.nan).dropna()
            
            if len(col_data) == 0:
                ax.text(0.5, 0.5, f'No hay datos válidos\npara {col}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'Distribución de {col} (Sin datos)')
            else:
                # Verificar que los datos sean finitos y tengan rango válido
                finite_data = col_data[np.isfinite(col_data)]
                
                if len(finite_data) == 0:
                    ax.text(0.5, 0.5, f'No hay datos finitos\npara {col}', 
                           ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f'Distribución de {col} (Sin datos finitos)')
                else:
                    # Verificar que el rango sea finito
                    data_min, data_max = finite_data.min(), finite_data.max()
                    if np.isfinite(data_min) and np.isfinite(data_max) and data_min != data_max:
                        try:
                            finite_data.hist(bins=min(50, len(finite_data)//2), ax=ax, edgecolor='black')
                            ax.set_title(f'Distribución de {col}')
                        except Exception as e:
                            ax.text(0.5, 0.5, f'Error al graficar\n{col}\n{str(e)[:50]}', 
                                   ha='center', va='center', transform=ax.transAxes)
                            ax.set_title(f'Distribución de {col} (Error)')
                    else:
                        ax.text(0.5, 0.5, f'Rango inválido\npara {col}\n(min={data_min:.2f}, max={data_max:.2f})', 
                               ha='center', va='center', transform=ax.transAxes)
                        ax.set_title(f'Distribución de {col} (Rango inválido)')
            
            ax.set_xlabel(col)
            ax.set_ylabel('Frecuencia')
            ax.grid(True, alpha=0.3)
        
        # Ocultar ejes extras
        for idx in range(len(numeric_cols), len(axes)):
            axes[idx].axis('off')
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{symbol}_data_distribution.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"   ✅ Guardado: {filepath}")
        
        plt.close()
    
    def plot_correlation_matrix(self, df: pd.DataFrame, symbol: str, save=True):
        """
        Matriz de correlación entre features.
        """
        print(f"\n🔗 Generando matriz de correlación...")
        
        numeric_df = df.select_dtypes(include=[np.number])
        
        if len(numeric_df.columns) < 2:
            print("   ⚠️  Se necesitan al menos 2 columnas numéricas")
            return
        
        plt.figure(figsize=(12, 10))
        correlation_matrix = numeric_df.corr()
        
        sns.heatmap(
            correlation_matrix,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            linewidths=1,
            cbar_kws={"shrink": 0.8}
        )
        
        plt.title(f'Matriz de Correlación - {symbol}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{symbol}_correlation_matrix.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"   ✅ Guardado: {filepath}")
        
        plt.close()
    
    def plot_training_history(self, history, symbol: str, save=True):
        """
        Visualizar historial de entrenamiento.
        """
        if not TF_AVAILABLE:
            print("   ⚠️  TensorFlow no disponible para visualización")
            return
        
        print(f"\n📊 Generando gráficos de entrenamiento...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Loss
        axes[0, 0].plot(history.history['loss'], label='Training Loss', color='blue')
        if 'val_loss' in history.history:
            axes[0, 0].plot(history.history['val_loss'], label='Validation Loss', color='red')
        axes[0, 0].set_title('Model Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # MAE
        if 'mae' in history.history:
            axes[0, 1].plot(history.history['mae'], label='Training MAE', color='blue')
            if 'val_mae' in history.history:
                axes[0, 1].plot(history.history['val_mae'], label='Validation MAE', color='red')
            axes[0, 1].set_title('Mean Absolute Error')
            axes[0, 1].set_xlabel('Epoch')
            axes[0, 1].set_ylabel('MAE')
            axes[0, 1].legend()
            axes[0, 1].grid(True, alpha=0.3)
        
        # Loss comparison (zoom)
        if 'val_loss' in history.history:
            axes[1, 0].plot(history.history['loss'], label='Training', color='blue', alpha=0.7)
            axes[1, 0].plot(history.history['val_loss'], label='Validation', color='red', alpha=0.7)
            axes[1, 0].set_title('Loss Comparison (Zoom)')
            axes[1, 0].set_xlabel('Epoch')
            axes[1, 0].set_ylabel('Loss')
            axes[1, 0].legend()
            axes[1, 0].grid(True, alpha=0.3)
            
            # Detectar overfitting
            train_loss = history.history['loss'][-10:]
            val_loss = history.history['val_loss'][-10:]
            if np.mean(val_loss) > np.mean(train_loss) * 1.1:
                axes[1, 0].text(0.5, 0.95, '⚠️ Possible Overfitting', 
                               transform=axes[1, 0].transAxes,
                               ha='center', va='top',
                               bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
        
        # Learning rate effect (if available)
        axes[1, 1].text(0.5, 0.5, 'Training Metrics Summary', 
                       ha='center', va='center', fontsize=14, fontweight='bold',
                       transform=axes[1, 1].transAxes)
        
        final_train_loss = history.history['loss'][-1]
        final_val_loss = history.history.get('val_loss', [0])[-1]
        
        summary_text = f"""
Final Training Loss: {final_train_loss:.6f}
Final Validation Loss: {final_val_loss:.6f}
Epochs: {len(history.history['loss'])}
        """
        
        axes[1, 1].text(0.5, 0.3, summary_text, 
                       ha='center', va='center', fontsize=10,
                       transform=axes[1, 1].transAxes,
                       family='monospace')
        axes[1, 1].axis('off')
        
        plt.suptitle(f'Training History - {symbol}', fontsize=16, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{symbol}_training_history.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"   ✅ Guardado: {filepath}")
        
        plt.close()
    
    def evaluate_model_performance(self, model, X_test, y_test, symbol: str) -> Dict:
        """
        Evaluación detallada del modelo.
        """
        print("\n" + "="*60)
        print("📊 EVALUACIÓN DEL MODELO")
        print("="*60)
        
        if not TF_AVAILABLE:
            return {}
        
        # Predicciones
        predictions = model.predict(X_test, verbose=0)
        
        # Métricas
        mae = np.mean(np.abs(predictions - y_test))
        mse = np.mean((predictions - y_test) ** 2)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((predictions - y_test) / (y_test + 1e-8))) * 100
        
        # Direction accuracy
        if len(predictions) > 1:
            pred_direction = np.diff(predictions.flatten()) > 0
            actual_direction = np.diff(y_test.flatten()) > 0
            direction_accuracy = np.mean(pred_direction == actual_direction) * 100
        else:
            direction_accuracy = 0.0
        
        results = {
            'mae': float(mae),
            'mse': float(mse),
            'rmse': float(rmse),
            'mape': float(mape),
            'direction_accuracy': float(direction_accuracy),
            'predictions': predictions.flatten().tolist(),
            'actuals': y_test.flatten().tolist()
        }
        
        print(f"\n📈 Métricas de Rendimiento:")
        print(f"   MAE (Mean Absolute Error): {mae:.4f}")
        print(f"   MSE (Mean Squared Error): {mse:.4f}")
        print(f"   RMSE (Root Mean Squared Error): {rmse:.4f}")
        print(f"   MAPE (Mean Absolute Percentage Error): {mape:.2f}%")
        print(f"   Direction Accuracy: {direction_accuracy:.2f}%")
        
        self.analysis_results['model_performance'] = results
        return results
    
    def plot_predictions_vs_actuals(self, predictions, actuals, symbol: str, save=True):
        """
        Gráfico de predicciones vs valores reales.
        """
        print(f"\n📊 Generando gráfico de predicciones vs reales...")
        
        fig, axes = plt.subplots(2, 1, figsize=(12, 10))
        
        # Time series comparison
        axes[0].plot(actuals, label='Actual', color='blue', alpha=0.7, linewidth=2)
        axes[0].plot(predictions, label='Predicted', color='red', alpha=0.7, linewidth=2)
        axes[0].set_title('Predicciones vs Valores Reales')
        axes[0].set_xlabel('Sample')
        axes[0].set_ylabel('Price')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # Scatter plot
        axes[1].scatter(actuals, predictions, alpha=0.5, s=20)
        
        # Perfect prediction line
        min_val = min(min(actuals), min(predictions))
        max_val = max(max(actuals), max(predictions))
        axes[1].plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Perfect Prediction')
        
        axes[1].set_title('Scatter: Predicciones vs Reales')
        axes[1].set_xlabel('Actual')
        axes[1].set_ylabel('Predicted')
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{symbol}_predictions_vs_actuals.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"   ✅ Guardado: {filepath}")
        
        plt.close()
    
    def plot_residuals(self, predictions, actuals, symbol: str, save=True):
        """
        Análisis de residuales.
        """
        print(f"\n📊 Generando análisis de residuales...")
        
        residuals = actuals - predictions
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Residuals over time - Filtrar infinitos
        finite_residuals = residuals[np.isfinite(residuals)]
        if len(finite_residuals) > 0:
            axes[0, 0].plot(finite_residuals, alpha=0.7)
            axes[0, 0].axhline(y=0, color='r', linestyle='--', linewidth=2)
            axes[0, 0].set_title('Residuales en el Tiempo')
        else:
            axes[0, 0].text(0.5, 0.5, 'No hay residuales\nfinitos', 
                           ha='center', va='center', transform=axes[0, 0].transAxes)
            axes[0, 0].set_title('Residuales en el Tiempo (Sin datos)')
        axes[0, 0].set_xlabel('Sample')
        axes[0, 0].set_ylabel('Residual')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Residuals distribution - Filtrar infinitos
        finite_residuals = residuals[np.isfinite(residuals)]
        if len(finite_residuals) > 0:
            axes[0, 1].hist(finite_residuals, bins=50, edgecolor='black', alpha=0.7)
            axes[0, 1].set_title('Distribución de Residuales')
        else:
            axes[0, 1].text(0.5, 0.5, 'No hay residuales\nfinitos', 
                           ha='center', va='center', transform=axes[0, 1].transAxes)
            axes[0, 1].set_title('Distribución de Residuales (Sin datos)')
        axes[0, 1].set_xlabel('Residual')
        axes[0, 1].set_ylabel('Frecuencia')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Q-Q plot (normalidad) - Filtrar infinitos
        finite_residuals = residuals[np.isfinite(residuals)]
        if len(finite_residuals) > 0:
            if SCIPY_AVAILABLE:
                stats.probplot(finite_residuals, dist="norm", plot=axes[1, 0])
                axes[1, 0].set_title('Q-Q Plot (Normalidad)')
            else:
                axes[1, 0].text(0.5, 0.5, 'Q-Q Plot\n(Requires scipy)', 
                               ha='center', va='center', transform=axes[1, 0].transAxes)
                axes[1, 0].set_title('Q-Q Plot (Normalidad)')
        else:
            axes[1, 0].text(0.5, 0.5, 'No hay residuales\nfinitos para Q-Q Plot', 
                           ha='center', va='center', transform=axes[1, 0].transAxes)
            axes[1, 0].set_title('Q-Q Plot (Sin datos)')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Residuals vs Predicted - Filtrar infinitos
        finite_mask = np.isfinite(predictions) & np.isfinite(residuals)
        if np.any(finite_mask):
            axes[1, 1].scatter(predictions[finite_mask], residuals[finite_mask], alpha=0.5, s=20)
            axes[1, 1].axhline(y=0, color='r', linestyle='--', linewidth=2)
            axes[1, 1].set_title('Residuales vs Predicciones')
        else:
            axes[1, 1].text(0.5, 0.5, 'No hay datos\nfinitos', 
                           ha='center', va='center', transform=axes[1, 1].transAxes)
            axes[1, 1].set_title('Residuales vs Predicciones (Sin datos)')
        axes[1, 1].set_xlabel('Predicted')
        axes[1, 1].set_ylabel('Residual')
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.suptitle(f'Análisis de Residuales - {symbol}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save:
            filepath = os.path.join(self.output_dir, f"{symbol}_residuals_analysis.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            print(f"   ✅ Guardado: {filepath}")
        
        plt.close()
    
    def generate_report(self, symbol: str):
        """
        Generar reporte completo en JSON.
        """
        report = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'analyses': self.analysis_results
        }
        
        filepath = os.path.join(self.output_dir, f"{symbol}_analysis_report.json")
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n✅ Reporte completo guardado: {filepath}")
        return report


class TrainingProgressCallback(Callback):
    """
    Callback personalizado para monitorear el entrenamiento.
    """
    
    def __init__(self, verbose=1):
        super().__init__()
        self.verbose = verbose
        self.epoch_losses = []
        self.epoch_val_losses = []
        
    def on_epoch_end(self, epoch, logs=None):
        logs = logs or {}
        loss = logs.get('loss', 0)
        val_loss = logs.get('val_loss', 0)
        
        self.epoch_losses.append(loss)
        self.epoch_val_losses.append(val_loss)
        
        if self.verbose:
            print(f"   Epoch {epoch+1}: loss={loss:.6f}, val_loss={val_loss:.6f}")
            
            # Detectar overfitting
            if epoch > 5 and val_loss > loss * 1.15:
                print(f"   ⚠️  Posible overfitting detectado (val_loss > train_loss * 1.15)")


"""
Script para ejecutar ciclo de aprendizaje manualmente
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

from src.services.advanced_learning import AdvancedLearningSystem
from src.core.logger import get_logger

logger = get_logger("learning_script")

def main():
    print("🧠 Sistema de Aprendizaje Avanzado")
    print("="*70)
    
    learning_system = AdvancedLearningSystem()
    
    # Ejecutar ciclo de aprendizaje
    summary = learning_system.run_learning_cycle()
    
    # Mostrar resumen
    print("\n📊 Resumen del Aprendizaje:")
    print("="*70)
    
    if summary.get('lessons_learned'):
        print("\n📚 Lecciones Aprendidas:")
        for lesson in summary['lessons_learned']:
            print(f"   {lesson}")
    
    if summary.get('trade_patterns'):
        patterns = summary['trade_patterns']
        print(f"\n📈 Patrones de Trading:")
        print(f"   Total trades: {patterns.get('total_trades', 0)}")
        print(f"   Win rate: {patterns.get('win_rate', 0)*100:.1f}%")
        print(f"   Avg win: {patterns.get('avg_win_pct', 0):.2f}%")
        print(f"   Avg loss: {patterns.get('avg_loss_pct', 0):.2f}%")
    
    if summary.get('prediction_accuracy'):
        accuracy = summary['prediction_accuracy']
        print(f"\n🎯 Precisión de Predicciones:")
        print(f"   Total predicciones: {accuracy.get('total_predictions', 0)}")
        print(f"   Precisión dirección: {accuracy.get('direction_accuracy', 0):.1f}%")
        print(f"   Error promedio: {accuracy.get('avg_error', 0):.2f}")
        print(f"   MAPE: {accuracy.get('mape', 0):.2f}%")
    
    if summary.get('strategy_params'):
        params = summary['strategy_params']
        print(f"\n⚙️  Parámetros de Estrategia Adaptativa:")
        print(f"   Umbral compra: {params.get('buy_threshold', 25)}")
        print(f"   Umbral venta: {params.get('sell_threshold', -25)}")
        print(f"   Confianza mínima: {params.get('min_confidence', 'MEDIUM')}")
    
    # Obtener resumen completo
    full_summary = learning_system.get_learning_summary()
    print(f"\n📊 Estadísticas Generales:")
    print(f"   Trades aprendidos: {full_summary.get('total_trades_learned', 0)}")
    print(f"   Predicciones rastreadas: {full_summary.get('total_predictions_tracked', 0)}")
    print(f"   Adaptaciones realizadas: {full_summary.get('adaptations_made', 0)}")
    
    print("\n✅ Ciclo de aprendizaje completado!")
    print("="*70)

if __name__ == "__main__":
    main()


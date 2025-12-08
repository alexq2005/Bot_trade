"""
Regime Detector - Detecta el régimen actual del mercado
Permite adaptar la estrategia según condiciones
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
from ta.trend import ADXIndicator


class RegimeDetector:
    """
    Detecta el régimen de mercado actual:
    - TRENDING: Mercado en tendencia clara (usar estrategias de momentum)
    - RANGING: Mercado lateral (usar reversión a la media)
    - VOLATILE: Alta volatilidad (reducir exposición)
    """
    
    def __init__(self):
        self.regimes = {
            'TRENDING': {
                'description': 'Mercado en tendencia',
                'strategy': 'Seguir tendencia, momentum',
                'buy_threshold_adj': -5,  # Más agresivo
                'position_multiplier': 1.2  # Aumentar posición
            },
            'RANGING': {
                'description': 'Mercado lateral',
                'strategy': 'Reversión a la media',
                'buy_threshold_adj': +10,  # Más conservador
                'position_multiplier': 0.8  # Reducir posición
            },
            'VOLATILE': {
                'description': 'Alta volatilidad',
                'strategy': 'Reducir riesgo, esperar',
                'buy_threshold_adj': +15,  # Muy conservador
                'position_multiplier': 0.5  # Mitad de posición
            }
        }
    
    def detect_regime(self, df: pd.DataFrame) -> Tuple[str, Dict]:
        """
        Detecta régimen de mercado
        
        Args:
            df: DataFrame con OHLCV (necesita al menos 30 registros)
        
        Returns:
            (regime_name, regime_info)
        """
        if len(df) < 30:
            return 'UNKNOWN', {'confidence': 'LOW', 'reason': 'Datos insuficientes'}
        
        try:
            # 1. Calcular ADX (Average Directional Index)
            adx_indicator = ADXIndicator(
                high=df['high'],
                low=df['low'],
                close=df['close'],
                window=14
            )
            adx = adx_indicator.adx().iloc[-1]
            
            # 2. Calcular volatilidad (desviación estándar de retornos)
            returns = df['close'].pct_change()
            volatility = returns.std() * np.sqrt(252)  # Anualizada
            
            # 3. Calcular range (High-Low) promedio
            df['range'] = (df['high'] - df['low']) / df['close']
            avg_range = df['range'].tail(20).mean()
            
            # 4. Determinar régimen
            regime = self._classify_regime(adx, volatility, avg_range)
            
            # 5. Calcular confianza
            confidence = self._calculate_confidence(adx, volatility)
            
            # 6. Info adicional
            info = {
                'regime': regime,
                'adx': round(adx, 2),
                'volatility': round(volatility * 100, 2),  # En porcentaje
                'avg_range': round(avg_range * 100, 2),
                'confidence': confidence,
                'strategy_adjustment': self.regimes[regime],
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            return regime, info
            
        except Exception as e:
            return 'UNKNOWN', {'error': str(e), 'confidence': 'LOW'}
    
    def _classify_regime(self, adx: float, volatility: float, avg_range: float) -> str:
        """
        Clasifica el régimen basado en métricas
        
        ADX:
        - > 25: Tendencia fuerte
        - 20-25: Tendencia moderada
        - < 20: Sin tendencia clara (ranging)
        
        Volatility:
        - > 0.30 (30%): Alta volatilidad
        - 0.15-0.30: Volatilidad normal
        - < 0.15: Baja volatilidad
        """
        # Alta volatilidad siempre prevalece
        if volatility > 0.30 or avg_range > 0.05:
            return 'VOLATILE'
        
        # Tendencia clara
        if adx > 25:
            return 'TRENDING'
        
        # Sin tendencia clara = ranging
        if adx < 20:
            return 'RANGING'
        
        # Zona gris (20-25): Considerar volatilidad
        if volatility > 0.20:
            return 'VOLATILE'
        else:
            return 'TRENDING'  # Beneficio de la duda a trending
    
    def _calculate_confidence(self, adx: float, volatility: float) -> str:
        """Calcula nivel de confianza en la clasificación"""
        # ADX muy alto o muy bajo = alta confianza
        if adx > 30 or adx < 15:
            adx_confidence = 'HIGH'
        elif adx > 25 or adx < 18:
            adx_confidence = 'MEDIUM'
        else:
            adx_confidence = 'LOW'
        
        # Volatilidad extrema = alta confianza
        if volatility > 0.35 or volatility < 0.10:
            vol_confidence = 'HIGH'
        elif volatility > 0.28 or volatility < 0.15:
            vol_confidence = 'MEDIUM'
        else:
            vol_confidence = 'LOW'
        
        # Combinar
        if adx_confidence == 'HIGH' and vol_confidence == 'HIGH':
            return 'HIGH'
        elif adx_confidence == 'LOW' or vol_confidence == 'LOW':
            return 'LOW'
        else:
            return 'MEDIUM'
    
    def adjust_parameters(self, regime: str, base_params: Dict) -> Dict:
        """
        Ajusta parámetros de trading según régimen
        
        Args:
            regime: TRENDING, RANGING, VOLATILE
            base_params: Parámetros base (buy_threshold, position_size, etc.)
        
        Returns:
            Parámetros ajustados
        """
        if regime not in self.regimes:
            return base_params
        
        adjustments = self.regimes[regime]
        adjusted = base_params.copy()
        
        # Ajustar threshold
        if 'buy_threshold' in adjusted:
            adjusted['buy_threshold'] += adjustments['buy_threshold_adj']
        
        # Ajustar tamaño de posición
        if 'position_size' in adjusted:
            adjusted['position_size'] *= adjustments['position_multiplier']
        
        if 'max_position_size_pct' in adjusted:
            adjusted['max_position_size_pct'] *= adjustments['position_multiplier']
        
        adjusted['regime'] = regime
        adjusted['regime_info'] = adjustments
        
        return adjusted
    
    def get_regime_summary(self, regime_info: Dict) -> str:
        """Genera resumen legible del régimen"""
        regime = regime_info.get('regime', 'UNKNOWN')
        adx = regime_info.get('adx', 0)
        vol = regime_info.get('volatility', 0)
        conf = regime_info.get('confidence', 'LOW')
        
        emoji = {
            'TRENDING': '📈',
            'RANGING': '↔️',
            'VOLATILE': '⚡',
            'UNKNOWN': '❓'
        }.get(regime, '❓')
        
        summary = f"{emoji} Régimen: {regime}\n"
        summary += f"   ADX: {adx} | Vol: {vol}%\n"
        summary += f"   Confianza: {conf}\n"
        
        if 'strategy_adjustment' in regime_info:
            adj = regime_info['strategy_adjustment']
            summary += f"   Estrategia: {adj['strategy']}\n"
        
        return summary


# Test
if __name__ == "__main__":
    import yfinance as yf
    
    detector = RegimeDetector()
    
    # Obtener datos
    df = yf.download('AAPL', period='3mo', interval='1d')
    df.columns = [c.lower() for c in df.columns]
    
    # Detectar régimen
    regime, info = detector.detect_regime(df)
    
    print("="*70)
    print("REGIME DETECTION TEST")
    print("="*70)
    print()
    print(detector.get_regime_summary(info))
    print()
    print("Ajustes recomendados:")
    base = {
        'buy_threshold': 25,
        'position_size': 100,
        'max_position_size_pct': 10
    }
    adjusted = detector.adjust_parameters(regime, base)
    print(f"  Buy threshold: {base['buy_threshold']} → {adjusted['buy_threshold']}")
    print(f"  Position size: {base['position_size']} → {adjusted['position_size']}")
    print()


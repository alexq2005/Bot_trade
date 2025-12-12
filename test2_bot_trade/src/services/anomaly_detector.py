"""
Anomaly Detector - Detecta comportamientos anómalos
Identifica volumen, precio o spread inusuales que preceden movimientos
"""
import pandas as pd
import numpy as np
from typing import Dict, List


class AnomalyDetector:
    """Detecta anomalías en volumen, precio, spread"""
    
    def detect(self, df: pd.DataFrame, current_quote: Dict = None) -> Dict:
        """
        Detecta anomalías
        
        Args:
            df: DataFrame histórico
            current_quote: Quote actual con bid/ask (opcional)
        """
        if len(df) < 20:
            return {'error': 'Datos insuficientes', 'score': 0}
        
        try:
            score = 0
            anomalies = []
            
            # 1. Anomalía de volumen
            current_volume = df['volume'].iloc[-1]
            avg_volume = df['volume'].tail(20).mean()
            
            if current_volume > avg_volume * 5:
                score += 25
                anomalies.append(('VOLUME_SPIKE', +25, f'Volumen {current_volume/avg_volume:.1f}x promedio'))
            elif current_volume > avg_volume * 3:
                score += 15
                anomalies.append(('HIGH_VOLUME', +15, f'Volumen {current_volume/avg_volume:.1f}x promedio'))
            
            # 2. Anomalía de precio
            current_price = df['close'].iloc[-1]
            prev_price = df['close'].iloc[-2]
            price_change = abs(current_price - prev_price) / prev_price
            
            if price_change > 0.10:  # >10% en una vela
                if current_price > prev_price:
                    score += 20
                    anomalies.append(('PRICE_BREAKOUT', +20, f'Subida {price_change*100:.1f}%'))
                else:
                    score -= 25
                    anomalies.append(('PRICE_CRASH', -25, f'Caída {price_change*100:.1f}%'))
            elif price_change > 0.05:  # >5%
                if current_price > prev_price:
                    score += 10
                    anomalies.append(('STRONG_MOVE_UP', +10, f'Subida {price_change*100:.1f}%'))
                else:
                    score -= 10
                    anomalies.append(('STRONG_MOVE_DOWN', -10, f'Caída {price_change*100:.1f}%'))
            
            # 3. Anomalía de spread (si hay quote)
            if current_quote:
                bid = current_quote.get('bid', current_quote.get('precioCompra', 0))
                ask = current_quote.get('ask', current_quote.get('precioVenta', 0))
                
                if bid > 0 and ask > bid:
                    spread = (ask - bid) / bid
                    
                    if spread > 0.03:  # >3% spread
                        score -= 10
                        anomalies.append(('WIDE_SPREAD', -10, f'Spread {spread*100:.2f}% (incertidumbre)'))
            
            return {
                'score': score,
                'anomalies': anomalies,
                'count': len(anomalies),
                'confidence': 'HIGH' if len(anomalies) > 0 else 'LOW'
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}


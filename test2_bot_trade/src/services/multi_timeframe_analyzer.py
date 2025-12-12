"""
Multi-Timeframe Analyzer - Analiza múltiples temporalidades
Mejora timing combinando tendencias de diferentes timeframes
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import yfinance as yf
from ta.trend import SMAIndicator, EMAIndicator
from ta.momentum import RSIIndicator


class MultiTimeframeAnalyzer:
    """
    Analiza múltiples timeframes para mejor timing
    
    Timeframes:
    - 1D (Diario): Tendencia principal
    - 4H: Tendencia intermedia  
    - 1H: Timing de entrada
    - 15M: Confirmación final (opcional)
    """
    
    def __init__(self):
        self.timeframes = {
            '1D': {'weight': 40, 'period': '3mo'},
            '4H': {'weight': 30, 'period': '1mo'},
            '1H': {'weight': 20, 'period': '7d'},
            '15M': {'weight': 10, 'period': '3d'}
        }
    
    def analyze_all_timeframes(self, symbol: str) -> Dict:
        """
        Analiza símbolo en todos los timeframes
        
        Returns:
            Dict con análisis completo y score ponderado
        """
        results = {}
        total_score = 0
        total_weight = 0
        
        for tf, config in self.timeframes.items():
            try:
                analysis = self._analyze_timeframe(symbol, tf, config['period'])
                
                if analysis and 'score' in analysis:
                    weight = config['weight']
                    weighted_score = analysis['score'] * (weight / 100)
                    total_score += weighted_score
                    total_weight += weight
                    
                    results[tf] = analysis
                    
            except Exception as e:
                results[tf] = {'error': str(e), 'score': 0}
        
        # Calcular score final ponderado
        final_score = total_score if total_weight > 0 else 0
        
        # Determinar señal basada en alineación
        signal = self._determine_signal(results, final_score)
        
        return {
            'signal': signal,
            'score': round(final_score, 2),
            'timeframes': results,
            'alignment': self._check_alignment(results),
            'confidence': self._calculate_confidence(results)
        }
    
    def _analyze_timeframe(self, symbol: str, interval: str, period: str) -> Dict:
        """Analiza un timeframe específico"""
        try:
            # Descargar datos
            df = yf.download(symbol, period=period, interval=interval, progress=False)
            
            if df.empty or len(df) < 20:
                return {'error': 'Datos insuficientes', 'score': 0}
            
            df.columns = [c.lower() for c in df.columns]
            
            # Calcular indicadores
            close = df['close']
            
            # SMA
            sma_20 = SMAIndicator(close, window=20).sma_indicator()
            sma_50 = SMAIndicator(close, window=min(50, len(df))).sma_indicator()
            
            # EMA
            ema_12 = EMAIndicator(close, window=12).ema_indicator()
            ema_26 = EMAIndicator(close, window=min(26, len(df))).ema_indicator()
            
            # RSI
            rsi = RSIIndicator(close, window=14).rsi()
            
            # Valores actuales
            current_price = close.iloc[-1]
            current_sma20 = sma_20.iloc[-1]
            current_sma50 = sma_50.iloc[-1] if len(df) >= 50 else current_sma20
            current_ema12 = ema_12.iloc[-1]
            current_ema26 = ema_26.iloc[-1] if len(df) >= 26 else current_ema12
            current_rsi = rsi.iloc[-1]
            
            # Calcular score
            score = 0
            factors = []
            
            # Tendencia (SMA)
            if current_price > current_sma20:
                score += 10
                factors.append(f'Price > SMA20 (+10)')
            else:
                score -= 10
                factors.append(f'Price < SMA20 (-10)')
            
            if current_sma20 > current_sma50:
                score += 15
                factors.append(f'SMA20 > SMA50 (+15)')
            else:
                score -= 15
                factors.append(f'SMA20 < SMA50 (-15)')
            
            # Momentum (EMA)
            if current_ema12 > current_ema26:
                score += 10
                factors.append(f'EMA12 > EMA26 (+10)')
            else:
                score -= 10
                factors.append(f'EMA12 < EMA26 (-10)')
            
            # RSI
            if current_rsi < 40:
                score += 10
                factors.append(f'RSI oversold (+10)')
            elif current_rsi > 60:
                score -= 10
                factors.append(f'RSI overbought (-10)')
            
            # Determinar tendencia
            if score > 15:
                trend = 'BULLISH'
            elif score < -15:
                trend = 'BEARISH'
            else:
                trend = 'NEUTRAL'
            
            return {
                'interval': interval,
                'score': score,
                'trend': trend,
                'factors': factors,
                'price': round(current_price, 2),
                'sma20': round(current_sma20, 2),
                'sma50': round(current_sma50, 2),
                'rsi': round(current_rsi, 2)
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}
    
    def _determine_signal(self, results: Dict, score: float) -> str:
        """Determina señal final basada en score y alineación"""
        if score >= 20:
            return 'BUY'
        elif score <= -20:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _check_alignment(self, results: Dict) -> Dict:
        """
        Verifica alineación entre timeframes
        
        Alineación perfecta:
        - Todos los timeframes con misma tendencia
        - Da más confianza a la señal
        """
        trends = [r.get('trend') for r in results.values() if 'trend' in r]
        
        if not trends:
            return {'aligned': False, 'percentage': 0}
        
        # Contar tendencias
        bullish = trends.count('BULLISH')
        bearish = trends.count('BEARISH')
        neutral = trends.count('NEUTRAL')
        total = len(trends)
        
        # Alineación alcista
        if bullish >= total * 0.75:  # 75%+ alcistas
            return {
                'aligned': True,
                'direction': 'BULLISH',
                'percentage': (bullish / total) * 100,
                'bonus': +15  # Bonus por alineación
            }
        
        # Alineación bajista
        if bearish >= total * 0.75:
            return {
                'aligned': True,
                'direction': 'BEARISH',
                'percentage': (bearish / total) * 100,
                'bonus': -15
            }
        
        # Sin alineación
        return {
            'aligned': False,
            'percentage': max(bullish, bearish, neutral) / total * 100,
            'bonus': 0
        }
    
    def _calculate_confidence(self, results: Dict) -> str:
        """Calcula confianza global del análisis"""
        successful = sum(1 for r in results.values() if 'score' in r and r['score'] != 0)
        total = len(results)
        
        success_rate = successful / total if total > 0 else 0
        
        if success_rate >= 0.75:  # 75%+ timeframes analizados
            return 'HIGH'
        elif success_rate >= 0.50:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_summary(self, analysis: Dict) -> str:
        """Genera resumen legible"""
        signal = analysis.get('signal', 'HOLD')
        score = analysis.get('score', 0)
        alignment = analysis.get('alignment', {})
        confidence = analysis.get('confidence', 'LOW')
        
        emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}.get(signal, '⚪')
        
        summary = f"{emoji} Señal Multi-Timeframe: {signal}\n"
        summary += f"   Score: {score} | Confianza: {confidence}\n"
        
        if alignment.get('aligned'):
            summary += f"   ✅ Alineación: {alignment['direction']} ({alignment['percentage']:.0f}%)\n"
        else:
            summary += f"   ⚠️  Sin alineación clara\n"
        
        summary += "\n   Timeframes:\n"
        for tf, result in analysis.get('timeframes', {}).items():
            if 'trend' in result:
                trend_emoji = {'BULLISH': '📈', 'BEARISH': '📉', 'NEUTRAL': '➡️'}.get(result['trend'], '❓')
                summary += f"   {tf}: {trend_emoji} {result['trend']} (Score: {result['score']})\n"
        
        return summary


# Test
if __name__ == "__main__":
    analyzer = MultiTimeframeAnalyzer()
    
    print("="*70)
    print("MULTI-TIMEFRAME ANALYSIS TEST")
    print("="*70)
    print()
    
    result = analyzer.analyze_all_timeframes('AAPL')
    
    print(analyzer.get_summary(result))
    print()
    print("Detalles completos:")
    print(result)


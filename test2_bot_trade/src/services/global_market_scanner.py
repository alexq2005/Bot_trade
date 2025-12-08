"""
Global Market Scanner
Sistema que escanea el mercado completo y encuentra oportunidades de trading automáticamente
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging
import json
from collections import defaultdict

logger = logging.getLogger('global_market_scanner')

class GlobalMarketScanner:
    """
    Escanea el mercado completo y encuentra oportunidades de trading
    
    Funcionalidades:
    - Escaneo automático de todos los instrumentos disponibles
    - Detección de oportunidades basada en múltiples criterios
    - Ranking y priorización automática
    - Filtrado inteligente
    - Actualización continua
    """
    
    def __init__(self, iol_client, data_service, trading_bot=None):
        """
        Args:
            iol_client: Cliente IOL para obtener instrumentos
            data_service: Servicio de datos históricos
            trading_bot: Referencia al bot (opcional, para usar sus estrategias)
        """
        self.iol_client = iol_client
        self.data_service = data_service
        self.trading_bot = trading_bot
        
        # Caché de resultados
        self.scan_cache = {}
        self.cache_ttl = timedelta(minutes=5)  # Cache por 5 minutos
        
        # Configuración
        self.min_score_threshold = 30.0  # Score mínimo para considerar oportunidad
        self.max_opportunities = 50  # Máximo de oportunidades a retornar
        self.min_volume = 1000000  # Volumen mínimo diario
        self.min_price = 1.0  # Precio mínimo (evitar penny stocks)
        
        # Estadísticas
        self.scan_stats = {
            'total_scans': 0,
            'opportunities_found': 0,
            'last_scan_time': None
        }
    
    def scan_market(self, 
                   categories: List[str] = None,
                   max_symbols: int = 500,
                   use_cache: bool = True) -> List[Dict]:
        """
        Escanea el mercado completo y encuentra oportunidades
        
        Args:
            categories: Categorías a escanear (None = todas)
            max_symbols: Máximo de símbolos a analizar
            use_cache: Usar caché si está disponible
            
        Returns:
            Lista de oportunidades ordenadas por score
        """
        try:
            # Verificar caché
            if use_cache and self._is_cache_valid():
                logger.info("Usando resultados de caché")
                return self.scan_cache.get('opportunities', [])
            
            logger.info(f"🔍 Iniciando escaneo global del mercado...")
            start_time = datetime.now()
            
            # 1. Obtener todos los instrumentos
            from src.services.iol_universe_loader import IOLUniverseLoader
            universe_loader = IOLUniverseLoader(self.iol_client)
            
            if categories is None:
                categories = ['acciones', 'cedears']  # Por defecto, acciones y CEDEARs
            
            all_instruments = universe_loader.get_all_instruments(categories)
            
            # 2. Combinar todos los símbolos
            all_symbols = []
            for category, symbols in all_instruments.items():
                all_symbols.extend(symbols[:max_symbols // len(all_instruments)])
            
            all_symbols = all_symbols[:max_symbols]
            logger.info(f"📊 Analizando {len(all_symbols)} símbolos...")
            
            # 3. Escanear cada símbolo
            opportunities = []
            scanned = 0
            
            for symbol in all_symbols:
                try:
                    opportunity = self._scan_symbol(symbol)
                    if opportunity and opportunity['score'] >= self.min_score_threshold:
                        opportunities.append(opportunity)
                    scanned += 1
                    
                    # Log progreso cada 50 símbolos
                    if scanned % 50 == 0:
                        logger.info(f"   Procesados: {scanned}/{len(all_symbols)} ({len(opportunities)} oportunidades)")
                
                except Exception as e:
                    logger.debug(f"Error escaneando {symbol}: {e}")
                    continue
            
            # 4. Ordenar por score (mayor a menor)
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            # 5. Limitar resultados
            opportunities = opportunities[:self.max_opportunities]
            
            # 6. Actualizar estadísticas
            elapsed = (datetime.now() - start_time).total_seconds()
            self.scan_stats['total_scans'] += 1
            self.scan_stats['opportunities_found'] += len(opportunities)
            self.scan_stats['last_scan_time'] = datetime.now()
            
            # 7. Guardar en caché
            self.scan_cache = {
                'opportunities': opportunities,
                'timestamp': datetime.now(),
                'symbols_scanned': scanned
            }
            
            logger.info(f"✅ Escaneo completado: {len(opportunities)} oportunidades encontradas en {elapsed:.1f}s")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error en escaneo global: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _scan_symbol(self, symbol: str) -> Optional[Dict]:
        """
        Escanea un símbolo individual y detecta oportunidades
        
        Returns:
            Dict con información de la oportunidad o None
        """
        try:
            # 1. Obtener datos históricos
            df = self.data_service.get_historical_data(symbol, period='3mo')
            if df is None or len(df) < 30:
                return None
            
            # 2. Filtros básicos
            if not self._passes_basic_filters(df, symbol):
                return None
            
            # 3. Análisis rápido (usar estrategias del bot si está disponible)
            analysis_result = self._quick_analysis(symbol, df)
            
            if not analysis_result:
                return None
            
            # 4. Calcular score total
            total_score = analysis_result.get('score', 0)
            
            # 5. Determinar señal
            signal = 'BUY' if total_score > 0 else 'SELL' if total_score < -self.min_score_threshold else None
            
            if signal is None:
                return None
            
            # 6. Calcular confianza
            confidence = self._calculate_confidence(analysis_result, df)
            
            # 7. Información adicional
            current_price = df['Close'].iloc[-1] if 'Close' in df.columns else df['close'].iloc[-1]
            volume = df['Volume'].iloc[-1] if 'Volume' in df.columns else df['volume'].iloc[-1] if 'volume' in df.columns else 0
            
            return {
                'symbol': symbol,
                'signal': signal,
                'score': abs(total_score),
                'confidence': confidence,
                'current_price': float(current_price),
                'volume': float(volume),
                'analysis': analysis_result,
                'timestamp': datetime.now().isoformat(),
                'factors': analysis_result.get('factors', [])
            }
            
        except Exception as e:
            logger.debug(f"Error escaneando {symbol}: {e}")
            return None
    
    def _passes_basic_filters(self, df: pd.DataFrame, symbol: str) -> bool:
        """Filtros básicos para descartar símbolos"""
        try:
            # Precio mínimo
            current_price = df['Close'].iloc[-1] if 'Close' in df.columns else df['close'].iloc[-1]
            if current_price < self.min_price:
                return False
            
            # Volumen mínimo
            if 'Volume' in df.columns:
                avg_volume = df['Volume'].tail(20).mean()
                if avg_volume < self.min_volume:
                    return False
            elif 'volume' in df.columns:
                avg_volume = df['volume'].tail(20).mean()
                if avg_volume < self.min_volume:
                    return False
            
            # Datos suficientes
            if len(df) < 30:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _quick_analysis(self, symbol: str, df: pd.DataFrame) -> Optional[Dict]:
        """
        Análisis rápido usando estrategias del bot o análisis simplificado
        """
        try:
            # Si tenemos acceso al bot, usar sus estrategias
            if self.trading_bot and hasattr(self.trading_bot, 'analyze_symbol'):
                # Análisis completo (puede ser lento, pero más preciso)
                result = self.trading_bot.analyze_symbol(symbol, df=df, quick_mode=True)
                if result:
                    return {
                        'score': result.get('score', 0),
                        'signal': result.get('signal', 'NEUTRAL'),
                        'factors': result.get('buy_factors', []) + result.get('sell_factors', []),
                        'analysis_type': 'full'
                    }
            
            # Análisis simplificado (más rápido)
            return self._simplified_analysis(symbol, df)
            
        except Exception as e:
            logger.debug(f"Error en análisis rápido de {symbol}: {e}")
            return self._simplified_analysis(symbol, df)
    
    def _simplified_analysis(self, symbol: str, df: pd.DataFrame) -> Optional[Dict]:
        """Análisis simplificado y rápido"""
        try:
            score = 0
            factors = []
            
            # Asegurar nombres de columnas
            df.columns = [c.capitalize() for c in df.columns]
            
            prices = df['Close'].values
            volumes = df['Volume'].values if 'Volume' in df.columns else np.ones(len(df))
            
            # 1. Momentum (últimos 5 días vs últimos 20 días)
            if len(prices) >= 20:
                short_momentum = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] > 0 else 0
                long_momentum = (prices[-1] - prices[-20]) / prices[-20] if prices[-20] > 0 else 0
                
                if short_momentum > 0.02:  # +2% en 5 días
                    score += 15
                    factors.append(f"Momentum corto: +{short_momentum:.2%}")
                
                if long_momentum > 0.05:  # +5% en 20 días
                    score += 10
                    factors.append(f"Momentum largo: +{long_momentum:.2%}")
            
            # 2. Volumen (aumento de volumen reciente)
            if len(volumes) >= 20:
                recent_volume = volumes[-5:].mean()
                avg_volume = volumes[-20:].mean()
                
                if recent_volume > avg_volume * 1.5:  # 50% más volumen
                    score += 10
                    factors.append(f"Volumen aumentado: +{(recent_volume/avg_volume - 1):.1%}")
            
            # 3. RSI simplificado
            if len(prices) >= 14:
                returns = np.diff(prices) / prices[:-1]
                gains = returns[returns > 0]
                losses = -returns[returns < 0]
                
                if len(gains) > 0 and len(losses) > 0:
                    avg_gain = gains[-14:].mean() if len(gains) >= 14 else gains.mean()
                    avg_loss = losses[-14:].mean() if len(losses) >= 14 else losses.mean()
                    
                    if avg_loss > 0:
                        rs = avg_gain / avg_loss
                        rsi = 100 - (100 / (1 + rs))
                        
                        if rsi < 30:  # Oversold
                            score += 20
                            factors.append(f"RSI Oversold: {rsi:.1f}")
                        elif rsi > 70:  # Overbought
                            score -= 20
                            factors.append(f"RSI Overbought: {rsi:.1f}")
            
            # 4. Breakout (precio rompiendo resistencia)
            if len(prices) >= 20:
                resistance = prices[-20:-5].max()
                current_price = prices[-1]
                
                if current_price > resistance * 1.02:  # 2% por encima de resistencia
                    score += 15
                    factors.append(f"Breakout: +{(current_price/resistance - 1):.2%}")
            
            return {
                'score': score,
                'signal': 'BUY' if score > 0 else 'SELL' if score < 0 else 'NEUTRAL',
                'factors': factors,
                'analysis_type': 'simplified'
            }
            
        except Exception as e:
            logger.debug(f"Error en análisis simplificado: {e}")
            return None
    
    def _calculate_confidence(self, analysis_result: Dict, df: pd.DataFrame) -> float:
        """Calcula confianza en la oportunidad (0-1)"""
        try:
            confidence = 0.5  # Base
            
            score = abs(analysis_result.get('score', 0))
            factors_count = len(analysis_result.get('factors', []))
            
            # Más score = más confianza
            if score > 50:
                confidence += 0.2
            elif score > 30:
                confidence += 0.1
            
            # Más factores = más confianza
            if factors_count >= 3:
                confidence += 0.2
            elif factors_count >= 2:
                confidence += 0.1
            
            # Volumen reciente
            if 'Volume' in df.columns:
                recent_volume = df['Volume'].tail(5).mean()
                avg_volume = df['Volume'].tail(20).mean()
                if recent_volume > avg_volume * 1.2:
                    confidence += 0.1
            
            return min(confidence, 1.0)
            
        except Exception:
            return 0.5
    
    def _is_cache_valid(self) -> bool:
        """Verifica si el caché es válido"""
        if 'timestamp' not in self.scan_cache:
            return False
        
        cache_time = self.scan_cache['timestamp']
        if isinstance(cache_time, str):
            cache_time = datetime.fromisoformat(cache_time)
        
        return (datetime.now() - cache_time) < self.cache_ttl
    
    def get_top_opportunities(self, n: int = 10) -> List[Dict]:
        """Obtiene las N mejores oportunidades"""
        opportunities = self.scan_market()
        return opportunities[:n]
    
    def get_opportunities_by_signal(self, signal: str = 'BUY') -> List[Dict]:
        """Obtiene oportunidades filtradas por señal"""
        opportunities = self.scan_market()
        return [opp for opp in opportunities if opp.get('signal') == signal]
    
    def get_scan_stats(self) -> Dict:
        """Obtiene estadísticas del escaneo"""
        return {
            **self.scan_stats,
            'cache_valid': self._is_cache_valid(),
            'cached_opportunities': len(self.scan_cache.get('opportunities', []))
        }

if __name__ == "__main__":
    print("🔍 Testing Global Market Scanner...")
    # Test básico
    print("✅ Scanner module loaded")


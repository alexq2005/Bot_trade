"""
Correlation Analyzer - Analiza correlación entre activos del portafolio
Evita sobre-concentración y mejora diversificación
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


class CorrelationAnalyzer:
    """Analiza correlación entre activos para mejorar diversificación"""
    
    def __init__(self, lookback_days: int = 60):
        """
        Args:
            lookback_days: Días de historial para calcular correlación
        """
        self.lookback_days = lookback_days
        self.correlation_cache = {}  # Cache de correlaciones calculadas
        self.cache_expiry = {}  # Expiración del cache
        
    def analyze_portfolio(self, 
                         symbols: List[str],
                         data_service=None) -> Dict:
        """
        Analiza correlación del portafolio completo
        
        Args:
            symbols: Lista de símbolos en el portafolio
            data_service: Servicio para obtener datos históricos
            
        Returns:
            Dict con análisis de correlación
        """
        if len(symbols) < 2:
            return {
                'error': 'Se necesitan al menos 2 símbolos',
                'correlation_matrix': None,
                'high_correlation_pairs': [],
                'diversification_score': 0.0
            }
        
        # Obtener datos históricos
        price_data = {}
        for symbol in symbols:
            try:
                if data_service:
                    df = data_service.get_historical_data(symbol, period='3mo')
                else:
                    # Fallback: usar datos simulados
                    df = self._get_simulated_data(symbol)
                
                if df is not None and len(df) > 0:
                    price_data[symbol] = df['close']
            except Exception as e:
                print(f"⚠️  Error obteniendo datos para {symbol}: {e}")
                continue
        
        if len(price_data) < 2:
            return {
                'error': 'Datos insuficientes para análisis',
                'correlation_matrix': None,
                'high_correlation_pairs': [],
                'diversification_score': 0.0
            }
        
        # Calcular matriz de correlación
        correlation_matrix = self._calculate_correlation_matrix(price_data)
        
        # Identificar pares altamente correlacionados
        high_correlation_pairs = self._find_high_correlation_pairs(correlation_matrix, threshold=0.7)
        
        # Calcular score de diversificación
        diversification_score = self._calculate_diversification_score(correlation_matrix)
        
        # Recomendaciones
        recommendations = self._generate_recommendations(
            symbols, correlation_matrix, high_correlation_pairs, diversification_score
        )
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'high_correlation_pairs': high_correlation_pairs,
            'diversification_score': diversification_score,
            'recommendations': recommendations,
            'symbols_analyzed': list(price_data.keys()),
            'analysis_date': datetime.now().isoformat()
        }
    
    def should_add_symbol(self,
                         new_symbol: str,
                         existing_symbols: List[str],
                         data_service=None,
                         max_correlation: float = 0.8) -> Dict:
        """
        Determina si agregar un símbolo mejoraría la diversificación
        
        Args:
            new_symbol: Nuevo símbolo a evaluar
            existing_symbols: Símbolos existentes en portafolio
            data_service: Servicio para obtener datos
            max_correlation: Correlación máxima permitida (default: 0.8)
            
        Returns:
            Dict con decisión y análisis
        """
        if not existing_symbols:
            return {
                'should_add': True,
                'reason': 'Portafolio vacío, cualquier símbolo mejora diversificación',
                'max_correlation': 0.0,
                'avg_correlation': 0.0
            }
        
        # Calcular correlación con símbolos existentes
        correlations = []
        for symbol in existing_symbols:
            try:
                corr = self._calculate_pair_correlation(new_symbol, symbol, data_service)
                if corr is not None:
                    correlations.append({
                        'symbol': symbol,
                        'correlation': corr
                    })
            except Exception as e:
                print(f"⚠️  Error calculando correlación {new_symbol}-{symbol}: {e}")
                continue
        
        if not correlations:
            return {
                'should_add': True,
                'reason': 'No se pudo calcular correlación, asumiendo baja',
                'max_correlation': 0.0,
                'avg_correlation': 0.0
            }
        
        max_corr = max(c['correlation'] for c in correlations)
        avg_corr = np.mean([c['correlation'] for c in correlations])
        
        should_add = max_corr < max_correlation
        
        return {
            'should_add': should_add,
            'reason': self._get_add_reason(should_add, max_corr, max_correlation),
            'max_correlation': max_corr,
            'avg_correlation': avg_corr,
            'correlations': correlations
        }
    
    def get_portfolio_risk(self,
                          symbols: List[str],
                          weights: Optional[Dict[str, float]] = None,
                          data_service=None) -> Dict:
        """
        Calcula riesgo del portafolio considerando correlaciones
        
        Args:
            symbols: Símbolos en portafolio
            weights: Pesos de cada activo (default: igual peso)
            data_service: Servicio para obtener datos
            
        Returns:
            Dict con métricas de riesgo
        """
        if weights is None:
            weights = {s: 1.0 / len(symbols) for s in symbols}
        
        # Obtener datos
        returns_data = {}
        for symbol in symbols:
            try:
                if data_service:
                    df = data_service.get_historical_data(symbol, period='3mo')
                else:
                    df = self._get_simulated_data(symbol)
                
                if df is not None and len(df) > 0:
                    returns_data[symbol] = df['close'].pct_change().dropna()
            except Exception as e:
                print(f"⚠️  Error obteniendo datos para {symbol}: {e}")
                continue
        
        if len(returns_data) < 2:
            return {
                'error': 'Datos insuficientes',
                'portfolio_volatility': 0.0,
                'diversification_benefit': 0.0
            }
        
        # Calcular volatilidad individual
        individual_volatilities = {
            s: returns_data[s].std() * np.sqrt(252)  # Anualizada
            for s in returns_data.keys()
        }
        
        # Calcular matriz de correlación
        returns_df = pd.DataFrame(returns_data)
        correlation_matrix = returns_df.corr()
        
        # Calcular volatilidad del portafolio
        portfolio_variance = 0.0
        for i, s1 in enumerate(returns_data.keys()):
            for j, s2 in enumerate(returns_data.keys()):
                w1 = weights.get(s1, 0)
                w2 = weights.get(s2, 0)
                vol1 = individual_volatilities[s1]
                vol2 = individual_volatilities[s2]
                corr = correlation_matrix.loc[s1, s2]
                
                portfolio_variance += w1 * w2 * vol1 * vol2 * corr
        
        portfolio_volatility = np.sqrt(portfolio_variance)
        
        # Beneficio de diversificación (vs promedio simple)
        avg_individual_vol = np.mean(list(individual_volatilities.values()))
        diversification_benefit = (avg_individual_vol - portfolio_volatility) / avg_individual_vol * 100
        
        return {
            'portfolio_volatility': portfolio_volatility,
            'avg_individual_volatility': avg_individual_vol,
            'diversification_benefit_pct': diversification_benefit,
            'correlation_matrix': correlation_matrix.to_dict(),
            'individual_volatilities': individual_volatilities
        }
    
    def _calculate_correlation_matrix(self, price_data: Dict[str, pd.Series]) -> pd.DataFrame:
        """Calcula matriz de correlación"""
        # Alinear series por fecha
        df = pd.DataFrame(price_data)
        df = df.dropna()  # Eliminar NaN
        
        if len(df) < 10:
            # Datos insuficientes, retornar matriz identidad
            symbols = list(price_data.keys())
            return pd.DataFrame(np.eye(len(symbols)), index=symbols, columns=symbols)
        
        # Calcular retornos
        returns_df = df.pct_change().dropna()
        
        # Matriz de correlación
        correlation_matrix = returns_df.corr()
        
        return correlation_matrix
    
    def _find_high_correlation_pairs(self, 
                                    correlation_matrix: pd.DataFrame,
                                    threshold: float = 0.7) -> List[Dict]:
        """Encuentra pares con alta correlación"""
        high_corr_pairs = []
        
        for i, symbol1 in enumerate(correlation_matrix.index):
            for j, symbol2 in enumerate(correlation_matrix.columns):
                if i < j:  # Evitar duplicados
                    corr = correlation_matrix.loc[symbol1, symbol2]
                    if abs(corr) >= threshold:
                        high_corr_pairs.append({
                            'symbol1': symbol1,
                            'symbol2': symbol2,
                            'correlation': corr,
                            'type': 'positive' if corr > 0 else 'negative'
                        })
        
        # Ordenar por correlación absoluta
        high_corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        return high_corr_pairs
    
    def _calculate_diversification_score(self, correlation_matrix: pd.DataFrame) -> float:
        """Calcula score de diversificación (0-100)"""
        if correlation_matrix.empty:
            return 0.0
        
        # Promedio de correlaciones absolutas (excluyendo diagonal)
        n = len(correlation_matrix)
        if n < 2:
            return 0.0
        
        # Obtener correlaciones (triángulo superior, excluyendo diagonal)
        correlations = []
        for i in range(n):
            for j in range(i + 1, n):
                corr = correlation_matrix.iloc[i, j]
                correlations.append(abs(corr))
        
        if not correlations:
            return 0.0
        
        avg_correlation = np.mean(correlations)
        
        # Score: 100 = no correlación, 0 = correlación perfecta
        diversification_score = (1 - avg_correlation) * 100
        
        return max(0.0, min(100.0, diversification_score))
    
    def _calculate_pair_correlation(self,
                                  symbol1: str,
                                  symbol2: str,
                                  data_service=None) -> Optional[float]:
        """Calcula correlación entre dos símbolos"""
        cache_key = f"{symbol1}_{symbol2}"
        
        # Verificar cache
        if cache_key in self.correlation_cache:
            if datetime.now() < self.cache_expiry.get(cache_key, datetime.min):
                return self.correlation_cache[cache_key]
        
        try:
            # Obtener datos
            if data_service:
                df1 = data_service.get_historical_data(symbol1, period='3mo')
                df2 = data_service.get_historical_data(symbol2, period='3mo')
            else:
                df1 = self._get_simulated_data(symbol1)
                df2 = self._get_simulated_data(symbol2)
            
            if df1 is None or df2 is None:
                return None
            
            # Alinear por fecha
            merged = pd.merge(
                df1[['close']], df2[['close']],
                left_index=True, right_index=True,
                suffixes=('_1', '_2')
            )
            
            if len(merged) < 10:
                return None
            
            # Calcular correlación de retornos
            returns1 = merged['close_1'].pct_change().dropna()
            returns2 = merged['close_2'].pct_change().dropna()
            
            # Alinear
            aligned = pd.concat([returns1, returns2], axis=1).dropna()
            
            if len(aligned) < 10:
                return None
            
            corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
            
            # Guardar en cache (24 horas)
            self.correlation_cache[cache_key] = corr
            self.cache_expiry[cache_key] = datetime.now() + timedelta(hours=24)
            
            return corr
            
        except Exception as e:
            print(f"⚠️  Error calculando correlación {symbol1}-{symbol2}: {e}")
            return None
    
    def _generate_recommendations(self,
                                 symbols: List[str],
                                 correlation_matrix: pd.DataFrame,
                                 high_corr_pairs: List[Dict],
                                 diversification_score: float) -> List[str]:
        """Genera recomendaciones de diversificación"""
        recommendations = []
        
        if diversification_score < 50:
            recommendations.append(
                f"⚠️  Baja diversificación (score: {diversification_score:.1f}/100). "
                "Considera agregar activos de diferentes sectores."
            )
        
        if high_corr_pairs:
            recommendations.append(
                f"⚠️  {len(high_corr_pairs)} par(es) altamente correlacionado(s). "
                "Considera reducir exposición en uno de cada par."
            )
            
            # Mostrar top 3 pares
            for pair in high_corr_pairs[:3]:
                recommendations.append(
                    f"   • {pair['symbol1']} - {pair['symbol2']}: "
                    f"correlación {pair['correlation']:.2f}"
                )
        
        if diversification_score > 70:
            recommendations.append(
                f"✅ Buena diversificación (score: {diversification_score:.1f}/100)"
            )
        
        return recommendations
    
    def _get_add_reason(self, should_add: bool, max_corr: float, threshold: float) -> str:
        """Genera razón para agregar/no agregar símbolo"""
        if should_add:
            return f"Correlación máxima ({max_corr:.2f}) está por debajo del umbral ({threshold:.2f})"
        else:
            return f"Correlación máxima ({max_corr:.2f}) excede el umbral ({threshold:.2f})"
    
    def _get_simulated_data(self, symbol: str) -> pd.DataFrame:
        """Genera datos simulados para testing"""
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        np.random.seed(hash(symbol) % 2**32)
        prices = 100 + np.cumsum(np.random.randn(60) * 0.02)
        return pd.DataFrame({
            'close': prices,
            'open': prices * 0.99,
            'high': prices * 1.01,
            'low': prices * 0.98,
            'volume': np.random.randint(1000, 10000, 60)
        }, index=dates)


# Test
if __name__ == "__main__":
    analyzer = CorrelationAnalyzer()
    
    # Test 1: Análisis de portafolio
    print("=== Test 1: Análisis de Portafolio ===")
    symbols = ['GGAL', 'PAMP', 'YPF', 'KO', 'LOMA']
    result = analyzer.analyze_portfolio(symbols)
    
    print(f"Score de diversificación: {result['diversification_score']:.1f}/100")
    print(f"Pares altamente correlacionados: {len(result['high_correlation_pairs'])}")
    print("\nRecomendaciones:")
    for rec in result['recommendations']:
        print(f"  {rec}")
    print()
    
    # Test 2: ¿Agregar símbolo?
    print("=== Test 2: ¿Agregar Nuevo Símbolo? ===")
    decision = analyzer.should_add_symbol('AAPL', ['GGAL', 'PAMP', 'YPF'])
    print(f"¿Agregar?: {decision['should_add']}")
    print(f"Razón: {decision['reason']}")
    print(f"Correlación máxima: {decision['max_correlation']:.2f}")


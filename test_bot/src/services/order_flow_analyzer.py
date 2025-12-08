"""
Order Flow Analyzer - Analiza flujo de órdenes (bid/ask)
Detecta presión compradora/vendedora en tiempo real
"""
from typing import Dict, Optional


class OrderFlowAnalyzer:
    """
    Analiza el libro de órdenes para detectar presión
    """
    
    def __init__(self, iol_client):
        self.iol_client = iol_client
    
    def analyze_flow(self, symbol: str) -> Dict:
        """
        Analiza flujo de órdenes
        
        Returns:
            Dict con presión, score y detalles
        """
        try:
            # Obtener profundidad de mercado
            depth = self.iol_client.get_market_depth(symbol)
            
            if 'error' in depth:
                return {'error': depth['error'], 'score': 0}
            
            # Analizar bids (compradores)
            bids = depth.get('bids', depth.get('compra', []))
            # Analizar asks (vendedores)  
            asks = depth.get('asks', depth.get('venta', []))
            
            if not bids or not asks:
                return {'error': 'No hay datos de profundidad', 'score': 0}
            
            # Calcular volumen total en cada lado
            bid_volume = sum(b.get('quantity', b.get('cantidad', 0)) for b in bids[:5])
            ask_volume = sum(a.get('quantity', a.get('cantidad', 0)) for a in asks[:5])
            
            # Calcular presión (ratio)
            if ask_volume == 0:
                pressure_ratio = 10.0  # Mucha presión compradora
            else:
                pressure_ratio = bid_volume / ask_volume
            
            # Calcular spread
            best_bid = bids[0].get('price', bids[0].get('precio', 0)) if bids else 0
            best_ask = asks[0].get('price', asks[0].get('precio', 0)) if asks else 0
            
            spread = (best_ask - best_bid) if best_ask > best_bid else 0
            spread_pct = (spread / best_ask * 100) if best_ask > 0 else 0
            
            # Determinar presión y score
            score = 0
            pressure = 'NEUTRAL'
            factors = []
            
            if pressure_ratio > 1.5:
                # Más compradores que vendedores
                score = min(30, int((pressure_ratio - 1) * 20))
                pressure = 'BUYING'
                factors.append(f'Presión compradora (+{score})')
            elif pressure_ratio < 0.67:
                # Más vendedores que compradores
                score = max(-30, -int((1 - pressure_ratio) * 30))
                pressure = 'SELLING'
                factors.append(f'Presión vendedora ({score})')
            
            # Spread ajusta score
            if spread_pct > 1.0:
                # Spread amplio = incertidumbre
                score = int(score * 0.7)  # Reducir confianza
                factors.append(f'Spread amplio ({spread_pct:.2f}%) reduce confianza')
            
            return {
                'pressure': pressure,
                'score': score,
                'pressure_ratio': round(pressure_ratio, 2),
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'spread': round(spread, 2),
                'spread_pct': round(spread_pct, 3),
                'best_bid': best_bid,
                'best_ask': best_ask,
                'factors': factors
            }
            
        except Exception as e:
            return {'error': str(e), 'score': 0}
    
    def get_summary(self, analysis: Dict) -> str:
        """Genera resumen legible"""
        pressure = analysis.get('pressure', 'NEUTRAL')
        score = analysis.get('score', 0)
        ratio = analysis.get('pressure_ratio', 1.0)
        
        emoji = {
            'BUYING': '🟢',
            'SELLING': '🔴',
            'NEUTRAL': '🟡'
        }.get(pressure, '⚪')
        
        summary = f"{emoji} Order Flow: {pressure}\n"
        summary += f"   Score: {score:+d}\n"
        summary += f"   Ratio Bid/Ask: {ratio:.2f}x\n"
        
        if 'factors' in analysis:
            for factor in analysis['factors']:
                summary += f"   • {factor}\n"
        
        return summary


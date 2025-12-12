"""
Commission Calculator - Calcula comisiones y spreads de IOL
Integra costos reales en decisiones de trading
"""
from typing import Dict, Optional
from decimal import Decimal, ROUND_HALF_UP


class CommissionCalculator:
    """Calcula comisiones y spreads para operaciones en IOL"""
    
    def __init__(self):
        # Comisiones IOL (actualizadas 2025)
        # Fuente: https://www.invertironline.com/tarifas
        self.commission_rates = {
            'cedear': 0.006,  # 0.6% por operación
            'accion_local': 0.006,  # 0.6% por operación
            'bono': 0.003,  # 0.3% por operación
            'opcion': 0.01,  # 1% por operación
            'default': 0.006  # Default: 0.6%
        }
        
        # Comisión mínima
        self.min_commission = 50.0  # $50 ARS mínimo
        
        # Spread típico (bid-ask)
        self.default_spread_pct = 0.005  # 0.5% típico
        
    def calculate_commission(self, 
                           symbol: str, 
                           price: float, 
                           quantity: int,
                           operation_type: str = 'BUY') -> Dict:
        """
        Calcula comisión para una operación
        
        Args:
            symbol: Símbolo del activo
            price: Precio por acción
            quantity: Cantidad de acciones
            operation_type: 'BUY' o 'SELL'
            
        Returns:
            Dict con comisión, total, etc.
        """
        # Determinar tipo de activo
        asset_type = self._detect_asset_type(symbol)
        commission_rate = self.commission_rates.get(asset_type, self.commission_rates['default'])
        
        # Calcular comisión
        total_value = price * quantity
        commission = total_value * commission_rate
        
        # Aplicar mínimo
        if commission < self.min_commission:
            commission = self.min_commission
        
        # Redondear a 2 decimales
        commission = float(Decimal(str(commission)).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        ))
        
        return {
            'commission': commission,
            'commission_rate': commission_rate,
            'total_value': total_value,
            'total_with_commission': total_value + commission if operation_type == 'BUY' else total_value - commission,
            'asset_type': asset_type,
            'operation_type': operation_type
        }
    
    def calculate_round_trip_cost(self,
                                 symbol: str,
                                 buy_price: float,
                                 sell_price: float,
                                 quantity: int) -> Dict:
        """
        Calcula costo total de ida y vuelta (compra + venta)
        
        Args:
            symbol: Símbolo
            buy_price: Precio de compra
            sell_price: Precio de venta
            quantity: Cantidad
            
        Returns:
            Dict con costos totales
        """
        buy_cost = self.calculate_commission(symbol, buy_price, quantity, 'BUY')
        sell_cost = self.calculate_commission(symbol, sell_price, quantity, 'SELL')
        
        total_commissions = buy_cost['commission'] + sell_cost['commission']
        total_cost = total_commissions
        
        # Calcular P&L neto (después de comisiones)
        gross_pnl = (sell_price - buy_price) * quantity
        net_pnl = gross_pnl - total_commissions
        
        # Calcular % mínimo necesario para cubrir costos
        min_profit_pct = (total_commissions / (buy_price * quantity)) * 100
        
        return {
            'buy_commission': buy_cost['commission'],
            'sell_commission': sell_cost['commission'],
            'total_commissions': total_commissions,
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'min_profit_pct_to_break_even': min_profit_pct,
            'break_even_price': buy_price * (1 + min_profit_pct / 100)
        }
    
    def estimate_spread(self, symbol: str, current_price: float) -> Dict:
        """
        Estima spread bid-ask
        
        Args:
            symbol: Símbolo
            current_price: Precio actual
            
        Returns:
            Dict con spread estimado
        """
        # Spread típico varía por liquidez
        # Activos líquidos: 0.2-0.5%
        # Activos ilíquidos: 1-2%
        
        spread_pct = self._estimate_spread_by_liquidity(symbol)
        spread_amount = current_price * spread_pct
        
        return {
            'spread_pct': spread_pct,
            'spread_amount': spread_amount,
            'bid_price': current_price * (1 - spread_pct / 2),
            'ask_price': current_price * (1 + spread_pct / 2),
            'estimated_cost': spread_amount
        }
    
    def should_execute_trade(self,
                            symbol: str,
                            entry_price: float,
                            exit_price: float,
                            quantity: int,
                            expected_profit_pct: float) -> Dict:
        """
        Determina si un trade es rentable después de comisiones
        
        Args:
            symbol: Símbolo
            entry_price: Precio de entrada
            exit_price: Precio de salida esperado
            quantity: Cantidad
            expected_profit_pct: Ganancia esperada (%)
            
        Returns:
            Dict con decisión y análisis
        """
        round_trip = self.calculate_round_trip_cost(symbol, entry_price, exit_price, quantity)
        spread = self.estimate_spread(symbol, entry_price)
        
        # Costo total (comisiones + spread)
        total_cost = round_trip['total_commissions'] + spread['estimated_cost']
        total_cost_pct = (total_cost / (entry_price * quantity)) * 100
        
        # Ganancia neta esperada
        expected_profit_amount = (exit_price - entry_price) * quantity
        net_profit = expected_profit_amount - total_cost
        net_profit_pct = (net_profit / (entry_price * quantity)) * 100
        
        # Decisión
        should_execute = net_profit_pct > 0.5  # Mínimo 0.5% de ganancia neta
        
        return {
            'should_execute': should_execute,
            'expected_profit_pct': expected_profit_pct,
            'total_cost_pct': total_cost_pct,
            'net_profit_pct': net_profit_pct,
            'total_cost': total_cost,
            'net_profit': net_profit,
            'break_even_price': round_trip['break_even_price'],
            'recommendation': 'EXECUTE' if should_execute else 'SKIP',
            'reason': self._get_reason(should_execute, net_profit_pct, total_cost_pct)
        }
    
    def _detect_asset_type(self, symbol: str) -> str:
        """Detecta tipo de activo por símbolo"""
        symbol_upper = symbol.upper()
        
        # CEDEARs (suelen tener formato específico)
        if any(x in symbol_upper for x in ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA']):
            return 'cedear'
        
        # Bonos (suelen tener formato específico)
        if any(x in symbol_upper for x in ['AL', 'AE', 'DICP', 'PARP']):
            return 'bono'
        
        # Opciones
        if 'OP' in symbol_upper or 'CALL' in symbol_upper or 'PUT' in symbol_upper:
            return 'opcion'
        
        # Default: acción local
        return 'accion_local'
    
    def _estimate_spread_by_liquidity(self, symbol: str) -> float:
        """Estima spread basado en liquidez del activo"""
        # Activos muy líquidos (índices, blue chips)
        high_liquidity = ['GGAL', 'PAMP', 'YPF', 'MIRG', 'TXAR', 'BBAR', 'BMA']
        
        # Activos medianamente líquidos
        medium_liquidity = ['KO', 'LOMA', 'EDN', 'CEPU']
        
        symbol_upper = symbol.upper()
        
        if any(x in symbol_upper for x in high_liquidity):
            return 0.002  # 0.2%
        elif any(x in symbol_upper for x in medium_liquidity):
            return 0.005  # 0.5%
        else:
            return 0.01  # 1% para activos menos líquidos
    
    def _get_reason(self, should_execute: bool, net_profit_pct: float, total_cost_pct: float) -> str:
        """Genera razón para la decisión"""
        if should_execute:
            return f"Rentable: +{net_profit_pct:.2f}% neto después de costos ({total_cost_pct:.2f}%)"
        else:
            if net_profit_pct < 0:
                return f"No rentable: {net_profit_pct:.2f}% neto (costos: {total_cost_pct:.2f}%)"
            else:
                return f"Ganancia muy pequeña: +{net_profit_pct:.2f}% neto (costos: {total_cost_pct:.2f}%)"


# Test
if __name__ == "__main__":
    calc = CommissionCalculator()
    
    # Test 1: Comisión simple
    print("=== Test 1: Comisión de Compra ===")
    result = calc.calculate_commission('GGAL', 1000.0, 10, 'BUY')
    print(f"Precio: ${result['total_value']:.2f}")
    print(f"Comisión: ${result['commission']:.2f} ({result['commission_rate']*100:.2f}%)")
    print(f"Total: ${result['total_with_commission']:.2f}")
    print()
    
    # Test 2: Round trip
    print("=== Test 2: Costo Ida y Vuelta ===")
    round_trip = calc.calculate_round_trip_cost('GGAL', 1000.0, 1050.0, 10)
    print(f"Comisión compra: ${round_trip['buy_commission']:.2f}")
    print(f"Comisión venta: ${round_trip['sell_commission']:.2f}")
    print(f"Total comisiones: ${round_trip['total_commissions']:.2f}")
    print(f"P&L bruto: ${round_trip['gross_pnl']:.2f}")
    print(f"P&L neto: ${round_trip['net_pnl']:.2f}")
    print(f"Mínimo para break-even: {round_trip['min_profit_pct_to_break_even']:.2f}%")
    print()
    
    # Test 3: Decisión de trade
    print("=== Test 3: ¿Ejecutar Trade? ===")
    decision = calc.should_execute_trade('GGAL', 1000.0, 1030.0, 10, 3.0)
    print(f"Ganancia esperada: {decision['expected_profit_pct']:.2f}%")
    print(f"Costo total: {decision['total_cost_pct']:.2f}%")
    print(f"Ganancia neta: {decision['net_profit_pct']:.2f}%")
    print(f"Decisión: {decision['recommendation']}")
    print(f"Razón: {decision['reason']}")


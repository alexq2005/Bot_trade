"""
Trailing Stop Loss - Maximiza ganancias protegiendo capital
Mueve el stop loss automáticamente cuando el precio sube
"""
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
import json


class TrailingStopLoss:
    """
    Gestiona trailing stop loss para posiciones abiertas
    
    Ejemplo:
        - Compra: $100, Stop inicial: $95 (5% riesgo)
        - Precio sube a $110 → Stop sube a $105 (asegura +5%)
        - Precio sube a $120 → Stop sube a $114 (asegura +14%)
        - Si el precio baja a $114 → Vende automáticamente
        - Ganancia asegurada: +14% (vs +0% con stop fijo)
    """
    
    def __init__(self, iol_client=None, telegram_bot=None):
        self.iol_client = iol_client
        self.telegram_bot = telegram_bot
        self.positions_file = Path("trailing_stops.json")
        self.trailing_stops = self._load_trailing_stops()
        
    def _load_trailing_stops(self) -> Dict:
        """Carga trailing stops guardados"""
        if not self.positions_file.exists():
            return {}
        
        try:
            with open(self.positions_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_trailing_stops(self):
        """Guarda trailing stops"""
        try:
            with open(self.positions_file, 'w') as f:
                json.dump(self.trailing_stops, f, indent=2)
        except Exception as e:
            print(f"⚠️  Error guardando trailing stops: {e}")
    
    def add_position(
        self, 
        symbol: str, 
        entry_price: float, 
        quantity: int,
        initial_stop_loss: float,
        trail_pct: float = 5.0,
        activation_pct: float = 3.0
    ):
        """
        Agrega una posición con trailing stop loss
        
        Args:
            symbol: Símbolo del activo
            entry_price: Precio de entrada
            quantity: Cantidad de acciones
            initial_stop_loss: Stop loss inicial
            trail_pct: % que mantiene de distancia (default: 5%)
            activation_pct: % de ganancia para activar trailing (default: 3%)
        """
        self.trailing_stops[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'initial_stop_loss': initial_stop_loss,
            'current_stop_loss': initial_stop_loss,
            'highest_price': entry_price,
            'trail_pct': trail_pct,
            'activation_pct': activation_pct,
            'activated': False,
            'created_at': datetime.now().isoformat(),
            'last_update': datetime.now().isoformat()
        }
        
        self._save_trailing_stops()
        
        print(f"✅ Trailing stop activado para {symbol}")
        print(f"   Entrada: ${entry_price:.2f}")
        print(f"   Stop inicial: ${initial_stop_loss:.2f}")
        print(f"   Trail: {trail_pct}% | Activación: {activation_pct}%")
    
    def update(self, symbol: str, current_price: float) -> Optional[Dict]:
        """
        Actualiza trailing stop para un símbolo
        
        Returns:
            None si no hay cambios
            Dict con acción si se debe vender
        """
        if symbol not in self.trailing_stops:
            return None
        
        position = self.trailing_stops[symbol]
        entry_price = position['entry_price']
        current_stop = position['current_stop_loss']
        highest_price = position['highest_price']
        trail_pct = position['trail_pct']
        activation_pct = position['activation_pct']
        
        # Actualizar highest price si es necesario
        if current_price > highest_price:
            position['highest_price'] = current_price
            highest_price = current_price
        
        # Calcular ganancia actual
        gain_pct = ((current_price - entry_price) / entry_price) * 100
        
        # Verificar si se debe activar el trailing
        if not position['activated'] and gain_pct >= activation_pct:
            position['activated'] = True
            print(f"\n🎯 Trailing Stop ACTIVADO para {symbol}")
            print(f"   Ganancia actual: +{gain_pct:.2f}%")
            print(f"   A partir de ahora, el stop se moverá con el precio")
            
            if self.telegram_bot:
                try:
                    self.telegram_bot.send_alert(
                        f"🎯 Trailing Stop Activado\n\n"
                        f"Símbolo: {symbol}\n"
                        f"Ganancia: +{gain_pct:.2f}%\n"
                        f"El stop loss se moverá automáticamente"
                    )
                except:
                    pass
        
        # Si está activado, calcular nuevo stop
        if position['activated']:
            # Nuevo stop = precio más alto - trail%
            new_stop = highest_price * (1 - trail_pct / 100)
            
            # Solo subir el stop, nunca bajarlo
            if new_stop > current_stop:
                old_stop = current_stop
                position['current_stop_loss'] = new_stop
                position['last_update'] = datetime.now().isoformat()
                
                print(f"\n📈 Stop Loss actualizado para {symbol}")
                print(f"   Precio actual: ${current_price:.2f}")
                print(f"   Stop anterior: ${old_stop:.2f}")
                print(f"   Stop nuevo: ${new_stop:.2f} (+${new_stop - old_stop:.2f})")
                print(f"   Ganancia asegurada: +{((new_stop - entry_price) / entry_price * 100):.2f}%")
                
                self._save_trailing_stops()
        
        # Verificar si se debe vender (precio toca el stop)
        active_stop = position['current_stop_loss']
        if current_price <= active_stop:
            print(f"\n🚨 TRAILING STOP ALCANZADO para {symbol}")
            print(f"   Precio actual: ${current_price:.2f}")
            print(f"   Stop loss: ${active_stop:.2f}")
            print(f"   → Se debe vender para asegurar ganancia")
            
            gain = ((current_price - entry_price) / entry_price) * 100
            
            if self.telegram_bot:
                try:
                    self.telegram_bot.send_alert(
                        f"🚨 TRAILING STOP ALCANZADO\n\n"
                        f"Símbolo: {symbol}\n"
                        f"Precio: ${current_price:.2f}\n"
                        f"Stop: ${active_stop:.2f}\n"
                        f"Ganancia: +{gain:.2f}%\n\n"
                        f"Se ejecutará venta automática"
                    )
                except:
                    pass
            
            # Remover de tracking (se venderá)
            del self.trailing_stops[symbol]
            self._save_trailing_stops()
            
            return {
                'action': 'SELL',
                'symbol': symbol,
                'reason': 'Trailing stop reached',
                'current_price': current_price,
                'stop_price': active_stop,
                'entry_price': entry_price,
                'gain_pct': gain
            }
        
        return None
    
    def update_all(self, prices: Dict[str, float]) -> list:
        """
        Actualiza todos los trailing stops
        
        Args:
            prices: Dict con {symbol: current_price}
            
        Returns:
            Lista de acciones a tomar (ventas)
        """
        actions = []
        
        for symbol in list(self.trailing_stops.keys()):
            if symbol in prices:
                action = self.update(symbol, prices[symbol])
                if action:
                    actions.append(action)
        
        return actions
    
    def remove_position(self, symbol: str):
        """Remueve trailing stop para un símbolo"""
        if symbol in self.trailing_stops:
            del self.trailing_stops[symbol]
            self._save_trailing_stops()
            print(f"✅ Trailing stop removido para {symbol}")
    
    def get_position_info(self, symbol: str) -> Optional[Dict]:
        """Obtiene información de trailing stop para un símbolo"""
        return self.trailing_stops.get(symbol)
    
    def get_all_positions(self) -> Dict:
        """Obtiene todos los trailing stops activos"""
        return self.trailing_stops.copy()
    
    def get_status_summary(self) -> str:
        """Genera resumen de estado de trailing stops"""
        if not self.trailing_stops:
            return "📊 No hay trailing stops activos"
        
        summary = f"📊 Trailing Stops Activos: {len(self.trailing_stops)}\n\n"
        
        for symbol, pos in self.trailing_stops.items():
            entry = pos['entry_price']
            current_stop = pos['current_stop_loss']
            highest = pos['highest_price']
            activated = "✅ ACTIVO" if pos['activated'] else "⏳ Esperando"
            
            gain_from_entry = ((current_stop - entry) / entry * 100)
            potential_from_high = ((highest - entry) / entry * 100)
            
            summary += f"{symbol}:\n"
            summary += f"  Entrada: ${entry:.2f}\n"
            summary += f"  Stop actual: ${current_stop:.2f}\n"
            summary += f"  Precio máximo: ${highest:.2f}\n"
            summary += f"  Estado: {activated}\n"
            summary += f"  Ganancia asegurada: +{gain_from_entry:.2f}%\n"
            summary += f"  Ganancia potencial: +{potential_from_high:.2f}%\n\n"
        
        return summary


# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia
    tsl = TrailingStopLoss()
    
    # Agregar posición
    tsl.add_position(
        symbol="AAPL",
        entry_price=100.0,
        quantity=10,
        initial_stop_loss=95.0,  # -5%
        trail_pct=5.0,           # Mantiene 5% de distancia
        activation_pct=3.0       # Activa con +3% ganancia
    )
    
    # Simular movimientos de precio
    print("\nSimulación:")
    print("="*50)
    
    # Precio sube a 102 (bajo threshold de activación)
    print("\nPrecio: $102")
    tsl.update("AAPL", 102.0)
    
    # Precio sube a 105 (activa trailing)
    print("\nPrecio: $105")
    tsl.update("AAPL", 105.0)
    
    # Precio sube a 110 (mueve stop)
    print("\nPrecio: $110")
    tsl.update("AAPL", 110.0)
    
    # Precio sube a 115 (mueve stop nuevamente)
    print("\nPrecio: $115")
    tsl.update("AAPL", 115.0)
    
    # Precio baja a 109 (toca stop)
    print("\nPrecio: $109")
    action = tsl.update("AAPL", 109.0)
    
    if action:
        print(f"\n✅ Acción: {action['action']}")
        print(f"   Ganancia: +{action['gain_pct']:.2f}%")


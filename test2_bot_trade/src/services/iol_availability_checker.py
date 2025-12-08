"""
IOL Availability Checker
Verifies if symbols and markets are available in IOL (InvertirOnline).
"""

import os
import sys
from typing import List, Dict, Optional, Tuple
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.connectors.iol_client import IOLClient
from src.services.operation_notifier import OperationNotifier


class IOLAvailabilityChecker:
    """
    Service to check if symbols are available in IOL.
    """
    
    def __init__(self, iol_client: Optional[IOLClient] = None):
        """
        Initialize the availability checker.
        
        Args:
            iol_client: Optional IOLClient instance. If None, will create one.
        """
        self.iol_client = iol_client or IOLClient()
        self.notifier = OperationNotifier()
        self._cache = {}  # Cache results to avoid repeated API calls
    
    def is_symbol_available(self, symbol: str, use_cache: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Check if a symbol is available in IOL.
        
        Args:
            symbol: Symbol to check (e.g., 'GGAL', 'AAPL')
            use_cache: Whether to use cached results
        
        Returns:
            Tuple of (is_available: bool, error_message: Optional[str])
        """
        # Check cache first
        if use_cache and symbol in self._cache:
            return self._cache[symbol]
        
        try:
            # Try to get quote from IOL
            quote = self.iol_client.get_quote(symbol)
            
            # Check if there's an error
            if "error" in quote:
                error_msg = quote.get("error", "Unknown error")
                status_code = quote.get("status_code")
                
                # 404 or similar means symbol not found
                if status_code == 404:
                    result = (False, f"El símbolo {symbol} no está disponible en IOL (404 Not Found)")
                elif status_code == 400:
                    result = (False, f"El símbolo {symbol} no es válido en IOL (400 Bad Request)")
                else:
                    result = (False, f"Error verificando {symbol} en IOL: {error_msg}")
            else:
                # Success - symbol is available
                result = (True, None)
            
            # Cache the result
            self._cache[symbol] = result
            return result
            
        except Exception as e:
            error_msg = f"Excepción verificando {symbol} en IOL: {str(e)}"
            result = (False, error_msg)
            self._cache[symbol] = result
            return result
    
    def check_multiple_symbols(self, symbols: List[str]) -> Dict[str, Tuple[bool, Optional[str]]]:
        """
        Check availability of multiple symbols.
        
        Args:
            symbols: List of symbols to check
        
        Returns:
            Dictionary mapping symbol to (is_available, error_message)
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.is_symbol_available(symbol)
        return results
    
    def get_unavailable_symbols(self, symbols: List[str]) -> List[Tuple[str, str]]:
        """
        Get list of symbols that are NOT available in IOL.
        
        Args:
            symbols: List of symbols to check
        
        Returns:
            List of tuples (symbol, error_message) for unavailable symbols
        """
        unavailable = []
        for symbol in symbols:
            is_available, error_msg = self.is_symbol_available(symbol)
            if not is_available:
                unavailable.append((symbol, error_msg or "No disponible en IOL"))
        return unavailable
    
    def check_market_availability(self, market_code: str, symbols: List[str]) -> Dict:
        """
        Check availability of symbols for a specific market.
        
        Args:
            market_code: Market code (e.g., 'ARG', 'USA')
            symbols: List of symbols to check
        
        Returns:
            Dictionary with availability summary
        """
        results = self.check_multiple_symbols(symbols)
        available = [s for s, (avail, _) in results.items() if avail]
        unavailable = [(s, err) for s, (avail, err) in results.items() if not avail]
        
        return {
            "market": market_code,
            "total_symbols": len(symbols),
            "available_count": len(available),
            "unavailable_count": len(unavailable),
            "available_symbols": available,
            "unavailable_symbols": unavailable,
            "availability_rate": len(available) / len(symbols) if symbols else 0.0
        }
    
    def notify_unavailable_symbols(self, symbols: List[str], context: str = "operación") -> bool:
        """
        Check symbols and send notifications for unavailable ones.
        
        Args:
            symbols: List of symbols to check
            context: Context for the notification (e.g., "entrenamiento", "operación")
        
        Returns:
            True if all symbols are available, False otherwise
        """
        unavailable = self.get_unavailable_symbols(symbols)
        
        if unavailable:
            # Send notification
            unavailable_list = "\n".join([f"  • {sym}: {err}" for sym, err in unavailable])
            message = f"⚠️ ALERTA: Símbolos no disponibles en IOL ({context}):\n{unavailable_list}"
            
            # Notify via console
            self.notifier.notify_alert(
                f"Símbolos no disponibles en IOL",
                message,
                level="warning"
            )
            
            # Also print to console
            print(f"\n{'='*60}")
            print(f"⚠️  ALERTA: Símbolos no disponibles en IOL")
            print(f"{'='*60}")
            for sym, err in unavailable:
                print(f"  ❌ {sym}: {err}")
            print(f"{'='*60}\n")
            
            return False
        
        return True
    
    def clear_cache(self):
        """Clear the availability cache."""
        self._cache.clear()


def check_symbol_availability(symbol: str, iol_client: Optional[IOLClient] = None) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to check if a single symbol is available in IOL.
    
    Args:
        symbol: Symbol to check
        iol_client: Optional IOLClient instance
    
    Returns:
        Tuple of (is_available: bool, error_message: Optional[str])
    """
    checker = IOLAvailabilityChecker(iol_client)
    return checker.is_symbol_available(symbol)


if __name__ == "__main__":
    # Test the availability checker
    print("=== IOL Availability Checker Test ===\n")
    
    checker = IOLAvailabilityChecker()
    
    # Test symbols
    test_symbols = ["GGAL", "YPFD", "AAPL", "INVALID_SYMBOL", "TSLA"]
    
    print("Verificando disponibilidad de símbolos en IOL...\n")
    for symbol in test_symbols:
        is_available, error = checker.is_symbol_available(symbol)
        status = "✅ Disponible" if is_available else f"❌ No disponible: {error}"
        print(f"{symbol}: {status}")


from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf


class YahooFinanceClient:
    """
    Client for fetching market data from Yahoo Finance.
    Acts as a fallback when IOL API is unavailable.
    """

    def _get_safe_stderr_context(self):
        """Context manager to safely handle stderr during yfinance calls"""
        import sys
        import io
        import contextlib
        
        @contextlib.contextmanager
        def safe_stderr():
            original_stderr = sys.stderr
            # Check if stderr is closed or invalid
            is_closed = False
            try:
                if hasattr(sys.stderr, 'closed') and sys.stderr.closed:
                    is_closed = True
            except:
                is_closed = True
                
            # If closed, replace with StringIO
            if is_closed:
                sys.stderr = io.StringIO()
            
            try:
                yield
            except (ValueError, IOError, OSError) as e:
                # If we get an I/O error, it might be because stderr closed during execution
                if "closed file" in str(e).lower() or "I/O operation" in str(e):
                    # Try to replace stderr and continue (though the exception is already raised)
                    sys.stderr = io.StringIO()
                raise
            finally:
                # Only restore if we didn't start with a closed stderr
                # If we started with closed stderr, we leave the StringIO replacement
                # to prevent future errors
                if not is_closed:
                    try:
                        sys.stderr = original_stderr
                    except:
                        pass
        
        return safe_stderr()

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieves real-time (delayed) quote data for a symbol.
        Args:
            symbol: The ticker symbol (e.g., 'GGAL.BA' for Buenos Aires).
        """
        try:
            # Append .BA for Buenos Aires market if not present and not a US stock
            if not symbol.endswith(".BA") and not symbol.endswith(".AR"):
                pass

            with self._get_safe_stderr_context():
                ticker = yf.Ticker(symbol)
                info = ticker.info

            # Extract relevant fields to match IOL structure roughly
            quote = {
                "symbol": symbol,
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose")
                or info.get("regularMarketPreviousClose"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "currency": info.get("currency"),
                "source": "Yahoo Finance",
            }
            return quote
        except Exception as e:
            # print(f"Error fetching Yahoo quote for {symbol}: {e}") # Reduce noise
            return None

    def get_history(self, symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        Retrieves historical data.
        """
        import warnings
        warnings.filterwarnings('ignore')
        
        try:
            with self._get_safe_stderr_context():
                ticker = yf.Ticker(symbol)
                history = ticker.history(period=period, interval=interval)
            
            return history if not history.empty else pd.DataFrame()
        except Exception as e:
            # print(f"Error fetching Yahoo history for {symbol}: {e}") # Reduce noise
            return pd.DataFrame()


if __name__ == "__main__":
    client = YahooFinanceClient()

    # Test US Stock
    print("Testing AAPL:")
    print(client.get_quote("AAPL"))

    # Test Argentine Stock (GGAL.BA)
    print("\nTesting GGAL.BA:")
    print(client.get_quote("GGAL.BA"))

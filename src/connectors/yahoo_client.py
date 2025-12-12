from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket


class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    """
    Session class with caching and rate limiting.
    This helps to avoid hitting Yahoo Finance's rate limits and speeds up repeated requests.
    """
    pass


class YahooFinanceClient:
    """
    Client for fetching market data from Yahoo Finance.
    Acts as a fallback when IOL API is unavailable.
    """
    _session: Optional[Session] = None

    @property
    def session(self) -> Session:
        """
        Initializes and returns a session for yfinance, enabling caching and impersonation.
        This is critical to avoid the 'Impersonating chrome136 is not supported' error.
        """
        if self._session is None:
            self._session = CachedLimiterSession(
                per_second=0.9,  # Rate limit to avoid being blocked
                cache_name='yfinance.cache',
                backend=SQLiteCache(),
                expire_after=pd.Timedelta(hours=1),
                # Use a modern, supported browser profile for impersonation
                impersonate="chrome110"
            )
        return self._session

    def _get_safe_stderr_context(self):
        """Context manager to safely handle stderr during yfinance calls"""
        import sys
        import io
        import contextlib
        
        @contextlib.contextmanager
        def safe_stderr():
            original_stderr = sys.stderr
            is_closed = False
            try:
                if hasattr(sys.stderr, 'closed') and sys.stderr.closed:
                    is_closed = True
            except:
                is_closed = True
                
            if is_closed:
                sys.stderr = io.StringIO()
            
            try:
                yield
            except (ValueError, IOError, OSError) as e:
                if "closed file" in str(e).lower() or "I/O operation" in str(e):
                    sys.stderr = io.StringIO()
                raise
            finally:
                if not is_closed:
                    try:
                        sys.stderr = original_stderr
                    except:
                        pass
        
        return safe_stderr()

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieves real-time (delayed) quote data for a symbol.
        """
        try:
            with self._get_safe_stderr_context():
                ticker = yf.Ticker(symbol, session=self.session)
                info = ticker.info

            quote = {
                "symbol": symbol,
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "currency": info.get("currency"),
                "source": "Yahoo Finance",
            }
            return quote
        except Exception:
            return None

    def get_history(self, symbol: str, period: str = "1mo", interval: str = "1d") -> pd.DataFrame:
        """
        Retrieves historical data.
        """
        import warnings
        warnings.filterwarnings('ignore')
        
        try:
            with self._get_safe_stderr_context():
                ticker = yf.Ticker(symbol, session=self.session)
                history = ticker.history(period=period, interval=interval)
            
            return history if not history.empty else pd.DataFrame()
        except Exception:
            return pd.DataFrame()


if __name__ == "__main__":
    client = YahooFinanceClient()

    # Test US Stock
    print("Testing AAPL:")
    print(client.get_quote("AAPL"))

    # Test Argentine Stock (GGAL.BA)
    print("\nTesting GGAL.BA:")
    print(client.get_quote("GGAL.BA"))

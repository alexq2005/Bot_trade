"""
Multi-Market Client for Global Trading
Supports: US, Argentina, Asia (Japan, Hong Kong, South Korea), Europe (UK, Germany, France)
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf


class MultiMarketClient:
    """
    Client for accessing multiple global markets.
    """

    # Market configurations
    MARKETS = {
        "USA": {
            "name": "🇺🇸 Estados Unidos",
            "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "WMT"],
            "suffix": "",
        },
        "ARG": {
            "name": "🇦🇷 Argentina - Acciones",
            "symbols": [
                "GGAL.BA",
                "YPFD.BA",
                "PAMP.BA",
                "ALUA.BA",
                "BBAR.BA",
                "CEPU.BA",
                "EDN.BA",
                "TRAN.BA",
                "VALO.BA",
                "LOMA.BA",
            ],
            "suffix": ".BA",
        },
        "ARG_BONDS": {
            "name": "🇦🇷 Argentina - Bonos Soberanos",
            "symbols": [
                "GD30.BA",
                "GD35.BA",
                "GD38.BA",
                "GD41.BA",
                "GD46.BA",
                "AL30.BA",
                "AL35.BA",
                "AL41.BA",
                "AE38.BA",
                "GD29.BA",
            ],
            "suffix": ".BA",
        },
        "ARG_CORP_BONDS": {
            "name": "🇦🇷 Argentina - Obligaciones Negociables",
            "symbols": [
                "PARY6O.BA",
                "TVPPO.BA",
                "IRCPO.BA",
                "PAMPO.BA",
                "YPFDO.BA",
            ],  # ONs de YPF, Pampa, etc.
            "suffix": ".BA",
        },
        "CEDEAR": {
            "name": "🇦🇷 CEDEARs (Acciones USA en Argentina)",
            "symbols": [
                "AAPL.BA",
                "MSFT.BA",
                "GOOGL.BA",
                "AMZN.BA",
                "TSLA.BA",
                "KO.BA",
                "DIS.BA",
                "NFLX.BA",
                "META.BA",
                "NVDA.BA",
            ],
            "suffix": ".BA",
        },
        "JPN": {
            "name": "🇯🇵 Japón (Tokio)",
            "symbols": [
                "7203.T",
                "6758.T",
                "9984.T",
                "8306.T",
                "6861.T",
                "9433.T",
                "4063.T",
                "6902.T",
                "8035.T",
                "4502.T",
            ],
            "suffix": ".T",
        },
        "HKG": {
            "name": "🇭🇰 Hong Kong",
            "symbols": [
                "0700.HK",
                "9988.HK",
                "0941.HK",
                "1299.HK",
                "2318.HK",
                "0005.HK",
                "3690.HK",
                "1810.HK",
                "2382.HK",
                "9618.HK",
            ],
            "suffix": ".HK",
        },
        "KOR": {
            "name": "🇰🇷 Corea del Sur (Seúl)",
            "symbols": [
                "005930.KS",
                "000660.KS",
                "035420.KS",
                "051910.KS",
                "005380.KS",
                "035720.KS",
                "006400.KS",
                "028260.KS",
                "105560.KS",
                "068270.KS",
            ],
            "suffix": ".KS",
        },
        "UK": {
            "name": "🇬🇧 Reino Unido (Londres)",
            "symbols": [
                "HSBA.L",
                "BP.L",
                "SHEL.L",
                "AZN.L",
                "ULVR.L",
                "DGE.L",
                "GSK.L",
                "RIO.L",
                "BARC.L",
                "LLOY.L",
            ],
            "suffix": ".L",
        },
        "GER": {
            "name": "🇩🇪 Alemania (Frankfurt)",
            "symbols": [
                "SAP.DE",
                "SIE.DE",
                "VOW3.DE",
                "BMW.DE",
                "ALV.DE",
                "DTE.DE",
                "BAS.DE",
                "MBG.DE",
                "DAI.DE",
                "ADS.DE",
            ],
            "suffix": ".DE",
        },
        "FRA": {
            "name": "🇫🇷 Francia (París)",
            "symbols": [
                "MC.PA",
                "OR.PA",
                "SAN.PA",
                "TTE.PA",
                "AIR.PA",
                "BNP.PA",
                "SU.PA",
                "ORA.PA",
                "CS.PA",
                "EL.PA",
            ],
            "suffix": ".PA",
        },
    }

    def __init__(self):
        self.active_markets = list(self.MARKETS.keys())

    def get_market_symbols(self, market_code):
        """Get symbols for a specific market."""
        return self.MARKETS.get(market_code, {}).get("symbols", [])

    def get_all_symbols(self):
        """Get all symbols across all markets."""
        all_symbols = []
        for market in self.MARKETS.values():
            all_symbols.extend(market["symbols"])
        return all_symbols

    def get_quote(self, symbol):
        """Get current quote for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            return {
                "symbol": symbol,
                "price": info.get("currentPrice", info.get("regularMarketPrice")),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "volume": info.get("volume", 0),
                "market_cap": info.get("marketCap", 0),
                "currency": info.get("currency", "USD"),
            }
        except Exception as e:
            return {"error": str(e), "symbol": symbol}

    def get_market_overview(self, market_code):
        """Get overview of all symbols in a market."""
        symbols = self.get_market_symbols(market_code)
        overview = []

        for symbol in symbols:
            quote = self.get_quote(symbol)
            if "error" not in quote:
                overview.append(quote)

        return {
            "market": market_code,
            "market_name": self.MARKETS[market_code]["name"],
            "symbols": overview,
            "timestamp": datetime.now().isoformat(),
        }

    def get_historical_data(self, symbol, period="1mo"):
        """Get historical data for a symbol."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return None

    def search_symbol(self, query):
        """Search for symbols across all markets."""
        results = []
        all_symbols = self.get_all_symbols()

        query_lower = query.lower()
        for symbol in all_symbols:
            if query_lower in symbol.lower():
                # Determine market
                market = self._get_market_for_symbol(symbol)
                results.append({"symbol": symbol, "market": market})

        return results

    def _get_market_for_symbol(self, symbol):
        """Determine which market a symbol belongs to."""
        for market_code, market_data in self.MARKETS.items():
            if symbol in market_data["symbols"]:
                return market_code
        return "UNKNOWN"


# Example usage
if __name__ == "__main__":
    client = MultiMarketClient()

    print("=== Multi-Market Client ===\n")

    # Test each market
    for market_code in client.MARKETS.keys():
        print(f"\n📊 {client.MARKETS[market_code]['name']}")
        print(f"Symbols: {len(client.MARKETS[market_code]['symbols'])}")

        # Get first symbol quote
        symbols = client.get_market_symbols(market_code)
        if symbols:
            quote = client.get_quote(symbols[0])
            if "error" not in quote:
                print(f"Sample: {quote['symbol']} - ${quote.get('price', 0):.2f}")

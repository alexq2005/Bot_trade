"""
Symbol Discovery Service
Discovers all available symbols from different markets for training and trading.
"""

import os
import sys
import yfinance as yf
import pandas as pd
from typing import List, Dict, Optional
import requests
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.connectors.multi_market_client import MultiMarketClient


class SymbolDiscovery:
    """
    Service to discover all available symbols from different markets.
    """
    
    # Market-specific symbol lists and sources
    MARKET_SOURCES = {
        "ARG": {
            "name": "🇦🇷 Argentina - Acciones",
            "method": "iol_api",  # Use IOL API or predefined list
            "predefined": [
                # Acciones principales
                "GGAL", "YPFD", "PAMP", "ALUA", "BBAR", "CEPU", "EDN", "TRAN", 
                "VALO", "LOMA", "MIRG", "BMA", "CRES", "DGCU2", "FERR", "GARO",
                "INVJ", "IRSA", "LEDE", "MOLI", "OEST", "PGR", "RICH", "ROSE",
                "SAMI", "SUPV", "TECO2", "TGNO4", "TGSU2", "TXAR", "VALE", "BYMA",
                # Más acciones
                "AGRO", "AUSO", "BHIP", "BOLT", "CADO", "CAPX", "CARC", "CECO2",
                "CELU", "COME", "CTIO", "DOME", "DYCA", "ERAR", "FIPL", "GCLA",
                "GRIM", "HAVA", "INTR", "LONG", "MERA", "METR", "MIRG", "MOLA",
                "MORI", "OEST", "PATA", "POLL", "RIGO", "SIDO", "TS", "TXAR",
                "VALU", "VIST", "VTI", "YELP"
            ]
        },
        "ARG_BONDS": {
            "name": "🇦🇷 Argentina - Bonos Soberanos",
            "method": "predefined",
            "predefined": [
                "GD30", "GD35", "GD38", "GD41", "GD46", "GD29", "GD26",
                "AL30", "AL35", "AL41", "AL29", "AL26",
                "AE38", "AE41", "AE46",
                "DICA", "DICP", "PARP", "PARA", "PARB", "PARC", "PARD", "PARE"
            ]
        },
        "ARG_CORP_BONDS": {
            "name": "🇦🇷 Argentina - Obligaciones Negociables",
            "method": "predefined",
            "predefined": [
                "PARY6O", "TVPPO", "IRCPO", "PAMPO", "YPFDO", "GGALO", "BBARO",
                "CEPUO", "EDNO", "TRANO", "LOMAO", "ALUAO", "BMAO"
            ]
        },
        "USA": {
            "name": "🇺🇸 Estados Unidos",
            "method": "yfinance_index",  # Get from S&P 500, NASDAQ, etc.
            "indices": ["SPY", "QQQ", "DIA"]  # ETFs that represent indices
        },
        "CEDEAR": {
            "name": "🇦🇷 CEDEARs",
            "method": "predefined",
            "predefined": [
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM",
                "V", "WMT", "JNJ", "PG", "MA", "DIS", "NFLX", "BAC", "XOM",
                "CVX", "KO", "PEP", "ABBV", "AVGO", "COST", "MRK", "TMO"
            ]
        },
        "JPN": {
            "name": "🇯🇵 Japón (Tokio)",
            "method": "predefined",
            "predefined": [
                "7203", "6758", "9984", "8306", "6861", "9433", "4063", "6902",
                "8035", "4502", "7267", "6098", "8058", "6752", "8411", "8053",
                "8001", "8056", "8031", "8766", "2914", "2802", "2503", "2267"
            ],
            "suffix": ".T"
        },
        "HKG": {
            "name": "🇭🇰 Hong Kong",
            "method": "predefined",
            "predefined": [
                "0700", "9988", "0941", "1299", "2318", "0005", "3690", "1810",
                "2382", "9618", "0388", "1398", "0939", "3988", "2628", "3328",
                "3968", "9983", "1177", "1928", "2020", "2269", "2331", "2388"
            ],
            "suffix": ".HK"
        },
        "KOR": {
            "name": "🇰🇷 Corea del Sur (Seúl)",
            "method": "predefined",
            "predefined": [
                "005930", "000660", "035420", "051910", "005380", "035720",
                "006400", "028260", "105560", "068270", "005490", "000270",
                "006800", "003670", "012330", "017670", "028300", "034730"
            ],
            "suffix": ".KS"
        },
        "UK": {
            "name": "🇬🇧 Reino Unido (Londres)",
            "method": "predefined",
            "predefined": [
                "HSBA", "BP", "SHEL", "AZN", "ULVR", "DGE", "GSK", "RIO",
                "BARC", "LLOY", "VOD", "BT", "TSCO", "BATS", "IMB", "PRU",
                "AV", "NG", "STAN", "CRDA", "REL", "AAL", "LAND", "EXPN"
            ],
            "suffix": ".L"
        },
        "GER": {
            "name": "🇩🇪 Alemania (Frankfurt)",
            "method": "predefined",
            "predefined": [
                "SAP", "SIE", "VOW3", "BMW", "ALV", "DTE", "BAS", "MBG",
                "DAI", "ADS", "BAYN", "DBK", "FME", "HEI", "IFX", "LIN",
                "MRK", "MUV2", "RWE", "SIE", "VNA", "WDI", "ZAL", "1COV"
            ],
            "suffix": ".DE"
        },
        "FRA": {
            "name": "🇫🇷 Francia (París)",
            "method": "predefined",
            "predefined": [
                "MC", "OR", "SAN", "TTE", "AIR", "BNP", "SU", "ORA",
                "CS", "EL", "ATO", "BNP", "CAP", "DG", "EN", "FP",
                "GLE", "KER", "LR", "ML", "OR", "PUB", "RNO", "VIE"
            ],
            "suffix": ".PA"
        }
    }
    
    def __init__(self):
        self.multi_market = MultiMarketClient()
    
    def get_sp500_symbols(self) -> List[str]:
        """Get all S&P 500 symbols using Wikipedia."""
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            sp500_table = tables[0]
            symbols = sp500_table['Symbol'].tolist()
            # Clean symbols (remove dots, replace with dash for yfinance)
            symbols = [s.replace('.', '-') for s in symbols]
            return symbols
        except Exception as e:
            print(f"Error obteniendo S&P 500: {e}")
            # Fallback to extended list of common symbols
            return [
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "WMT",
                "JNJ", "PG", "MA", "DIS", "NFLX", "BAC", "XOM", "CVX", "KO", "PEP",
                "ABBV", "AVGO", "COST", "MRK", "TMO", "ACN", "ADBE", "CRM", "CSCO", "DHR",
                "LIN", "NEE", "TXN", "UNH", "VZ", "WFC", "HD", "MCD", "NKE", "SBUX"
            ]
    
    def get_nasdaq_symbols(self, limit: int = 100) -> List[str]:
        """Get NASDAQ symbols (limited to most liquid)."""
        try:
            # Use yfinance to get NASDAQ-100
            nasdaq = yf.Ticker("QQQ")
            holdings = nasdaq.get_info()
            # This might not work directly, so use predefined list
            return [
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX",
                "AMD", "INTC", "CMCSA", "ADBE", "PYPL", "AVGO", "COST", "PEP",
                "CSCO", "QCOM", "TXN", "AMGN", "ISRG", "BKNG", "VRTX", "ADI"
            ]
        except Exception as e:
            print(f"Error obteniendo NASDAQ: {e}")
            return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"]
    
    def get_argentina_symbols_from_iol(self) -> List[str]:
        """Get Argentina symbols from IOL API (if available)."""
        try:
            from src.connectors.iol_client import IOLClient
            client = IOLClient()
            # IOL might have an endpoint for available instruments
            # For now, return predefined list
            return self.MARKET_SOURCES["ARG"]["predefined"]
        except Exception as e:
            print(f"Error obteniendo símbolos de IOL: {e}")
            return self.MARKET_SOURCES["ARG"]["predefined"]
    
    def discover_symbols(self, market_code: str, include_suffix: bool = True) -> List[str]:
        """
        Discover all available symbols for a given market.
        
        Args:
            market_code: Market code (ARG, USA, ARG_BONDS, etc.)
            include_suffix: Whether to include market suffix (.BA, etc.)
        
        Returns:
            List of symbol strings
        """
        market_config = self.MARKET_SOURCES.get(market_code)
        if not market_config:
            return []
        
        method = market_config.get("method", "predefined")
        symbols = []
        
        if method == "predefined":
            symbols = market_config.get("predefined", [])
        
        elif method == "yfinance_index":
            # Get symbols from major indices
            if market_code == "USA":
                # Combine S&P 500 and NASDAQ
                sp500 = self.get_sp500_symbols()
                nasdaq = self.get_nasdaq_symbols()
                # Also add popular ETFs and other major stocks
                additional = [
                    "SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "VEA", "VWO",
                    "ARKK", "ARKQ", "ARKW", "ARKG", "ARKF", "TQQQ", "SQQQ",
                    "BRK-B", "BRK.A", "GE", "F", "GM", "BA", "CAT", "DE"
                ]
                symbols = list(set(sp500 + nasdaq + additional))
        
        elif method == "iol_api":
            if market_code == "ARG":
                symbols = self.get_argentina_symbols_from_iol()
        
        # If no symbols found but market exists in multi_market, use those
        if not symbols and market_code in self.multi_market.MARKETS:
            symbols = self.multi_market.MARKETS[market_code].get("symbols", [])
        
        # Add suffix if needed
        if include_suffix:
            # Check if market config has suffix defined
            market_config_suffix = market_config.get("suffix")
            if market_config_suffix:
                suffix = market_config_suffix
            else:
                # Fallback to multi_market client
                suffix = self.multi_market.MARKETS.get(market_code, {}).get("suffix", "")
            
            if suffix:
                symbols = [f"{s}{suffix}" if not s.endswith(suffix) else s for s in symbols]
        
        # Remove duplicates and sort
        symbols = sorted(list(set(symbols)))
        
        return symbols
    
    def get_all_markets_symbols(self) -> Dict[str, List[str]]:
        """Get all symbols for all markets."""
        result = {}
        for market_code in self.MARKET_SOURCES.keys():
            result[market_code] = self.discover_symbols(market_code)
        return result
    
    def search_symbols(self, query: str, market_code: Optional[str] = None) -> List[str]:
        """
        Search for symbols matching a query.
        
        Args:
            query: Search query (symbol name or partial match)
            market_code: Optional market to search in
        
        Returns:
            List of matching symbols
        """
        if market_code:
            all_symbols = self.discover_symbols(market_code)
        else:
            # Search across all markets
            all_symbols = []
            for market in self.MARKET_SOURCES.keys():
                all_symbols.extend(self.discover_symbols(market))
        
        query_upper = query.upper()
        matches = [s for s in all_symbols if query_upper in s.upper()]
        
        return matches
    
    def get_market_info(self, market_code: str) -> Dict:
        """Get information about a market."""
        market_config = self.MARKET_SOURCES.get(market_code, {})
        symbols = self.discover_symbols(market_code)
        
        return {
            "code": market_code,
            "name": market_config.get("name", market_code),
            "symbol_count": len(symbols),
            "symbols": symbols[:50],  # First 50 for preview
            "method": market_config.get("method", "predefined")
        }


def get_available_symbols_for_market(market_code: str) -> List[str]:
    """
    Convenience function to get available symbols for a market.
    
    Args:
        market_code: Market code (ARG, USA, ARG_BONDS, etc.)
    
    Returns:
        List of symbol strings
    """
    discovery = SymbolDiscovery()
    return discovery.discover_symbols(market_code)


if __name__ == "__main__":
    # Test the discovery service
    discovery = SymbolDiscovery()
    
    print("=== Symbol Discovery Test ===\n")
    
    # Test each market
    for market_code in ["ARG", "ARG_BONDS", "USA", "CEDEAR"]:
        print(f"\n{market_code}:")
        symbols = discovery.discover_symbols(market_code)
        print(f"  Found {len(symbols)} symbols")
        print(f"  Sample: {symbols[:10]}")


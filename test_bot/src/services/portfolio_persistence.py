"""
Portfolio persistence
Save and load portfolio from JSON file
"""

import json
import os
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from src.connectors.iol_client import IOLClient
from src.connectors.tienda_broker_client import get_tienda_broker_portfolio

PORTFOLIO_FILE = "my_portfolio.json"


def sync_from_tienda_broker() -> bool:
    """
    Synchronize local portfolio with Tienda Broker via web scraping.
    Fetches real-time holdings and updates my_portfolio.json.
    """
    print("🔄 Syncing portfolio from Tienda Broker...")
    try:
        # 1. Scrape Data
        print("   Step 1: Calling get_tienda_broker_portfolio()...")
        tb_assets = get_tienda_broker_portfolio()
        print(f"   Step 1 complete: Received {len(tb_assets) if tb_assets else 0} assets")

        if not tb_assets:
            print("⚠️ No assets found or scraping failed.")
            return False

        # 2. Merge with existing portfolio
        print("   Step 2: Loading current portfolio...")
        current_portfolio = load_portfolio() or []
        current_dict = {asset["symbol"]: asset for asset in current_portfolio}

        # Update/Add assets
        print("   Step 3: Merging assets...")
        for new_asset in tb_assets:
            symbol = new_asset["symbol"]
            current_dict[symbol] = new_asset

        # Convert back to list
        merged_portfolio = list(current_dict.values())

        print("   Step 4: Saving portfolio...")
        save_portfolio(merged_portfolio)
        print(f"✅ Portfolio synced! {len(tb_assets)} assets from Tienda Broker.")
        print(f"   Total assets after merge: {len(merged_portfolio)}")
        return True

    except Exception as e:
        print(f"❌ Tienda Broker sync failed: {e}")
        print(f"   Full traceback:")
        traceback.print_exc()
        return False


def get_dolar_mep() -> float:
    """
    Get current MEP/CCL dollar rate from DolarApi.com
    Returns: float (MEP rate) or None if error
    """
    try:
        response = requests.get("https://dolarapi.com/v1/dolares/bolsa", timeout=5)
        if response.status_code == 200:
            data = response.json()
            # Use 'venta' (sell) price as reference
            mep_rate = data.get("venta", data.get("promedio", 1000))
            print(f"💵 Dólar MEP actual: ${mep_rate:.2f}")
            return float(mep_rate)
    except Exception as e:
        print(f"⚠️ No se pudo obtener dólar MEP: {e}. Usando default $1050.")

    # Default fallback
    return 1050.0


def save_portfolio(portfolio: List[Dict[str, Any]]) -> bool:
    """Save portfolio to JSON file."""
    try:
        with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"portfolio": portfolio, "last_updated": datetime.now().isoformat()},
                f,
                indent=2,
                ensure_ascii=False,
            )
        return True
    except Exception as e:
        print(f"Error saving portfolio: {e}")
        return False


def load_portfolio() -> Optional[List[Dict[str, Any]]]:
    """Load portfolio from JSON file."""
    try:
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                from typing import cast
                return cast(List[Dict[str, Any]], data.get("portfolio", []))
        return None
    except Exception as e:
        print(f"Error loading portfolio: {e}")
        return None


def sync_from_iol(iol_client: IOLClient) -> bool:
    """
    Synchronize local portfolio with IOL account.
    Fetches real-time holdings from IOL and updates my_portfolio.json.

    Args:
        iol_client: Authenticated IOLClient instance

    Returns:
        bool: True if successful, False otherwise
    """
    print("🔄 Syncing portfolio from IOL...")
    try:
        # 1. Get Argentina Portfolio
        port_arg = iol_client.get_portfolio(country="argentina")

        # 2. Get US Portfolio
        try:
            port_us = iol_client.get_portfolio(country="estados_Unidos")
            if "activos" in port_us:
                # Merge assets
                if "activos" in port_arg:
                    port_arg["activos"].extend(port_us["activos"])
                else:
                    port_arg["activos"] = port_us["activos"]
        except Exception:
            pass  # US portfolio might fail or be empty, ignore

        new_portfolio = []

        if "activos" in port_arg:
            for asset in port_arg["activos"]:
                symbol = asset["titulo"]["simbolo"]
                quantity = asset["cantidad"]

                # Skip if quantity is 0
                if quantity <= 0:
                    continue

                # Determine market
                market = "ARG"
                if symbol in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "KO", "TSM", "NU"]:
                    market = "US"

                entry = {
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_price": asset.get("ppc", 0.0),  # Precio Promedio de Compra
                    "market": market,
                    "factor": 1.0,
                    "total_val": asset.get("valorizado", 0.0),
                }
                new_portfolio.append(entry)

        if new_portfolio:
            # MERGE LOGIC
            current_portfolio = load_portfolio() or []
            current_dict = {asset["symbol"]: asset for asset in current_portfolio}

            for iol_asset in new_portfolio:
                current_dict[iol_asset["symbol"]] = iol_asset

            merged_portfolio = list(current_dict.values())

            save_portfolio(merged_portfolio)
            print(f"✅ Portfolio synced! {len(new_portfolio)} assets from IOL.")
            return True
        else:
            print("⚠️ No assets found in IOL portfolio.")
            return False

    except Exception as e:
        print(f"❌ Portfolio sync failed: {e}")
        return False


def update_prices_from_iol(iol_client: IOLClient) -> bool:
    """
    Update current prices of all assets in the portfolio using IOL API.
    Converts CEDEAR prices from USD to ARS using current MEP rate.

    Args:
        iol_client: Authenticated IOLClient instance

    Returns:
        bool: True if successful
    """
    print("🔄 Updating portfolio prices from IOL...")
    try:
        portfolio = load_portfolio()
        if not portfolio:
            print("⚠️ Portfolio is empty.")
            return False

        # Get current MEP dollar rate
        dolar_mep = get_dolar_mep()

        updated_count = 0
        total_value = 0.0

        # BOND PRICE DIVISIONS
        # Some bonds quote per 1000 nominals, others per 100
        BONDS_1000 = [
            "BPOC7",
            "BA37D",
            "GD35",
            "AL30",
            "GD30",
            "AL29",
            "GD29",
            "AE38",
            "GD38",
            "GD41",
            "GD46",
            "AL35",
        ]
        BONDS_100 = ["TTM26", "T15D5", "TX26", "TX28", "TX24", "T2X4", "T2X5"]

        # CEDEAR ratios (how many CEDEARs = 1 underlying stock)
        # Actualizados a Nov 2025
        CEDEAR_RATIOS = {
            "AAPL": 20,
            "AMD": 10,
            "AMZN": 144,
            "BABA": 9,
            "BIDU": 11,
            "BP": 5,
            "C": 3,
            "CAT": 20,
            "CSCO": 5,
            "CVX": 8,
            "DESP": 1,
            "DIS": 12,
            "EBAY": 2,
            "ERJ": 1,
            "FB": 8,  # META
            "META": 8,
            "GE": 1,
            "GLOB": 2,
            "GOOGL": 58,
            "HMY": 1,
            "IBM": 5,
            "INTC": 5,
            "JNJ": 5,
            "JPM": 5,
            "KO": 5,
            "MELI": 60,
            "MMM": 5,
            "MO": 2,
            "MSFT": 30,
            "NFLX": 48,
            "NKE": 3,
            "NVDA": 24,  # Ajustado post-split
            "PBR": 1,
            "PFE": 2,
            "PG": 5,
            "QCOM": 11,
            "SLB": 3,
            "SNAP": 1,
            "T": 3,
            "TSLA": 15,
            "TSM": 9,
            "TWTR": 2,
            "TX": 3,
            "V": 6,
            "WFC": 5,
            "WMT": 6,
            "X": 3,
            "XOM": 5,
            "NU": 6,  # Ajustado
            "SPY": 20,
            "QQQ": 20,
            "DIA": 20,
            "EEM": 5,
            "XLE": 2,
            "XLF": 2,
            "EWZ": 2,
            "ARKK": 2,
        }

        for asset in portfolio:
            symbol = asset["symbol"]
            qty = asset["quantity"]
            clean_symbol = symbol.replace(".BA", "")

            # Skip if quantity is 0
            if qty <= 0:
                total_value += asset.get("total_val", 0)
                continue

            try:
                quote = iol_client.get_quote(symbol)
                if quote and "ultimoPrecio" in quote:
                    raw_price = quote["ultimoPrecio"]

                    # Priority 1: Check if it's a BOND
                    if clean_symbol in BONDS_1000:
                        current_price = raw_price / 1000.0
                        print(
                            f"   📊 Bono /1000 {symbol}: ${raw_price:,.2f} / 1000 = ${current_price:,.2f} ARS"
                        )
                    elif clean_symbol in BONDS_100:
                        current_price = raw_price / 100.0
                        print(
                            f"   📊 Bono /100 {symbol}: ${raw_price:,.2f} / 100 = ${current_price:,.2f} ARS"
                        )
                    # Priority 2: Check if it's a CEDEAR
                    elif clean_symbol in CEDEAR_RATIOS:
                        ratio = CEDEAR_RATIOS[clean_symbol]
                        cedear_price_usd = raw_price / ratio
                        current_price = cedear_price_usd * dolar_mep
                        print(
                            f"   💱 CEDEAR {symbol} ({ratio}:1): ${raw_price:.2f} USD / {ratio} = ${cedear_price_usd:.2f} USD x ${dolar_mep:.2f} = ${current_price:,.2f} ARS"
                        )
                    else:
                        # Argentine stocks - price is already in ARS
                        current_price = raw_price
                        print(f"   ✅ {symbol}: ${current_price:,.2f} ARS")

                    asset["last_price"] = current_price
                    asset["total_val"] = qty * current_price
                    asset["avg_price"] = current_price

                    updated_count += 1
                else:
                    print(f"   ⚠️ Could not get quote for {symbol}")
            except Exception as e:
                print(f"   ❌ Error updating {symbol}: {e}")

            total_value += asset.get("total_val", 0)

        if updated_count > 0:
            save_portfolio(portfolio)
            print(f"✅ Updated prices for {updated_count} assets.")
            print(f"   New Total Value: ${total_value:,.2f}")
            return True
        else:
            print("⚠️ No prices updated.")
            return False

    except Exception as e:
        print(f"❌ Price update failed: {e}")
        return False


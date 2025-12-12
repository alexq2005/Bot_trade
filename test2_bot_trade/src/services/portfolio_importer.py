"""
Portfolio Importer
Import portfolios from CSV, Excel, or broker statements
"""

import json
from datetime import datetime

import pandas as pd


class PortfolioImporter:
    """
    Import and manage portfolio data from various sources.
    """

    def __init__(self):
        self.portfolio = []

    def import_from_csv(self, file_path):
        """
        Import portfolio from CSV file.
        Expected columns: symbol, quantity, avg_price, market
        """
        try:
            df = pd.read_csv(file_path)

            # Validate columns
            required_cols = ["symbol", "quantity", "avg_price"]
            if not all(col in df.columns for col in required_cols):
                return {"error": f"Missing required columns. Need: {required_cols}"}

            # Convert to portfolio format
            self.portfolio = []
            for _, row in df.iterrows():
                position = {
                    "symbol": row["symbol"],
                    "quantity": int(row["quantity"]),
                    "avg_price": float(row["avg_price"]),
                    "market": row.get("market", "US"),
                    "imported_at": datetime.now().isoformat(),
                }
                self.portfolio.append(position)

            return {
                "success": True,
                "positions": len(self.portfolio),
                "total_value": sum(p["quantity"] * p["avg_price"] for p in self.portfolio),
            }

        except Exception as e:
            return {"error": str(e)}

    def import_from_excel(self, file_path, sheet_name="Portfolio"):
        """Import portfolio from Excel file."""
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # Convert to CSV format and use existing logic
            csv_path = file_path.replace(".xlsx", "_temp.csv").replace(".xls", "_temp.csv")
            df.to_csv(csv_path, index=False)
            result = self.import_from_csv(csv_path)

            # Clean up temp file
            import os

            if os.path.exists(csv_path):
                os.remove(csv_path)

            return result

        except Exception as e:
            return {"error": str(e)}

    def import_from_json(self, file_path):
        """Import portfolio from JSON file."""
        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            if isinstance(data, list):
                self.portfolio = data
            elif isinstance(data, dict) and "positions" in data:
                self.portfolio = data["positions"]
            else:
                return {"error": "Invalid JSON format"}

            return {"success": True, "positions": len(self.portfolio)}

        except Exception as e:
            return {"error": str(e)}

    def import_from_iol_statement(self, statement_text):
        """
        Import from IOL account statement (text format).
        This is a simplified parser - adapt to actual IOL format.
        """
        try:
            positions = []
            lines = statement_text.strip().split("\n")

            for line in lines[1:]:  # Skip header
                parts = line.split(",")
                if len(parts) >= 3:
                    positions.append(
                        {
                            "symbol": parts[0].strip(),
                            "quantity": int(parts[1].strip()),
                            "avg_price": float(parts[2].strip()),
                            "market": "ARG",
                            "imported_at": datetime.now().isoformat(),
                        }
                    )

            self.portfolio = positions
            return {"success": True, "positions": len(positions)}

        except Exception as e:
            return {"error": str(e)}

    def get_portfolio(self):
        """Get current portfolio."""
        return self.portfolio

    def get_portfolio_summary(self):
        """Get portfolio summary with statistics."""
        if not self.portfolio:
            return {"error": "No portfolio loaded"}

        total_value = 0
        for p in self.portfolio:
            if "total_val" in p:
                total_value += p["total_val"]
            else:
                # Fallback to standard calculation
                total_value += p["quantity"] * p["avg_price"]

        # Group by market
        by_market = {}
        for position in self.portfolio:
            market = position.get("market", "US")
            if market not in by_market:
                by_market[market] = []
            by_market[market].append(position)

        return {
            "total_positions": len(self.portfolio),
            "total_value": total_value,
            "markets": list(by_market.keys()),
            "by_market": {
                market: {
                    "positions": len(positions),
                    "value": sum(
                        p.get("total_val", p["quantity"] * p["avg_price"]) for p in positions
                    ),
                }
                for market, positions in by_market.items()
            },
            "positions": self.portfolio,
        }

    def export_to_csv(self, file_path):
        """Export current portfolio to CSV."""
        if not self.portfolio:
            return {"error": "No portfolio to export"}

        try:
            df = pd.DataFrame(self.portfolio)
            df.to_csv(file_path, index=False)
            return {"success": True, "file": file_path}
        except Exception as e:
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    importer = PortfolioImporter()

    print("=== Portfolio Importer ===\n")

    # Example: Create sample CSV
    sample_data = """symbol,quantity,avg_price,market
AAPL,100,150.50,US
MSFT,50,380.25,US
GGAL.BA,200,7850.00,ARG
SAP.DE,30,125.75,EU"""

    with open("sample_portfolio.csv", "w") as f:
        f.write(sample_data)

    # Import
    result = importer.import_from_csv("sample_portfolio.csv")
    print(f"Import Result: {result}")

    # Get summary
    summary = importer.get_portfolio_summary()
    print(f"\nPortfolio Summary:")
    print(f"Total Positions: {summary['total_positions']}")
    print(f"Total Value: ${summary['total_value']:,.2f}")
    print(f"Markets: {', '.join(summary['markets'])}")

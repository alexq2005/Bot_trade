import sys
import os
# Add project root to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Fix encoding for Windows console
from src.core.console_utils import setup_windows_console, safe_print
setup_windows_console()

from src.connectors.iol_client import IOLClient
from src.core.config import settings

def test_connection():
    safe_print("--- Starting IOL Connection Test ---")
    
    # Check if credentials are set (simple check)
    if not settings.IOL_USERNAME or settings.IOL_USERNAME == "your_username_here":
        safe_print("[ERROR] IOL_USERNAME not configured in .env")
        safe_print("Please create .env file with valid credentials.")
        return

    try:
        client = IOLClient()
        safe_print(f"[OK] Client initialized for user: {client.username}")
        
        safe_print("Attempting to fetch quote for GGAL...")
        quote = client.get_quote("GGAL")
        
        if quote and "error" not in quote:
            safe_print("[SUCCESS] Connection Successful!")
            safe_print(f"Market Data Received: {quote}")
        elif quote and "error" in quote:
            safe_print(f"[ERROR] Connection established but error received: {quote.get('error', 'Unknown error')}")
        else:
            safe_print("[WARNING] Connection established but no data received.")
            
    except Exception as e:
        safe_print(f"[ERROR] Connection Failed: {str(e)}")

if __name__ == "__main__":
    test_connection()

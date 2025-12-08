import asyncio
import os
import json
import subprocess
import sys

# Fix for running async code inside Streamlit
import nest_asyncio
from dotenv import load_dotenv

nest_asyncio.apply()


class TiendaBrokerClient:
    def __init__(self):
        load_dotenv()
        self.email = os.getenv("TB_EMAIL")
        self.password = os.getenv("TB_PASSWORD")
        self.login_url = "https://app.tiendabroker.com/accounts"
        self.portfolio_url = "https://app.tiendabroker.com/operar/estado-cuenta"

    async def get_portfolio(self):
        """
        Logs in and scrapes the portfolio table.
        Returns a list of assets: [{'symbol': 'GGAL', 'quantity': 10, ...}]
        """
        # Lazy import to avoid startup errors if playwright not installed
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("❌ Playwright no está instalado. Ejecuta: pip install playwright")
            print("   Luego: playwright install chromium")
            return []

        print("🚀 Starting Tienda Broker Sync...")

        async with async_playwright() as p:
            # Launch browser (headless=True for production, False for debug)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                # Validate credentials
                if not self.email or not self.password:
                    print("❌ Error: TB_EMAIL o TB_PASSWORD no están configurados en .env")
                    print("   Agrega estas líneas a tu archivo .env:")
                    print("   TB_EMAIL=tu_email@ejemplo.com")
                    print("   TB_PASSWORD=tu_contraseña")
                    return []

                # 1. Login
                print(f"🔑 Logging in to {self.login_url}...")
                await page.goto(self.login_url, wait_until="networkidle")

                # Take screenshot for debugging
                await page.screenshot(path="tb_login_page.png")
                print("📸 Screenshot saved as tb_login_page.png")

                # Try multiple selectors for email field
                email_selectors = [
                    "input[type='email']",
                    "input[name='email']",
                    "input[placeholder*='mail' i]",
                    "input[id*='email' i]",
                    "#email",
                    "#username",
                ]

                email_filled = False
                for selector in email_selectors:
                    try:
                        await page.fill(selector, self.email, timeout=2000)
                        print(f"✅ Email filled using selector: {selector}")
                        email_filled = True
                        break
                    except:
                        continue

                if not email_filled:
                    print("❌ No se pudo encontrar el campo de email")
                    print("   Revisa tb_login_page.png para ver la estructura de la página")
                    return []

                # Try multiple selectors for password field
                password_selectors = [
                    "input[type='password']",
                    "input[name='password']",
                    "input[placeholder*='contraseña' i]",
                    "input[id*='password' i]",
                    "#password",
                ]

                password_filled = False
                for selector in password_selectors:
                    try:
                        await page.fill(selector, self.password, timeout=2000)
                        print(f"✅ Password filled using selector: {selector}")
                        password_filled = True
                        break
                    except:
                        continue

                if not password_filled:
                    print("❌ No se pudo encontrar el campo de contraseña")
                    return []

                # Click login button with multiple selectors
                button_selectors = [
                    "button[type='submit']",
                    "button:has-text('Ingresar')",
                    "button:has-text('Login')",
                    "button:has-text('Entrar')",
                    "input[type='submit']",
                    "button.btn-primary",
                    "button.login-button",
                    "form button",
                ]

                button_clicked = False
                for selector in button_selectors:
                    try:
                        await page.click(selector, timeout=2000)
                        print(f"✅ Login button clicked using selector: {selector}")
                        button_clicked = True
                        break
                    except:
                        continue

                if not button_clicked:
                    print("❌ No se pudo encontrar el botón de login")
                    print("   Intentando presionar Enter en el campo de contraseña...")
                    # Fallback: press Enter on password field
                    try:
                        await page.press("input[type='password']", "Enter")
                        print("✅ Enter pressed on password field")
                    except:
                        print("❌ Tampoco funcionó presionar Enter")
                        return []

                # Wait for navigation/login to complete
                print("⏳ Waiting for login...")
                await page.wait_for_load_state("networkidle")

                # 2. Navigate to Portfolio
                # We might already be there or need to click a link
                # Let's try to find a link with text "Tenencia" or "Portafolio"
                print("🔍 Navigating to Portfolio...")

                # Try direct URL if we knew it, otherwise click
                # Based on previous dump, we saw "Tenencia" in headers
                # Let's assume we are redirected to dashboard.
                # We need to find the portfolio table.

                # Wait for the table to appear
                try:
                    await page.wait_for_selector("div.table", timeout=10000)
                    print("✅ Portfolio table found!")
                except:
                    print("⚠️ Table not found immediately. Trying to navigate...")
                    # Try clicking "Tenencia" or similar
                    await page.click("text=Tenencia")
                    await page.wait_for_selector("div.table")

                # 3. Extract Data
                print("📥 Extracting data...")
                assets = []

                # Find all content rows
                rows = await page.query_selector_all("div.content-row")
                print(f"Found {len(rows)} rows.")

                for row in rows:
                    cols = await row.query_selector_all("div.content-item")
                    # We expect at least 5 columns based on analysis
                    if len(cols) >= 5:
                        # Extract text
                        ticker_text = await cols[0].inner_text()
                        qty_text = await cols[1].inner_text()
                        price_text = await cols[2].inner_text()
                        total_text = await cols[4].inner_text()

                        # Clean data
                        symbol = ticker_text.strip()

                        # Parse Quantity (remove dots if any, though usually qty is int)
                        # Example: "28" or "1.000"
                        qty_clean = qty_text.strip().replace(".", "").replace(",", ".")
                        try:
                            quantity = float(qty_clean)
                        except:
                            quantity = 0.0

                        # Parse Price (AR$ 13.380,00 -> 13380.00)
                        price_clean = (
                            price_text.replace("AR$", "").replace(".", "").replace(",", ".").strip()
                        )
                        try:
                            price = float(price_clean)
                        except:
                            price = 0.0

                        # Parse Total
                        total_clean = (
                            total_text.replace("AR$", "").replace(".", "").replace(",", ".").strip()
                        )
                        try:
                            total_val = float(total_clean)
                        except:
                            total_val = 0.0

                        if symbol and quantity > 0:
                            asset = {
                                "symbol": symbol,
                                "quantity": quantity,
                                "avg_price": price,  # Using current price as avg for now
                                "total_val": total_val,
                                "market": "ARG",  # Default
                            }
                            assets.append(asset)
                            print(f"   ✅ Found: {symbol} x {quantity} = ${total_val:,.2f}")

                return assets

            except Exception as e:
                print(f"❌ Error scraping Tienda Broker: {e}")
                # Take screenshot for debug
                await page.screenshot(path="tb_error.png")
                return []
            finally:
                await browser.close()


# Wrapper for synchronous call
def get_tienda_broker_portfolio():
    """
    Runs the scraper in a separate process to avoid asyncio/Streamlit conflicts.
    """
    print("🚀 Launching scraper subprocess...")

    # Path to the scraper script
    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "run_scraper.py"
    )

    # Use the same python interpreter
    python_exe = sys.executable

    # Force UTF-8 encoding for the subprocess
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        result = subprocess.run(
            [python_exe, script_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
            env=env,
        )

        output = result.stdout

        # Extract JSON part
        if "__JSON_START__" in output and "__JSON_END__" in output:
            json_str = output.split("__JSON_START__")[1].split("__JSON_END__")[0].strip()
            return json.loads(json_str)
        else:
            print("❌ Scraper output format invalid")
            print("Output:", output)
            return []

    except subprocess.CalledProcessError as e:
        print(f"❌ Scraper process failed: {e}")
        print("Stderr:", e.stderr)
        return []
    except Exception as e:
        print(f"❌ Error running scraper subprocess: {e}")
        return []

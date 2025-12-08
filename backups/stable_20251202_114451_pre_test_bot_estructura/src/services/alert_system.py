"""
Alert System for Trading Signals
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class AlertSystem:
    """
    Alert system for trading signals.
    Supports console, email, and file logging.
    """

    def __init__(self, email_config=None):
        """
        Args:
            email_config: Dict with 'smtp_server', 'smtp_port', 'username', 'password', 'to_email'
        """
        self.email_config = email_config
        self.alerts_log = []

    def send_alert(self, alert_type, symbol, message, data=None):
        """
        Send alert through multiple channels.

        Args:
            alert_type: 'BUY', 'SELL', 'HOLD', 'WARNING', 'INFO'
            symbol: Stock symbol
            message: Alert message
            data: Additional data (dict)
        """
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "symbol": symbol,
            "message": message,
            "data": data or {},
        }

        self.alerts_log.append(alert)

        # Console alert
        self._console_alert(alert)

        # File logging
        self._log_to_file(alert)

        # Email alert (if configured and critical)
        if self.email_config and alert_type in ["BUY", "SELL", "WARNING"]:
            self._send_email_alert(alert)

        return alert

    def _console_alert(self, alert):
        """Print alert to console with colors."""
        colors = {
            "BUY": "\033[92m",  # Green
            "SELL": "\033[91m",  # Red
            "HOLD": "\033[93m",  # Yellow
            "WARNING": "\033[95m",  # Magenta
            "INFO": "\033[94m",  # Blue
        }
        reset = "\033[0m"

        color = colors.get(alert["type"], "")

        print(f"\n{color}{'='*60}")
        print(f"🚨 ALERT: {alert['type']}")
        print(f"Symbol: {alert['symbol']}")
        print(f"Time: {alert['timestamp']}")
        print(f"Message: {alert['message']}")
        if alert["data"]:
            print(f"Data: {json.dumps(alert['data'], indent=2)}")
        print(f"{'='*60}{reset}\n")

    def _log_to_file(self, alert):
        """Log alert to file."""
        log_file = "alerts.log"

        with open(log_file, "a") as f:
            f.write(json.dumps(alert) + "\n")

    def _send_email_alert(self, alert):
        """Send email alert."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["username"]
            msg["To"] = self.email_config["to_email"]
            msg["Subject"] = f"🚨 Trading Alert: {alert['type']} - {alert['symbol']}"

            body = f"""
            <html>
            <body>
                <h2>Trading Alert</h2>
                <p><strong>Type:</strong> {alert['type']}</p>
                <p><strong>Symbol:</strong> {alert['symbol']}</p>
                <p><strong>Time:</strong> {alert['timestamp']}</p>
                <p><strong>Message:</strong> {alert['message']}</p>
                <p><strong>Data:</strong></p>
                <pre>{json.dumps(alert['data'], indent=2)}</pre>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, "html"))

            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            server.login(self.email_config["username"], self.email_config["password"])
            server.send_message(msg)
            server.quit()

            print(f"✅ Email alert sent to {self.email_config['to_email']}")
        except Exception as e:
            print(f"❌ Failed to send email alert: {e}")

    def get_recent_alerts(self, limit=10):
        """Get recent alerts."""
        return self.alerts_log[-limit:]

    def clear_alerts(self):
        """Clear alerts log."""
        self.alerts_log = []


# Example usage
if __name__ == "__main__":
    # Initialize without email (console only)
    alert_system = AlertSystem()

    # Send different types of alerts
    alert_system.send_alert(
        "BUY",
        "AAPL",
        "Strong buy signal detected",
        data={"price": 150.00, "rsi": 28.5, "macd": "bullish_crossover", "confidence": 0.85},
    )

    alert_system.send_alert(
        "SELL",
        "MSFT",
        "Overbought condition - consider taking profits",
        data={"price": 380.00, "rsi": 72.3, "take_profit": 385.00},
    )

    alert_system.send_alert(
        "WARNING", "GOOGL", "High volatility detected", data={"atr": 15.5, "volatility": 0.45}
    )

    # Get recent alerts
    print("\nRecent Alerts:")
    for alert in alert_system.get_recent_alerts():
        print(f"- {alert['type']}: {alert['symbol']} at {alert['timestamp']}")

"""
Logging configuration for IOL Quantum AI system.
"""

import logging
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "iol_quantum.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

# Create logger
logger = logging.getLogger("iol_quantum")

# Set levels for specific modules
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("playwright").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Name of the module

    Returns:
        Logger instance
    """
    return logging.getLogger(f"iol_quantum.{name}")

"""
Custom exceptions for IOL Quantum AI system.
"""


class IOLAuthenticationError(Exception):
    """Raised when IOL authentication fails."""

    pass


class IOLAPIError(Exception):
    """Raised when IOL API returns an error."""

    pass


class TiendaBrokerScrapingError(Exception):
    """Raised when Tienda Broker scraping fails."""

    pass


class TiendaBrokerLoginError(Exception):
    """Raised when Tienda Broker login fails."""

    pass


class PortfolioSyncError(Exception):
    """Raised when portfolio synchronization fails."""

    pass


class PriceFetchError(Exception):
    """Raised when price fetching fails."""

    pass


class ModelTrainingError(Exception):
    """Raised when model training fails."""

    pass


class DataValidationError(Exception):
    """Raised when data validation fails."""

    pass

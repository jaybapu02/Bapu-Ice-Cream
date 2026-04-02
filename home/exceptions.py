class OrderProcessingError(Exception):
    """Exception raised when an error occurs during order processing."""
    pass

class PaymentFailedError(Exception):
    """Exception raised when a payment processing failure occurs."""
    pass

class StockUnavailableError(Exception):
    """Exception raised when the requested ice cream stock is unavailable."""
    pass

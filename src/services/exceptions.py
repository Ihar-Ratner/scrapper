import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ScraperError(Exception):
    """Base exception for scraper errors"""
    def __init__(self, message: str, articule: Optional[str] = None, user_id: Optional[int] = None):
        super().__init__(message)
        self.message = message
        self.articule = articule
        self.user_id = user_id
        self.logged = False

class ProductNotFoundError(ScraperError):
    """Product not found on website"""
    pass

class NetworkError(ScraperError):
    """Network-related errors (retryable)"""
    pass

class ValidationError(ScraperError):
    """Input validation errors"""
    pass

class CacheError(ScraperError):
    """Cache-related errors"""
    pass

class BotError(ScraperError):
    """Bot-related errors"""
    pass

class StorageError(ScraperError):
    """Storage-related errors"""
    pass

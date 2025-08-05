import logging
import traceback
from typing import Optional, Callable, Any, Dict
from functools import wraps
from .exceptions import *

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling service"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.retryable_errors = {NetworkError, TimeoutError, ConnectionError}
    
    def handle_scraper_error(self, error: Exception, articule: str, user_id: int) -> str:
        """Handle scraper errors with appropriate user messages"""
        if isinstance(error, ProductNotFoundError):
            return f"❌ Product {articule} not found on Wildberries"
        elif isinstance(error, NetworkError):
            return f"⚠️ Network error for {articule}. Please try again later."
        elif isinstance(error, ValidationError):
            return f"❌ Invalid article ID: {articule}"
        else:
            logger.error(f"Unexpected error for {articule}: {error}")
            return f"❌ Error processing {articule}. Please try again."
    
    def handle_bot_error(self, error: Exception, user_id: int) -> str:
        """Handle bot errors with user-friendly messages"""
        if isinstance(error, ValidationError):
            return "❌ Invalid input. Please check your command format."
        elif isinstance(error, StorageError):
            return "⚠️ Storage error. Your data may not be saved."
        else:
            logger.error(f"Bot error for user {user_id}: {error}")
            return "❌ Bot error. Please try again later."
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log error with context"""
        if not hasattr(error, 'logged') or not error.logged:
            logger.error(f"Error: {error}", exc_info=True, extra=context)
            error.logged = True
    
    def is_retryable(self, error: Exception) -> bool:
        """Check if error is retryable"""
        return type(error) in self.retryable_errors
    
    def get_error_stats(self) -> Dict[str, int]:
        """Get error statistics"""
        return self.error_counts.copy()

def handle_errors(func: Callable) -> Callable:
    """Decorator for consistent error handling"""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Optional[Any]:
        try:
            return await func(*args, **kwargs)
        except ProductNotFoundError as e:
            logger.warning(f"Product not found: {e}")
            return None
        except NetworkError as e:
            logger.error(f"Network error: {e}")
            return None
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return None
    return wrapper

# Add to error_handler.py
def retry_on_network_error(max_retries: int = 3, delay: float = 1.0):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except NetworkError as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

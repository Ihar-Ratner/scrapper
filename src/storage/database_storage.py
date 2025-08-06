from typing import List, Dict, Any, Optional
from .database_manager import DatabaseManager
from ..config.settings import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseStorage:
    """Database-based storage implementation"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def load_articules_for(self, user_id: int) -> List[str]:
        """Load articles for user from database"""
        try:
            return self.db_manager.get_user_articles(user_id)
        except Exception as e:
            logger.error(f"Error loading articles for user {user_id}: {e}")
            return []
    
    def save_articules_for(self, user_id: int, articules: List[str]) -> None:
        """Save articles for user to database"""
        try:
            # Remove existing articles
            existing = self.db_manager.get_user_articles(user_id)
            to_remove = [art for art in existing if art not in articules]
            if to_remove:
                self.db_manager.remove_articles(user_id, to_remove)
            
            # Add new articles
            to_add = [art for art in articules if art not in existing]
            if to_add:
                self.db_manager.add_articles(user_id, to_add)
        except Exception as e:
            logger.error(f"Error saving articles for user {user_id}: {e}")
            raise
    
    def load_results_for(self, user_id: int) -> List[Dict[str, Any]]:
        """Load price results for user from database"""
        try:
            # Get latest prices with product names
            latest_prices = self.db_manager.get_latest_prices_with_names(user_id)
            return [
                {
                    "articule": articule,
                    "product_name": data.get("product_name", "Unknown Product"),
                    "final_price": data.get("price_string", "0"),  # Use original price string
                    "last_execution": data.get("scraped_at", "2024-01-01T00:00:00")
                }
                for articule, data in latest_prices.items()
            ]
        except Exception as e:
            logger.error(f"Error loading results for user {user_id}: {e}")
            return []
    
    def save_results_for(self, user_id: int, results: List[Dict[str, Any]]) -> None:
        """Save price results for user to database"""
        try:
            for result in results:
                self.db_manager.save_product_price(
                    articule=result["articule"],
                    product_name=result["product_name"],
                    final_price=result["final_price"],
                    user_id=user_id
                )
        except Exception as e:
            logger.error(f"Error saving results for user {user_id}: {e}")
            raise

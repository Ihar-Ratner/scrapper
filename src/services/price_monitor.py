import asyncio
import logging
import re
from typing import List, Optional
from datetime import datetime
from ..models.product import Product
from ..storage.database_storage import DatabaseStorage
from ..scraper.wildberries import WildberriesScraper
from .cache_manager import CacheManager
from ..config.settings import settings
from .exceptions import *
from .error_handler import ErrorHandler, handle_errors

logger = logging.getLogger(__name__)

def parse_price(price_str: str) -> float:
    """Parse price string to float - from your working code"""
    try:
        m = re.search(r"[\d\s]+,\d{2}", price_str)
        if m:
            return float(m.group().replace(" ", "").replace(",", "."))
        else:
            # Fallback: try to extract any number
            numbers = re.findall(r'[\d\s,]+', price_str)
            if numbers:
                clean_number = numbers[0].replace(" ", "").replace(",", ".")
                return float(clean_number)
            return 0.0
    except Exception as e:
        logger.error(f"Error parsing price '{price_str}': {e}")
        return 0.0

class PriceMonitor:
    def __init__(self, storage: DatabaseStorage, scraper: WildberriesScraper, cache_manager: CacheManager = None):
        self.storage = storage
        self.scraper = scraper
        self.cache_manager = cache_manager or CacheManager()
        self.error_handler = ErrorHandler()
    
    @handle_errors
    async def check_prices_for_user(self, user_id: int) -> List[str]:
        """Check prices for a specific user with enhanced error handling"""
        try:
            # Load user's tracked articles
            articules = self.storage.load_articules_for(user_id)
            if not articules:
                return ["❗ No articles tracked. Use /add to add some!"]
            
            logger.info(f"User {user_id}: Checking {len(articules)} products")
            
            # Load previous results for comparison
            old_products = self.storage.load_results_for(user_id)
            old_map = {}
            for item in old_products:
                try:
                    price_str = item.get("final_price", "0")
                    old_map[item["articule"]] = parse_price(price_str)
                except Exception as e:
                    logger.error(f"Error parsing old price for {item.get('articule', 'unknown')}: {e}")
                    old_map[item["articule"]] = 0.0
            
            # Concurrent processing with rate limiting using settings
            semaphore = asyncio.Semaphore(settings.scraping.max_concurrent_requests)
            
            async def process_article(articule: str):
                """Process a single article with enhanced error handling"""
                async with semaphore:
                    try:
                        # Try to get from cache first
                        cached_product = await self.cache_manager.get_product(articule)
                        
                        if cached_product:
                            logger.debug(f"User {user_id}: Using cached data for {articule}")
                            return cached_product, "cached"
                        else:
                            # Scrape fresh data with rate limiting
                            await asyncio.sleep(settings.scraping.rate_limit_delay)
                            logger.info(f"User {user_id}: Scraping {articule}")
                            product = await self.scraper.get_product_details(articule)
                            
                            if not product:
                                raise ProductNotFoundError(f"Product {articule} not found", articule, user_id)
                            
                            # Cache the result
                            await self.cache_manager.cache_product(product)
                            return product, "scraped"
                            
                    except ProductNotFoundError:
                        raise
                    except NetworkError:
                        raise
                    except Exception as e:
                        logger.error(f"Error processing {articule} for user {user_id}: {e}")
                        raise ScraperError(f"Failed to process {articule}", articule, user_id)
            
            # Run all tasks concurrently
            tasks = [process_article(art) for art in articules]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results with better error handling
            new_products = []
            messages = []
            cache_hits = 0
            cache_misses = 0
            
            for i, result in enumerate(results):
                articule = articules[i]
                
                if isinstance(result, Exception):
                    # Handle specific error types
                    error_message = self.error_handler.handle_scraper_error(result, articule, user_id)
                    messages.append(error_message)
                    self.error_handler.log_error(result, {"articule": articule, "user_id": user_id})
                    continue
                
                product, source = result
                
                if source == "cached":
                    cache_hits += 1
                elif source == "scraped":
                    cache_misses += 1
                
                if product:
                    new_products.append(product)
                    
                    # Compare with old price
                    old_price = old_map.get(articule, 0)
                    new_price = parse_price(product.final_price)
                    
                    logger.info(f"User {user_id}: {articule} - Old: {old_price}, New: {new_price}")
                    
                    if new_price != old_price:
                        diff = new_price - old_price
                        sign = "+" if diff > 0 else ""
                        messages.append(
                            f"ℹ️ {product.product_name[:50]}: {old_price:.2f} → <b>{new_price:.2f}</b> ({sign}{diff:.2f})"
                        )
                    # else:
                    #     messages.append(f"ℹ️ {product.product_name[:50]}: unchanged at <b>{new_price:.2f}</b>")
            
            # Log cache statistics
            logger.info(f"User {user_id}: Cache hits={cache_hits}, misses={cache_misses}")
            
            # Save new results
            if new_products:
                try:
                    data = [
                        {
                            "articule": p.articule,
                            "product_name": p.product_name,
                            "final_price": p.final_price,
                            "last_execution": p.last_execution.isoformat()
                        }
                        for p in new_products
                    ]
                    self.storage.save_results_for(user_id, data)
                    logger.info(f"User {user_id}: Saved {len(new_products)} results")
                except Exception as e:
                    logger.error(f"Error saving results for user {user_id}: {e}")
                    messages.append("⚠️ Some results may not be saved due to storage error.")
            
            # return messages if messages else ["ℹ️ No price changes detected."]
            # At the end, replace line 162 with:
            if not messages:
                if not new_products:
                    return ["❌ Unable to check any products. All requests failed."]
                else:
                    return []  # ✅ Return empty list = no message sent (silent)
            else:
                return messages  # ✅ Return actual change messages
            
        except Exception as e:
            logger.error(f"Error in price monitoring for user {user_id}: {e}")
            return [self.error_handler.handle_bot_error(e, user_id)]

    async def get_cache_stats(self) -> dict[str, any]:
        """Get cache statistics"""
        return self.cache_manager.get_stats()
    
    async def clear_cache(self) -> None:
        """Clear all cache entries"""
        await self.cache_manager.clear_all()
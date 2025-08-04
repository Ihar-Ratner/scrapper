# import asyncio
# import logging
# import re
# from typing import List, Optional
# from datetime import datetime
# from ..models.product import Product
# from ..storage.file_storage import FileStorage
# from ..scraper.wildberries import WildberriesScraper

# logger = logging.getLogger(__name__)

# def parse_price(price_str: str) -> float:
#     """Parse price string to float - from your working code"""
#     try:
#         m = re.search(r"[\d\s]+,\d{2}", price_str)
#         if m:
#             return float(m.group().replace(" ", "").replace(",", "."))
#         else:
#             # Fallback: try to extract any number
#             numbers = re.findall(r'[\d\s,]+', price_str)
#             if numbers:
#                 clean_number = numbers[0].replace(" ", "").replace(",", ".")
#                 return float(clean_number)
#             return 0.0
#     except Exception as e:
#         logger.error(f"Error parsing price '{price_str}': {e}")
#         return 0.0

# class PriceMonitor:
#     def __init__(self, storage: FileStorage, scraper: WildberriesScraper):
#         self.storage = storage
#         self.scraper = scraper
    
#     async def check_prices_for_user(self, user_id: int) -> List[str]:
#         """Check prices for a specific user and return comparison messages"""
#         try:
#             # Load user's tracked articles
#             articules = self.storage.load_articules_for(user_id)
#             if not articules:
#                 return ["❗ No articles tracked. Use /add to add some!"]
            
#             logger.info(f"User {user_id}: Checking {len(articules)} products")
            
#             # Load previous results with proper price parsing
#             old_products = self.storage.load_results_for(user_id)
#             old_map = {}
#             for item in old_products:
#                 try:
#                     price_str = item.get("final_price", "0")
#                     old_map[item["articule"]] = parse_price(price_str)
#                 except Exception as e:
#                     logger.error(f"Error parsing old price for {item.get('articule', 'unknown')}: {e}")
#                     old_map[item["articule"]] = 0.0
            
#             # Scrape current prices
#             new_products = []
#             messages = []
            
#             for articule in articules:
#                 try:
#                     logger.info(f"Scraping {articule} for user {user_id}")
#                     product = await self.scraper.get_product_details(articule)
                    
#                     if product:
#                         new_products.append(product)
                        
#                         # Compare with old price using proper parsing
#                         old_price = old_map.get(articule, 0)
#                         new_price = parse_price(product.final_price)
                        
#                         logger.info(f"User {user_id}: {articule} - Old: {old_price}, New: {new_price}")
                        
#                         if new_price != old_price:
#                             diff = new_price - old_price
#                             sign = "+" if diff > 0 else ""
#                             messages.append(
#                                 f"ℹ️ {product.product_name[:50]}: {old_price:.2f} → <b>{new_price:.2f}</b> ({sign}{diff:.2f})"
#                             )
#                         else:
#                             messages.append(f"ℹ️ {product.product_name[:50]}: unchanged at <b>{new_price:.2f}</b>")
#                     else:
#                         messages.append(f"❌ {articule}: Failed to scrape")
                        
#                 except Exception as e:
#                     logger.error(f"Error processing {articule} for user {user_id}: {e}")
#                     messages.append(f"❌ {articule}: {str(e)}")
                
#                 # Rate limiting
#                 await asyncio.sleep(2)
            
#             # Save new results
#             if new_products:
#                 data = [
#                     {
#                         "articule": p.articule,
#                         "product_name": p.product_name,
#                         "final_price": p.final_price,
#                         "last_execution": p.last_execution.isoformat()
#                     }
#                     for p in new_products
#                 ]
#                 self.storage.save_results_for(user_id, data)
#                 logger.info(f"User {user_id}: Saved {len(new_products)} results")
            
#             return messages if messages else ["ℹ️ No price changes detected."]
            
#         except Exception as e:
#             logger.error(f"Error in price monitoring for user {user_id}: {e}")
#             import traceback
#             traceback.print_exc()
#             return [f"❌ Error during price check: {str(e)}"]

import asyncio
import logging
import re
from typing import List, Optional
from datetime import datetime
from ..models.product import Product
from ..storage.file_storage import FileStorage
from ..scraper.wildberries import WildberriesScraper
from .cache_manager import CacheManager

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
    def __init__(self, storage: FileStorage, scraper: WildberriesScraper, cache_manager: CacheManager = None):
        self.storage = storage
        self.scraper = scraper
        self.cache_manager = cache_manager or CacheManager()
    
    async def check_prices_for_user(self, user_id: int) -> List[str]:
        """Check prices for a specific user with caching"""
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
            
            # Get current prices with caching
            new_products = []
            messages = []
            cache_hits = 0
            cache_misses = 0
            
            for articule in articules:
                try:
                    # Try to get from cache first
                    cached_product = await self.cache_manager.get_product(articule)
                    
                    if cached_product:
                        # Use cached data
                        product = cached_product
                        cache_hits += 1
                        logger.debug(f"User {user_id}: Using cached data for {articule}")
                    else:
                        # Scrape fresh data
                        logger.info(f"User {user_id}: Scraping {articule}")
                        product = await self.scraper.get_product_details(articule)
                        cache_misses += 1
                        
                        # Cache the result
                        if product:
                            await self.cache_manager.cache_product(product)
                    
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
                        else:
                            messages.append(f"ℹ️ {product.product_name[:50]}: unchanged at <b>{new_price:.2f}</b>")
                    else:
                        messages.append(f"❌ {articule}: Failed to scrape")
                        
                except Exception as e:
                    logger.error(f"Error processing {articule} for user {user_id}: {e}")
                    messages.append(f"❌ {articule}: {str(e)}")
                
                # Reduced rate limiting since we're using cache
                await asyncio.sleep(1)
            
            # Log cache statistics
            logger.info(f"User {user_id}: Cache hits={cache_hits}, misses={cache_misses}")
            
            # Save new results
            if new_products:
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
            
            return messages if messages else ["ℹ️ No price changes detected."]
            
        except Exception as e:
            logger.error(f"Error in price monitoring for user {user_id}: {e}")
            import traceback
            traceback.print_exc()
            return [f"❌ Error during price check: {str(e)}"]
    
    async def get_cache_stats(self) -> dict[str, any]:
        """Get cache statistics"""
        return self.cache_manager.get_stats()
    
    async def clear_cache(self) -> None:
        """Clear all cache entries"""
        await self.cache_manager.clear_all()
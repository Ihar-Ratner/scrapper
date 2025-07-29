import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime
from ..models.product import Product

logger = logging.getLogger(__name__)

class WildberriesScraper:
    def __init__(self, browser_pool):
        self.browser_pool = browser_pool
    
    async def get_product_details(self, articule: str) -> Optional[Product]:
        """Scrape product details from Wildberries - based on working code"""
        try:
            async with self.browser_pool.get_page() as page:
                url = f"https://www.wildberries.by/catalog/{articule}/detail.aspx"
                
                logger.info(f"Scraping {articule} from {url}")
                
                # Navigate to page with more reliable wait strategy
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait for either the title or price to appear (whichever comes first)
                try:
                    await page.wait_for_selector(".product-page__title, .price-block__final-price", 
                                               timeout=20000, state="visible")
                except:
                    # If that fails, just wait a bit
                    await asyncio.sleep(5)
                
                # Wait a bit for dynamic content to load
                await asyncio.sleep(2)
                
                # Wait for product name with multiple selectors
                name_selectors = [
                    ".product-page__title",
                    "h1.product-page__title", 
                    "[data-testid='product-title']",
                    "h1",
                    ".product-page__title-text",
                    ".product-page__title h1",
                    ".product-page__title span"
                ]
                
                product_name = None
                for selector in name_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=5000)
                        product_name = await element.text_content()
                        if product_name and product_name.strip():
                            break
                    except:
                        continue
                
                if not product_name:
                    # Try JavaScript as fallback
                    try:
                        product_name = await page.evaluate("""
                            () => {
                                const selectors = [
                                    '.product-page__title',
                                    'h1.product-page__title',
                                    '[data-testid="product-title"]',
                                    'h1',
                                    '.product-page__title-text'
                                ];
                                for (const selector of selectors) {
                                    const el = document.querySelector(selector);
                                    if (el && el.textContent.trim()) {
                                        return el.textContent.trim();
                                    }
                                }
                                return null;
                            }
                        """)
                    except:
                        pass
                    
                if not product_name:
                    raise Exception(f"Product name not found for {articule}")
                
                # Wait for price with multiple selectors
                price_selectors = [
                    "ins.price-block__final-price.red-price",
                    ".price-block__final-price",
                    "[data-testid='price']",
                    ".price",
                    ".price-block__final-price ins",
                    ".price-block__final-price .red-price",
                    ".price-block__final-price span",
                    ".price-block__final-price .price",
                    ".product-page__price .price",
                    ".product-page__price ins",
                    ".product-page__price .red-price"
                ]
                
                final_price = None
                for selector in price_selectors:
                    try:
                        # Try locator first
                        element = await page.locator(selector).first
                        await element.wait_for(state="visible", timeout=3000)
                        final_price = await element.text_content()
                        if final_price and final_price.strip():
                            break
                    except:
                        try:
                            # Try direct selector
                            element = await page.wait_for_selector(selector, timeout=3000)
                            final_price = await element.text_content()
                            if final_price and final_price.strip():
                                break
                        except:
                            continue
                
                if not final_price:
                    # Try JavaScript as fallback
                    try:
                        final_price = await page.evaluate("""
                            () => {
                                const selectors = [
                                    'ins.price-block__final-price.red-price',
                                    '.price-block__final-price',
                                    '[data-testid="price"]',
                                    '.price',
                                    '.price-block__final-price ins',
                                    '.price-block__final-price .red-price',
                                    '.product-page__price .price',
                                    '.product-page__price ins'
                                ];
                                for (const selector of selectors) {
                                    const el = document.querySelector(selector);
                                    if (el && el.textContent.trim()) {
                                        return el.textContent.trim();
                                    }
                                }
                                return null;
                            }
                        """)
                    except:
                        pass
                    
                if not final_price:
                    # Log the page content for debugging
                    page_content = await page.content()
                    logger.error(f"Price not found for {articule}. Page title: {await page.title()}")
                    logger.error(f"Page URL: {page.url}")
                    raise Exception(f"Price not found for {articule}")
                
                logger.info(f"Successfully scraped {articule}: {product_name.strip()} - {final_price.strip()}")
                
                return Product(
                    articule=articule,
                    product_name=product_name.strip(),
                    final_price=final_price.strip(),
                    last_execution=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error(f"Failed to scrape {articule}: {e}")
            return None
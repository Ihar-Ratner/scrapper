import asyncio
from playwright.async_api import async_playwright, Browser, Page
from contextlib import asynccontextmanager
from typing import Optional
import logging
from ..config.settings import settings

logger = logging.getLogger(__name__)

class BrowserPool:
    def __init__(self, max_browsers: int = None):
        self.max_browsers = max_browsers or settings.max_browsers
        self.browsers: list[Browser] = []
        self.semaphore = asyncio.Semaphore(self.max_browsers)
        self.playwright = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize the Playwright instance and browser pool"""
        if self._initialized:
            return
            
        try:
            self.playwright = await async_playwright().start()
            logger.info(f"Browser pool initialized with max {self.max_browsers} browsers")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize browser pool: {e}")
            raise
    
    async def cleanup(self):
        """Clean up all browsers and Playwright instance"""
        try:
            # Close all browsers
            for browser in self.browsers:
                try:
                    await browser.close()
                except Exception as e:
                    logger.warning(f"Error closing browser: {e}")
            
            self.browsers.clear()
            
            # Stop Playwright
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            self._initialized = False
            logger.info("Browser pool cleaned up")
        except Exception as e:
            logger.error(f"Error during browser pool cleanup: {e}")
    
    @asynccontextmanager
    async def get_browser(self):
        """Get a browser from the pool (context manager)"""
        if not self._initialized:
            raise RuntimeError("Browser pool not initialized. Call initialize() first.")
        
        async with self.semaphore:
            # Get or create browser
            if not self.browsers:
                browser = await self.playwright.chromium.launch(
                    headless=False,  # Much faster than headless=False
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-web-security",
                        "--disable-features=VizDisplayCompositor"
                    ]
                )
                self.browsers.append(browser)
                logger.debug("Created new browser instance")
            
            browser = self.browsers.pop()
            try:
                yield browser
            finally:
                # Return browser to pool
                self.browsers.append(browser)
    
    @asynccontextmanager
    async def get_page(self):
        """Get a page from a browser in the pool"""
        async with self.get_browser() as browser:
            page = await browser.new_page()
            try:
                # Set realistic headers
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                })
                
                yield page
            finally:
                await page.close()

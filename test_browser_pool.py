import asyncio
from browser_pool import BrowserPool

async def test_browser_pool():
    pool = BrowserPool(max_browsers=2)
    
    try:
        await pool.initialize()
        print("✅ Browser pool initialized")
        
        # Test scraping multiple products
        test_articles = ["123456", "789012", "345678"]
        
        for art in test_articles:
            async with pool.get_page() as page:
                print(f"✅ Got page for article {art}")
                # You can add actual scraping logic here
        
        print("✅ All tests passed")
        
    finally:
        await pool.cleanup()
        print("✅ Browser pool cleaned up")

if __name__ == "__main__":
    asyncio.run(test_browser_pool()) 
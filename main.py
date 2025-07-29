import asyncio
import logging
import os
from telegram.ext import Application, CommandHandler
from src.scraper.browser_pool import BrowserPool
from src.scraper.wildberries import WildberriesScraper
from src.storage.file_storage import FileStorage
from src.services.price_monitor import PriceMonitor
from src.services.subscription import SubscriptionService
from src.bot.handlers.commands import CommandHandlers

# Setup logging
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=logging.INFO
)

async def main():
    try:
        # Initialize components
        storage = FileStorage()
        browser_pool = BrowserPool(max_browsers=3)
        await browser_pool.initialize()
        
        scraper = WildberriesScraper(browser_pool)
        price_monitor = PriceMonitor(storage, scraper)
        subscription_service = SubscriptionService()
        
        # Initialize command handlers - FIX: Use the created instance
        handlers = CommandHandlers(price_monitor, storage, subscription_service)
        
        # Initialize bot
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            print("Error: TELEGRAM_TOKEN environment variable not set")
            return
        
        app = Application.builder().token(token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", handlers.start_command))
        app.add_handler(CommandHandler("add", handlers.add_command))
        app.add_handler(CommandHandler("show", handlers.show_command))
        app.add_handler(CommandHandler("check", handlers.check_command))
        app.add_handler(CommandHandler("compare", handlers.compare_command))
        app.add_handler(CommandHandler("remove", handlers.remove_command))
        app.add_handler(CommandHandler("subscribe", handlers.subscribe_command))
        app.add_handler(CommandHandler("unsubscribe", handlers.unsubscribe_command))
        app.add_handler(CommandHandler("setinterval", handlers.setinterval_command))
        
        # Start bot
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        print("Bot started successfully! ��")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down...")
        finally:
            await app.stop()
            await browser_pool.cleanup()
            
    except Exception as e:
        print(f"Error starting bot: {e}")
        logging.error(f"Bot startup error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
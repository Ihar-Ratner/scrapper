import asyncio
import logging
import os
from telegram.ext import Application, CommandHandler
from src.scraper.browser_pool import BrowserPool
from src.scraper.wildberries import WildberriesScraper
from src.services.price_monitor import PriceMonitor
from src.services.subscription import SubscriptionService
from src.services.cache_manager import CacheManager
from src.bot.handlers.commands import CommandHandlers
from src.config.settings import settings
from src.storage.database_storage import DatabaseStorage
from src.storage.database_manager import DatabaseManager
from src.bot.scheduler import Scheduler

# Setup logging using settings
logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
    level=getattr(logging, settings.log_level),
    # Uncomment for logging to file
    #filename=settings.log_file
)

async def main():
    try:
        # Validate required settings
        if not settings.telegram_token:
            print("Error: TELEGRAM_TOKEN environment variable not set")
            return


        # Initialize components using settings
        storage = DatabaseStorage()
        browser_pool = BrowserPool(max_browsers=settings.max_browsers)
        await browser_pool.initialize()

        
        # Initialize database manager
        db_manager = DatabaseManager()

        # Initialize cache manager using settings
        cache_manager = CacheManager(
            memory_cache_size=settings.cache.memory_cache_size,
            cache_ttl_minutes=settings.cache.cache_ttl_minutes,
            disk_cache_enabled=settings.cache.disk_cache_enabled,
            cache_dir=settings.cache.cache_dir
        )
        
        scraper = WildberriesScraper(browser_pool)
        price_monitor = PriceMonitor(storage, scraper, cache_manager)
        subscription_service = SubscriptionService(db_manager)
        
        # Initialize command handlers - FIX: Use the created instance
        handlers = CommandHandlers(price_monitor, storage, subscription_service)
        
        app = Application.builder().token(settings.telegram_token).build()

        # Initialize scheduler with database manager
        scheduler = Scheduler(app.job_queue, price_monitor, db_manager)
        
        # Add handlers
        app.add_handler(CommandHandler("help", handlers.help_command))
        app.add_handler(CommandHandler("add", handlers.add_command))
        app.add_handler(CommandHandler("show", handlers.show_command))
        app.add_handler(CommandHandler("check", handlers.check_command))
        app.add_handler(CommandHandler("remove", handlers.remove_command))
        app.add_handler(CommandHandler("subscribe", handlers.subscribe_command))
        app.add_handler(CommandHandler("unsubscribe", handlers.unsubscribe_command))
        app.add_handler(CommandHandler("setinterval", handlers.setinterval_command))
        app.add_handler(CommandHandler("cache", handlers.cache_command))

        # Restore scheduled jobs
        await scheduler.restore_jobs()

        # Start cache cleanup task
        asyncio.create_task(cache_cleanup_task(cache_manager))
        
        # Start bot
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        
        print("Bot started successfully! ��")
        print(f"Configuration: {settings.max_browsers} browsers, {settings.cache.memory_cache_size} cache items")

         # Start cache cleanup task
        asyncio.create_task(cache_cleanup_task(cache_manager))
        
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

async def cache_cleanup_task(cache_manager: CacheManager):
    """Periodic cache cleanup task"""
    while True:
        try:
            #await asyncio.sleep(300)  # Run every 5 minutes
            await asyncio.sleep(settings.cache.cleanup_interval_minutes * 60)
            await cache_manager.clear_expired()
        except Exception as e:
            logging.error(f"Cache cleanup error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

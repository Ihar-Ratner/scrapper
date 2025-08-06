import logging
import re
import asyncio  # Add this import
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from ...services.price_monitor import PriceMonitor
from ...services.validation import validate_article_ids
from ...services.subscription import SubscriptionService
from ...storage.file_storage import FileStorage
from ...config.settings import settings
from ...services.exceptions import *
from ...services.error_handler import ErrorHandler
from ...storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class CommandHandlers:
    def __init__(self, price_monitor: PriceMonitor, storage: FileStorage, subscription_service: SubscriptionService):
        self.price_monitor = price_monitor
        self.storage = storage
        self.subscription_service = subscription_service
        self.error_handler = ErrorHandler()  # Add this
        self.db_manager = DatabaseManager()
    
    async def start_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - exact copy from your working telegram_message.py"""
        #user = update.effective_user
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)

        welcome_text = (
            "🎉 Welcome to Wildberries Price Monitor!\n\n"
            "Commands:\n"
            "• /add <article_id> - Add product to track\n"
            "• /show - Show tracked products\n"
            "• /check - Check current prices\n"
            "• /compare - Compare with previous prices\n"
            "• /remove <article_id> - Remove product\n"
            "• /subscribe - Start periodic updates\n"
            "• /unsubscribe - Stop periodic updates\n"
            "• /setinterval <minutes> - Set update interval\n"
            "• /cache - Show cache statistics\n"
            "• /help - Show this help"
        )

        # text = (
        #     f"Hi {user.mention_markdown_v2()}\\!  \n"
        #     "To start using this bot, you have to prepare your data:\n"
        #     "1\\. Add product with `add` command\n"
        #     "2\\. Execute `check` command to collect data about interested product\n"
        #     "3\\. Read instructions below to manage your tracking list\n\n\n"
        #     "Send `/check <articule>` to fetch product details\\.\n"
        #     "`/add <id1,id2,…>` to add new articules\\.\n"
        #     "`/remove <art1,art2,…> or /remove art1 art2` to remove some products from you tracking list\\.\n"
        #     "`/show` to get articule: product name that you are currently tracking\\.\n"
        #     "`/compare` to compare latest prices with current ones\\.\n"
        #     "`/subscribe` to start product tracking \\(default value is evey 5 mins\\)\\.\n"
        #     "`/unsubscribe` to stop product tracking\\.\n"
        #     "`/setinterval <minutes>` to set up your own tracking interval if you are subscribed\\.\n"
        # )
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    async def errors_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Show error statistics"""
        stats = self.error_handler.get_error_stats()

    async def add_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /add command with article existence validation"""
        #user_id = update.effective_user.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)
        
        if not ctx.args:
            await update.message.reply_text("Usage: /add <article_id1> <article_id2> ...")
            return
        
        # Validate article IDs format
        article_ids = " ".join(ctx.args).split()
        valid_ids, invalid_ids = validate_article_ids(article_ids)
        
        if invalid_ids:
            error_msg = f"❌ Invalid article IDs (numbers only): {', '.join(invalid_ids)}"
            if valid_ids:
                error_msg += f"\n✅ Valid IDs will be processed: {', '.join(valid_ids)}"
            await update.message.reply_text(error_msg)
            return
        
        if not valid_ids:
            await update.message.reply_text("❌ No valid article IDs provided.")
            return
        
        # Check which articles are already tracked
        current_articules = self.storage.load_articules_for(user_id)
        new_articules = [aid for aid in valid_ids if aid not in current_articules]
        
        if not new_articules:
            await update.message.reply_text("ℹ️ All articles are already tracked.")
            return
        
        # Validate article existence on Wildberries
        await update.message.reply_text("🔍 Validating articles... This may take a moment.")
        
        existing_articles = []
        non_existing_articles = []
        
        # Check each article for existence
        for articule in new_articules:
            try:
                # Use the new existence check method
                if await self.price_monitor.scraper.check_product_exists(articule):
                    existing_articles.append(articule)
                else:
                    non_existing_articles.append(articule)

            except ValidationError as e:
                error_msg = self.error_handler.handle_bot_error(e, user_id)
                await update.message.reply_text(error_msg)
                non_existing_articles.append(articule)                    
            except Exception as e:
                logger.error(f"Error validating article {articule}: {e}")
                non_existing_articles.append(articule)
            
            # Rate limiting between checks
            await asyncio.sleep(1)
        
        # Report results
        messages = []
        
        if existing_articles:
            # Add existing articles to tracking
            all_articules = current_articules + existing_articles
            self.storage.save_articules_for(user_id, all_articules)
            messages.append(f"✅ Added {len(existing_articles)} article(s): {', '.join(existing_articles)}")
        
        if non_existing_articles:
            messages.append(f"❌ Articles not found: {', '.join(non_existing_articles)}")
        
        # Send results
        if messages:
            await update.message.reply_text("\n".join(messages))
        else:
            await update.message.reply_text("ℹ️ No valid articles to add.")
    
    # async def add_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    #     """Handle /add command"""
    #     user_id = update.effective_user.id
        
    #     if not ctx.args:
    #         await update.message.reply_text("Usage: /add <article_id1> <article_id2> ...")
    #         return
        
    #     # Validate article IDs
    #     article_ids = " ".join(ctx.args).split()
    #     valid_ids, invalid_ids = validate_article_ids(article_ids)
        
    #     if invalid_ids:
    #         error_msg = f"❌ Invalid article IDs (numbers only): {', '.join(invalid_ids)}"
    #         if valid_ids:
    #             error_msg += f"\n✅ Valid IDs will be processed: {', '.join(valid_ids)}"
    #         await update.message.reply_text(error_msg)
    #         return
        
    #     if not valid_ids:
    #         await update.message.reply_text("❌ No valid article IDs provided.")
    #         return
        
    #     # Add articles
    #     current_articules = self.storage.load_articules_for(user_id)
    #     new_articules = [aid for aid in valid_ids if aid not in current_articules]
        
    #     if not new_articules:
    #         await update.message.reply_text("ℹ️ All articles are already tracked.")
    #         return
        
    #     # Save new articules
    #     all_articules = current_articules + new_articules
    #     self.storage.save_articules_for(user_id, all_articules)
        
    #     await update.message.reply_text(
    #         f"✅ Added {len(new_articules)} article(s): {', '.join(new_articules)}"
    #     )
    
    async def show_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /show command - exact match to your working version"""
        #user_id = update.effective_user.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)
        results = self.storage.load_results_for(user_id)
        
        if not results:
            await update.message.reply_text("❗ No products tracked yet.")
            return
        
        lines = [
            f"📦 <b>{item['articule']}</b>: {item['product_name']}"
            for item in results
        ]
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    
    async def check_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /check command"""
        #user_id = update.effective_user.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)
        await update.message.reply_text(" Checking prices... This may take a moment.")
        
        try:
            messages = await self.price_monitor.check_prices_for_user(user_id)
            
            if len(messages) > 1:
                # Send messages in chunks to avoid length limits
                for i in range(0, len(messages), 5):
                    chunk = messages[i:i+5]
                    await update.message.reply_text("\n".join(chunk), parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(messages[0], parse_mode=ParseMode.HTML)
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error during price check: {str(e)}")
    
    async def compare_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /compare command"""
        #user_id = update.effective_user.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)
        await update.message.reply_text("🔄 Comparing prices... This may take a moment.")
        
        try:
            messages = await self.price_monitor.check_prices_for_user(user_id)
            
            if len(messages) > 1:
                # Send messages in chunks to avoid length limits
                for i in range(0, len(messages), 5):
                    chunk = messages[i:i+5]
                    await update.message.reply_text("\n".join(chunk), parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(messages[0], parse_mode=ParseMode.HTML)
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error during comparison: {str(e)}")
    
    async def remove_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /remove command - exact match to your working version"""
        #user_id = update.effective_user.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)
        raw = " ".join(ctx.args).strip()
        
        if not raw:
            await update.message.reply_text("Usage: /remove <art1,art2 …>\n⚠️ Only numeric article IDs are allowed.")
            return
        
        parts = re.split(r"[,\s;]+", raw)
        to_remove_raw = {p.strip() for p in parts if p.strip()}
        
        # Validate that all IDs are numeric
        invalid_ids = []
        valid_ids = []
        
        for art_id in to_remove_raw:
            if art_id.isdigit():
                valid_ids.append(art_id)
            else:
                invalid_ids.append(art_id)
        
        # Report invalid IDs
        if invalid_ids:
            error_msg = f"❌ Invalid article IDs (must be numbers only): {', '.join(invalid_ids)}"
            if valid_ids:
                error_msg += f"\n✅ Valid IDs will still be processed: {', '.join(valid_ids)}"
            await update.message.reply_text(error_msg)
            return
        
        # Process valid IDs
        if not valid_ids:
            await update.message.reply_text("❌ No valid numeric article IDs provided.")
            return
        
        to_remove = set(valid_ids)
        
        existing = self.storage.load_articules_for(user_id)
        if not existing:
            await update.message.reply_text("❗ No articules to remove.")
            return
        
        kept, removed = [], []
        for art in existing:
            if art in to_remove:
                removed.append(art)
            else:
                kept.append(art)
        
        if not removed:
            await update.message.reply_text(
                f"ℹ️ None of {', '.join(to_remove)} found in your tracking list."
            )
            return
        
        # Save updated articules
        self.storage.save_articules_for(user_id, kept)
        
        # Also remove from results
        results = self.storage.load_results_for(user_id)
        results = [item for item in results if item["articule"] not in to_remove]
        self.storage.save_results_for(user_id, results)
        
        await update.message.reply_text(
            f"✅ Removed {len(removed)} articule(s): {', '.join(removed)}"
        )    
    async def subscribe_command(self, update, ctx):
        #user_id = update.effective_user.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)
        subs = self.subscription_service.load_subscribers()
        
        if user_id in subs:
            return await update.message.reply_text("✅ Already subscribed.")
        
        subs.add(user_id)
        self.subscription_service.save_subscribers(subs)
        
        intervals = self.subscription_service.load_intervals()
        #interval = intervals.get(str(user_id), 300)
        interval = intervals.get(str(user_id), settings.bot.default_interval)
        self.subscription_service.schedule_compare_for(user_id, ctx.job_queue, interval, self.broadcast_one_user)
        
        await update.message.reply_text(f"🟢 Subscribed! You'll get updates every {interval//60} min.")
    
    async def unsubscribe_command(self, update, ctx):
        """Handle /unsubscribe command"""
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)
        
        # Load current subscribers
        subs = self.subscription_service.load_subscribers()
        
        if user_id not in subs:
            return await update.message.reply_text("ℹ️ You're not subscribed.")
        
        # Remove user from subscribers list (file-based)
        subs.remove(user_id)
        self.subscription_service.save_subscribers(subs)
        
        # 🔑 FIX: Update database subscription status
        self.db_manager.remove_subscription(user_id)  # ← This sets is_active = False
        
        # Remove scheduled job
        for job in ctx.job_queue.get_jobs_by_name(f"compare_{user_id}"):
            job.schedule_removal()
        
        await update.message.reply_text("🔴 Unsubscribed from periodic updates.")
    
    async def setinterval_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        #user_id = update.effective_user.id
        user_id = update.effective_user.id
        username = update.effective_user.username
        user = self.db_manager.get_or_create_user(user_id, username)

        try:
            if not ctx.args:
                return await update.message.reply_text("Usage: /setinterval <minutes>")
            
            try:
                minutes = int(ctx.args[0])
                if minutes <= 0:
                    raise ValueError()
            except ValueError:
                return await update.message.reply_text("Please provide a positive integer for minutes.")
            
            user_id = update.effective_user.id
            
            intervals = self.subscription_service.load_intervals()
            intervals[str(user_id)] = minutes * 60
            self.subscription_service.save_intervals(intervals)
            
            subs = self.subscription_service.load_subscribers()
            if user_id in subs:
                self.subscription_service.schedule_compare_for(user_id, ctx.job_queue, minutes * 60, self.broadcast_one_user)
                await update.message.reply_text(f"⏰ Interval updated to {minutes} min. Updates will continue.")
            else:
                await update.message.reply_text(f"⏰ Interval set to {minutes} min. Use /subscribe to start receiving updates.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            await update.message.reply_text(f"❌ Failed to set interval: {e}")
    
    async def broadcast_one_user(self, context: ContextTypes.DEFAULT_TYPE):
        user_id = context.job.chat_id
        messages = await self.price_monitor.check_prices_for_user(user_id)
        
        if messages:
            await context.bot.send_message(
                chat_id=user_id,
                text="\n".join(messages),
                parse_mode=ParseMode.HTML
            )

    # Add to your existing CommandHandlers class

    async def cache_command(self, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        """Handle /cache command - show cache statistics and management"""
        
        async def show_cache_stats():
            """Helper function to show cache statistics"""
            try:
                stats = await self.price_monitor.get_cache_stats()
                
                stats_text = (
                    f"📊 <b>Cache Statistics</b>\n\n"
                    f"🔄 Memory cache: {stats['memory_cache_size']} items\n"
                    f" Disk cache: {stats['disk_cache_files']} files\n"
                    f"✅ Cache hits: {stats['hits']}\n"
                    f"❌ Cache misses: {stats['misses']}\n"
                    f" Hit rate: {stats['hit_rate_percent']}%\n"
                    f"️ Evictions: {stats['evictions']}\n"
                    f"📊 Total requests: {stats['total_requests']}\n\n"
                    f"Commands:\n"
                    f"• /cache clear - Clear all cache"
                )
                
                await update.message.reply_text(stats_text, parse_mode=ParseMode.HTML)
            except Exception as e:
                await update.message.reply_text(f"❌ Error getting cache stats: {str(e)}")
        
        # Handle different commands
        if not ctx.args:
            # Show cache stats
            await show_cache_stats()
            return
        
        if ctx.args[0] == "clear":
            # Clear cache
            try:
                await self.price_monitor.clear_cache()
                await update.message.reply_text("🗑️ Cache cleared successfully!")
            except Exception as e:
                await update.message.reply_text(f"❌ Error clearing cache: {str(e)}")
            return
        
        # Invalid command
        await update.message.reply_text(
            "Usage: /cache [clear]\n"
            "• /cache - Show cache statistics\n"
            "• /cache clear - Clear all cache"
        )

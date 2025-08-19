import logging
from typing import Dict, Set
from telegram.ext import JobQueue
from ..services.price_monitor import PriceMonitor
from ..storage.database_manager import DatabaseManager
from ..config.settings import settings

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, job_queue: JobQueue, price_monitor: PriceMonitor, db_manager: DatabaseManager):
        self.job_queue = job_queue
        self.price_monitor = price_monitor
        self.db_manager = db_manager
    
    async def restore_jobs(self):
        """Restore scheduled jobs for existing subscribers from database"""
        try:
            # Load active subscriptions from database
            active_subscriptions = self.db_manager.get_active_subscriptions()
            
            for subscription in active_subscriptions:
                user_id = subscription.user_id
                interval = subscription.interval_seconds
                
                self.schedule_compare_for(user_id, interval)
                logger.info(f"Restored job for user {user_id} with interval {interval}s")
                
        except Exception as e:
            logger.error(f"Error restoring jobs: {e}")
    
    def schedule_compare_for(self, user_id: int, interval: int):
        """Schedule price comparison job for a user"""
        job_name = f"compare_{user_id}"
        
        # Remove existing job if any
        for job in self.job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
        
        # Add new job
        self.job_queue.run_repeating(
            self.broadcast_one_user,
            interval=interval,
            first=interval,
            name=job_name,
            chat_id=user_id
        )
        logger.info(f"Scheduled job for user {user_id} with interval {interval}s")
    
    async def broadcast_one_user(self, context):
        """Broadcast price updates to a user"""
        user_id = context.job.chat_id
        logger.info(f"Starting scheduled comparison for user {user_id}")
        
        try:
            messages = await self.price_monitor.check_prices_for_user(user_id, is_manual_check=False)
            
            # Filter for price changes only
            price_change_messages = []
            for message in messages:
                if " " in message and "→" in message:
                    price_change_messages.append(message)
            
            if price_change_messages:
                # Send price change notifications
                for msg in price_change_messages:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=msg,
                        parse_mode='HTML'
                    )
                logger.info(f"User {user_id}: Sent {len(price_change_messages)} price change notifications")
            else:
                # Send "no changes" message
                await context.bot.send_message(
                    chat_id=user_id,
                    text="ℹ️ No price changes detected.",
                    parse_mode='HTML'
                )
                logger.info(f"User {user_id}: Sent no changes notification")
                
        except Exception as e:
            logger.error(f"User {user_id}: Error in broadcast: {e}")
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Error during price check: {str(e)[:100]}"
                )
            except:
                pass

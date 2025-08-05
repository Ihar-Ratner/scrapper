import logging
from typing import Dict, Set
from telegram.ext import JobQueue
from ..services.price_monitor import PriceMonitor
from ..storage.file_storage import FileStorage
from ..config.settings import settings

logger = logging.getLogger(__name__)

class Scheduler:
    def __init__(self, job_queue: JobQueue, price_monitor: PriceMonitor, storage: FileStorage):
        self.job_queue = job_queue
        self.price_monitor = price_monitor
        self.storage = storage
    
    async def restore_jobs(self):
        """Restore scheduled jobs for existing subscribers"""
        try:
            # Load subscribers and intervals
            subs = self.load_subscribers()
            intervals = self.load_intervals()
            
            for user_id in subs:
                #interval = intervals.get(str(user_id), 300)  # Default 5 
                interval = intervals.get(str(user_id), settings.bot.default_interval)
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
            messages = await self.price_monitor.check_prices_for_user(user_id)
            
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
    
    def load_subscribers(self) -> Set[int]:
        """Load list of subscribed users"""
        try:
            subs_file = Path("subscribers.txt")
            if not subs_file.exists():
                return set()
            
            with open(subs_file, "r") as f:
                return {int(line.strip()) for line in f if line.strip()}
        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
            return set()
    
    def save_subscribers(self, subs: Set[int]) -> None:
        """Save list of subscribed users"""
        try:
            with open("subscribers.txt", "w") as f:
                for user_id in subs:
                    f.write(f"{user_id}\n")
        except Exception as e:
            logger.error(f"Error saving subscribers: {e}")
    
    def load_intervals(self) -> Dict[str, int]:
        """Load user intervals"""
        try:
            intervals_file = Path("intervals.json")
            if not intervals_file.exists():
                return {}
            
            import json
            with open(intervals_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading intervals: {e}")
            return {}
    
    def save_intervals(self, intervals: Dict[str, int]) -> None:
        """Save user intervals"""
        try:
            import json
            with open("intervals.json", "w") as f:
                json.dump(intervals, f)
        except Exception as e:
            logger.error(f"Error saving intervals: {e}")

from pathlib import Path

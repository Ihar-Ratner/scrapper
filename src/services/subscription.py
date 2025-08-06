import json
import logging
from pathlib import Path
from typing import Set, Dict
from telegram.ext import JobQueue
from ..storage.database_manager import DatabaseManager

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def save_subscribers(self, subs: Set[int]) -> None:
        """Save subscribers to database"""
        try:
            for user_id in subs:
                self.db_manager.save_subscription(user_id)
        except Exception as e:
            logger.error(f"Error saving subscribers: {e}")
    
    def load_subscribers(self) -> Set[int]:
        """Load subscribers from database"""
        try:
            active_subscriptions = self.db_manager.get_active_subscriptions()
            return {sub.user_id for sub in active_subscriptions}
        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
            return set()
    
    def save_intervals(self, intervals: Dict[str, int]) -> None:
        """Save intervals to database"""
        try:
            for user_id_str, interval_seconds in intervals.items():
                user_id = int(user_id_str)
                self.db_manager.save_subscription(user_id, interval_seconds)
        except Exception as e:
            logger.error(f"Error saving intervals: {e}")
    
    def load_intervals(self) -> Dict[str, int]:
        """Load intervals from database"""
        try:
            active_subscriptions = self.db_manager.get_active_subscriptions()
            return {str(sub.user_id): sub.interval_seconds for sub in active_subscriptions}
        except Exception as e:
            logger.error(f"Error loading intervals: {e}")
            return {}
    
    def schedule_compare_for(self, user_id: int, job_queue: JobQueue, interval: int, callback):
        """Schedule comparison job and save to database"""
        try:
            # Save subscription to database
            self.db_manager.save_subscription(user_id, interval)
            
            # Schedule job
            job_name = f"compare_{user_id}"
            
            # Remove existing job if any
            for job in job_queue.get_jobs_by_name(job_name):
                job.schedule_removal()
            
            # Add new job
            job_queue.run_repeating(
                callback,
                interval=interval,
                first=interval,
                name=job_name,
                chat_id=user_id
            )
            logger.info(f"Scheduled job for user {user_id} with interval {interval}s")
            
        except Exception as e:
            logger.error(f"Error scheduling job for user {user_id}: {e}")

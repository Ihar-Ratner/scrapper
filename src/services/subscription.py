import json
import logging
from pathlib import Path
from typing import Set, Dict
from telegram.ext import JobQueue

logger = logging.getLogger(__name__)

class SubscriptionService:
    def __init__(self, data_root: Path = None):
        self.data_root = data_root or Path(".")
        self.subscribers_file = self.data_root / "subscribers.txt"
        self.intervals_file = self.data_root / "intervals.json"
    
    def load_subscribers(self) -> Set[int]:
        if not self.subscribers_file.exists():
            return set()
        try:
            return {int(u) for u in self.subscribers_file.read_text().splitlines() if u}
        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
            return set()
    
    def save_subscribers(self, subs: Set[int]) -> None:
        try:
            self.subscribers_file.write_text("\n".join(str(u) for u in subs) + "\n")
        except Exception as e:
            logger.error(f"Error saving subscribers: {e}")
    
    def load_intervals(self) -> Dict[str, int]:
        if not self.intervals_file.exists():
            return {}
        try:
            return json.loads(self.intervals_file.read_text())
        except Exception as e:
            logger.error(f"Error loading intervals: {e}")
            return {}
    
    def save_intervals(self, intervals: Dict[str, int]) -> None:
        try:
            self.intervals_file.write_text(json.dumps(intervals, indent=2))
        except Exception as e:
            logger.error(f"Error saving intervals: {e}")
    
    def schedule_compare_for(self, user_id: int, job_queue: JobQueue, interval: int, callback):
        job_name = f"compare_{user_id}"
        
        for job in job_queue.get_jobs_by_name(job_name):
            job.schedule_removal()
        
        job_queue.run_repeating(
            callback=callback,
            interval=interval,
            first=interval,
            chat_id=user_id,
            name=job_name
        )
        logger.info(f"Scheduled job for user {user_id} with interval {interval}s")

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class User:
    user_id: int
    articules: List[str]
    is_subscribed: bool = False
    interval_minutes: int = 5
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

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

@dataclass
class Product:
    articule: str
    product_name: str
    final_price: str
    last_execution: datetime
    
    @property
    def price_float(self) -> float:
        """Extract numeric price from string"""
        import re
        price_match = re.search(r'[\d\s]+[,.]?\d{0,2}', self.final_price)
        if price_match:
            price_str = price_match.group().replace(' ', '').replace(',', '.')
            return float(price_str)
        return 0.0

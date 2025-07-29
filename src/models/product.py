from dataclasses import dataclass
from datetime import datetime
import re

@dataclass
class Product:
    articule: str
    product_name: str
    final_price: str
    last_execution: datetime
    
    @property
    def price_float(self) -> float:
        """Extract numeric price from string - using your working parse_price logic"""
        try:
            m = re.search(r"[\d\s]+,\d{2}", self.final_price)
            if m:
                return float(m.group().replace(" ", "").replace(",", "."))
            else:
                # Fallback: try to extract any number
                numbers = re.findall(r'[\d\s,]+', self.final_price)
                if numbers:
                    clean_number = numbers[0].replace(" ", "").replace(",", ".")
                    return float(clean_number)
                return 0.0
        except Exception as e:
            return 0.0
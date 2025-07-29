import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass
class Settings:
    # Telegram settings
    telegram_token: str
    
    # Browser settings
    max_browsers: int = 3
    headless: bool = True
    
    # Scraping settings
    scrape_timeout: int = 45
    retry_attempts: int = 3
    rate_limit_delay: float = 2.0
    
    # Storage settings
    data_root: Path = Path("data")
    
    # Logging settings
    log_level: str = "INFO"
    log_file: Path = Path("logs/bot.log")
    
    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            telegram_token=os.getenv("TELEGRAM_TOKEN", ""),
            max_browsers=int(os.getenv("MAX_BROWSERS", "3")),
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            scrape_timeout=int(os.getenv("SCRAPE_TIMEOUT", "45")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "2.0")),
            data_root=Path(os.getenv("DATA_ROOT", "data")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=Path(os.getenv("LOG_FILE", "logs/bot.log"))
        )

# Global settings instance
settings = Settings.from_env() 

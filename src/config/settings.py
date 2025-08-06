import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass
class CacheConfig:
    """Cache configuration settings"""
    memory_cache_size: int = 500
    cache_ttl_minutes: int = 15
    disk_cache_enabled: bool = True
    cache_dir: str = "cache"
    cleanup_interval_minutes: int = 5

@dataclass
class ScrapingConfig:
    """Scraping configuration settings"""
    max_concurrent_requests: int = 3
    request_timeout: int = 30
    retry_attempts: int = 3
    rate_limit_delay: float = 2.0

@dataclass
class BotConfig:
    """Bot configuration settings"""
    max_message_length: int = 4096
    message_batch_size: int = 5
    default_interval: int = 300

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    host: str = "localhost"
    port: int = 5432
    database: str = "wildberries_bot"
    username: str = "bot_user"
    password: str = "your_secure_password"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30

@dataclass
class Settings:
    # Core settings
    telegram_token: str
    max_browsers: int = 3
    headless: bool = True
    scrape_timeout: int = 45
    retry_attempts: int = 3
    rate_limit_delay: float = 2.0
    data_root: Path = Path("data")
    log_level: str = "INFO"
    log_file: Path = Path("logs/bot.log")
    debug: bool = False
    
    # Feature settings
    default_interval: int = 300  # 5 minutes
    max_products_per_user: int = 50
    message_chunk_size: int = 5
    enable_metrics: bool = False
    
    # Configuration objects
    cache: CacheConfig = CacheConfig()
    scraping: ScrapingConfig = ScrapingConfig()
    bot: BotConfig = BotConfig()
    database: DatabaseConfig = DatabaseConfig()
    
    @property
    def database_url(self) -> str:
        """Get database URL"""
        return f"postgresql://{self.database.username}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.database}"
    
    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            # Core settings
            telegram_token=os.getenv("TELEGRAM_TOKEN", ""),
            max_browsers=int(os.getenv("MAX_BROWSERS", "3")),
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            scrape_timeout=int(os.getenv("SCRAPE_TIMEOUT", "45")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "2.0")),
            data_root=Path(os.getenv("DATA_ROOT", "data")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=Path(os.getenv("LOG_FILE", "logs/bot.log")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            default_interval=int(os.getenv("DEFAULT_INTERVAL", "300")),
            max_products_per_user=int(os.getenv("MAX_PRODUCTS_PER_USER", "50")),
            message_chunk_size=int(os.getenv("MESSAGE_CHUNK_SIZE", "5")),
            enable_metrics=os.getenv("ENABLE_METRICS", "false").lower() == "true",
            
            # Cache configuration
            cache=CacheConfig(
                memory_cache_size=int(os.getenv("CACHE_MEMORY_SIZE", "500")),
                cache_ttl_minutes=int(os.getenv("CACHE_TTL_MINUTES", "15")),
                disk_cache_enabled=os.getenv("CACHE_DISK_ENABLED", "true").lower() == "true",
                cache_dir=os.getenv("CACHE_DIR", "cache"),
                cleanup_interval_minutes=int(os.getenv("CACHE_CLEANUP_INTERVAL", "5"))
            ),
            
            # Scraping configuration
            scraping=ScrapingConfig(
                max_concurrent_requests=int(os.getenv("SCRAPING_MAX_CONCURRENT", "3")),
                request_timeout=int(os.getenv("SCRAPING_TIMEOUT", "30")),
                retry_attempts=int(os.getenv("SCRAPING_RETRY_ATTEMPTS", "3")),
                rate_limit_delay=float(os.getenv("SCRAPING_RATE_LIMIT_DELAY", "2.0"))
            ),
            
            # Bot configuration
            bot=BotConfig(
                max_message_length=int(os.getenv("BOT_MAX_MESSAGE_LENGTH", "4096")),
                message_batch_size=int(os.getenv("BOT_MESSAGE_BATCH_SIZE", "5")),
                default_interval=int(os.getenv("BOT_DEFAULT_INTERVAL", "300"))
            ),
            
            # Database configuration
            database=DatabaseConfig(
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", "wildberries_bot"),
                username=os.getenv("DB_USER", "bot_user"),
                password=os.getenv("DB_PASSWORD", "test_password"),
                pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
                pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30"))
            )
        )

# Global settings instance
settings = Settings.from_env()

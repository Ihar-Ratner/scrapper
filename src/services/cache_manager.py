import asyncio
import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from ..models.product import Product

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Represents a cached product entry"""
    articule: str
    product_name: str
    final_price: str
    cached_at: datetime
    expires_at: datetime
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "articule": self.articule,
            "product_name": self.product_name,
            "final_price": self.final_price,
            "cached_at": self.cached_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        return cls(
            articule=data["articule"],
            product_name=data["product_name"],
            final_price=data["final_price"],
            cached_at=datetime.fromisoformat(data["cached_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"])
        )

class CacheManager:
    """Multi-level caching system for product data"""
    
    def __init__(self, 
                 memory_cache_size: int = 1000,
                 cache_ttl_minutes: int = 10,
                 disk_cache_enabled: bool = True,
                 cache_dir: str = "cache"):
        
        # Memory cache (fastest)
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._memory_cache_size = memory_cache_size
        
        # Disk cache (persistent)
        self._disk_cache_enabled = disk_cache_enabled
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(exist_ok=True)
        
        # Cache settings
        self._cache_ttl = timedelta(minutes=cache_ttl_minutes)
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(f"Cache initialized: memory_size={memory_cache_size}, ttl={cache_ttl_minutes}min")
    
    async def get_product(self, articule: str) -> Optional[Product]:
        """Get product from cache, returns None if not found or expired"""
        try:
            # Try memory cache first
            if articule in self._memory_cache:
                entry = self._memory_cache[articule]
                if not entry.is_expired():
                    self._hits += 1
                    logger.debug(f"Memory cache HIT for {articule}")
                    return self._entry_to_product(entry)
                else:
                    # Remove expired entry
                    del self._memory_cache[articule]
            
            # Try disk cache
            if self._disk_cache_enabled:
                entry = await self._load_from_disk(articule)
                if entry and not entry.is_expired():
                    # Add to memory cache
                    self._add_to_memory_cache(articule, entry)
                    self._hits += 1
                    logger.debug(f"Disk cache HIT for {articule}")
                    return self._entry_to_product(entry)
            
            self._misses += 1
            logger.debug(f"Cache MISS for {articule}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting product from cache for {articule}: {e}")
            return None
    
    async def cache_product(self, product: Product) -> None:
        """Cache a product with current timestamp"""
        try:
            entry = CacheEntry(
                articule=product.articule,
                product_name=product.product_name,
                final_price=product.final_price,
                cached_at=datetime.now(),
                expires_at=datetime.now() + self._cache_ttl
            )
            
            # Add to memory cache
            self._add_to_memory_cache(product.articule, entry)
            
            # Add to disk cache
            if self._disk_cache_enabled:
                await self._save_to_disk(product.articule, entry)
            
            logger.debug(f"Cached product {product.articule}")
            
        except Exception as e:
            logger.error(f"Error caching product {product.articule}: {e}")
    
    def _add_to_memory_cache(self, articule: str, entry: CacheEntry) -> None:
        """Add entry to memory cache with LRU eviction"""
        if len(self._memory_cache) >= self._memory_cache_size:
            # Remove oldest entry (simple FIFO for now)
            oldest_key = next(iter(self._memory_cache))
            del self._memory_cache[oldest_key]
            self._evictions += 1
        
        self._memory_cache[articule] = entry
    
    async def _save_to_disk(self, articule: str, entry: CacheEntry) -> None:
        """Save cache entry to disk"""
        try:
            cache_file = self._cache_dir / f"{articule}.json"
            cache_file.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Error saving to disk cache for {articule}: {e}")
    
    async def _load_from_disk(self, articule: str) -> Optional[CacheEntry]:
        """Load cache entry from disk"""
        try:
            cache_file = self._cache_dir / f"{articule}.json"
            if cache_file.exists():
                data = json.loads(cache_file.read_text(encoding="utf-8"))
                return CacheEntry.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading from disk cache for {articule}: {e}")
        return None
    
    def _entry_to_product(self, entry: CacheEntry) -> Product:
        """Convert cache entry to Product object"""
        return Product(
            articule=entry.articule,
            product_name=entry.product_name,
            final_price=entry.final_price,
            last_execution=entry.cached_at
        )
    
    async def clear_expired(self) -> int:
        """Clear expired entries from both memory and disk cache"""
        cleared_count = 0
        
        # Clear expired from memory
        expired_keys = [
            key for key, entry in self._memory_cache.items() 
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._memory_cache[key]
            cleared_count += 1
        
        # Clear expired from disk
        if self._disk_cache_enabled:
            for cache_file in self._cache_dir.glob("*.json"):
                try:
                    data = json.loads(cache_file.read_text(encoding="utf-8"))
                    entry = CacheEntry.from_dict(data)
                    if entry.is_expired():
                        cache_file.unlink()
                        cleared_count += 1
                except Exception as e:
                    logger.error(f"Error processing cache file {cache_file}: {e}")
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} expired cache entries")
        
        return cleared_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "memory_cache_size": len(self._memory_cache),
            "disk_cache_files": len(list(self._cache_dir.glob("*.json"))) if self._disk_cache_enabled else 0,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate_percent": round(hit_rate, 2),
            "evictions": self._evictions,
            "total_requests": total_requests
        }
    
    async def clear_all(self) -> None:
        """Clear all cache entries"""
        self._memory_cache.clear()
        
        if self._disk_cache_enabled:
            for cache_file in self._cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting cache file {cache_file}: {e}")
        
        logger.info("All cache entries cleared") 
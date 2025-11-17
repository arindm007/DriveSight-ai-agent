"""
Simple in-memory cache manager with TTL support
"""
import hashlib
import time
from typing import Optional, Dict, Any
from .logger import setup_logger
from .config import Config

logger = setup_logger(__name__)

class CacheManager:
    """In-memory cache with TTL support"""
    
    def __init__(self, ttl: int = Config.CACHE_TTL):
        """Initialize cache"""
        self.ttl = ttl
        self._cache: Dict[str, tuple] = {}  # {key: (value, timestamp)}
    
    def _hash_image(self, image_data: bytes) -> str:
        """Generate hash of image data"""
        return hashlib.sha256(image_data).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if not expired
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        
        # Check if expired
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            logger.debug(f"Cache entry expired: {key}")
            return None
        
        logger.debug(f"Cache hit: {key}")
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = (value, time.time())
        logger.debug(f"Cache set: {key}")
    
    def get_by_image_hash(self, image_data: bytes) -> Optional[Any]:
        """
        Get cached result by image hash
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Cached analysis result or None
        """
        key = self._hash_image(image_data)
        return self.get(key)
    
    def set_by_image_hash(self, image_data: bytes, result: Any) -> None:
        """
        Cache analysis result by image hash
        
        Args:
            image_data: Raw image bytes
            result: Analysis result to cache
        """
        key = self._hash_image(image_data)
        self.set(key, result)
    
    def clear(self) -> None:
        """Clear all cache"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def clear_expired(self) -> None:
        """Remove all expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")


# Singleton instance
_cache = CacheManager()

def get_cache() -> CacheManager:
    """Get cache singleton"""
    return _cache

"""
Cache Service Interface - OHT-50 Backend
Abstract interface for caching services (Memory, Redis, etc.)
"""

from abc import abstractmethod
from typing import Any, Optional, Dict
from .base_service import IBaseService


class ICacheService(IBaseService):
    """
    Interface for caching services
    
    Defines contract for all caching implementations including
    memory cache, Redis cache, and multi-level caching strategies.
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists, None otherwise
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None = no expiration)
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            bool: True if deleted, False if key not found
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all cache entries
        
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear cache entries matching pattern
        
        Args:
            pattern: Key pattern (e.g., "robot:*")
            
        Returns:
            int: Number of keys deleted
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict with cache statistics:
            {
                "hits": int,
                "misses": int,
                "hit_rate": float,
                "size": int,
                "max_size": int
            }
        """
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment counter in cache
        
        Args:
            key: Counter key
            amount: Increment amount
            
        Returns:
            int: New counter value
        """
        pass
    
    @abstractmethod
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for existing key
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass

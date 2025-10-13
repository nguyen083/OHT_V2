"""
Redis Cache Service Implementation - OHT-50 Backend
Production-ready Redis caching with fallback support
"""

import json
import logging
from typing import Any, Optional, Dict
import redis.asyncio as redis

from app.domain.interfaces.cache_service import ICacheService

logger = logging.getLogger(__name__)


class RedisCacheService(ICacheService):
    """
    Redis-based cache implementation
    
    Provides distributed caching with automatic expiration,
    connection pooling, and error handling.
    """
    
    def __init__(self, redis_url: str = None, redis_host: str = "localhost", redis_port: int = 6379):
        """
        Initialize Redis cache service
        
        Args:
            redis_url: Redis connection URL
            redis_host: Redis host
            redis_port: Redis port
        """
        self.redis_url = redis_url or f"redis://{redis_host}:{redis_port}"
        self.redis_host = redis_host
        self.redis_port = redis_port
        self.client: Optional[redis.Redis] = None
        self._initialized = False
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
        
        logger.info(f"RedisCacheService created for {self.redis_url}")
    
    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        try:
            self.client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.client.ping()
            self._initialized = True
            logger.info("✅ Redis cache service initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis initialization failed: {e}")
            self._initialized = False
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown Redis connection"""
        try:
            if self.client:
                await self.client.close()
                logger.info("✅ Redis cache service shutdown")
            return True
        except Exception as e:
            logger.error(f"❌ Redis shutdown failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis health"""
        try:
            if not self.client:
                return {
                    "healthy": False,
                    "status": "unhealthy",
                    "details": {"error": "Client not initialized"}
                }
            
            # Ping Redis
            await self.client.ping()
            
            # Get info
            info = await self.client.info()
            
            return {
                "healthy": True,
                "status": "healthy",
                "details": {
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "stats": self.stats
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Redis health check failed: {e}")
            return {
                "healthy": False,
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service_name": "RedisCacheService",
            "version": "1.0.0",
            "state": "running" if self._initialized else "stopped",
            "uptime": 0,  # TODO: Track uptime
            "metadata": {
                "redis_url": self.redis_url,
                "stats": self.stats
            }
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if not self.client:
                self.stats["errors"] += 1
                return None
            
            value = await self.client.get(key)
            
            if value:
                self.stats["hits"] += 1
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            else:
                self.stats["misses"] += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ Redis get failed for key {key}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            if not self.client:
                self.stats["errors"] += 1
                return False
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)
            
            # Set with or without TTL
            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis set failed for key {key}: {e}")
            self.stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if not self.client:
                return False
            
            result = await self.client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"❌ Redis delete failed for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if not self.client:
                return False
            
            result = await self.client.exists(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"❌ Redis exists check failed for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            if not self.client:
                return False
            
            await self.client.flushdb()
            logger.warning("⚠️ Redis cache cleared (flushdb)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis clear failed: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear keys matching pattern"""
        try:
            if not self.client:
                return 0
            
            # Scan for keys matching pattern
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            
            # Delete keys
            if keys:
                deleted = await self.client.delete(*keys)
                logger.info(f"🗑️ Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"❌ Redis clear_pattern failed: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter"""
        try:
            if not self.client:
                return 0
            
            result = await self.client.incrby(key, amount)
            return result
            
        except Exception as e:
            logger.error(f"❌ Redis increment failed for key {key}: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        try:
            if not self.client:
                return False
            
            result = await self.client.expire(key, ttl)
            return result
            
        except Exception as e:
            logger.error(f"❌ Redis expire failed for key {key}: {e}")
            return False

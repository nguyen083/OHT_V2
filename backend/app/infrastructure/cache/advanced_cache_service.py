# 🚀 ADVANCED MULTI-LEVEL CACHE SERVICE - Phase 3 Implementation
"""
Advanced caching service with intelligent TTL and multi-level strategy
L1: Memory cache (fastest, limited size)
L2: Redis cache (shared, persistent)
L3: Database cache (slowest, most durable)

Phase 3: Performance optimization with intelligent cache warming and eviction
"""

import asyncio
import json
import time
import logging
from typing import Any, Dict, Optional, List, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import pickle
from collections import OrderedDict

from app.domain.interfaces.cache_service import ICacheService
from app.infrastructure.cache.redis_cache_service import RedisCacheService

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache level enumeration"""
    L1_MEMORY = "L1_MEMORY"
    L2_REDIS = "L2_REDIS"
    L3_DATABASE = "L3_DATABASE"


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l3_hits: int = 0
    l3_misses: int = 0
    evictions: int = 0
    warming_operations: int = 0
    total_operations: int = 0
    avg_response_time_ms: float = 0.0
    cache_size_bytes: int = 0
    
    def get_l1_hit_ratio(self) -> float:
        total = self.l1_hits + self.l1_misses
        return (self.l1_hits / total * 100) if total > 0 else 0.0
    
    def get_l2_hit_ratio(self) -> float:
        total = self.l2_hits + self.l2_misses
        return (self.l2_hits / total * 100) if total > 0 else 0.0
    
    def get_overall_hit_ratio(self) -> float:
        total_hits = self.l1_hits + self.l2_hits + self.l3_hits
        total_operations = self.total_operations
        return (total_hits / total_operations * 100) if total_operations > 0 else 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    ttl: int
    created_at: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl <= 0:  # Never expires
            return False
        return time.time() - self.created_at > self.ttl
    
    def update_access(self):
        """Update access metadata"""
        self.last_accessed = time.time()
        self.access_count += 1


class LRUCache:
    """
    High-performance LRU cache implementation with intelligent eviction
    """
    
    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_memory_bytes = 0
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get item from cache with LRU update"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry.is_expired():
                    del self.cache[key]
                    self.current_memory_bytes -= entry.size_bytes
                    return None
                
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                entry.update_access()
                return entry
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set item in cache with intelligent eviction"""
        async with self._lock:
            # Calculate size
            try:
                size_bytes = len(pickle.dumps(value))
            except (pickle.PicklingError, TypeError):
                size_bytes = len(str(value).encode('utf-8'))
            
            # Check if single item is too large
            if size_bytes > self.max_memory_bytes * 0.5:  # 50% of max memory
                logger.warning(f"Cache item too large: {size_bytes} bytes, skipping")
                return False
            
            # Remove existing entry if updating
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_memory_bytes -= old_entry.size_bytes
                del self.cache[key]
            
            # Evict items if necessary
            await self._evict_if_needed(size_bytes)
            
            # Create new entry
            entry = CacheEntry(
                key=key,
                value=value,
                ttl=ttl,
                created_at=time.time(),
                last_accessed=time.time(),
                size_bytes=size_bytes
            )
            
            self.cache[key] = entry
            self.current_memory_bytes += size_bytes
            
            return True
    
    async def delete(self, key: str) -> bool:
        """Delete item from cache"""
        async with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                self.current_memory_bytes -= entry.size_bytes
                del self.cache[key]
                return True
            return False
    
    async def clear(self) -> bool:
        """Clear all cache entries"""
        async with self._lock:
            self.cache.clear()
            self.current_memory_bytes = 0
            return True
    
    async def _evict_if_needed(self, new_item_size: int):
        """Intelligent cache eviction based on size and memory limits"""
        # Evict expired items first
        expired_keys = [
            key for key, entry in list(self.cache.items())
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            entry = self.cache[key]
            self.current_memory_bytes -= entry.size_bytes
            del self.cache[key]
        
        # Evict LRU items if still over limits
        while (len(self.cache) >= self.max_size or 
               self.current_memory_bytes + new_item_size > self.max_memory_bytes):
            
            if not self.cache:
                break
                
            # Remove least recently used item
            key, entry = self.cache.popitem(last=False)
            self.current_memory_bytes -= entry.size_bytes
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "memory_usage_bytes": self.current_memory_bytes,
            "memory_limit_bytes": self.max_memory_bytes,
            "memory_usage_percent": round(
                self.current_memory_bytes / self.max_memory_bytes * 100, 2
            )
        }


class AdvancedCacheService(ICacheService):
    """
    Advanced multi-level cache service with intelligent TTL and warming strategies
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.service_name = "AdvancedCacheService"
        self.initialized = False
        
        # L1 Cache: Memory (fastest)
        self.l1_cache = LRUCache(max_size=10000, max_memory_mb=200)
        
        # L2 Cache: Redis (shared)
        self.l2_cache = RedisCacheService(redis_url)
        
        # Cache configuration
        self.intelligent_ttl_enabled = True
        self.cache_warming_enabled = True
        self.auto_eviction_enabled = True
        
        # Metrics tracking
        self.metrics = CacheMetrics()
        self.operation_times: List[float] = []
        
        # Cache warming strategies
        self.warming_strategies: Dict[str, Callable] = {}
        
        logger.info(f"✅ {self.service_name} initialized with multi-level caching")
    
    async def initialize(self) -> bool:
        """Initialize all cache levels"""
        try:
            # Initialize L2 Redis cache
            redis_success = await self.l2_cache.initialize()
            if not redis_success:
                logger.warning("Redis cache initialization failed, continuing with L1 only")
            
            self.initialized = True
            logger.info(f"✅ {self.service_name} initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ {self.service_name} initialization failed: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown all cache levels"""
        try:
            await self.l2_cache.shutdown()
            await self.l1_cache.clear()
            
            self.initialized = False
            logger.info(f"✅ {self.service_name} shutdown completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ {self.service_name} shutdown failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all cache levels"""
        try:
            # Check L1 cache
            l1_stats = self.l1_cache.get_stats()
            
            # Check L2 cache
            l2_health = await self.l2_cache.health_check()
            
            # Overall health assessment
            l1_healthy = l1_stats["memory_usage_percent"] < 90
            l2_healthy = l2_health.get("status") == "healthy"
            
            overall_status = "healthy" if (l1_healthy and l2_healthy) else "degraded"
            
            return {
                "service": self.service_name,
                "status": overall_status,
                "initialized": self.initialized,
                "l1_cache": {
                    "status": "healthy" if l1_healthy else "degraded",
                    "stats": l1_stats
                },
                "l2_cache": l2_health,
                "metrics": asdict(self.metrics),
                "performance": {
                    "l1_hit_ratio": self.metrics.get_l1_hit_ratio(),
                    "l2_hit_ratio": self.metrics.get_l2_hit_ratio(),
                    "overall_hit_ratio": self.metrics.get_overall_hit_ratio(),
                    "avg_response_time_ms": self.metrics.avg_response_time_ms
                }
            }
            
        except Exception as e:
            return {
                "service": self.service_name,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": self.service_name,
            "initialized": self.initialized,
            "metrics": asdict(self.metrics)
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Multi-level cache get with intelligent promotion
        L1 -> L2 -> L3 -> Miss
        """
        start_time = time.time()
        self.metrics.total_operations += 1
        
        try:
            # Try L1 cache first (fastest)
            l1_entry = await self.l1_cache.get(key)
            if l1_entry is not None:
                self.metrics.l1_hits += 1
                await self._record_operation_time(start_time)
                return l1_entry.value
            
            self.metrics.l1_misses += 1
            
            # Try L2 cache (Redis)
            l2_value = await self.l2_cache.get(key)
            if l2_value is not None:
                self.metrics.l2_hits += 1
                
                # Promote to L1 cache with intelligent TTL
                ttl = await self._calculate_intelligent_ttl(key, l2_value)
                await self.l1_cache.set(key, l2_value, ttl)
                
                await self._record_operation_time(start_time)
                return l2_value
            
            self.metrics.l2_misses += 1
            
            # Cache miss - consider warming if strategy exists
            if self.cache_warming_enabled and key in self.warming_strategies:
                asyncio.create_task(self._warm_cache_key(key))
            
            await self._record_operation_time(start_time)
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            await self._record_operation_time(start_time)
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Multi-level cache set with intelligent distribution
        """
        start_time = time.time()
        self.metrics.total_operations += 1
        
        try:
            # Calculate intelligent TTL if not provided
            if ttl is None:
                ttl = await self._calculate_intelligent_ttl(key, value)
            
            # Set in both L1 and L2 caches
            l1_success = await self.l1_cache.set(key, value, ttl)
            l2_success = await self.l2_cache.set(key, value, ttl)
            
            # Consider success if at least one level succeeds
            success = l1_success or l2_success
            
            if not success:
                logger.warning(f"Failed to set cache key {key} in any level")
            
            await self._record_operation_time(start_time)
            return success
            
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            await self._record_operation_time(start_time)
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete from all cache levels"""
        start_time = time.time()
        self.metrics.total_operations += 1
        
        try:
            l1_deleted = await self.l1_cache.delete(key)
            l2_deleted = await self.l2_cache.delete(key)
            
            await self._record_operation_time(start_time)
            return l1_deleted or l2_deleted
            
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            await self._record_operation_time(start_time)
            return False
    
    async def clear(self) -> bool:
        """Clear all cache levels"""
        start_time = time.time()
        
        try:
            l1_cleared = await self.l1_cache.clear()
            l2_cleared = await self.l2_cache.clear()
            
            # Reset metrics
            self.metrics = CacheMetrics()
            self.operation_times.clear()
            
            await self._record_operation_time(start_time)
            return l1_cleared and l2_cleared
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            await self._record_operation_time(start_time)
            return False
    
    async def _calculate_intelligent_ttl(self, key: str, value: Any) -> int:
        """
        Calculate intelligent TTL based on key patterns and value characteristics
        """
        if not self.intelligent_ttl_enabled:
            return 300  # Default 5 minutes
        
        # TTL strategies based on key patterns
        ttl_strategies = {
            # High-frequency data (short TTL)
            "telemetry": 60,      # 1 minute
            "status": 30,         # 30 seconds
            "heartbeat": 15,      # 15 seconds
            
            # Medium-frequency data (medium TTL)
            "config": 900,        # 15 minutes
            "user": 600,          # 10 minutes
            "session": 1800,      # 30 minutes
            
            # Low-frequency data (long TTL)
            "module": 3600,       # 1 hour
            "map": 7200,          # 2 hours
            "firmware": 10800,    # 3 hours
        }
        
        # Determine TTL based on key prefix
        for pattern, ttl in ttl_strategies.items():
            if key.startswith(pattern):
                return ttl
        
        # Default TTL based on value size
        try:
            value_size = len(str(value))
            if value_size < 1000:  # Small values
                return 300          # 5 minutes
            elif value_size < 10000:  # Medium values
                return 600           # 10 minutes
            else:  # Large values
                return 1800          # 30 minutes
        except:
            return 300  # Default fallback
    
    async def _warm_cache_key(self, key: str):
        """Execute cache warming strategy for a specific key"""
        try:
            if key in self.warming_strategies:
                warming_func = self.warming_strategies[key]
                value = await warming_func(key)
                
                if value is not None:
                    ttl = await self._calculate_intelligent_ttl(key, value)
                    await self.set(key, value, ttl)
                    self.metrics.warming_operations += 1
                    
                    logger.info(f"Cache warming completed for key: {key}")
                    
        except Exception as e:
            logger.error(f"Cache warming failed for key {key}: {e}")
    
    def register_warming_strategy(self, key_pattern: str, warming_func: Callable):
        """Register a cache warming strategy for specific key patterns"""
        self.warming_strategies[key_pattern] = warming_func
        logger.info(f"Registered cache warming strategy for pattern: {key_pattern}")
    
    async def _record_operation_time(self, start_time: float):
        """Record operation timing for performance metrics"""
        operation_time = time.time() - start_time
        self.operation_times.append(operation_time)
        
        # Keep only last 1000 operations for average calculation
        if len(self.operation_times) > 1000:
            self.operation_times = self.operation_times[-1000:]
        
        # Update average response time
        self.metrics.avg_response_time_ms = (
            sum(self.operation_times) / len(self.operation_times) * 1000
        )
    
    def get_advanced_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        l1_stats = self.l1_cache.get_stats()
        
        return {
            "service": self.service_name,
            "metrics": asdict(self.metrics),
            "performance": {
                "l1_hit_ratio": round(self.metrics.get_l1_hit_ratio(), 2),
                "l2_hit_ratio": round(self.metrics.get_l2_hit_ratio(), 2),
                "overall_hit_ratio": round(self.metrics.get_overall_hit_ratio(), 2),
                "avg_response_time_ms": round(self.metrics.avg_response_time_ms, 2),
                "operations_per_second": len(self.operation_times) / max(sum(self.operation_times), 0.001)
            },
            "l1_cache": l1_stats,
            "configuration": {
                "intelligent_ttl_enabled": self.intelligent_ttl_enabled,
                "cache_warming_enabled": self.cache_warming_enabled,
                "auto_eviction_enabled": self.auto_eviction_enabled,
                "warming_strategies_count": len(self.warming_strategies)
            }
        }


# Global service instance
_advanced_cache_service = None

async def get_advanced_cache_service() -> AdvancedCacheService:
    """Get singleton advanced cache service instance"""
    global _advanced_cache_service
    if _advanced_cache_service is None:
        _advanced_cache_service = AdvancedCacheService()
        await _advanced_cache_service.initialize()
    return _advanced_cache_service

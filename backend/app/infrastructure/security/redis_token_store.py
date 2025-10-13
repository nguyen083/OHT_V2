"""
Redis Token Store Implementation - OHT-50 Backend
Scalable token blacklist management using Redis
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.domain.interfaces.token_store import ITokenStore
from app.domain.interfaces.cache_service import ICacheService

logger = logging.getLogger(__name__)


class RedisTokenStore(ITokenStore):
    """
    Redis-based token store implementation
    
    Provides scalable, distributed token blacklist management
    with automatic expiration and audit logging.
    """
    
    def __init__(self, cache_service: ICacheService):
        """
        Initialize token store
        
        Args:
            cache_service: Cache service for token storage
        """
        self.cache = cache_service
        self.prefix_blacklist = "token:blacklist:"
        self.prefix_reset = "token:reset:"
        self._initialized = False
        
        # Audit log
        self.audit_log = []
        
        logger.info("RedisTokenStore initialized")
    
    async def initialize(self) -> bool:
        """Initialize token store"""
        try:
            # Ensure cache is initialized
            if not self.cache._initialized:
                await self.cache.initialize()
            
            self._initialized = True
            logger.info("✅ Token store initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Token store initialization failed: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown token store"""
        try:
            # Cache will be shutdown by container
            self._initialized = False
            logger.info("✅ Token store shutdown")
            return True
        except Exception as e:
            logger.error(f"❌ Token store shutdown failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check token store health"""
        try:
            # Check cache health
            cache_health = await self.cache.health_check()
            
            # Get blacklist count
            count = await self.get_blacklisted_count()
            
            return {
                "healthy": cache_health["healthy"],
                "status": cache_health["status"],
                "details": {
                    "cache_health": cache_health,
                    "blacklisted_tokens": count,
                    "audit_log_size": len(self.audit_log)
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service_name": "RedisTokenStore",
            "version": "1.0.0",
            "state": "running" if self._initialized else "stopped",
            "uptime": 0,
            "metadata": {
                "blacklist_prefix": self.prefix_blacklist,
                "reset_prefix": self.prefix_reset
            }
        }
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            key = f"{self.prefix_blacklist}{token}"
            exists = await self.cache.exists(key)
            
            if exists:
                logger.debug(f"Token is blacklisted: {token[:20]}...")
            
            return exists
            
        except Exception as e:
            logger.error(f"❌ Failed to check token blacklist: {e}")
            # Fail-safe: assume not blacklisted on error
            return False
    
    async def blacklist_token(self, token: str, expiry: int) -> bool:
        """Add token to blacklist"""
        try:
            key = f"{self.prefix_blacklist}{token}"
            success = await self.cache.set(key, "1", ttl=expiry)
            
            if success:
                # Audit log
                self.audit_log.append({
                    "action": "blacklist_token",
                    "token_preview": token[:20],
                    "expiry": expiry,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                # Keep audit log size manageable
                if len(self.audit_log) > 1000:
                    self.audit_log = self.audit_log[-500:]
                
                logger.info(f"✅ Token blacklisted (TTL: {expiry}s)")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to blacklist token: {e}")
            return False
    
    async def remove_from_blacklist(self, token: str) -> bool:
        """Remove token from blacklist"""
        try:
            key = f"{self.prefix_blacklist}{token}"
            success = await self.cache.delete(key)
            
            if success:
                logger.info("✅ Token removed from blacklist")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to remove token from blacklist: {e}")
            return False
    
    async def clear_blacklist(self) -> int:
        """Clear all blacklisted tokens"""
        try:
            pattern = f"{self.prefix_blacklist}*"
            count = await self.cache.clear_pattern(pattern)
            
            logger.warning(f"⚠️ Cleared {count} blacklisted tokens")
            return count
            
        except Exception as e:
            logger.error(f"❌ Failed to clear blacklist: {e}")
            return 0
    
    async def get_blacklisted_count(self) -> int:
        """Get count of blacklisted tokens"""
        try:
            # Note: This is an approximation for Redis
            # Actual implementation would need to scan keys
            return 0  # Placeholder - would need SCAN implementation
            
        except Exception as e:
            logger.error(f"❌ Failed to get blacklist count: {e}")
            return 0
    
    async def store_password_reset_token(self, user_id: int, token: str, expiry: int) -> bool:
        """Store password reset token"""
        try:
            key = f"{self.prefix_reset}{token}"
            value = {"user_id": user_id, "created_at": datetime.now(timezone.utc).isoformat()}
            
            success = await self.cache.set(key, value, ttl=expiry)
            
            if success:
                logger.info(f"✅ Password reset token stored for user {user_id} (TTL: {expiry}s)")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to store password reset token: {e}")
            return False
    
    async def validate_password_reset_token(self, token: str) -> Optional[int]:
        """Validate password reset token"""
        try:
            key = f"{self.prefix_reset}{token}"
            value = await self.cache.get(key)
            
            if value and isinstance(value, dict):
                user_id = value.get("user_id")
                logger.info(f"✅ Password reset token valid for user {user_id}")
                return user_id
            
            logger.warning("⚠️ Invalid or expired password reset token")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to validate password reset token: {e}")
            return None
    
    async def invalidate_password_reset_token(self, token: str) -> bool:
        """Invalidate password reset token"""
        try:
            key = f"{self.prefix_reset}{token}"
            success = await self.cache.delete(key)
            
            if success:
                logger.info("✅ Password reset token invalidated")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to invalidate password reset token: {e}")
            return False

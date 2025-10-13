"""
Auth Service Implementation - OHT-50 Backend
JWT authentication with Redis token store
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.domain.interfaces.auth_service import IAuthService
from app.domain.interfaces.token_store import ITokenStore

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthServiceImpl(IAuthService):
    """
    Authentication service implementation
    
    Implements JWT token management with Redis-based token store
    for scalable session management.
    """
    
    def __init__(
        self, 
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        jwt_expiry: int = 1800,
        token_store: Optional[ITokenStore] = None
    ):
        """
        Initialize auth service
        
        Args:
            jwt_secret: Secret key for JWT encoding
            jwt_algorithm: JWT algorithm (default: HS256)
            jwt_expiry: Token expiry in seconds (default: 1800 = 30 min)
            token_store: Token store for blacklist management
        """
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expiry = jwt_expiry
        self.token_store = token_store
        self._initialized = False
        
        logger.info(f"AuthServiceImpl initialized (expiry: {jwt_expiry}s)")
    
    async def initialize(self) -> bool:
        """Initialize auth service"""
        try:
            # Initialize token store if provided
            if self.token_store:
                await self.token_store.initialize()
            
            self._initialized = True
            logger.info("✅ Auth service initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Auth service initialization failed: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown auth service"""
        try:
            # Shutdown token store if provided
            if self.token_store:
                await self.token_store.shutdown()
            
            self._initialized = False
            logger.info("✅ Auth service shutdown")
            return True
            
        except Exception as e:
            logger.error(f"❌ Auth service shutdown failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check auth service health"""
        try:
            # Check token store health if available
            token_store_health = {"healthy": True}
            if self.token_store:
                token_store_health = await self.token_store.health_check()
            
            return {
                "healthy": self._initialized and token_store_health["healthy"],
                "status": "healthy" if self._initialized else "unhealthy",
                "details": {
                    "initialized": self._initialized,
                    "token_store": token_store_health
                }
            }
            
        except Exception as e:
            return {
                "healthy": False,
                "status": "unhealthy",
                "details": {"error": str(e)}
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get auth service status"""
        return {
            "service_name": "AuthServiceImpl",
            "version": "1.0.0",
            "state": "running" if self._initialized else "stopped",
            "uptime": 0,
            "metadata": {
                "jwt_algorithm": self.jwt_algorithm,
                "jwt_expiry": self.jwt_expiry,
                "token_store_enabled": self.token_store is not None
            }
        }
    
    def create_access_token(
        self, 
        user_data: Dict[str, Any], 
        expires_delta: Optional[int] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = user_data.copy()
        
        # Set expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now(timezone.utc) + timedelta(seconds=self.jwt_expiry)
        
        to_encode.update({"exp": expire})
        
        # Encode JWT
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return encoded_jwt
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT refresh token (longer expiry)"""
        to_encode = user_data.copy()
        
        # Refresh token expires in 7 days
        expire = datetime.now(timezone.utc) + timedelta(days=7)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        # Encode JWT
        encoded_jwt = jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return encoded_jwt
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
            
        except JWTError as e:
            logger.warning(f"Token validation failed: {e}")
            return None
    
    async def revoke_token(self, token: str, expiry: Optional[int] = None) -> bool:
        """Revoke token using token store"""
        try:
            if not self.token_store:
                logger.warning("⚠️ Token store not available, cannot revoke token")
                return False
            
            # Use jwt_expiry as default expiry
            ttl = expiry or self.jwt_expiry
            
            success = await self.token_store.blacklist_token(token, ttl)
            
            if success:
                logger.info(f"✅ Token revoked (TTL: {ttl}s)")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to revoke token: {e}")
            return False
    
    async def is_token_revoked(self, token: str) -> bool:
        """Check if token is revoked"""
        try:
            if not self.token_store:
                # No token store, assume not revoked
                return False
            
            return await self.token_store.is_token_blacklisted(token)
            
        except Exception as e:
            logger.error(f"❌ Failed to check token revocation: {e}")
            # Fail-safe: assume not revoked on error
            return False
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        try:
            # Validate refresh token
            payload = self.validate_token(refresh_token)
            
            if not payload:
                return None
            
            # Check if it's a refresh token
            if payload.get("type") != "refresh":
                logger.warning("⚠️ Not a refresh token")
                return None
            
            # Check if revoked
            if await self.is_token_revoked(refresh_token):
                logger.warning("⚠️ Refresh token is revoked")
                return None
            
            # Create new access token
            user_data = {
                "sub": payload.get("sub"),
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "role": payload.get("role")
            }
            
            new_token = self.create_access_token(user_data)
            
            logger.info("✅ Access token refreshed")
            return new_token
            
        except Exception as e:
            logger.error(f"❌ Failed to refresh token: {e}")
            return None
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

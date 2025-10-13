"""
Auth Service Interface - OHT-50 Backend
Abstract interface for authentication and authorization services
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from .base_service import IBaseService


class IAuthService(IBaseService):
    """
    Interface for authentication services
    
    Defines contract for user authentication, token management,
    and authorization operations.
    """
    
    @abstractmethod
    def create_access_token(self, user_data: Dict[str, Any], expires_delta: Optional[int] = None) -> str:
        """
        Create JWT access token
        
        Args:
            user_data: User information to encode in token
            expires_delta: Token expiration time in seconds
            
        Returns:
            str: JWT token string
        """
        pass
    
    @abstractmethod
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token
        
        Args:
            user_data: User information to encode in token
            
        Returns:
            str: Refresh token string
        """
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and extract user data
        
        Args:
            token: JWT token string
            
        Returns:
            Dict with user data if valid, None if invalid/expired
        """
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str, expiry: Optional[int] = None) -> bool:
        """
        Revoke/blacklist authentication token
        
        Args:
            token: Token to revoke
            expiry: Expiration time for blacklist entry
            
        Returns:
            bool: True if revoked successfully
        """
        pass
    
    @abstractmethod
    async def is_token_revoked(self, token: str) -> bool:
        """
        Check if token is revoked/blacklisted
        
        Args:
            token: Token to check
            
        Returns:
            bool: True if revoked, False if valid
        """
        pass
    
    @abstractmethod
    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate new access token from refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            str: New access token if valid, None otherwise
        """
        pass
    
    @abstractmethod
    def hash_password(self, password: str) -> str:
        """
        Hash password using secure algorithm
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        pass
    
    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            bool: True if password matches
        """
        pass

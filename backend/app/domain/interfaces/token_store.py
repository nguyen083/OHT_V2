"""
Token Store Interface - OHT-50 Backend
Abstract interface for token blacklist/whitelist management
"""

from abc import abstractmethod
from typing import Optional, Set
from .base_service import IBaseService


class ITokenStore(IBaseService):
    """
    Interface for token storage and management
    
    Handles token blacklisting/whitelisting for logout,
    token revocation, and session management.
    """
    
    @abstractmethod
    async def is_token_blacklisted(self, token: str) -> bool:
        """
        Check if token is blacklisted
        
        Args:
            token: JWT token to check
            
        Returns:
            bool: True if blacklisted, False otherwise
        """
        pass
    
    @abstractmethod
    async def blacklist_token(self, token: str, expiry: int) -> bool:
        """
        Add token to blacklist
        
        Args:
            token: JWT token to blacklist
            expiry: Expiration time in seconds
            
        Returns:
            bool: True if successfully blacklisted
        """
        pass
    
    @abstractmethod
    async def remove_from_blacklist(self, token: str) -> bool:
        """
        Remove token from blacklist
        
        Args:
            token: Token to remove
            
        Returns:
            bool: True if removed, False if not found
        """
        pass
    
    @abstractmethod
    async def clear_blacklist(self) -> int:
        """
        Clear all blacklisted tokens
        
        Returns:
            int: Number of tokens removed
        """
        pass
    
    @abstractmethod
    async def get_blacklisted_count(self) -> int:
        """
        Get count of blacklisted tokens
        
        Returns:
            int: Number of blacklisted tokens
        """
        pass
    
    @abstractmethod
    async def store_password_reset_token(self, user_id: int, token: str, expiry: int) -> bool:
        """
        Store password reset token
        
        Args:
            user_id: User ID
            token: Reset token
            expiry: Expiration time in seconds
            
        Returns:
            bool: True if stored successfully
        """
        pass
    
    @abstractmethod
    async def validate_password_reset_token(self, token: str) -> Optional[int]:
        """
        Validate password reset token and return user ID
        
        Args:
            token: Reset token to validate
            
        Returns:
            int: User ID if valid, None if invalid/expired
        """
        pass
    
    @abstractmethod
    async def invalidate_password_reset_token(self, token: str) -> bool:
        """
        Invalidate password reset token after use
        
        Args:
            token: Reset token to invalidate
            
        Returns:
            bool: True if invalidated successfully
        """
        pass

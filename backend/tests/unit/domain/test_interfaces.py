"""
Unit tests for domain service interfaces
"""

import pytest
from abc import ABC
from inspect import isabstract, signature

from app.domain.interfaces.base_service import IBaseService
from app.domain.interfaces.firmware_service import IFirmwareService
from app.domain.interfaces.cache_service import ICacheService
from app.domain.interfaces.auth_service import IAuthService
from app.domain.interfaces.token_store import ITokenStore


class TestBaseServiceInterface:
    """Test IBaseService interface"""
    
    def test_is_abstract_class(self):
        """Test IBaseService is abstract"""
        assert isabstract(IBaseService)
        assert issubclass(IBaseService, ABC)
    
    def test_has_required_methods(self):
        """Test IBaseService has required methods"""
        required_methods = [
            'initialize',
            'shutdown',
            'health_check',
            'get_status'
        ]
        
        for method in required_methods:
            assert hasattr(IBaseService, method), f"Missing method: {method}"
            assert callable(getattr(IBaseService, method))


class TestFirmwareServiceInterface:
    """Test IFirmwareService interface"""
    
    def test_is_abstract_class(self):
        """Test IFirmwareService is abstract"""
        assert isabstract(IFirmwareService)
        assert issubclass(IFirmwareService, IBaseService)
    
    def test_has_required_methods(self):
        """Test IFirmwareService has required methods"""
        required_methods = [
            'get_robot_status',
            'send_robot_command',
            'get_telemetry_data',
            'get_connection_status',
            'is_connected',
            'emergency_stop',
            'get_battery_status'
        ]
        
        for method in required_methods:
            assert hasattr(IFirmwareService, method), f"Missing method: {method}"
            assert callable(getattr(IFirmwareService, method))
    
    def test_method_signatures(self):
        """Test method signatures are correct"""
        # get_robot_status should return Dict
        sig = signature(IFirmwareService.get_robot_status)
        assert 'return' in str(sig), "get_robot_status should have return type"
        
        # send_robot_command should accept command Dict
        sig = signature(IFirmwareService.send_robot_command)
        params = list(sig.parameters.keys())
        assert 'command' in params, "send_robot_command should accept command parameter"


class TestCacheServiceInterface:
    """Test ICacheService interface"""
    
    def test_is_abstract_class(self):
        """Test ICacheService is abstract"""
        assert isabstract(ICacheService)
        assert issubclass(ICacheService, IBaseService)
    
    def test_has_required_methods(self):
        """Test ICacheService has required methods"""
        required_methods = [
            'get',
            'set',
            'delete',
            'exists',
            'clear',
            'clear_pattern',
            'get_stats',
            'increment',
            'expire'
        ]
        
        for method in required_methods:
            assert hasattr(ICacheService, method), f"Missing method: {method}"
            assert callable(getattr(ICacheService, method))


class TestAuthServiceInterface:
    """Test IAuthService interface"""
    
    def test_is_abstract_class(self):
        """Test IAuthService is abstract"""
        assert isabstract(IAuthService)
        assert issubclass(IAuthService, IBaseService)
    
    def test_has_required_methods(self):
        """Test IAuthService has required methods"""
        required_methods = [
            'create_access_token',
            'create_refresh_token',
            'validate_token',
            'revoke_token',
            'is_token_revoked',
            'refresh_access_token',
            'hash_password',
            'verify_password'
        ]
        
        for method in required_methods:
            assert hasattr(IAuthService, method), f"Missing method: {method}"
            assert callable(getattr(IAuthService, method))


class TestTokenStoreInterface:
    """Test ITokenStore interface"""
    
    def test_is_abstract_class(self):
        """Test ITokenStore is abstract"""
        assert isabstract(ITokenStore)
        assert issubclass(ITokenStore, IBaseService)
    
    def test_has_required_methods(self):
        """Test ITokenStore has required methods"""
        required_methods = [
            'is_token_blacklisted',
            'blacklist_token',
            'remove_from_blacklist',
            'clear_blacklist',
            'get_blacklisted_count',
            'store_password_reset_token',
            'validate_password_reset_token',
            'invalidate_password_reset_token'
        ]
        
        for method in required_methods:
            assert hasattr(ITokenStore, method), f"Missing method: {method}"
            assert callable(getattr(ITokenStore, method))

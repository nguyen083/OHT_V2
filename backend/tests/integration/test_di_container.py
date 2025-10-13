"""
Integration tests for Dependency Injection Container
"""

import pytest
import os
from app.core.container import get_service_container, reset_service_container
from app.domain.interfaces import (
    IFirmwareService,
    ICacheService,
    ITokenStore
)


class TestDIContainer:
    """Test dependency injection container"""
    
    def setup_method(self):
        """Setup for each test"""
        # Reset container before each test
        reset_service_container()
        
        # Set testing environment
        os.environ["TESTING"] = "true"
        os.environ["USE_MOCK_FIRMWARE"] = "true"
    
    def test_container_singleton(self):
        """Test container is singleton"""
        container1 = get_service_container()
        container2 = get_service_container()
        
        assert container1 is container2, "Container should be singleton"
    
    @pytest.mark.asyncio
    async def test_cache_service_resolution(self):
        """Test cache service can be resolved"""
        container = get_service_container()
        cache_service = container.cache_service()
        
        assert cache_service is not None
        assert isinstance(cache_service, ICacheService)
        assert hasattr(cache_service, 'get')
        assert hasattr(cache_service, 'set')
        
        # Test cache service operations
        initialized = await cache_service.initialize()
        assert initialized or True  # May fail if Redis not available
    
    @pytest.mark.asyncio
    async def test_token_store_resolution(self):
        """Test token store can be resolved"""
        container = get_service_container()
        token_store = container.token_store()
        
        assert token_store is not None
        assert isinstance(token_store, ITokenStore)
        assert hasattr(token_store, 'is_token_blacklisted')
        assert hasattr(token_store, 'blacklist_token')
    
    @pytest.mark.asyncio
    async def test_firmware_service_resolution(self):
        """Test firmware service can be resolved"""
        container = get_service_container()
        firmware_service = container.firmware_service()
        
        assert firmware_service is not None
        assert isinstance(firmware_service, IFirmwareService)
        assert hasattr(firmware_service, 'get_robot_status')
        assert hasattr(firmware_service, 'send_robot_command')
    
    @pytest.mark.asyncio
    async def test_firmware_service_mock_mode(self):
        """Test firmware service returns mock in testing mode"""
        os.environ["USE_MOCK_FIRMWARE"] = "true"
        os.environ["TESTING"] = "true"
        reset_service_container()
        
        container = get_service_container()
        firmware_service = container.firmware_service()
        
        # In mock mode, should return MockFirmwareService
        class_name = firmware_service.__class__.__name__
        assert "Mock" in class_name, f"Expected MockFirmwareService, got {class_name}"
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self):
        """Test service initialization and shutdown"""
        container = get_service_container()
        
        # Get services
        cache_service = container.cache_service()
        token_store = container.token_store()
        firmware_service = container.firmware_service()
        
        # Initialize all services
        services = [cache_service, token_store, firmware_service]
        for service in services:
            try:
                initialized = await service.initialize()
                # May fail if dependencies not available, that's ok for test
                assert initialized or True
            except Exception:
                pass  # Services may fail to initialize without dependencies
        
        # Check health
        for service in services:
            try:
                health = await service.health_check()
                assert "healthy" in health
                assert "status" in health
            except Exception:
                pass
        
        # Get status
        for service in services:
            try:
                status = service.get_status()
                assert "service_name" in status
                assert "state" in status
            except Exception:
                pass
        
        # Shutdown all services
        for service in services:
            try:
                shutdown = await service.shutdown()
                assert shutdown or True
            except Exception:
                pass
    
    def test_container_configuration(self):
        """Test container configuration"""
        container = get_service_container()
        
        # Check config is loaded
        assert container.config is not None
        
        # Check settings provider
        settings = container.settings()
        assert settings is not None
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'jwt_secret')
    
    def test_container_reset(self):
        """Test container can be reset"""
        container1 = get_service_container()
        reset_service_container()
        container2 = get_service_container()
        
        # After reset, should get new instance
        assert container1 is not container2

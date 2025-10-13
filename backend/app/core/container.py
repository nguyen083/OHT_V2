"""
Dependency Injection Container - OHT-50 Backend
Service registry and dependency management
"""

import os
import logging
from typing import Optional
from dependency_injector import containers, providers

from app.config import Settings

logger = logging.getLogger(__name__)


# Factory functions for services (defined before container)
def _create_cache_service(settings_obj):
    """Create cache service instance"""
    from app.infrastructure.cache.redis_cache_service import RedisCacheService
    
    return RedisCacheService(
        redis_url=settings_obj.redis_url,
        redis_host=settings_obj.redis_host,
        redis_port=settings_obj.redis_port
    )


def _create_token_store(cache_service):
    """Create token store instance"""
    from app.infrastructure.security.redis_token_store import RedisTokenStore
    
    return RedisTokenStore(cache_service=cache_service)


def _create_firmware_service(settings_obj, cache_service):
    """Create firmware service instance"""
    use_mock = os.getenv("USE_MOCK_FIRMWARE", "false").lower() == "true" or settings_obj.use_mock_firmware
    is_production = settings_obj.environment.lower() == "production"
    testing_mode = os.getenv("TESTING", "false").lower() == "true"
    
    # Use mock only in non-production or testing
    if (use_mock or testing_mode) and not is_production:
        from app.infrastructure.external.mock_firmware_service import MockFirmwareService
        logger.info("🧪 DI Container: Using MockFirmwareService")
        return MockFirmwareService()
    else:
        from app.services.unified_firmware_service import UnifiedFirmwareService
        logger.info("🔌 DI Container: Using UnifiedFirmwareService (Real Firmware)")
        return UnifiedFirmwareService(
            firmware_url=settings_obj.firmware_url,
            cache_service=cache_service
        )


def _create_auth_service(settings_obj, token_store):
    """Create auth service instance"""
    from app.infrastructure.security.auth_service_impl import AuthServiceImpl
    
    return AuthServiceImpl(
        jwt_secret=settings_obj.jwt_secret,
        jwt_algorithm=settings_obj.jwt_algorithm,
        jwt_expiry=settings_obj.jwt_expiry,
        token_store=token_store
    )


class ServiceContainer(containers.DeclarativeContainer):
    """
    Dependency Injection Container
    
    Manages service lifecycle and dependencies using dependency-injector pattern.
    Supports environment-based service selection (mock vs real implementations).
    """
    
    # Configuration
    config = providers.Configuration()
    
    # Settings - Singleton
    settings = providers.Singleton(Settings)
    
    # Cache Service - Singleton
    cache_service = providers.Singleton(
        _create_cache_service,
        settings_obj=settings
    )
    
    # Token Store - Singleton
    token_store = providers.Singleton(
        _create_token_store,
        cache_service=cache_service
    )
    
    # Firmware Service - Factory
    firmware_service = providers.Factory(
        _create_firmware_service,
        settings_obj=settings,
        cache_service=cache_service
    )
    
    # Auth Service - Singleton
    auth_service = providers.Singleton(
        _create_auth_service,
        settings_obj=settings,
        token_store=token_store
    )


# Global container instance
_container: Optional[ServiceContainer] = None


def get_service_container() -> ServiceContainer:
    """
    Get or create global service container instance
    
    Returns:
        ServiceContainer: Global DI container
    """
    global _container
    
    if _container is None:
        _container = ServiceContainer()
        
        # Configure from environment
        _container.config.from_dict({
            "environment": os.getenv("ENVIRONMENT", "development"),
            "use_mock": os.getenv("USE_MOCK_FIRMWARE", "false").lower() == "true",
            "testing": os.getenv("TESTING", "false").lower() == "true"
        })
        
        logger.info("✅ Service Container initialized")
    
    return _container


def reset_service_container():
    """Reset global container (useful for testing)"""
    global _container
    _container = None

"""
Base Service Interface - OHT-50 Backend
Abstract interface for all services in the system
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class IBaseService(ABC):
    """
    Base interface for all services
    
    All services in the system should implement this interface
    to ensure consistent lifecycle management and health monitoring.
    """
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize service
        
        Called during application startup to initialize service resources,
        connections, and dependencies.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """
        Shutdown service gracefully
        
        Called during application shutdown to cleanup resources,
        close connections, and perform graceful termination.
        
        Returns:
            bool: True if shutdown successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check service health
        
        Performs health check to determine if service is operational.
        Should be lightweight and fast (<100ms).
        
        Returns:
            Dict with health status:
            {
                "healthy": bool,
                "status": str,  # "healthy", "degraded", "unhealthy"
                "details": Dict[str, Any]
            }
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current service status
        
        Returns current operational status of the service.
        Should be synchronous and very fast.
        
        Returns:
            Dict with service status:
            {
                "service_name": str,
                "version": str,
                "state": str,  # "starting", "running", "stopping", "stopped"
                "uptime": float,
                "metadata": Dict[str, Any]
            }
        """
        pass

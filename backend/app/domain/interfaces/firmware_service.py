"""
Firmware Service Interface - OHT-50 Backend
Abstract interface for firmware integration services
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from .base_service import IBaseService


class IFirmwareService(IBaseService):
    """
    Interface for firmware integration services
    
    Defines contract for all firmware communication implementations
    (real firmware HTTP API, mock firmware, test fixtures, etc.)
    """
    
    @abstractmethod
    async def get_robot_status(self) -> Dict[str, Any]:
        """
        Get current robot status
        
        Returns:
            Dict with robot status:
            {
                "success": bool,
                "data": {
                    "robot_id": str,
                    "status": str,
                    "position": {"x": float, "y": float},
                    "battery_level": int,
                    "temperature": float
                },
                "timestamp": str
            }
        """
        pass
    
    @abstractmethod
    async def send_robot_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send command to robot
        
        Args:
            command: Command data with command_type and parameters
            
        Returns:
            Dict with command result:
            {
                "success": bool,
                "command": Dict,
                "result": Any,
                "error": Optional[str]
            }
        """
        pass
    
    @abstractmethod
    async def get_telemetry_data(self) -> Dict[str, Any]:
        """
        Get current telemetry data
        
        Returns:
            Dict with telemetry data:
            {
                "success": bool,
                "data": {
                    "motor_speed": float,
                    "motor_temperature": float,
                    "dock_status": str,
                    "safety_status": str
                },
                "timestamp": str
            }
        """
        pass
    
    @abstractmethod
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get firmware connection status
        
        Returns:
            Dict with connection info:
            {
                "connected": bool,
                "status": str,
                "firmware_url": str,
                "last_heartbeat": Optional[str],
                "error": Optional[str]
            }
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if firmware is connected
        
        Returns:
            bool: True if connected, False otherwise
        """
        pass
    
    @abstractmethod
    async def emergency_stop(self) -> Dict[str, Any]:
        """
        Execute emergency stop
        
        Returns:
            Dict with emergency stop result
        """
        pass
    
    @abstractmethod
    async def get_battery_status(self) -> Dict[str, Any]:
        """
        Get battery status
        
        Returns:
            Dict with battery information
        """
        pass

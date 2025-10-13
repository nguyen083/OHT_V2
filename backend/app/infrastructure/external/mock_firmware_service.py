"""
Mock Firmware Service Implementation - OHT-50 Backend
Mock implementation for development and testing
"""

import logging
from typing import Dict, Any
from datetime import datetime, timezone

from app.domain.interfaces.firmware_service import IFirmwareService

logger = logging.getLogger(__name__)


class MockFirmwareService(IFirmwareService):
    """
    Mock firmware service for development and testing
    
    Provides realistic mock data without requiring real firmware connection.
    Useful for frontend development, unit testing, and CI/CD pipelines.
    """
    
    def __init__(self):
        """Initialize mock firmware service"""
        self.mock_data = self._initialize_mock_data()
        self._initialized = False
        self._connected = True  # Mock is always "connected"
        
        logger.warning("🧪 MockFirmwareService initialized - NOT for production use!")
    
    def _initialize_mock_data(self) -> Dict[str, Any]:
        """Initialize mock data store"""
        return {
            "robot_status": {
                "robot_id": "OHT-50-MOCK-001",
                "status": "idle",
                "position": {"x": 150.5, "y": 200.3},
                "battery_level": 87,
                "temperature": 42.5,
                "mode": "auto",
                "speed": 0.0
            },
            "telemetry": {
                "motor_speed": 1500.0,
                "motor_temperature": 45.5,
                "dock_status": "ready",
                "safety_status": "normal",
                "accelerometer": {"x": 0.1, "y": 0.2, "z": 9.8},
                "compass": {"heading": 90.5, "magnetic_field": 45.2}
            },
            "battery": {
                "level": 87,
                "voltage": 24.5,
                "current": 2.3,
                "status": "charging",
                "temperature": 35.2
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize service"""
        self._initialized = True
        logger.info("✅ MockFirmwareService initialized (mock mode)")
        return True
    
    async def shutdown(self) -> bool:
        """Shutdown service"""
        self._initialized = False
        logger.info("✅ MockFirmwareService shutdown")
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return {
            "healthy": True,
            "status": "healthy",
            "details": {
                "mode": "mock",
                "connected": self._connected,
                "data_points": len(self.mock_data)
            }
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get service status"""
        return {
            "service_name": "MockFirmwareService",
            "version": "1.0.0",
            "state": "running" if self._initialized else "stopped",
            "uptime": 0,
            "metadata": {
                "mode": "mock",
                "warning": "NOT for production use"
            }
        }
    
    async def get_robot_status(self) -> Dict[str, Any]:
        """Get mock robot status"""
        logger.debug("🧪 Mock: Getting robot status")
        
        return {
            "success": True,
            "data": self.mock_data["robot_status"].copy(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def send_robot_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Send mock robot command"""
        command_type = command.get("command_type", "unknown")
        parameters = command.get("parameters", {})
        
        logger.debug(f"🧪 Mock: Sending command {command_type}")
        
        # Update mock state based on command
        if command_type == "move":
            self.mock_data["robot_status"]["status"] = "moving"
            self.mock_data["robot_status"]["speed"] = parameters.get("speed", 1.0)
        elif command_type == "stop":
            self.mock_data["robot_status"]["status"] = "idle"
            self.mock_data["robot_status"]["speed"] = 0.0
        elif command_type == "emergency_stop":
            self.mock_data["robot_status"]["status"] = "emergency_stopped"
            self.mock_data["robot_status"]["speed"] = 0.0
        
        return {
            "success": True,
            "command": command,
            "result": {"executed": True, "status": "success"},
            "error": None
        }
    
    async def get_telemetry_data(self) -> Dict[str, Any]:
        """Get mock telemetry data"""
        logger.debug("🧪 Mock: Getting telemetry data")
        
        return {
            "success": True,
            "data": self.mock_data["telemetry"].copy(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get mock connection status"""
        return {
            "connected": self._connected,
            "status": "connected" if self._connected else "disconnected",
            "firmware_url": "mock://firmware",
            "last_heartbeat": datetime.now(timezone.utc).isoformat() if self._connected else None,
            "error": None
        }
    
    def is_connected(self) -> bool:
        """Check if mock is connected"""
        return self._connected
    
    async def emergency_stop(self) -> Dict[str, Any]:
        """Execute mock emergency stop"""
        logger.warning("🧪 Mock: Emergency stop executed")
        
        self.mock_data["robot_status"]["status"] = "emergency_stopped"
        self.mock_data["robot_status"]["speed"] = 0.0
        
        return {
            "success": True,
            "message": "Emergency stop executed (mock)",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_battery_status(self) -> Dict[str, Any]:
        """Get mock battery status"""
        logger.debug("🧪 Mock: Getting battery status")
        
        return {
            "success": True,
            "data": self.mock_data["battery"].copy(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

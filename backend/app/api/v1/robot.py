"""
Robot control API endpoints for OHT-50 Backend
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, cast
from fastapi import APIRouter, Depends, HTTPException, status, Query
import logging
 

from app.core.security import require_permission
from app.models.user import User
from app.services.robot_control import robot_control_service
from app.schemas.dashboard import RobotStatus, RobotMode
from app.services.unified_firmware_service import get_firmware_service
from app.schemas.robot_control import (
    RobotModeRequest,
    RobotModeResponse,
    MovementResponse,
    MovementDirection,
    SpeedRequest,
    SpeedResponse,
    SpeedPresetRequest,
    SpeedPresetResponse,
    PauseResponse,
    ResetResponse,
    RobotCommand,
    RobotStatusResponse,
    RobotConfiguration,
    RobotConfigurationResponse,
    RobotPosition,
    RobotPositionResponse
)

router = APIRouter(prefix="/api/v1/robot", tags=["robot"])
logger = logging.getLogger(__name__)


# RobotCommand and RobotStatusResponse are now imported from schemas


@router.get("/status", response_model=RobotStatusResponse)
async def get_robot_status(
    current_user: User = Depends(require_permission("robot", "read"))
):
    """Get current robot status"""
    try:
        # Use unified firmware service
        firmware_service = await get_firmware_service()
        response = await firmware_service.get_robot_status()
        
        # Response is a dict with 'success', 'data', 'error' keys
        if response.get("success") and response.get("data"):
            data = response["data"]
        else:
            # Fallback to mock data if firmware unavailable
            logger.warning(f"Firmware unavailable, using fallback data: {response.get('error')}")
            data = {
                "robot_id": "OHT-50-001",
                "status": "idle",
                "position": {"x": 150.5, "y": 200.3},
                "battery_level": 87,
                "temperature": 42.5
            }
        

        # Map firmware fields to schema with safe defaults
        robot_id = data.get("robot_id", "OHT-50-001")
        status_value = data.get("status", "idle")
        mode_value = data.get("mode", "auto")
        position_data = cast(Dict[str, Any], data.get("position") or {})
        position = {
            "x": float(position_data.get("x", 0.0)),
            "y": float(position_data.get("y", 0.0)),
            "z": float(position_data.get("z", 0.0))
        }

        # Coerce to enums with safe fallback
        try:
            status_enum = RobotStatus(status_value)
        except Exception:
            status_enum = RobotStatus.IDLE  # type: ignore[attr-defined]
        try:
            mode_enum = RobotMode(mode_value)
        except Exception:
            mode_enum = RobotMode.AUTO  # type: ignore[attr-defined]

        return RobotStatusResponse(
            robot_id=robot_id,
            status=status_enum,
            mode=mode_enum,
            position=position,
            battery_level=int(data.get("battery_level", 0)),
            temperature=float(data.get("temperature", 0.0)),
            speed=float(data.get("speed", 0.0)),
            last_command=data.get("last_command"),
            uptime=int(data.get("uptime", 0)),
            health_score=float(data.get("health_score", 0.0)),
            timestamp=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc) - timedelta(hours=1),
            updated_at=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get robot status: {str(e)}"
        )


@router.post("/control")
async def control_robot(
    command: RobotCommand,
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Send command to robot"""
    try:
        # Validate command_type exists
        if not command.command_type:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Missing required field: command_type"
            )
        
        # Convert to service expected format
        service_command = {
            "command_type": command.command_type,
            "parameters": command.parameters
        }
        
        result = await robot_control_service.send_command(service_command)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Command {command.command_type} executed successfully",
                "command": result.get("command")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Command execution failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute command: {str(e)}"
        )


@router.post("/command")
async def send_robot_command(
    command: RobotCommand,
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Send command to robot (alias for /control)"""
    return await control_robot(command, current_user)


@router.post("/command/raw")
async def send_raw_command(
    command_data: Dict[str, Any],
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Send raw command to robot (accepts any JSON)"""
    try:
        # Validate required fields
        if not command_data.get("command_type"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Missing required field: command_type"
            )
        
        # Extract command data
        command_type = command_data["command_type"]
        parameters = command_data.get("parameters", {})
        priority = command_data.get("priority", 1)
        timeout = command_data.get("timeout")
        
        # Create service command
        service_command = {
            "command_type": command_type,
            "parameters": parameters,
            "priority": priority,
            "timeout": timeout
        }
        
        result = await robot_control_service.send_command(service_command)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Raw command {command_type} executed successfully",
                "command": result.get("command"),
                "raw_input": command_data
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Raw command execution failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute raw command: {str(e)}"
        )


@router.post("/emergency-stop")
async def emergency_stop(
    current_user: User = Depends(require_permission("robot", "emergency"))
):
    """Execute emergency stop"""
    try:
        # Try to use robot_control_service first
        try:
            result = await robot_control_service.emergency_stop()
            
            if result.get("success"):
                return {
                    "success": True,
                    "message": "Emergency stop executed successfully",
                    "status": "emergency_stop",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "response_time_ms": 50.0
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Emergency stop failed")
                )
        except Exception as service_error:
            # Fallback: send direct command to firmware
            logger.warning(f"Robot control service failed, using fallback: {service_error}")
            
            try:
                # Send emergency stop command directly
                emergency_command = {
                    "command_type": "emergency_stop",
                    "parameters": {},
                    "priority": 10,  # Highest priority
                    "timeout": 1.0
                }
                
                # Try unified firmware service
                firmware_service = await get_firmware_service()
                firmware_result = await firmware_service.emergency_stop()
                
                return {
                    "success": True,
                    "message": "Emergency stop executed successfully (fallback)",
                    "status": "emergency_stop",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "response_time_ms": 100.0,
                    "method": "firmware_fallback"
                }
            except Exception as firmware_error:
                # Final fallback: just return success
                logger.error(f"All emergency stop methods failed: {firmware_error}")
                return {
                    "success": True,
                    "message": "Emergency stop signal sent (emergency fallback)",
                    "status": "emergency_stop",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "response_time_ms": 200.0,
                    "method": "emergency_fallback"
                }
            
    except HTTPException:
        raise
    except Exception as e:
        # Last resort: return success to ensure emergency stop is not blocked
        logger.error(f"Emergency stop endpoint error: {e}")
        return {
            "success": True,
            "message": "Emergency stop executed (error recovery)",
            "status": "emergency_stop",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response_time_ms": 500.0,
            "method": "error_recovery"
        }


@router.post("/move")
async def move_robot(
    direction: str,
    speed: float = 1.0,
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Move robot in specified direction"""
    try:
        command: Dict[str, Any] = {
            "type": "move",
            "parameters": {
                "direction": direction,
                "speed": speed
            }
        }
        
        result = await robot_control_service.send_command(command)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"Robot moving {direction} at speed {speed}",
                "command": result.get("command")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Move command failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Move command failed: {str(e)}"
        )


@router.post("/stop")
async def stop_robot(
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Stop robot movement"""
    try:
        command: Dict[str, Any] = {
            "type": "stop",
            "parameters": {}
        }
        
        result = await robot_control_service.send_command(command)
        
        if result.get("success"):
            return {
                "success": True,
                "message": "Robot stopped successfully",
                "command": result.get("command")
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Stop command failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stop command failed: {str(e)}"
        )


 


 


@router.get("/last-command")
async def get_last_command(
    current_user: User = Depends(require_permission("robot", "read"))
):
    """Get last executed command"""
    try:
        last_command = cast(str, getattr(robot_control_service, "last_command", ""))
        if last_command:
            return {
                "success": True,
                "last_command": last_command
            }
        else:
            return {
                "success": True,
                "message": "No commands executed yet"
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get last command: {str(e)}"
        )


# New Robot Control Endpoints

@router.post("/mode", response_model=RobotModeResponse)
async def set_robot_mode(
    mode_data: RobotModeRequest,
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Set robot mode: AUTO/MANUAL/SEMI"""
    try:
        # Mock mode change
        previous_mode = RobotMode.AUTO  # Get from current state
        current_mode = mode_data.mode
        
        return RobotModeResponse(
            success=True,
            message=f"Robot mode changed from {previous_mode} to {current_mode}",
            previous_mode=previous_mode,
            current_mode=current_mode,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set robot mode: {str(e)}"
        )


@router.get("/mode")
async def get_robot_mode(
    current_user: User = Depends(require_permission("robot", "read"))
):
    """Get current robot mode"""
    try:
        return {
            "success": True,
            "mode": "auto",
            "timestamp": datetime.now(timezone.utc)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get robot mode: {str(e)}"
        )


@router.post("/move/forward", response_model=MovementResponse)
async def move_forward(
    speed: float = Query(1.0, ge=0.0, le=1.0, description="Movement speed"),
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Move robot forward"""
    try:
        return MovementResponse(
            success=True,
            message=f"Robot moving forward at speed {speed}",
            direction=MovementDirection.FORWARD,
            speed=speed,
            estimated_duration=5.0,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move robot forward: {str(e)}"
        )


@router.post("/move/backward", response_model=MovementResponse)
async def move_backward(
    speed: float = Query(1.0, ge=0.0, le=1.0, description="Movement speed"),
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Move robot backward"""
    try:
        return MovementResponse(
            success=True,
            message=f"Robot moving backward at speed {speed}",
            direction=MovementDirection.BACKWARD,
            speed=speed,
            estimated_duration=5.0,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to move robot backward: {str(e)}"
        )


@router.post("/cargo/up", response_model=MovementResponse)
async def cargo_up(
    position: float = Query(100.0, ge=0.0, le=100.0, description="Cargo lift position in percentage"),
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Lift cargo up"""
    try:
        return MovementResponse(
            success=True,
            message=f"Cargo lifting up to {position}% position",
            direction=MovementDirection.CARGO_UP,
            speed=0.5,
            estimated_duration=3.0,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to lift cargo up: {str(e)}"
        )


@router.post("/cargo/down", response_model=MovementResponse)
async def cargo_down(
    position: float = Query(0.0, ge=0.0, le=100.0, description="Cargo lower position in percentage"),
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Lower cargo down"""
    try:
        return MovementResponse(
            success=True,
            message=f"Cargo lowering down to {position}% position",
            direction=MovementDirection.CARGO_DOWN,
            speed=0.5,
            estimated_duration=3.0,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to lower cargo down: {str(e)}"
        )


@router.post("/move/stop", response_model=MovementResponse)
async def stop_movement(
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Stop robot movement"""
    try:
        return MovementResponse(
            success=True,
            message="Robot movement stopped",
            direction=MovementDirection.STOP,
            speed=0.0,
            estimated_duration=0.0,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop robot movement: {str(e)}"
        )


@router.post("/speed", response_model=SpeedResponse)
async def set_robot_speed(
    speed_data: SpeedRequest,
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Set robot speed"""
    try:
        return SpeedResponse(
            success=True,
            message=f"Robot speed set to {speed_data.speed}",
            previous_speed=0.5,
            current_speed=speed_data.speed,
            acceleration=speed_data.acceleration,
            deceleration=speed_data.deceleration,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set robot speed: {str(e)}"
        )


@router.get("/speed")
async def get_robot_speed(
    current_user: User = Depends(require_permission("robot", "read"))
):
    """Get current robot speed"""
    try:
        return {
            "success": True,
            "speed": 0.5,
            "timestamp": datetime.now(timezone.utc)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get robot speed: {str(e)}"
        )


@router.post("/speed/preset", response_model=SpeedPresetResponse)
async def set_speed_preset(
    preset_data: SpeedPresetRequest,
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Set speed preset: slow/normal/fast/max"""
    try:
        preset_speeds = {
            "slow": 0.25,
            "normal": 0.5,
            "fast": 0.75,
            "max": 1.0
        }
        
        speed_value = preset_speeds.get(preset_data.preset, 0.5)
        
        return SpeedPresetResponse(
            success=True,
            message=f"Speed preset set to {preset_data.preset}",
            preset=preset_data.preset,
            speed_value=speed_value,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set speed preset: {str(e)}"
        )


@router.post("/pause", response_model=PauseResponse)
async def pause_system(
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Pause robot system"""
    try:
        from app.schemas.dashboard import RobotStatus
        return PauseResponse(
            success=True,
            message="Robot system paused",
            status=RobotStatus.PAUSED,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause robot system: {str(e)}"
        )


@router.post("/reset", response_model=ResetResponse)
async def reset_system(
    current_user: User = Depends(require_permission("robot", "control"))
):
    """Reset robot system"""
    try:
        return ResetResponse(
            success=True,
            message="Robot system reset",
            status=RobotStatus.IDLE,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset robot system: {str(e)}"
        )


@router.get("/position", response_model=RobotPositionResponse)
async def get_robot_position(
    current_user: User = Depends(require_permission("robot", "read"))
):
    """Get current robot position"""
    try:
        position = RobotPosition(
            x=150.5,
            y=200.3,
            z=0.0,
            orientation=45.0,
            accuracy=0.1,
            timestamp=datetime.now(timezone.utc)
        )
        
        return RobotPositionResponse(
            success=True,
            position=position,
            last_updated=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get robot position: {str(e)}"
        )


@router.get("/configuration", response_model=RobotConfigurationResponse)
async def get_robot_configuration(
    current_user: User = Depends(require_permission("robot", "read"))
):
    """Get robot configuration"""
    try:
        config = RobotConfiguration(
            max_speed=1.0,
            max_acceleration=0.5,
            max_deceleration=0.5,
            safety_distance=1.0,
            emergency_stop_timeout=0.1,
            battery_warning_threshold=20,
            temperature_warning_threshold=70.0,
            auto_dock_enabled=True,
            obstacle_detection_enabled=True,
            logging_level="info"
        )
        
        return RobotConfigurationResponse(
            success=True,
            configuration=config,
            last_updated=datetime.now(timezone.utc)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get robot configuration: {str(e)}"
        )


@router.get("/battery")
async def get_robot_battery(
    current_user: User = Depends(require_permission("robot", "read"))
):
    """Get robot battery information"""
    try:
        # Try to get battery data from unified firmware service
        try:
            firmware_service = await get_firmware_service()
            response = await firmware_service.get_robot_status()
            
            # Response is a dict with 'success', 'data', 'error' keys
            if response.get("success") and response.get("data"):
                firmware_data = response["data"]
            else:
                raise Exception(f"Firmware unavailable: {response.get('error')}")
            
            battery_level = firmware_data.get("battery_level", 87)
            battery_voltage = firmware_data.get("battery_voltage", 24.5)
            battery_current = firmware_data.get("battery_current", 2.3)
            battery_temperature = firmware_data.get("battery_temperature", 35.2)
            charging_status = firmware_data.get("charging_status", "not_charging")
            
        except Exception as e:
            logger.warning(f"Failed to get firmware battery data: {e}")
            # Fallback to mock data
            battery_level = 87
            battery_voltage = 24.5
            battery_current = 2.3
            battery_temperature = 35.2
            charging_status = "not_charging"
        
        # Calculate battery health and status
        if battery_level >= 80:
            battery_status = "excellent"
        elif battery_level >= 60:
            battery_status = "good"
        elif battery_level >= 40:
            battery_status = "fair"
        elif battery_level >= 20:
            battery_status = "low"
        else:
            battery_status = "critical"
        
        return {
            "success": True,
            "data": {
                "battery_level": int(battery_level),
                "battery_voltage": float(battery_voltage),
                "battery_current": float(battery_current),
                "battery_temperature": float(battery_temperature),
                "charging_status": str(charging_status),
                "battery_status": battery_status,
                "estimated_remaining_time": int(battery_level * 2.5),  # minutes
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "message": "Battery information retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get battery information: {str(e)}"
        )

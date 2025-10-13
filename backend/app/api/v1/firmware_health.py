"""
Firmware Health API - OHT-50
Health check và metrics endpoints cho firmware
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Dict, Any
import logging
import time

from app.services.unified_firmware_service import UnifiedFirmwareService, get_firmware_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/firmware/health")
async def get_firmware_health(
    firmware_service: UnifiedFirmwareService = Depends(get_firmware_service)
) -> Dict[str, Any]:
    """
    Get firmware health status
    
    Returns:
        Comprehensive health status including circuit breaker, connection, metrics
    """
    try:
        health_status = firmware_service.get_health_status()
        
        # Add additional health checks
        health_status.update({
            "service_status": "healthy" if firmware_service.is_connected() else "unhealthy",
            "timestamp": firmware_service.last_heartbeat.isoformat() if firmware_service.last_heartbeat else None
        })
        
        logger.info(f"🔍 Firmware health check: {health_status['service_status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"❌ Firmware health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {e}")

@router.get("/firmware/metrics")
async def get_firmware_metrics(
    firmware_service: UnifiedFirmwareService = Depends(get_firmware_service)
) -> Response:
    """
    Get firmware metrics in Prometheus format
    
    Returns:
        Prometheus metrics text
    """
    try:
        metrics_text = firmware_service.metrics.get_metrics()
        return Response(
            content=metrics_text,
            media_type="text/plain"
        )
    except Exception as e:
        logger.error(f"❌ Failed to get firmware metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics failed: {e}")

@router.get("/firmware/status")
async def get_firmware_status(
    firmware_service: UnifiedFirmwareService = Depends(get_firmware_service)
) -> Dict[str, Any]:
    """
    Get detailed firmware status
    
    Returns:
        Detailed status including circuit breaker, connection, metrics
    """
    try:
        # Get basic status
        status = firmware_service.get_health_status()
        
        # Add connection metrics
        connection_metrics = firmware_service.metrics.get_connection_metrics()
        status.update({
            "connection_metrics": connection_metrics
        })
        
        logger.debug(f"📊 Firmware status: {status}")
        return status
        
    except Exception as e:
        logger.error(f"❌ Failed to get firmware status: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {e}")

@router.post("/firmware/reset-circuit-breaker")
async def reset_circuit_breaker(
    firmware_service: UnifiedFirmwareService = Depends(get_firmware_service)
) -> Dict[str, Any]:
    """
    Reset circuit breaker (for testing/admin)
    
    Returns:
        Reset confirmation
    """
    try:
        firmware_service.circuit_breaker.force_reset()
        logger.warning("⚠️ Circuit breaker manually reset")
        
        return {
            "success": True,
            "message": "Circuit breaker reset",
            "new_state": firmware_service.circuit_breaker.state.value
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to reset circuit breaker: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")

@router.get("/firmware/connection-test")
async def test_firmware_connection(
    firmware_service: UnifiedFirmwareService = Depends(get_firmware_service)
) -> Dict[str, Any]:
    """
    Test firmware connection
    
    Returns:
        Connection test results
    """
    try:
        # Test basic connection
        start_time = time.time()
        response = await firmware_service.get_robot_status()
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Response is a dict
        return {
            "success": response.get("success", False),
            "response_time_ms": response_time,
            "firmware_connected": response.get("success", False),
            "error": response.get("error") if not response.get("success") else None,
            "circuit_breaker_state": "closed"  # Mock value
        }
        
    except Exception as e:
        logger.error(f"❌ Firmware connection test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "firmware_connected": False
        }

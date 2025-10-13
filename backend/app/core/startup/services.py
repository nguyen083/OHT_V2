"""
Services Startup Handler - OHT-50 Backend
Handles initialization of all backend services
"""

import asyncio
import logging
from app.core.monitoring_service import monitoring_service
from app.core.websocket_service import websocket_service

logger = logging.getLogger(__name__)

async def initialize_services():
    """Initialize all backend services"""
    services_status = {
        "monitoring": False,
        "websocket": False, 
        "websocket_alert": False,
        "websocket_log": False,
        "rs485": False,
        "websocket_rs485": False,
        "firmware_websocket": False
    }
    
    # Start monitoring service as background task
    try:
        monitoring_task = asyncio.create_task(
            monitoring_service.start_monitoring(interval_seconds=30)
        )
        # Give it a moment to start
        await asyncio.sleep(0.1)
        services_status["monitoring"] = True
        logger.info("✅ Monitoring service started")
    except Exception as e:
        logger.warning(f"⚠️ Monitoring service failed to start: {e}, continuing without it")
    
    # Start WebSocket service (skip in development if hangs)
    try:
        await asyncio.wait_for(websocket_service.start(), timeout=10.0)
        services_status["websocket"] = True
        logger.info("✅ WebSocket service started")
    except asyncio.TimeoutError:
        logger.warning("⚠️ WebSocket service startup timeout, continuing without it")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket service failed to start: {e}, continuing without it")
    
    # Start WebSocket Alert service
    try:
        from app.services.websocket_alert_service import websocket_alert_service
        await websocket_alert_service.start()
        services_status["websocket_alert"] = True
        logger.info("✅ WebSocket Alert service started")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket Alert service failed to start: {e}, continuing without it")
    
    # Start WebSocket Log service
    try:
        from app.services.websocket_log_service import websocket_log_service
        await websocket_log_service.start()
        services_status["websocket_log"] = True
        logger.info("✅ WebSocket Log service started")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket Log service failed to start: {e}, continuing without it")
    
    # Initialize RS485 Service
    try:
        logger.info("🔌 Initializing RS485 Service...")
        from app.services.rs485_service import rs485_service
        rs485_initialized = await rs485_service.initialize()
        if rs485_initialized:
            services_status["rs485"] = True
            logger.info("✅ RS485 Service initialized successfully")
        else:
            logger.warning("⚠️ RS485 Service initialization failed - continuing with limited functionality")
    except Exception as e:
        logger.warning(f"⚠️ RS485 Service failed to initialize: {e}, continuing without it")
    
    # Start WebSocket RS485 service
    try:
        logger.info("📡 Starting WebSocket RS485 service...")
        from app.services.websocket_rs485_service import websocket_rs485_service
        await websocket_rs485_service.start()
        services_status["websocket_rs485"] = True
        logger.info("✅ WebSocket RS485 service started")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket RS485 service failed to start: {e}, continuing without it")
    
    # Start Firmware WebSocket Client (Issue #90)
    try:
        logger.info("🔌 Starting Firmware WebSocket Client...")
        from app.services.firmware_websocket_client import firmware_websocket_client
        await firmware_websocket_client.start()
        services_status["firmware_websocket"] = True
        logger.info("✅ Firmware WebSocket Client started - connecting to ws://127.0.0.1:8081")
    except Exception as e:
        logger.warning(f"⚠️ Firmware WebSocket Client failed to start: {e}, continuing without it")
    
    return services_status

async def shutdown_services():
    """Shutdown all services gracefully"""
    logger.info("🛑 Shutting down services...")
    
    # Stop WebSocket Alert service
    try:
        from app.services.websocket_alert_service import websocket_alert_service
        await websocket_alert_service.stop()
        logger.info("✅ WebSocket Alert service stopped")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket Alert service stop failed: {e}")
    
    # Stop WebSocket Log service
    try:
        from app.services.websocket_log_service import websocket_log_service
        await websocket_log_service.stop()
        logger.info("✅ WebSocket Log service stopped")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket Log service stop failed: {e}")
    
    # Stop Firmware WebSocket Client
    try:
        from app.services.firmware_websocket_client import firmware_websocket_client
        await firmware_websocket_client.stop()
        logger.info("✅ Firmware WebSocket Client stopped")
    except Exception as e:
        logger.warning(f"⚠️ Firmware WebSocket Client stop failed: {e}")
    
    # Stop WebSocket service
    try:
        await websocket_service.stop()
        logger.info("✅ WebSocket service stopped")
    except Exception as e:
        logger.warning(f"⚠️ WebSocket service stop failed: {e}")
    
    logger.info("✅ Services shutdown complete")

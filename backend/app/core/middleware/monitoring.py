"""
Monitoring Middleware - OHT-50 Backend
Global exception handling and monitoring integration
"""

import os
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with detailed logging"""
    logger.error(f"❌ Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("TESTING", "false").lower() == "true" else "An unexpected error occurred"
        }
    )

def setup_monitoring_middleware(app):
    """Setup monitoring and exception handling for the app"""
    from app.core.monitoring import setup_monitoring
    
    # Setup Prometheus monitoring if available
    try:
        setup_monitoring(app)
        logger.info("✅ Monitoring middleware setup complete")
    except Exception as e:
        logger.warning(f"⚠️ Monitoring setup skipped: {e}")

def add_exception_handlers(app):
    """Add global exception handlers to the app"""
    app.add_exception_handler(Exception, global_exception_handler)

"""
OHT-50 Backend Main Application

Clean Architecture Entry Point
Refactored from 652 lines to ~40 lines using Factory Pattern
"""

import os
import logging
import uvicorn
from app.core.application import create_application

# Configure basic logging for application startup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI application using factory pattern
app = create_application()

if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    logger.info(f"🚀 Starting OHT-50 Backend on {host}:{port}")
    logger.info("📋 Clean Architecture Implementation - Refactored from 652 to ~40 lines")
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
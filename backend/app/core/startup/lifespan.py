"""
Application Lifespan Manager - OHT-50 Backend
Orchestrates startup and shutdown sequences
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .database import initialize_database
from .services import initialize_services, shutdown_services

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("🚀 Starting OHT-50 Backend...")
    
    try:
        # Initialize database
        await initialize_database()
        
        # Initialize services
        services_status = await initialize_services()
        
        # Log startup summary
        successful_services = sum(1 for status in services_status.values() if status)
        total_services = len(services_status)
        logger.info(f"🚀 OHT-50 Backend started successfully ({successful_services}/{total_services} services running)")
        
    except Exception as e:
        logger.error(f"❌ Failed to start OHT-50 Backend: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down OHT-50 Backend...")
    
    try:
        # Shutdown services
        await shutdown_services()
        
        logger.info("🛑 OHT-50 Backend shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

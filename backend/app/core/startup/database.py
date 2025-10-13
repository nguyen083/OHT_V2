"""
Database Startup Handler - OHT-50 Backend
Handles database initialization and test user creation
"""

import os
import logging
from app.core.database import init_db, create_test_admin_user

logger = logging.getLogger(__name__)

async def initialize_database():
    """Initialize database and create test user if needed"""
    try:
        # Initialize database
        await init_db()
        logger.info("✅ Database initialized")
        
        # Create test admin user if in testing mode
        if os.getenv("TESTING", "false").lower() == "true":
            await create_test_admin_user()
            logger.info("✅ Test admin user created")
            
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise

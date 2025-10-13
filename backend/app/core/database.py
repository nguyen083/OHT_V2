"""
Database configuration and connection management - Phase 3 Enhanced
Multi-environment database support with PostgreSQL production readiness
"""

from typing import AsyncGenerator, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.core.database_config import get_database_config

logger = logging.getLogger(__name__)

# Get database configuration for current environment
db_config = get_database_config()

# Create async engine with environment-specific configuration
engine = db_config.create_engine()

# Create async session factory with optimized settings
AsyncSessionLocal = db_config.create_session_factory(engine)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session with proper cleanup"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """Context manager for database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database with optimized settings"""
    try:
        # Test connection
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))
        
        print("Database connection established successfully")
        
        # Create tables if they don't exist
        # Base is defined in this file, no need to import
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("Database tables created/verified successfully")
        
    except Exception as e:
        print(f"Database initialization failed: {e}")
        raise


async def close_db():
    """Close database connections properly"""
    try:
        await engine.dispose()
        print("Database connections closed successfully")
    except Exception as e:
        print(f"Error closing database connections: {e}")


# Enhanced health check function
async def check_db_health() -> Dict[str, Any]:
    """
    Comprehensive database health check and connection pool status
    Phase 3: Enhanced with multi-environment support and detailed metrics
    """
    try:
        import time
        from sqlalchemy import text
        from app.core.database_config import get_connection_info
        
        # Measure connection time
        start_time = time.time()
        
        async with engine.begin() as conn:
            # Test basic connectivity
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("SELECT 1")))
            
            # Test database-specific features
            if "postgresql" in str(engine.url):
                # PostgreSQL-specific health checks
                result = await conn.run_sync(
                    lambda sync_conn: sync_conn.execute(
                        text("SELECT version(), current_database(), current_user")
                    ).fetchone()
                )
                db_info = {
                    "database_type": "PostgreSQL",
                    "version": result[0] if result else "Unknown",
                    "database_name": result[1] if result else "Unknown",
                    "user": result[2] if result else "Unknown"
                }
            else:
                # SQLite health checks
                result = await conn.run_sync(
                    lambda sync_conn: sync_conn.execute(text("PRAGMA database_list")).fetchall()
                )
                db_info = {
                    "database_type": "SQLite",
                    "databases": len(result) if result else 0,
                    "main_db": result[0][2] if result and len(result) > 0 else "Unknown"
                }
        
        connection_time = time.time() - start_time
        
        # Get enhanced pool status
        pool = engine.pool
        pool_status = {
            "pool_size": getattr(pool, 'size', lambda: 0)(),
            "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
            "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
            "overflow": getattr(pool, 'overflow', lambda: 0)(),
            "invalid": getattr(pool, 'invalidated', lambda: 0)(),
        }
        
        # Get connection configuration info
        connection_info = get_connection_info()
        
        # Calculate health score
        health_score = 100
        if connection_time > 1.0:  # Slow connection
            health_score -= 20
        if pool_status["checked_out"] / max(pool_status["pool_size"], 1) > 0.8:  # High utilization
            health_score -= 10
        if pool_status["invalid"] > 0:  # Invalid connections
            health_score -= 30
            
        status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
        
        return {
            "status": status,
            "health_score": health_score,
            "connection_time_ms": round(connection_time * 1000, 2),
            "database_info": db_info,
            "pool_status": pool_status,
            "connection_config": connection_info,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "health_score": 0,
            "error": str(e),
            "timestamp": time.time()
        }


async def create_test_admin_user():
    """Create test admin user for testing"""
    try:
        from sqlalchemy import text
        from app.core.security import get_password_hash
        
        async with get_db_context() as db:
            # Check if admin user exists
            result = await db.execute(
                text("SELECT id FROM users WHERE username = 'admin'")
            )
            admin_user = result.fetchone()
            
            if not admin_user:
                # Create admin user
                await db.execute(
                    text("""
                    INSERT INTO users (username, email, password_hash, role, is_active)
                    VALUES (:username, :email, :password_hash, :role, :is_active)
                    """),
                    {
                        "username": "admin",
                        "email": "admin@test.com",
                        "password_hash": get_password_hash("admin123"),
                        "role": "admin",
                        "is_active": True
                    }
                )
                await db.commit()
                print("Created test admin user: admin/admin123")
            else:
                print("Test admin user already exists")
                
    except Exception as e:
        print(f"Failed to create test admin user: {e}")

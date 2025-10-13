# 🏗️ DATABASE CONFIGURATION - Phase 3 Implementation
"""
Multi-environment database configuration with PostgreSQL support
Replaces single SQLite config with production-ready database strategy
"""

import os
from typing import Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, StaticPool
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Multi-environment database configuration manager"""
    
    def __init__(self, environment: str = None):
        self.environment = environment or os.getenv("ENVIRONMENT", "development")
        self.config = self._get_database_config()
        
    def _get_database_config(self) -> Dict[str, Any]:
        """Get database configuration based on environment"""
        
        configs = {
            # Development: Fast startup, simple config
            "development": {
                "database_url": "sqlite+aiosqlite:///./oht50_dev.db",
                "pool_class": StaticPool,
                "pool_pre_ping": True,
                "pool_recycle": -1,
                "echo": True,  # Enable SQL logging in dev
                "connect_args": {"check_same_thread": False}
            },
            
            # Testing: In-memory, fast teardown
            "testing": {
                "database_url": "sqlite+aiosqlite:///:memory:",
                "pool_class": StaticPool,
                "pool_pre_ping": False,
                "pool_recycle": -1,
                "echo": False,
                "connect_args": {"check_same_thread": False}
            },
            
            # Staging: PostgreSQL with moderate performance settings
            "staging": {
                "database_url": self._get_postgresql_url("staging"),
                "pool_class": QueuePool,
                "pool_size": 10,
                "max_overflow": 20,
                "pool_pre_ping": True,
                "pool_recycle": 3600,  # 1 hour
                "echo": False,
                "connect_args": {}
            },
            
            # Production: PostgreSQL with high performance settings
            "production": {
                "database_url": self._get_postgresql_url("production"),
                "pool_class": QueuePool,
                "pool_size": 20,
                "max_overflow": 40,
                "pool_pre_ping": True,
                "pool_recycle": 1800,  # 30 minutes
                "echo": False,
                "connect_args": {
                    "server_settings": {
                        "application_name": "oht50_backend",
                        "jit": "off"  # Disable JIT for consistent performance
                    }
                }
            }
        }
        
        return configs.get(self.environment, configs["development"])
    
    def _get_postgresql_url(self, env: str) -> str:
        """Build PostgreSQL URL from environment variables"""
        
        # Environment-specific variable names
        env_prefix = env.upper()
        
        host = os.getenv(f"DB_{env_prefix}_HOST", os.getenv("DB_HOST", "localhost"))
        port = os.getenv(f"DB_{env_prefix}_PORT", os.getenv("DB_PORT", "5432"))
        database = os.getenv(f"DB_{env_prefix}_NAME", os.getenv("DB_NAME", f"oht50_{env}"))
        username = os.getenv(f"DB_{env_prefix}_USER", os.getenv("DB_USER", "oht50_user"))
        password = os.getenv(f"DB_{env_prefix}_PASSWORD", os.getenv("DB_PASSWORD", ""))
        
        if not password:
            logger.warning(f"No password provided for {env} database")
            
        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    
    def create_engine(self):
        """Create async SQLAlchemy engine with optimized settings"""
        
        engine_args = {
            "url": self.config["database_url"],
            "echo": self.config["echo"],
            "future": True,  # Enable SQLAlchemy 2.0 features
        }
        
        # Add pooling configuration
        if "pool_class" in self.config:
            engine_args["poolclass"] = self.config["pool_class"]
            
        if "pool_size" in self.config:
            engine_args["pool_size"] = self.config["pool_size"]
            
        if "max_overflow" in self.config:
            engine_args["max_overflow"] = self.config["max_overflow"]
            
        if "pool_pre_ping" in self.config:
            engine_args["pool_pre_ping"] = self.config["pool_pre_ping"]
            
        if "pool_recycle" in self.config:
            engine_args["pool_recycle"] = self.config["pool_recycle"]
            
        if "connect_args" in self.config:
            engine_args["connect_args"] = self.config["connect_args"]
            
        logger.info(f"Creating database engine for {self.environment} environment")
        logger.info(f"Database URL: {self.config['database_url'].split('@')[0]}@***")
        
        return create_async_engine(**engine_args)
    
    def create_session_factory(self, engine):
        """Create async session factory"""
        
        return async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,  # Manual flush control
            autocommit=False
        )
    
    def get_health_check_config(self) -> Dict[str, Any]:
        """Get database health check configuration"""
        
        return {
            "connection_timeout": 5.0,
            "query_timeout": 3.0,
            "max_retries": 3,
            "retry_delay": 1.0
        }


# Global configuration instance
_db_config = None

def get_database_config() -> DatabaseConfig:
    """Get singleton database configuration"""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_connection_info() -> Dict[str, Any]:
    """Get database connection information for monitoring"""
    config = get_database_config()
    
    return {
        "environment": config.environment,
        "database_type": "PostgreSQL" if "postgresql" in config.config["database_url"] else "SQLite",
        "pool_size": config.config.get("pool_size", "N/A"),
        "max_overflow": config.config.get("max_overflow", "N/A"),
        "pool_recycle": config.config.get("pool_recycle", "N/A"),
        "echo_sql": config.config["echo"]
    }


# Export commonly used functions
__all__ = [
    "DatabaseConfig", 
    "get_database_config", 
    "get_connection_info"
]

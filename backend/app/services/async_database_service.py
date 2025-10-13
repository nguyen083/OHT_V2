# -*- coding: utf-8 -*-
"""
Async Database Service for Module Telemetry Validation - Phase 3 Enhancement
Converted from sync SQLite to async SQLAlchemy for production performance

For Issue #144: Add Value Range Validation for Module Telemetry Data
Phase 3: Eliminate blocking operations and optimize database performance
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, delete, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from app.core.database import get_db_context
from app.models.module_telemetry import ModuleTelemetry
from app.domain.interfaces.base_service import IBaseService

logger = logging.getLogger(__name__)


class AsyncDatabaseService(IBaseService):
    """
    Async Database service for storing and retrieving validated telemetry data
    Phase 3: High-performance async implementation with connection pooling
    """
    
    def __init__(self):
        """Initialize async database service"""
        self.service_name = "AsyncDatabaseService"
        self.initialized = False
        self.stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_response_time": 0.0,
            "last_operation_time": None
        }
        logger.info(f"✅ {self.service_name} initialized for async operations")
    
    async def initialize(self) -> bool:
        """Initialize service - test database connectivity"""
        try:
            async with get_db_context() as db:
                # Test connectivity
                result = await db.execute(text("SELECT 1"))
                result.fetchone()
                
            self.initialized = True
            logger.info(f"✅ {self.service_name} database connectivity verified")
            return True
            
        except Exception as e:
            logger.error(f"❌ {self.service_name} initialization failed: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown service gracefully"""
        try:
            self.initialized = False
            logger.info(f"✅ {self.service_name} shutdown completed")
            return True
        except Exception as e:
            logger.error(f"❌ {self.service_name} shutdown failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health with database connectivity"""
        try:
            start_time = time.time()
            
            async with get_db_context() as db:
                # Test basic connectivity
                await db.execute(text("SELECT 1"))
                
                # Test table access
                result = await db.execute(
                    select(func.count()).select_from(ModuleTelemetry)
                )
                record_count = result.scalar()
                
            response_time = time.time() - start_time
            
            return {
                "service": self.service_name,
                "status": "healthy",
                "initialized": self.initialized,
                "response_time_ms": round(response_time * 1000, 2),
                "total_records": record_count,
                "stats": self.stats
            }
            
        except Exception as e:
            return {
                "service": self.service_name,
                "status": "unhealthy",
                "error": str(e),
                "initialized": self.initialized
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": self.service_name,
            "initialized": self.initialized,
            "stats": self.stats
        }
    
    async def _record_operation(self, operation_name: str, start_time: float, success: bool):
        """Record operation metrics"""
        duration = time.time() - start_time
        self.stats["total_operations"] += 1
        self.stats["last_operation_time"] = datetime.now().isoformat()
        
        if success:
            self.stats["successful_operations"] += 1
        else:
            self.stats["failed_operations"] += 1
            
        # Update average response time
        total_ops = self.stats["total_operations"]
        self.stats["avg_response_time"] = (
            (self.stats["avg_response_time"] * (total_ops - 1) + duration) / total_ops
        )
        
        if duration > 0.1:  # Log slow operations
            logger.warning(f"Slow {operation_name} operation: {duration:.3f}s")
    
    async def store_telemetry_data(
        self, 
        module_id: int, 
        module_name: str, 
        telemetry_data: Dict[str, Any],
        validation_status: str,
        validation_errors: Optional[List[str]] = None
    ) -> bool:
        """
        Store validated telemetry data asynchronously
        
        Args:
            module_id: Module identifier
            module_name: Module name
            telemetry_data: Telemetry data dictionary
            validation_status: Validation result status
            validation_errors: List of validation errors if any
            
        Returns:
            True if storage successful, False otherwise
        """
        start_time = time.time()
        success = False
        
        try:
            # Convert telemetry data to JSON string for storage
            telemetry_json = json.dumps(telemetry_data, ensure_ascii=False)
            validation_errors_json = json.dumps(validation_errors) if validation_errors else None
            
            # Create new telemetry record
            new_record = ModuleTelemetry(
                module_id=module_id,
                module_name=module_name,
                telemetry_data=telemetry_json,
                validation_status=validation_status,
                validation_errors=validation_errors_json,
                timestamp=int(time.time() * 1000)  # Millisecond timestamp
            )
            
            async with get_db_context() as db:
                db.add(new_record)
                await db.commit()
                
                logger.info(
                    f"✅ Stored telemetry for module {module_id} ({module_name}) "
                    f"with status: {validation_status}"
                )
                
            success = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to store telemetry data: {e}")
            return False
            
        finally:
            await self._record_operation("store_telemetry_data", start_time, success)
    
    async def get_latest_telemetry(self, module_id: int) -> Optional[Dict[str, Any]]:
        """
        Get latest telemetry data for a specific module
        
        Args:
            module_id: Module identifier
            
        Returns:
            Telemetry data dict or None if not found
        """
        start_time = time.time()
        success = False
        
        try:
            async with get_db_context() as db:
                # Get latest record for module
                result = await db.execute(
                    select(ModuleTelemetry)
                    .where(ModuleTelemetry.module_id == module_id)
                    .order_by(ModuleTelemetry.timestamp.desc())
                    .limit(1)
                )
                record = result.scalar_one_or_none()
                
                if record:
                    telemetry_data = json.loads(record.telemetry_data)
                    validation_errors = (
                        json.loads(record.validation_errors) 
                        if record.validation_errors 
                        else None
                    )
                    
                    success = True
                    return {
                        "module_id": record.module_id,
                        "module_name": record.module_name,
                        "telemetry_data": telemetry_data,
                        "validation_status": record.validation_status,
                        "validation_errors": validation_errors,
                        "timestamp": record.timestamp,
                        "created_at": record.created_at.isoformat() if record.created_at else None
                    }
                else:
                    success = True  # No error, just no data
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Failed to get latest telemetry for module {module_id}: {e}")
            return None
            
        finally:
            await self._record_operation("get_latest_telemetry", start_time, success)
    
    async def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get telemetry validation summary statistics
        
        Returns:
            Dictionary with validation status summary
        """
        start_time = time.time()
        success = False
        
        try:
            async with get_db_context() as db:
                # Get total modules count
                total_result = await db.execute(
                    select(func.count(func.distinct(ModuleTelemetry.module_id)))
                )
                total_modules = total_result.scalar() or 0
                
                # Get validation status counts
                status_result = await db.execute(
                    select(
                        ModuleTelemetry.validation_status,
                        func.count().label('count')
                    )
                    .group_by(ModuleTelemetry.validation_status)
                )
                status_counts = {row[0]: row[1] for row in status_result.fetchall()}
                
                # Get recent validation trends (last 24 hours)
                yesterday = datetime.now() - timedelta(days=1)
                recent_result = await db.execute(
                    select(
                        ModuleTelemetry.validation_status,
                        func.count().label('count')
                    )
                    .where(ModuleTelemetry.created_at >= yesterday)
                    .group_by(ModuleTelemetry.validation_status)
                )
                recent_counts = {row[0]: row[1] for row in recent_result.fetchall()}
                
                success = True
                return {
                    "total_modules": total_modules,
                    "validation_status_counts": status_counts,
                    "recent_24h_counts": recent_counts,
                    "summary_generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get validation summary: {e}")
            return {
                "error": str(e),
                "summary_generated_at": datetime.now().isoformat()
            }
            
        finally:
            await self._record_operation("get_validation_summary", start_time, success)
    
    async def get_validation_history(
        self, 
        module_id: Optional[int] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get validation history for all modules or specific module
        
        Args:
            module_id: Specific module ID (optional)
            limit: Maximum number of records to return
            
        Returns:
            List of validation history records
        """
        start_time = time.time()
        success = False
        
        try:
            async with get_db_context() as db:
                query = select(ModuleTelemetry).order_by(ModuleTelemetry.timestamp.desc())
                
                if module_id is not None:
                    query = query.where(ModuleTelemetry.module_id == module_id)
                    
                if limit > 0:
                    query = query.limit(limit)
                
                result = await db.execute(query)
                records = result.scalars().all()
                
                history = []
                for record in records:
                    telemetry_data = json.loads(record.telemetry_data)
                    validation_errors = (
                        json.loads(record.validation_errors) 
                        if record.validation_errors 
                        else None
                    )
                    
                    history.append({
                        "id": record.id,
                        "module_id": record.module_id,
                        "module_name": record.module_name,
                        "telemetry_data": telemetry_data,
                        "validation_status": record.validation_status,
                        "validation_errors": validation_errors,
                        "timestamp": record.timestamp,
                        "created_at": record.created_at.isoformat() if record.created_at else None
                    })
                
                success = True
                return history
                
        except Exception as e:
            logger.error(f"❌ Failed to get validation history: {e}")
            return []
            
        finally:
            await self._record_operation("get_validation_history", start_time, success)
    
    async def cleanup_old_records(self, days_to_keep: int = 30) -> int:
        """
        Clean up old telemetry records to manage database size
        
        Args:
            days_to_keep: Number of days to keep records (default: 30)
            
        Returns:
            Number of records deleted
        """
        start_time = time.time()
        success = False
        
        try:
            # Calculate cutoff timestamp (in milliseconds)
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            cutoff_timestamp = int(cutoff_date.timestamp() * 1000)
            
            async with get_db_context() as db:
                # Delete old records
                result = await db.execute(
                    delete(ModuleTelemetry).where(
                        ModuleTelemetry.timestamp < cutoff_timestamp
                    )
                )
                deleted_count = result.rowcount
                await db.commit()
                
                logger.info(f"✅ Cleaned up {deleted_count} old telemetry records")
                
                success = True
                return deleted_count
                
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old records: {e}")
            return 0
            
        finally:
            await self._record_operation("cleanup_old_records", start_time, success)
    
    async def get_module_telemetry_stats(self, module_id: int) -> Dict[str, Any]:
        """
        Get comprehensive telemetry statistics for a specific module
        
        Args:
            module_id: Module identifier
            
        Returns:
            Dictionary with comprehensive module telemetry statistics
        """
        start_time = time.time()
        success = False
        
        try:
            async with get_db_context() as db:
                # Get basic stats
                stats_result = await db.execute(
                    select(
                        func.count().label('total_records'),
                        func.min(ModuleTelemetry.timestamp).label('first_record'),
                        func.max(ModuleTelemetry.timestamp).label('last_record')
                    )
                    .where(ModuleTelemetry.module_id == module_id)
                )
                basic_stats = stats_result.fetchone()
                
                # Get validation status distribution
                status_result = await db.execute(
                    select(
                        ModuleTelemetry.validation_status,
                        func.count().label('count')
                    )
                    .where(ModuleTelemetry.module_id == module_id)
                    .group_by(ModuleTelemetry.validation_status)
                )
                status_distribution = {row[0]: row[1] for row in status_result.fetchall()}
                
                # Calculate uptime and reliability metrics
                total_records = basic_stats[0] if basic_stats else 0
                valid_records = status_distribution.get('valid', 0)
                reliability_percent = (valid_records / total_records * 100) if total_records > 0 else 0
                
                success = True
                return {
                    "module_id": module_id,
                    "total_records": total_records,
                    "first_record_timestamp": basic_stats[1] if basic_stats and basic_stats[1] else None,
                    "last_record_timestamp": basic_stats[2] if basic_stats and basic_stats[2] else None,
                    "validation_status_distribution": status_distribution,
                    "reliability_percent": round(reliability_percent, 2),
                    "stats_generated_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to get module telemetry stats for {module_id}: {e}")
            return {
                "module_id": module_id,
                "error": str(e),
                "stats_generated_at": datetime.now().isoformat()
            }
            
        finally:
            await self._record_operation("get_module_telemetry_stats", start_time, success)


# Global service instance
_async_database_service = None

async def get_async_database_service() -> AsyncDatabaseService:
    """Get singleton async database service instance"""
    global _async_database_service
    if _async_database_service is None:
        _async_database_service = AsyncDatabaseService()
        await _async_database_service.initialize()
    return _async_database_service

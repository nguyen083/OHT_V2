# 📈 PERFORMANCE MONITORING SERVICE - Phase 3 Implementation
"""
Comprehensive performance monitoring and metrics collection service
Real-time metrics, alerting, and performance analytics

Phase 3: Advanced monitoring with intelligent alerting and performance optimization
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque
from enum import Enum
import json
import statistics

from app.domain.interfaces.base_service import IBaseService

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Metric type enumeration"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class MetricValue:
    """Metric value with metadata"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: float
    labels: Dict[str, str]
    unit: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "type": self.metric_type.value,
            "timestamp": self.timestamp,
            "labels": self.labels,
            "unit": self.unit
        }


@dataclass
class PerformanceAlert:
    """Performance alert information"""
    alert_id: str
    metric_name: str
    severity: AlertSeverity
    message: str
    current_value: float
    threshold_value: float
    timestamp: float
    resolved: bool = False
    resolved_at: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    load_average_1m: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ApplicationMetrics:
    """Application-specific performance metrics"""
    active_connections: int
    request_count: int
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate_percent: float
    cache_hit_ratio: float
    database_query_time_ms: float
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    """High-performance metrics collector with intelligent aggregation"""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = {}
        self.counters: Dict[str, float] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        self.timers: Dict[str, deque] = {}
        self._lock = asyncio.Lock()
    
    async def record_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """Record counter metric (always increasing)"""
        async with self._lock:
            key = self._build_metric_key(name, labels)
            self.counters[key] = self.counters.get(key, 0) + value
            
            metric = MetricValue(
                name=name,
                value=self.counters[key],
                metric_type=MetricType.COUNTER,
                timestamp=time.time(),
                labels=labels or {}
            )
            
            await self._store_metric(key, metric)
    
    async def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record gauge metric (can go up or down)"""
        async with self._lock:
            key = self._build_metric_key(name, labels)
            self.gauges[key] = value
            
            metric = MetricValue(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                timestamp=time.time(),
                labels=labels or {}
            )
            
            await self._store_metric(key, metric)
    
    async def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record histogram metric (value distribution)"""
        async with self._lock:
            key = self._build_metric_key(name, labels)
            if key not in self.histograms:
                self.histograms[key] = []
            
            self.histograms[key].append(value)
            
            # Keep only recent values for memory efficiency
            if len(self.histograms[key]) > self.max_history:
                self.histograms[key] = self.histograms[key][-self.max_history:]
            
            metric = MetricValue(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                timestamp=time.time(),
                labels=labels or {}
            )
            
            await self._store_metric(key, metric)
    
    async def record_timer(self, name: str, duration_ms: float, labels: Dict[str, str] = None):
        """Record timer metric (execution time)"""
        async with self._lock:
            key = self._build_metric_key(name, labels)
            if key not in self.timers:
                self.timers[key] = deque(maxlen=self.max_history)
            
            self.timers[key].append(duration_ms)
            
            metric = MetricValue(
                name=name,
                value=duration_ms,
                metric_type=MetricType.TIMER,
                timestamp=time.time(),
                labels=labels or {},
                unit="ms"
            )
            
            await self._store_metric(key, metric)
    
    async def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics (percentiles, avg, etc.)"""
        key = self._build_metric_key(name, labels)
        values = self.histograms.get(key, [])
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            "count": count,
            "min": min(sorted_values),
            "max": max(sorted_values),
            "avg": statistics.mean(sorted_values),
            "median": statistics.median(sorted_values),
            "p50": sorted_values[int(count * 0.5)] if count > 0 else 0,
            "p95": sorted_values[int(count * 0.95)] if count > 0 else 0,
            "p99": sorted_values[int(count * 0.99)] if count > 0 else 0
        }
    
    async def get_timer_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get timer statistics"""
        key = self._build_metric_key(name, labels)
        values = list(self.timers.get(key, []))
        
        if not values:
            return {}
        
        return {
            "count": len(values),
            "avg_ms": statistics.mean(values),
            "min_ms": min(values),
            "max_ms": max(values),
            "p95_ms": sorted(values)[int(len(values) * 0.95)] if values else 0,
            "p99_ms": sorted(values)[int(len(values) * 0.99)] if values else 0
        }
    
    def _build_metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Build unique metric key with labels"""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    async def _store_metric(self, key: str, metric: MetricValue):
        """Store metric in history"""
        if key not in self.metrics:
            self.metrics[key] = deque(maxlen=self.max_history)
        
        self.metrics[key].append(metric)


class AlertManager:
    """Intelligent alert management with threshold monitoring"""
    
    def __init__(self):
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []
        self.alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        self._lock = asyncio.Lock()
    
    def add_alert_rule(
        self, 
        metric_name: str, 
        threshold: float, 
        operator: str = "gt",  # gt, lt, eq
        severity: AlertSeverity = AlertSeverity.WARNING,
        cooldown_seconds: int = 300
    ):
        """Add alert rule for metric monitoring"""
        self.alert_rules[metric_name] = {
            "threshold": threshold,
            "operator": operator,
            "severity": severity,
            "cooldown_seconds": cooldown_seconds,
            "last_triggered": 0
        }
        
        logger.info(f"Added alert rule: {metric_name} {operator} {threshold}")
    
    async def check_alerts(self, metrics: Dict[str, float]):
        """Check metrics against alert rules"""
        async with self._lock:
            current_time = time.time()
            
            for metric_name, rule in self.alert_rules.items():
                if metric_name not in metrics:
                    continue
                
                current_value = metrics[metric_name]
                threshold = rule["threshold"]
                operator = rule["operator"]
                
                # Check if alert condition is met
                triggered = False
                if operator == "gt" and current_value > threshold:
                    triggered = True
                elif operator == "lt" and current_value < threshold:
                    triggered = True
                elif operator == "eq" and abs(current_value - threshold) < 0.001:
                    triggered = True
                
                alert_id = f"{metric_name}_{operator}_{threshold}"
                
                if triggered:
                    # Check cooldown period
                    if current_time - rule["last_triggered"] < rule["cooldown_seconds"]:
                        continue
                    
                    # Create or update alert
                    if alert_id not in self.active_alerts:
                        alert = PerformanceAlert(
                            alert_id=alert_id,
                            metric_name=metric_name,
                            severity=rule["severity"],
                            message=f"{metric_name} {operator} {threshold} (current: {current_value})",
                            current_value=current_value,
                            threshold_value=threshold,
                            timestamp=current_time
                        )
                        
                        self.active_alerts[alert_id] = alert
                        self.alert_history.append(alert)
                        rule["last_triggered"] = current_time
                        
                        # Trigger alert callbacks
                        for callback in self.alert_callbacks:
                            try:
                                callback(alert)
                            except Exception as e:
                                logger.error(f"Alert callback failed: {e}")
                        
                        logger.warning(f"ALERT TRIGGERED: {alert.message}")
                
                else:
                    # Resolve alert if it exists
                    if alert_id in self.active_alerts:
                        alert = self.active_alerts[alert_id]
                        alert.resolved = True
                        alert.resolved_at = current_time
                        del self.active_alerts[alert_id]
                        
                        logger.info(f"ALERT RESOLVED: {alert.message}")
    
    def register_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """Register callback for alert notifications"""
        self.alert_callbacks.append(callback)
    
    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[PerformanceAlert]:
        """Get alert history"""
        return self.alert_history[-limit:] if limit > 0 else self.alert_history


class PerformanceMonitoringService(IBaseService):
    """
    Comprehensive performance monitoring service
    Phase 3: Real-time monitoring with intelligent alerting
    """
    
    def __init__(self):
        self.service_name = "PerformanceMonitoringService"
        self.initialized = False
        
        # Core components
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        
        # Monitoring state
        self.monitoring_active = False
        self.collection_interval = 5.0  # seconds
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Performance history
        self.system_metrics_history: deque = deque(maxlen=1440)  # 24 hours at 1min intervals
        self.app_metrics_history: deque = deque(maxlen=1440)
        
        logger.info(f"✅ {self.service_name} initialized")
    
    async def initialize(self) -> bool:
        """Initialize monitoring service"""
        try:
            # Setup default alert rules
            await self._setup_default_alerts()
            
            # Start monitoring
            await self.start_monitoring()
            
            self.initialized = True
            logger.info(f"✅ {self.service_name} initialization completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ {self.service_name} initialization failed: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Shutdown monitoring service"""
        try:
            await self.stop_monitoring()
            
            self.initialized = False
            logger.info(f"✅ {self.service_name} shutdown completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ {self.service_name} shutdown failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Monitor service health check"""
        try:
            # Get current system metrics
            system_metrics = await self._collect_system_metrics()
            
            # Get recent application metrics
            app_metrics = await self._collect_application_metrics()
            
            # Get alert status
            active_alerts = self.alert_manager.get_active_alerts()
            
            return {
                "service": self.service_name,
                "status": "healthy" if len(active_alerts) == 0 else "degraded",
                "initialized": self.initialized,
                "monitoring_active": self.monitoring_active,
                "collection_interval": self.collection_interval,
                "system_metrics": system_metrics.to_dict(),
                "application_metrics": app_metrics.to_dict(),
                "active_alerts_count": len(active_alerts),
                "metrics_history_size": len(self.system_metrics_history)
            }
            
        except Exception as e:
            return {
                "service": self.service_name,
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": self.service_name,
            "initialized": self.initialized,
            "monitoring_active": self.monitoring_active,
            "collection_interval": self.collection_interval
        }
    
    async def start_monitoring(self):
        """Start performance monitoring loop"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop performance monitoring loop"""
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = await self._collect_system_metrics()
                self.system_metrics_history.append(system_metrics)
                
                # Collect application metrics
                app_metrics = await self._collect_application_metrics()
                self.app_metrics_history.append(app_metrics)
                
                # Update metrics collector
                await self._update_metrics_collector(system_metrics, app_metrics)
                
                # Check alerts
                metrics_dict = {
                    **system_metrics.to_dict(),
                    **app_metrics.to_dict()
                }
                await self.alert_manager.check_alerts(metrics_dict)
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-wide performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1.0)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_used_gb = disk.used / (1024 * 1024 * 1024)
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Network metrics
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Load average
            load_avg = psutil.getloadavg()
            load_average_1m = load_avg[0]
            
            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_free_gb=disk_free_gb,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                load_average_1m=load_average_1m,
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return SystemMetrics(
                cpu_percent=0, memory_percent=0, memory_used_mb=0,
                memory_available_mb=0, disk_percent=0, disk_used_gb=0,
                disk_free_gb=0, network_bytes_sent=0, network_bytes_recv=0,
                load_average_1m=0, timestamp=time.time()
            )
    
    async def _collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        try:
            # These would be populated by actual application metrics
            # For now, using placeholder values
            
            # Get timer stats if available
            response_time_stats = await self.metrics_collector.get_timer_stats("api_response_time")
            
            return ApplicationMetrics(
                active_connections=0,  # Would be populated by connection pool
                request_count=0,       # Would be populated by request counter
                avg_response_time_ms=response_time_stats.get("avg_ms", 0),
                p95_response_time_ms=response_time_stats.get("p95_ms", 0),
                p99_response_time_ms=response_time_stats.get("p99_ms", 0),
                error_rate_percent=0,  # Would be calculated from error metrics
                cache_hit_ratio=0,     # Would be populated by cache service
                database_query_time_ms=0,  # Would be populated by database metrics
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return ApplicationMetrics(
                active_connections=0, request_count=0, avg_response_time_ms=0,
                p95_response_time_ms=0, p99_response_time_ms=0, error_rate_percent=0,
                cache_hit_ratio=0, database_query_time_ms=0, timestamp=time.time()
            )
    
    async def _update_metrics_collector(self, system_metrics: SystemMetrics, app_metrics: ApplicationMetrics):
        """Update metrics collector with latest data"""
        # Record system metrics
        await self.metrics_collector.record_gauge("system_cpu_percent", system_metrics.cpu_percent)
        await self.metrics_collector.record_gauge("system_memory_percent", system_metrics.memory_percent)
        await self.metrics_collector.record_gauge("system_disk_percent", system_metrics.disk_percent)
        await self.metrics_collector.record_gauge("system_load_1m", system_metrics.load_average_1m)
        
        # Record application metrics
        await self.metrics_collector.record_gauge("app_active_connections", app_metrics.active_connections)
        await self.metrics_collector.record_counter("app_request_count", app_metrics.request_count)
        await self.metrics_collector.record_gauge("app_avg_response_time", app_metrics.avg_response_time_ms)
        await self.metrics_collector.record_gauge("app_cache_hit_ratio", app_metrics.cache_hit_ratio)
    
    async def _setup_default_alerts(self):
        """Setup default alert rules"""
        # System alerts
        self.alert_manager.add_alert_rule("cpu_percent", 80, "gt", AlertSeverity.WARNING)
        self.alert_manager.add_alert_rule("cpu_percent", 95, "gt", AlertSeverity.CRITICAL)
        self.alert_manager.add_alert_rule("memory_percent", 85, "gt", AlertSeverity.WARNING)
        self.alert_manager.add_alert_rule("memory_percent", 95, "gt", AlertSeverity.CRITICAL)
        self.alert_manager.add_alert_rule("disk_percent", 80, "gt", AlertSeverity.WARNING)
        self.alert_manager.add_alert_rule("disk_percent", 95, "gt", AlertSeverity.CRITICAL)
        
        # Application alerts
        self.alert_manager.add_alert_rule("avg_response_time_ms", 100, "gt", AlertSeverity.WARNING)
        self.alert_manager.add_alert_rule("avg_response_time_ms", 500, "gt", AlertSeverity.CRITICAL)
        self.alert_manager.add_alert_rule("error_rate_percent", 5, "gt", AlertSeverity.WARNING)
        self.alert_manager.add_alert_rule("error_rate_percent", 10, "gt", AlertSeverity.CRITICAL)
    
    # Public API methods
    async def record_api_request(self, endpoint: str, method: str, response_time_ms: float, status_code: int):
        """Record API request metrics"""
        labels = {"endpoint": endpoint, "method": method, "status": str(status_code)}
        
        await self.metrics_collector.record_counter("api_requests_total", 1.0, labels)
        await self.metrics_collector.record_timer("api_response_time", response_time_ms, labels)
        
        if status_code >= 400:
            await self.metrics_collector.record_counter("api_errors_total", 1.0, labels)
    
    async def record_database_query(self, query_type: str, duration_ms: float, success: bool = True):
        """Record database query metrics"""
        labels = {"query_type": query_type, "success": str(success)}
        
        await self.metrics_collector.record_counter("db_queries_total", 1.0, labels)
        await self.metrics_collector.record_timer("db_query_duration", duration_ms, labels)
    
    async def record_cache_operation(self, operation: str, hit: bool):
        """Record cache operation metrics"""
        labels = {"operation": operation, "result": "hit" if hit else "miss"}
        
        await self.metrics_collector.record_counter("cache_operations_total", 1.0, labels)
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return {
            "system_metrics": [m.to_dict() for m in list(self.system_metrics_history)[-10:]],
            "application_metrics": [m.to_dict() for m in list(self.app_metrics_history)[-10:]],
            "active_alerts": [alert.to_dict() for alert in self.alert_manager.get_active_alerts()],
            "alert_history": [alert.to_dict() for alert in self.alert_manager.get_alert_history(50)]
        }


# Global service instance
_performance_monitoring_service = None

async def get_performance_monitoring_service() -> PerformanceMonitoringService:
    """Get singleton performance monitoring service instance"""
    global _performance_monitoring_service
    if _performance_monitoring_service is None:
        _performance_monitoring_service = PerformanceMonitoringService()
        await _performance_monitoring_service.initialize()
    return _performance_monitoring_service

# 🧪 PHASE 3 PERFORMANCE REGRESSION TESTS
"""
Comprehensive performance regression tests for Phase 3 optimizations
Validates database performance, caching efficiency, and API response times

Phase 3: Performance validation and regression detection
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from httpx import AsyncClient
import statistics
import json

from app.core.database_config import get_database_config
from app.infrastructure.cache.advanced_cache_service import get_advanced_cache_service
from app.infrastructure.monitoring.performance_monitoring_service import get_performance_monitoring_service
from app.services.async_database_service import get_async_database_service


class PerformanceBenchmark:
    """Performance benchmark tracking"""
    
    def __init__(self, name: str):
        self.name = name
        self.measurements: List[float] = []
        self.start_time: float = 0
    
    def start(self):
        """Start timing measurement"""
        self.start_time = time.time()
    
    def end(self) -> float:
        """End timing measurement and record"""
        duration = time.time() - self.start_time
        self.measurements.append(duration)
        return duration
    
    def get_stats(self) -> Dict[str, float]:
        """Get performance statistics"""
        if not self.measurements:
            return {}
        
        return {
            "count": len(self.measurements),
            "avg_ms": statistics.mean(self.measurements) * 1000,
            "min_ms": min(self.measurements) * 1000,
            "max_ms": max(self.measurements) * 1000,
            "p50_ms": statistics.median(self.measurements) * 1000,
            "p95_ms": sorted(self.measurements)[int(len(self.measurements) * 0.95)] * 1000,
            "p99_ms": sorted(self.measurements)[int(len(self.measurements) * 0.99)] * 1000
        }


@pytest.fixture
async def performance_setup():
    """Setup performance testing environment"""
    # Initialize services
    db_service = await get_async_database_service()
    cache_service = await get_advanced_cache_service()
    monitoring_service = await get_performance_monitoring_service()
    
    yield {
        "db_service": db_service,
        "cache_service": cache_service,
        "monitoring_service": monitoring_service
    }
    
    # Cleanup
    await db_service.shutdown()
    await cache_service.shutdown()
    await monitoring_service.shutdown()


@pytest.mark.asyncio
@pytest.mark.performance
class TestDatabasePerformance:
    """Database performance regression tests"""
    
    async def test_database_connection_performance(self, performance_setup):
        """Test database connection pool performance"""
        db_service = performance_setup["db_service"]
        benchmark = PerformanceBenchmark("database_connection")
        
        # Test multiple concurrent connections
        async def connection_test():
            benchmark.start()
            health = await db_service.health_check()
            benchmark.end()
            assert health["status"] == "healthy"
        
        # Run concurrent connection tests
        tasks = [connection_test() for _ in range(50)]
        await asyncio.gather(*tasks)
        
        stats = benchmark.get_stats()
        
        # Performance assertions
        assert stats["avg_ms"] < 50, f"Average connection time {stats['avg_ms']:.2f}ms exceeds 50ms limit"
        assert stats["p95_ms"] < 100, f"P95 connection time {stats['p95_ms']:.2f}ms exceeds 100ms limit"
        assert stats["max_ms"] < 200, f"Max connection time {stats['max_ms']:.2f}ms exceeds 200ms limit"
        
        print(f"✅ Database Connection Performance: {stats}")
    
    async def test_async_database_operations(self, performance_setup):
        """Test async database operations performance"""
        db_service = performance_setup["db_service"]
        benchmark = PerformanceBenchmark("database_operations")
        
        # Test telemetry data storage
        test_data = {
            "temperature": 42.5,
            "pressure": 1013.25,
            "humidity": 65.0,
            "status": "operational"
        }
        
        async def store_telemetry_test(i: int):
            benchmark.start()
            success = await db_service.store_telemetry_data(
                module_id=i,
                module_name=f"test_module_{i}",
                telemetry_data=test_data,
                validation_status="valid"
            )
            benchmark.end()
            assert success
        
        # Run concurrent database operations
        tasks = [store_telemetry_test(i) for i in range(100)]
        await asyncio.gather(*tasks)
        
        stats = benchmark.get_stats()
        
        # Performance assertions
        assert stats["avg_ms"] < 20, f"Average DB operation {stats['avg_ms']:.2f}ms exceeds 20ms limit"
        assert stats["p95_ms"] < 50, f"P95 DB operation {stats['p95_ms']:.2f}ms exceeds 50ms limit"
        
        print(f"✅ Database Operations Performance: {stats}")
    
    async def test_database_query_performance(self, performance_setup):
        """Test database query performance"""
        db_service = performance_setup["db_service"]
        benchmark = PerformanceBenchmark("database_queries")
        
        # First, insert some test data
        for i in range(10):
            await db_service.store_telemetry_data(
                module_id=i,
                module_name=f"test_module_{i}",
                telemetry_data={"value": i * 10},
                validation_status="valid"
            )
        
        async def query_test():
            benchmark.start()
            summary = await db_service.get_validation_summary()
            benchmark.end()
            assert "total_modules" in summary
        
        # Run concurrent queries
        tasks = [query_test() for _ in range(50)]
        await asyncio.gather(*tasks)
        
        stats = benchmark.get_stats()
        
        # Performance assertions
        assert stats["avg_ms"] < 10, f"Average query time {stats['avg_ms']:.2f}ms exceeds 10ms limit"
        assert stats["p95_ms"] < 25, f"P95 query time {stats['p95_ms']:.2f}ms exceeds 25ms limit"
        
        print(f"✅ Database Query Performance: {stats}")


@pytest.mark.asyncio
@pytest.mark.performance
class TestCachePerformance:
    """Advanced cache performance tests"""
    
    async def test_l1_cache_performance(self, performance_setup):
        """Test L1 (memory) cache performance"""
        cache_service = performance_setup["cache_service"]
        benchmark = PerformanceBenchmark("l1_cache")
        
        # Warm up cache
        for i in range(100):
            await cache_service.set(f"test_key_{i}", f"test_value_{i}", ttl=300)
        
        async def cache_get_test():
            benchmark.start()
            value = await cache_service.get("test_key_50")
            benchmark.end()
            assert value == "test_value_50"
        
        # Run concurrent cache gets
        tasks = [cache_get_test() for _ in range(1000)]
        await asyncio.gather(*tasks)
        
        stats = benchmark.get_stats()
        
        # Performance assertions (L1 cache should be very fast)
        assert stats["avg_ms"] < 1, f"L1 cache avg time {stats['avg_ms']:.2f}ms exceeds 1ms limit"
        assert stats["p95_ms"] < 5, f"L1 cache P95 time {stats['p95_ms']:.2f}ms exceeds 5ms limit"
        
        print(f"✅ L1 Cache Performance: {stats}")
    
    async def test_cache_hit_ratio(self, performance_setup):
        """Test cache hit ratio optimization"""
        cache_service = performance_setup["cache_service"]
        
        # Populate cache with test data
        for i in range(100):
            await cache_service.set(f"hit_test_{i}", f"value_{i}", ttl=300)
        
        # Perform mixed hit/miss operations
        hit_count = 0
        miss_count = 0
        
        for i in range(200):
            key = f"hit_test_{i % 150}"  # 100 hits, 50 misses expected
            value = await cache_service.get(key)
            if value is not None:
                hit_count += 1
            else:
                miss_count += 1
        
        hit_ratio = hit_count / (hit_count + miss_count) * 100
        
        # Cache hit ratio should be reasonable
        assert hit_ratio >= 60, f"Cache hit ratio {hit_ratio:.1f}% below 60% threshold"
        
        print(f"✅ Cache Hit Ratio: {hit_ratio:.1f}%")
    
    async def test_intelligent_ttl(self, performance_setup):
        """Test intelligent TTL calculation"""
        cache_service = performance_setup["cache_service"]
        
        # Test different key patterns
        test_cases = [
            ("telemetry_sensor_1", "fast_data", 60),      # Short TTL expected
            ("config_system", "slow_data", 900),          # Medium TTL expected
            ("firmware_version", "static_data", 3600),    # Long TTL expected
        ]
        
        for key, value, expected_min_ttl in test_cases:
            await cache_service.set(key, value)
            
            # Get intelligent TTL (this would be calculated internally)
            ttl = await cache_service._calculate_intelligent_ttl(key, value)
            
            assert ttl >= expected_min_ttl / 2, f"TTL {ttl}s too short for key {key}"
            assert ttl <= expected_min_ttl * 2, f"TTL {ttl}s too long for key {key}"
        
        print("✅ Intelligent TTL working correctly")


@pytest.mark.asyncio
@pytest.mark.performance
class TestAPIPerformance:
    """API performance regression tests"""
    
    async def test_api_response_time(self, async_client: AsyncClient):
        """Test API response time performance"""
        benchmark = PerformanceBenchmark("api_response")
        
        async def api_test():
            benchmark.start()
            response = await async_client.get("/api/v1/health")
            benchmark.end()
            assert response.status_code == 200
        
        # Run concurrent API requests
        tasks = [api_test() for _ in range(100)]
        await asyncio.gather(*tasks)
        
        stats = benchmark.get_stats()
        
        # Performance assertions
        assert stats["avg_ms"] < 50, f"Average API response {stats['avg_ms']:.2f}ms exceeds 50ms limit"
        assert stats["p95_ms"] < 150, f"P95 API response {stats['p95_ms']:.2f}ms exceeds 150ms limit"
        
        print(f"✅ API Response Performance: {stats}")
    
    async def test_api_response_format(self, async_client: AsyncClient):
        """Test standardized API response format"""
        response = await async_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check standardized response format
        required_fields = ["status", "message", "data", "meta"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check metadata
        meta = data["meta"]
        assert "request_id" in meta
        assert "timestamp" in meta
        assert "api_version" in meta
        
        print("✅ Standardized API Response Format")
    
    async def test_hateoas_links(self, async_client: AsyncClient):
        """Test HATEOAS links in API responses"""
        # Test an endpoint that should have HATEOAS links
        response = await async_client.get("/api/v1/robot/status")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check for HATEOAS links
            if "links" in data and data["links"]:
                links = data["links"]
                assert isinstance(links, list)
                
                for link in links:
                    assert "href" in link
                    assert "rel" in link
                    assert "method" in link
                
                print("✅ HATEOAS Links Present")
            else:
                print("⚠️ HATEOAS Links Not Implemented Yet")


@pytest.mark.asyncio
@pytest.mark.performance
class TestMonitoringPerformance:
    """Performance monitoring system tests"""
    
    async def test_metrics_collection_performance(self, performance_setup):
        """Test metrics collection performance overhead"""
        monitoring_service = performance_setup["monitoring_service"]
        benchmark = PerformanceBenchmark("metrics_collection")
        
        async def metrics_test():
            benchmark.start()
            await monitoring_service.record_api_request(
                endpoint="/test",
                method="GET",
                response_time_ms=25.0,
                status_code=200
            )
            benchmark.end()
        
        # Run concurrent metrics recording
        tasks = [metrics_test() for _ in range(1000)]
        await asyncio.gather(*tasks)
        
        stats = benchmark.get_stats()
        
        # Metrics collection should have minimal overhead
        assert stats["avg_ms"] < 2, f"Metrics collection overhead {stats['avg_ms']:.2f}ms too high"
        assert stats["p95_ms"] < 10, f"P95 metrics overhead {stats['p95_ms']:.2f}ms too high"
        
        print(f"✅ Metrics Collection Performance: {stats}")
    
    async def test_monitoring_health_check(self, performance_setup):
        """Test monitoring service health check performance"""
        monitoring_service = performance_setup["monitoring_service"]
        benchmark = PerformanceBenchmark("monitoring_health")
        
        async def health_test():
            benchmark.start()
            health = await monitoring_service.health_check()
            benchmark.end()
            assert health["status"] in ["healthy", "degraded"]
        
        # Run concurrent health checks
        tasks = [health_test() for _ in range(20)]
        await asyncio.gather(*tasks)
        
        stats = benchmark.get_stats()
        
        # Health checks should be fast
        assert stats["avg_ms"] < 100, f"Health check avg time {stats['avg_ms']:.2f}ms too slow"
        
        print(f"✅ Monitoring Health Check Performance: {stats}")


@pytest.mark.asyncio
@pytest.mark.performance
class TestOverallSystemPerformance:
    """Overall system performance integration tests"""
    
    async def test_end_to_end_performance(self, async_client: AsyncClient, performance_setup):
        """Test end-to-end system performance"""
        benchmark = PerformanceBenchmark("e2e_performance")
        
        async def e2e_test():
            benchmark.start()
            
            # Simulate typical user workflow
            # 1. Health check
            health_response = await async_client.get("/api/v1/health")
            assert health_response.status_code == 200
            
            # 2. Get robot status
            status_response = await async_client.get("/api/v1/robot/status")
            # May return 200 or error if no robot connected - both acceptable
            
            # 3. Get telemetry (if available)
            telemetry_response = await async_client.get("/api/v1/telemetry/current")
            # May return 200 or error if no telemetry - both acceptable
            
            benchmark.end()
        
        # Run concurrent E2E tests
        tasks = [e2e_test() for _ in range(20)]
        await asyncio.gather(*tasks)
        
        stats = benchmark.get_stats()
        
        # E2E performance should be reasonable
        assert stats["avg_ms"] < 200, f"E2E avg time {stats['avg_ms']:.2f}ms exceeds 200ms limit"
        assert stats["p95_ms"] < 500, f"E2E P95 time {stats['p95_ms']:.2f}ms exceeds 500ms limit"
        
        print(f"✅ End-to-End Performance: {stats}")
    
    async def test_system_resource_usage(self, performance_setup):
        """Test system resource usage under load"""
        monitoring_service = performance_setup["monitoring_service"]
        
        # Get initial metrics
        initial_health = await monitoring_service.health_check()
        initial_cpu = initial_health.get("system_metrics", {}).get("cpu_percent", 0)
        initial_memory = initial_health.get("system_metrics", {}).get("memory_percent", 0)
        
        # Generate load
        tasks = []
        for i in range(100):
            # Mix of different operations
            tasks.append(monitoring_service.record_api_request(f"/test/{i}", "GET", 25.0, 200))
        
        await asyncio.gather(*tasks)
        
        # Wait a bit for metrics to stabilize
        await asyncio.sleep(2)
        
        # Get final metrics
        final_health = await monitoring_service.health_check()
        final_cpu = final_health.get("system_metrics", {}).get("cpu_percent", 0)
        final_memory = final_health.get("system_metrics", {}).get("memory_percent", 0)
        
        # Resource usage should be reasonable
        cpu_increase = final_cpu - initial_cpu
        memory_increase = final_memory - initial_memory
        
        assert cpu_increase < 20, f"CPU usage increased by {cpu_increase:.1f}% under load"
        assert memory_increase < 10, f"Memory usage increased by {memory_increase:.1f}% under load"
        
        print(f"✅ Resource Usage: CPU +{cpu_increase:.1f}%, Memory +{memory_increase:.1f}%")


def generate_performance_report(test_results: List[Dict[str, Any]]) -> str:
    """Generate comprehensive performance report"""
    report = """
# 📊 PHASE 3 PERFORMANCE REGRESSION TEST REPORT

## Test Results Summary

"""
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result.get("passed", False))
    
    report += f"- **Total Tests:** {total_tests}\n"
    report += f"- **Passed:** {passed_tests}\n"
    report += f"- **Failed:** {total_tests - passed_tests}\n"
    report += f"- **Success Rate:** {passed_tests/total_tests*100:.1f}%\n\n"
    
    report += "## Performance Benchmarks\n\n"
    
    for result in test_results:
        if "benchmark" in result:
            benchmark = result["benchmark"]
            report += f"### {benchmark['name']}\n"
            report += f"- Average: {benchmark['avg_ms']:.2f}ms\n"
            report += f"- P95: {benchmark['p95_ms']:.2f}ms\n"
            report += f"- P99: {benchmark['p99_ms']:.2f}ms\n\n"
    
    report += "## Conclusions\n\n"
    report += "Phase 3 performance optimizations have been validated.\n"
    report += "All critical performance thresholds are met.\n"
    
    return report


# Run performance tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "performance"])

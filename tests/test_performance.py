"""
Performance and caching system tests for B-TCRimer.
Tests caching functionality, database optimization, and performance monitoring.
"""

import pytest
import time
import tempfile
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.cache_manager import CacheManager, cached
from utils.performance_monitor import PerformanceMonitor
from utils.db_optimizer import ConnectionPool, QueryOptimizer

class TestCacheManager:
    """Test suite for caching system"""
    
    @pytest.fixture
    def cache_manager(self):
        """Create fresh cache manager for each test"""
        return CacheManager()
    
    def test_basic_caching(self, cache_manager):
        """Test basic cache set/get operations"""
        key = "test_key"
        value = {"data": "test_value", "number": 42}
        
        # Test set
        result = cache_manager.set(key, value, ttl=60)
        assert result is True
        
        # Test get
        cached_value = cache_manager.get(key)
        assert cached_value == value
        
        # Test non-existent key
        non_existent = cache_manager.get("non_existent_key")
        assert non_existent is None
    
    def test_cache_expiration(self, cache_manager):
        """Test cache TTL and expiration"""
        key = "expire_test"
        value = "expires_soon"
        
        # Set with 1 second TTL
        cache_manager.set(key, value, ttl=1)
        
        # Should be available immediately
        cached_value = cache_manager.get(key)
        assert cached_value == value
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired now
        expired_value = cache_manager.get(key)
        assert expired_value is None
    
    def test_cache_with_parameters(self, cache_manager):
        """Test parameterized caching"""
        key = "param_test"
        value1 = "value1"
        value2 = "value2"
        
        # Cache with different parameters
        cache_manager.set(key, value1, params={"param": "A"})
        cache_manager.set(key, value2, params={"param": "B"})
        
        # Retrieve with parameters
        cached_value1 = cache_manager.get(key, params={"param": "A"})
        cached_value2 = cache_manager.get(key, params={"param": "B"})
        
        assert cached_value1 == value1
        assert cached_value2 == value2
    
    def test_cache_deletion(self, cache_manager):
        """Test cache deletion"""
        key = "delete_test"
        value = "to_be_deleted"
        
        # Set and verify
        cache_manager.set(key, value)
        assert cache_manager.get(key) == value
        
        # Delete and verify
        result = cache_manager.delete(key)
        assert result is True
        assert cache_manager.get(key) is None
    
    def test_cache_stats(self, cache_manager):
        """Test cache statistics"""
        # Perform some cache operations
        cache_manager.set("key1", "value1")
        cache_manager.set("key2", "value2")
        
        # Generate hits and misses
        cache_manager.get("key1")  # Hit
        cache_manager.get("key2")  # Hit
        cache_manager.get("nonexistent")  # Miss
        
        stats = cache_manager.get_stats()
        
        assert stats['hits'] >= 2
        assert stats['misses'] >= 1
        assert stats['total_requests'] >= 3
        assert stats['session_items'] >= 2
    
    def test_cache_decorator(self):
        """Test caching decorator functionality"""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x * y
        
        # First call should execute function
        result1 = expensive_function(5, 10)
        assert result1 == 50
        assert call_count == 1
        
        # Second call should use cache
        result2 = expensive_function(5, 10)
        assert result2 == 50
        assert call_count == 1  # Should not increment
        
        # Different parameters should execute function again
        result3 = expensive_function(3, 7)
        assert result3 == 21
        assert call_count == 2

class TestPerformanceMonitor:
    """Test suite for performance monitoring"""
    
    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor for testing"""
        return PerformanceMonitor(max_samples=100)
    
    def test_response_time_tracking(self, performance_monitor):
        """Test response time tracking"""
        page = "test_page"
        response_time = 1.5
        
        # Track response time
        performance_monitor.track_response_time(page, response_time)
        
        # Verify tracking
        assert len(performance_monitor.metrics['response_times']) == 1
        assert page in performance_monitor.metrics['page_loads']
        
        page_stats = performance_monitor.metrics['page_loads'][page]
        assert page_stats['count'] == 1
        assert page_stats['avg_time'] == response_time
    
    def test_function_call_tracking(self, performance_monitor):
        """Test function performance tracking"""
        function_name = "test_function"
        execution_time = 0.5
        
        # Track function call
        performance_monitor.track_function_call(function_name, execution_time)
        
        # Verify tracking
        assert function_name in performance_monitor.metrics['function_calls']
        
        func_stats = performance_monitor.metrics['function_calls'][function_name]
        assert func_stats['calls'] == 1
        assert func_stats['avg_time'] == execution_time
    
    def test_performance_summary(self, performance_monitor):
        """Test performance summary generation"""
        # Add some test data
        performance_monitor.track_response_time("page1", 1.0)
        performance_monitor.track_response_time("page2", 2.5)  # Slow
        performance_monitor.track_error("TestError", "Test error message", "page1")
        
        # Get summary
        summary = performance_monitor.get_performance_summary(1)
        
        assert summary['total_requests'] == 2
        assert summary['slow_requests'] == 1  # page2 is slow
        assert summary['error_count'] == 1
        assert len(summary['performance_issues']) >= 0

class TestDatabaseOptimizer:
    """Test suite for database optimization"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database file"""
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        yield db_path
        os.close(db_fd)
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_connection_pool(self, temp_db_path):
        """Test database connection pool"""
        pool = ConnectionPool(database_path=temp_db_path, pool_size=3)
        
        # Test getting connection
        with pool.get_connection() as conn:
            assert conn is not None
            # Test basic query
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
        
        # Test pool statistics
        stats = pool.get_stats()
        assert stats['pool_size'] == 3
        assert stats['total_created'] >= 1
    
    def test_query_optimizer(self, temp_db_path):
        """Test query optimization and monitoring"""
        pool = ConnectionPool(database_path=temp_db_path, pool_size=2)
        optimizer = QueryOptimizer(pool)
        
        # Create test table
        optimizer.execute_query("""
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                value INTEGER
            )
        """, fetch='none')
        
        # Test insert
        optimizer.execute_query(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            ("test", 42),
            fetch='none'
        )
        
        # Test select
        result = optimizer.execute_query(
            "SELECT name, value FROM test_table WHERE name = ?",
            ("test",),
            fetch='one'
        )
        
        assert result is not None
        assert result[0] == "test"
        assert result[1] == 42
        
        # Test batch operation
        batch_data = [("item1", 1), ("item2", 2), ("item3", 3)]
        rows_affected = optimizer.execute_batch(
            "INSERT INTO test_table (name, value) VALUES (?, ?)",
            batch_data
        )
        
        assert rows_affected == 3
        
        # Check query statistics
        stats = optimizer.get_query_stats()
        assert len(stats) > 0

class TestIntegrationScenarios:
    """Test integration scenarios combining multiple systems"""
    
    def test_cached_database_queries(self):
        """Test caching of database query results"""
        cache_manager = CacheManager()
        
        @cached(ttl=60)
        def get_user_data(user_id):
            # Simulate database query
            time.sleep(0.1)  # Simulate query time
            return {"user_id": user_id, "name": f"User {user_id}"}
        
        # First call - should execute query
        start_time = time.time()
        result1 = get_user_data(123)
        first_call_time = time.time() - start_time
        
        # Second call - should use cache
        start_time = time.time()
        result2 = get_user_data(123)
        second_call_time = time.time() - start_time
        
        # Results should be identical
        assert result1 == result2
        
        # Second call should be much faster
        assert second_call_time < first_call_time
        assert second_call_time < 0.05  # Should be near-instantaneous
    
    def test_performance_monitoring_with_caching(self):
        """Test performance monitoring with cached functions"""
        performance_monitor = PerformanceMonitor()
        
        call_count = 0
        
        def monitored_cached_function(x):
            nonlocal call_count
            call_count += 1
            start_time = time.time()
            
            # Simulate work
            time.sleep(0.1)
            result = x * 2
            
            execution_time = time.time() - start_time
            performance_monitor.track_function_call(
                "monitored_cached_function",
                execution_time
            )
            
            return result
        
        # Apply caching
        cached_function = cached(ttl=60)(monitored_cached_function)
        
        # First call
        result1 = cached_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # Second call (cached)
        result2 = cached_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment
        
        # Verify performance tracking
        assert "monitored_cached_function" in performance_monitor.metrics['function_calls']

def run_performance_tests():
    """Run all performance tests manually"""
    print("🧪 Running Performance & Caching Tests...")
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    try:
        # Test 1: Basic Caching
        print("  Testing basic caching...")
        cache_manager = CacheManager()
        
        cache_manager.set("test_key", {"data": "test"}, ttl=60)
        cached_value = cache_manager.get("test_key")
        
        assert cached_value == {"data": "test"}
        
        test_results['passed'] += 1
        print("  ✅ Basic caching test passed")
        
    except Exception as e:
        test_results['failed'] += 1
        test_results['errors'].append(f"Basic caching: {str(e)}")
        print(f"  ❌ Basic caching test failed: {str(e)}")
    
    try:
        # Test 2: Cache Decorator
        print("  Testing cache decorator...")
        
        call_count = 0
        
        @cached(ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        result1 = test_function(5)
        result2 = test_function(5)
        
        assert result1 == result2 == 10
        assert call_count == 1  # Should only be called once
        
        test_results['passed'] += 1
        print("  ✅ Cache decorator test passed")
        
    except Exception as e:
        test_results['failed'] += 1
        test_results['errors'].append(f"Cache decorator: {str(e)}")
        print(f"  ❌ Cache decorator test failed: {str(e)}")
    
    try:
        # Test 3: Performance Monitoring
        print("  Testing performance monitoring...")
        
        monitor = PerformanceMonitor(max_samples=50)
        
        monitor.track_response_time("test_page", 1.5)
        monitor.track_function_call("test_function", 0.5)
        
        summary = monitor.get_performance_summary(1)
        
        assert summary['total_requests'] == 1
        assert "test_function" in monitor.metrics['function_calls']
        
        test_results['passed'] += 1
        print("  ✅ Performance monitoring test passed")
        
    except Exception as e:
        test_results['failed'] += 1
        test_results['errors'].append(f"Performance monitoring: {str(e)}")
        print(f"  ❌ Performance monitoring test failed: {str(e)}")
    
    # Print results
    print(f"\n🧪 Performance Test Results:")
    print(f"  ✅ Passed: {test_results['passed']}")
    print(f"  ❌ Failed: {test_results['failed']}")
    
    if test_results['errors']:
        print(f"  🚨 Errors:")
        for error in test_results['errors']:
            print(f"    - {error}")
    
    return test_results

if __name__ == "__main__":
    run_performance_tests()
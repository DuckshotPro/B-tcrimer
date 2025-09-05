"""
Database optimization and connection pooling system for B-TCRimer.
Implements connection pooling, query optimization, and database maintenance.
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from queue import Queue, Empty
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

class ConnectionPool:
    """High-performance database connection pool"""
    
    def __init__(self, database_path: str = None, pool_size: int = 10, timeout: int = 30):
        self.database_path = database_path or 'sql_app.db'
        self.pool_size = pool_size
        self.timeout = timeout
        self.pool = Queue(maxsize=pool_size)
        self.active_connections = 0
        self.total_connections_created = 0
        self.pool_stats = {
            'connections_requested': 0,
            'connections_returned': 0,
            'timeouts': 0,
            'active_connections': 0
        }
        self._lock = threading.RLock()
        
        # Initialize pool
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool with connections"""
        try:
            for _ in range(self.pool_size):
                conn = self._create_connection()
                if conn:
                    self.pool.put(conn)
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {str(e)}")
    
    def _create_connection(self) -> Optional[sqlite3.Connection]:
        """Create optimized database connection"""
        try:
            conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,
                timeout=self.timeout,
                isolation_level=None  # Autocommit mode for better performance
            )
            
            # Optimize connection settings
            conn.execute("PRAGMA journal_mode=WAL")  # Write-ahead logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes
            conn.execute("PRAGMA cache_size=10000")  # 10MB cache
            conn.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
            conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory mapping
            
            self.total_connections_created += 1
            logger.debug(f"Created optimized database connection #{self.total_connections_created}")
            
            return conn
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {str(e)}")
            return None
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool with automatic return"""
        conn = None
        try:
            with self._lock:
                self.pool_stats['connections_requested'] += 1
            
            try:
                conn = self.pool.get(timeout=self.timeout)
                with self._lock:
                    self.active_connections += 1
                    self.pool_stats['active_connections'] = self.active_connections
                
                # Test connection
                conn.execute("SELECT 1")
                
                yield conn
                
            except Empty:
                # Pool is empty, create new connection
                with self._lock:
                    self.pool_stats['timeouts'] += 1
                
                logger.warning("Connection pool exhausted, creating temporary connection")
                conn = self._create_connection()
                if conn:
                    yield conn
                else:
                    raise Exception("Failed to create database connection")
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
            raise
        
        finally:
            if conn:
                try:
                    # Return connection to pool if there's space
                    if not self.pool.full():
                        self.pool.put(conn)
                        with self._lock:
                            self.pool_stats['connections_returned'] += 1
                    else:
                        conn.close()
                    
                    with self._lock:
                        self.active_connections = max(0, self.active_connections - 1)
                        self.pool_stats['active_connections'] = self.active_connections
                
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {str(e)}")
    
    def close_all(self):
        """Close all connections in pool"""
        try:
            while not self.pool.empty():
                try:
                    conn = self.pool.get_nowait()
                    conn.close()
                except Empty:
                    break
                except Exception as e:
                    logger.error(f"Error closing pooled connection: {str(e)}")
            
            logger.info("All database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing connection pool: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._lock:
            return {
                'pool_size': self.pool_size,
                'active_connections': self.active_connections,
                'available_connections': self.pool.qsize(),
                'total_created': self.total_connections_created,
                'connections_requested': self.pool_stats['connections_requested'],
                'connections_returned': self.pool_stats['connections_returned'],
                'timeouts': self.pool_stats['timeouts']
            }

class QueryOptimizer:
    """Database query optimization and monitoring"""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.connection_pool = connection_pool
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # 1 second
        
    def execute_query(self, query: str, params: Tuple = None, fetch: str = 'all') -> Any:
        """Execute optimized query with performance monitoring"""
        start_time = time.time()
        query_hash = hash(query.strip().lower())
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Fetch results based on type
                if fetch == 'all':
                    result = cursor.fetchall()
                elif fetch == 'one':
                    result = cursor.fetchone()
                elif fetch == 'many':
                    result = cursor.fetchmany(100)  # Limit to 100 rows
                else:
                    result = cursor.rowcount
                
                execution_time = time.time() - start_time
                
                # Update query statistics
                self._update_query_stats(query_hash, query, execution_time)
                
                # Log slow queries
                if execution_time > self.slow_query_threshold:
                    logger.warning(f"Slow query detected ({execution_time:.2f}s): {query[:100]}...")
                
                return result
                
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_query_stats(query_hash, query, execution_time, error=str(e))
            logger.error(f"Query execution error ({execution_time:.2f}s): {str(e)}")
            raise
    
    def execute_batch(self, query: str, param_list: List[Tuple]) -> int:
        """Execute batch operations for better performance"""
        start_time = time.time()
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, param_list)
                
                execution_time = time.time() - start_time
                logger.info(f"Batch operation completed: {len(param_list)} rows in {execution_time:.2f}s")
                
                return cursor.rowcount
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Batch operation error ({execution_time:.2f}s): {str(e)}")
            raise
    
    def _update_query_stats(self, query_hash: int, query: str, execution_time: float, error: str = None):
        """Update query performance statistics"""
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                'query': query[:100] + '...' if len(query) > 100 else query,
                'executions': 0,
                'total_time': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'errors': 0,
                'last_error': None
            }
        
        stats = self.query_stats[query_hash]
        stats['executions'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['executions']
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        
        if error:
            stats['errors'] += 1
            stats['last_error'] = error
    
    def get_query_stats(self) -> List[Dict[str, Any]]:
        """Get query performance statistics"""
        return sorted(
            self.query_stats.values(),
            key=lambda x: x['avg_time'],
            reverse=True
        )
    
    def optimize_database(self) -> Dict[str, Any]:
        """Perform database optimization operations"""
        results = {
            'vacuum_completed': False,
            'analyze_completed': False,
            'reindex_completed': False,
            'old_data_cleaned': 0,
            'optimization_time': 0
        }
        
        start_time = time.time()
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                # VACUUM to reclaim space and defragment
                logger.info("Starting database VACUUM operation...")
                cursor.execute("VACUUM")
                results['vacuum_completed'] = True
                
                # ANALYZE to update query planner statistics
                logger.info("Starting database ANALYZE operation...")
                cursor.execute("ANALYZE")
                results['analyze_completed'] = True
                
                # REINDEX to rebuild indexes
                logger.info("Starting database REINDEX operation...")
                cursor.execute("REINDEX")
                results['reindex_completed'] = True
                
                # Clean old data (older than 30 days)
                cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
                
                # Clean old error logs
                cursor.execute("""
                    DELETE FROM error_logs 
                    WHERE timestamp < ? AND resolved = 1
                """, (cutoff_date,))
                old_errors_cleaned = cursor.rowcount
                
                # Clean old system health logs (keep only last 7 days)
                health_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
                cursor.execute("""
                    DELETE FROM system_health_logs 
                    WHERE timestamp < ?
                """, (health_cutoff,))
                old_health_cleaned = cursor.rowcount
                
                results['old_data_cleaned'] = old_errors_cleaned + old_health_cleaned
                
                results['optimization_time'] = time.time() - start_time
                
                logger.info(f"Database optimization completed in {results['optimization_time']:.2f}s")
                logger.info(f"Cleaned {results['old_data_cleaned']} old records")
                
        except Exception as e:
            logger.error(f"Database optimization failed: {str(e)}")
            results['error'] = str(e)
        
        return results
    
    def create_indexes(self) -> Dict[str, bool]:
        """Create performance indexes"""
        indexes = {
            'users_username_idx': 'CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)',
            'users_email_idx': 'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
            'error_logs_timestamp_idx': 'CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp)',
            'error_logs_severity_idx': 'CREATE INDEX IF NOT EXISTS idx_error_logs_severity ON error_logs(severity)',
            'system_health_timestamp_idx': 'CREATE INDEX IF NOT EXISTS idx_health_timestamp ON system_health_logs(timestamp)'
        }
        
        results = {}
        
        try:
            with self.connection_pool.get_connection() as conn:
                cursor = conn.cursor()
                
                for index_name, index_sql in indexes.items():
                    try:
                        cursor.execute(index_sql)
                        results[index_name] = True
                        logger.info(f"Created index: {index_name}")
                    except Exception as e:
                        results[index_name] = False
                        logger.error(f"Failed to create index {index_name}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Index creation failed: {str(e)}")
        
        return results

class DatabaseMaintenance:
    """Automated database maintenance system"""
    
    def __init__(self, connection_pool: ConnectionPool):
        self.connection_pool = connection_pool
        self.last_maintenance = None
        self.maintenance_interval = 24 * 60 * 60  # 24 hours
    
    def should_run_maintenance(self) -> bool:
        """Check if maintenance should run"""
        if not self.last_maintenance:
            return True
        
        return (datetime.now() - self.last_maintenance).total_seconds() > self.maintenance_interval
    
    def run_maintenance(self) -> Dict[str, Any]:
        """Run automated database maintenance"""
        if not self.should_run_maintenance():
            return {'skipped': True, 'reason': 'Too soon since last maintenance'}
        
        logger.info("Starting automated database maintenance...")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'tasks_completed': [],
            'errors': []
        }
        
        try:
            optimizer = QueryOptimizer(self.connection_pool)
            
            # Run optimization
            opt_results = optimizer.optimize_database()
            if 'error' not in opt_results:
                results['tasks_completed'].append('optimization')
                results['optimization_results'] = opt_results
            else:
                results['errors'].append(f"Optimization failed: {opt_results['error']}")
            
            # Create/update indexes
            index_results = optimizer.create_indexes()
            successful_indexes = sum(1 for success in index_results.values() if success)
            if successful_indexes > 0:
                results['tasks_completed'].append('indexes')
                results['indexes_created'] = successful_indexes
            
            # Update last maintenance time
            self.last_maintenance = datetime.now()
            
            results['end_time'] = datetime.now().isoformat()
            results['success'] = True
            
            logger.info(f"Database maintenance completed. Tasks: {', '.join(results['tasks_completed'])}")
            
        except Exception as e:
            results['errors'].append(f"Maintenance failed: {str(e)}")
            results['success'] = False
            logger.error(f"Database maintenance failed: {str(e)}")
        
        return results

# Global instances
connection_pool = ConnectionPool()
query_optimizer = QueryOptimizer(connection_pool)
db_maintenance = DatabaseMaintenance(connection_pool)

def get_optimized_connection():
    """Get optimized database connection from pool"""
    return connection_pool.get_connection()

def execute_optimized_query(query: str, params: Tuple = None, fetch: str = 'all') -> Any:
    """Execute query with optimization and monitoring"""
    return query_optimizer.execute_query(query, params, fetch)

def show_database_performance_dashboard():
    """Display database performance dashboard for admins"""
    import streamlit as st
    
    st.markdown("### 🗄️ Database Performance")
    
    # Connection pool stats
    pool_stats = connection_pool.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Active Connections",
            pool_stats['active_connections'],
            help="Currently active database connections"
        )
    
    with col2:
        st.metric(
            "Available Connections",
            pool_stats['available_connections'],
            help="Connections available in the pool"
        )
    
    with col3:
        st.metric(
            "Total Requests",
            f"{pool_stats['connections_requested']:,}",
            help="Total connection requests"
        )
    
    with col4:
        st.metric(
            "Pool Timeouts",
            pool_stats['timeouts'],
            delta_color="inverse",
            help="Number of connection timeouts"
        )
    
    # Query performance stats
    st.markdown("#### Query Performance")
    
    query_stats = query_optimizer.get_query_stats()
    if query_stats:
        # Show top 10 slowest queries
        slow_queries = query_stats[:10]
        
        import pandas as pd
        df = pd.DataFrame([{
            'Query': stat['query'],
            'Executions': stat['executions'],
            'Avg Time (s)': f"{stat['avg_time']:.3f}",
            'Max Time (s)': f"{stat['max_time']:.3f}",
            'Errors': stat['errors']
        } for stat in slow_queries])
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No query statistics available yet")
    
    # Maintenance actions
    st.markdown("#### Database Maintenance")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔧 Optimize Database"):
            with st.spinner("Optimizing database..."):
                results = query_optimizer.optimize_database()
                if 'error' not in results:
                    st.success(f"Optimization completed in {results['optimization_time']:.2f}s")
                    if results['old_data_cleaned'] > 0:
                        st.info(f"Cleaned {results['old_data_cleaned']} old records")
                else:
                    st.error(f"Optimization failed: {results['error']}")
    
    with col2:
        if st.button("📊 Create Indexes"):
            with st.spinner("Creating database indexes..."):
                results = query_optimizer.create_indexes()
                successful = sum(1 for success in results.values() if success)
                if successful > 0:
                    st.success(f"Created {successful} database indexes")
                else:
                    st.error("Failed to create indexes")
    
    with col3:
        if st.button("🔄 Run Maintenance"):
            with st.spinner("Running database maintenance..."):
                results = db_maintenance.run_maintenance()
                if results.get('success'):
                    st.success(f"Maintenance completed. Tasks: {', '.join(results['tasks_completed'])}")
                else:
                    st.error(f"Maintenance failed: {'; '.join(results.get('errors', []))}")
    
    # Show last maintenance info
    if db_maintenance.last_maintenance:
        st.info(f"Last maintenance: {db_maintenance.last_maintenance.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.warning("Database maintenance has never been run")
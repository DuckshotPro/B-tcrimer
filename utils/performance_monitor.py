"""
Performance monitoring and optimization system for B-TCRimer.
Tracks response times, memory usage, and provides performance insights.
"""

import streamlit as st
import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from collections import deque
from utils.logging_config import get_logger

logger = get_logger(__name__)

class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""
    
    def __init__(self, max_samples: int = 1000):
        self.max_samples = max_samples
        self.metrics = {
            'response_times': deque(maxlen=max_samples),
            'memory_usage': deque(maxlen=max_samples),
            'cpu_usage': deque(maxlen=max_samples),
            'function_calls': {},
            'page_loads': {},
            'user_sessions': {},
            'errors': deque(maxlen=max_samples)
        }
        self.performance_thresholds = {
            'slow_response_time': 2.0,  # seconds
            'high_memory_usage': 80.0,  # percent
            'high_cpu_usage': 80.0      # percent
        }
        self._lock = threading.RLock()
        
        # Start background monitoring
        self._start_system_monitoring()
    
    def _start_system_monitoring(self):
        """Start background system resource monitoring"""
        def monitor_system():
            while True:
                try:
                    # Get system metrics
                    memory_percent = psutil.virtual_memory().percent
                    cpu_percent = psutil.cpu_percent(interval=1)
                    
                    timestamp = datetime.now()
                    
                    with self._lock:
                        self.metrics['memory_usage'].append({
                            'timestamp': timestamp,
                            'value': memory_percent
                        })
                        
                        self.metrics['cpu_usage'].append({
                            'timestamp': timestamp,
                            'value': cpu_percent
                        })
                    
                    # Check for performance issues
                    if memory_percent > self.performance_thresholds['high_memory_usage']:
                        logger.warning(f"High memory usage detected: {memory_percent:.1f}%")
                    
                    if cpu_percent > self.performance_thresholds['high_cpu_usage']:
                        logger.warning(f"High CPU usage detected: {cpu_percent:.1f}%")
                    
                    time.sleep(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    logger.error(f"System monitoring error: {str(e)}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = threading.Thread(target=monitor_system, daemon=True)
        monitor_thread.start()
    
    def track_response_time(self, page: str, response_time: float):
        """Track page response time"""
        with self._lock:
            timestamp = datetime.now()
            
            self.metrics['response_times'].append({
                'timestamp': timestamp,
                'page': page,
                'response_time': response_time
            })
            
            # Update page load statistics
            if page not in self.metrics['page_loads']:
                self.metrics['page_loads'][page] = {
                    'count': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'slow_loads': 0
                }
            
            stats = self.metrics['page_loads'][page]
            stats['count'] += 1
            stats['total_time'] += response_time
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['min_time'] = min(stats['min_time'], response_time)
            stats['max_time'] = max(stats['max_time'], response_time)
            
            if response_time > self.performance_thresholds['slow_response_time']:
                stats['slow_loads'] += 1
                logger.warning(f"Slow page load detected: {page} took {response_time:.2f}s")
    
    def track_function_call(self, function_name: str, execution_time: float, args_hash: str = ""):
        """Track function execution performance"""
        with self._lock:
            key = f"{function_name}:{args_hash}" if args_hash else function_name
            
            if key not in self.metrics['function_calls']:
                self.metrics['function_calls'][key] = {
                    'function': function_name,
                    'calls': 0,
                    'total_time': 0,
                    'avg_time': 0,
                    'min_time': float('inf'),
                    'max_time': 0,
                    'slow_calls': 0
                }
            
            stats = self.metrics['function_calls'][key]
            stats['calls'] += 1
            stats['total_time'] += execution_time
            stats['avg_time'] = stats['total_time'] / stats['calls']
            stats['min_time'] = min(stats['min_time'], execution_time)
            stats['max_time'] = max(stats['max_time'], execution_time)
            
            if execution_time > 1.0:  # 1 second threshold for functions
                stats['slow_calls'] += 1
    
    def track_user_session(self, user_id: str, action: str):
        """Track user session activity"""
        with self._lock:
            if user_id not in self.metrics['user_sessions']:
                self.metrics['user_sessions'][user_id] = {
                    'first_seen': datetime.now(),
                    'last_seen': datetime.now(),
                    'actions': 0,
                    'pages_visited': set()
                }
            
            session = self.metrics['user_sessions'][user_id]
            session['last_seen'] = datetime.now()
            session['actions'] += 1
            session['pages_visited'].add(action)
    
    def track_error(self, error_type: str, error_message: str, page: str = ""):
        """Track application errors for performance impact analysis"""
        with self._lock:
            self.metrics['errors'].append({
                'timestamp': datetime.now(),
                'error_type': error_type,
                'error_message': error_message,
                'page': page
            })
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the last N hours"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Filter recent metrics
            recent_response_times = [
                r for r in self.metrics['response_times']
                if r['timestamp'] > cutoff_time
            ]
            
            recent_memory_usage = [
                m for m in self.metrics['memory_usage']
                if m['timestamp'] > cutoff_time
            ]
            
            recent_cpu_usage = [
                c for c in self.metrics['cpu_usage']
                if c['timestamp'] > cutoff_time
            ]
            
            recent_errors = [
                e for e in self.metrics['errors']
                if e['timestamp'] > cutoff_time
            ]
            
            # Calculate summary statistics
            summary = {
                'time_period': f"Last {hours} hour(s)",
                'total_requests': len(recent_response_times),
                'avg_response_time': 0,
                'slow_requests': 0,
                'avg_memory_usage': 0,
                'avg_cpu_usage': 0,
                'error_count': len(recent_errors),
                'active_users': len([
                    s for s in self.metrics['user_sessions'].values()
                    if s['last_seen'] > cutoff_time
                ]),
                'performance_issues': []
            }
            
            if recent_response_times:
                response_times = [r['response_time'] for r in recent_response_times]
                summary['avg_response_time'] = sum(response_times) / len(response_times)
                summary['slow_requests'] = len([
                    r for r in response_times
                    if r > self.performance_thresholds['slow_response_time']
                ])
            
            if recent_memory_usage:
                memory_values = [m['value'] for m in recent_memory_usage]
                summary['avg_memory_usage'] = sum(memory_values) / len(memory_values)
                
                if summary['avg_memory_usage'] > self.performance_thresholds['high_memory_usage']:
                    summary['performance_issues'].append('High memory usage detected')
            
            if recent_cpu_usage:
                cpu_values = [c['value'] for c in recent_cpu_usage]
                summary['avg_cpu_usage'] = sum(cpu_values) / len(cpu_values)
                
                if summary['avg_cpu_usage'] > self.performance_thresholds['high_cpu_usage']:
                    summary['performance_issues'].append('High CPU usage detected')
            
            if summary['slow_requests'] > summary['total_requests'] * 0.1:  # More than 10% slow
                summary['performance_issues'].append('High number of slow requests')
            
            if summary['error_count'] > 10:  # More than 10 errors per hour
                summary['performance_issues'].append('High error rate detected')
            
            return summary
    
    def get_top_slow_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top slowest function calls"""
        with self._lock:
            sorted_functions = sorted(
                self.metrics['function_calls'].values(),
                key=lambda x: x['avg_time'],
                reverse=True
            )
            return sorted_functions[:limit]
    
    def get_page_performance(self) -> List[Dict[str, Any]]:
        """Get page performance statistics"""
        with self._lock:
            return sorted(
                self.metrics['page_loads'].values(),
                key=lambda x: x['avg_time'],
                reverse=True
            )
    
    def clear_metrics(self):
        """Clear all performance metrics"""
        with self._lock:
            self.metrics['response_times'].clear()
            self.metrics['function_calls'].clear()
            self.metrics['page_loads'].clear()
            self.metrics['user_sessions'].clear()
            self.metrics['errors'].clear()
            logger.info("Performance metrics cleared")

def performance_monitor(monitor_instance: PerformanceMonitor = None):
    """Decorator for monitoring function performance"""
    if monitor_instance is None:
        monitor_instance = PerformanceMonitor()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Create args hash for caching differentiation
                args_hash = str(hash(str(args) + str(sorted(kwargs.items()))))[:8]
                
                monitor_instance.track_function_call(
                    func.__name__, 
                    execution_time, 
                    args_hash
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                monitor_instance.track_error(
                    type(e).__name__,
                    str(e),
                    func.__name__
                )
                raise
        
        return wrapper
    return decorator

class PageLoadTimer:
    """Context manager for tracking page load times"""
    
    def __init__(self, page_name: str, monitor_instance: PerformanceMonitor = None):
        self.page_name = page_name
        self.monitor = monitor_instance or performance_monitor_instance
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            load_time = time.time() - self.start_time
            self.monitor.track_response_time(self.page_name, load_time)

def show_performance_dashboard():
    """Display comprehensive performance dashboard"""
    st.markdown("### ⚡ Performance Monitoring")
    
    # Get performance summary
    summary_1h = performance_monitor_instance.get_performance_summary(1)
    summary_24h = performance_monitor_instance.get_performance_summary(24)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Avg Response Time",
            f"{summary_1h['avg_response_time']:.2f}s",
            delta=f"{summary_1h['avg_response_time'] - summary_24h['avg_response_time']:+.2f}s",
            delta_color="inverse",
            help="Average response time for the last hour"
        )
    
    with col2:
        st.metric(
            "Active Users",
            summary_1h['active_users'],
            delta=summary_1h['active_users'] - summary_24h['active_users'],
            help="Currently active users"
        )
    
    with col3:
        st.metric(
            "Memory Usage",
            f"{summary_1h['avg_memory_usage']:.1f}%",
            delta=f"{summary_1h['avg_memory_usage'] - summary_24h['avg_memory_usage']:+.1f}%",
            delta_color="inverse",
            help="Average memory usage"
        )
    
    with col4:
        st.metric(
            "Error Rate",
            f"{summary_1h['error_count']}/hr",
            delta=summary_1h['error_count'] - summary_24h['error_count'],
            delta_color="inverse",
            help="Errors in the last hour"
        )
    
    # Performance issues alerts
    if summary_1h['performance_issues']:
        st.warning("⚠️ Performance Issues Detected:")
        for issue in summary_1h['performance_issues']:
            st.write(f"• {issue}")
    else:
        st.success("✅ No performance issues detected")
    
    # Detailed performance metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🐌 Slowest Functions")
        slow_functions = performance_monitor_instance.get_top_slow_functions(5)
        
        if slow_functions:
            import pandas as pd
            df = pd.DataFrame([{
                'Function': func['function'],
                'Avg Time (s)': f"{func['avg_time']:.3f}",
                'Calls': func['calls'],
                'Slow Calls': func['slow_calls']
            } for func in slow_functions])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No function performance data available")
    
    with col2:
        st.markdown("#### 📄 Page Performance")
        page_stats = performance_monitor_instance.get_page_performance()
        
        if page_stats:
            import pandas as pd
            df = pd.DataFrame([{
                'Page': list(performance_monitor_instance.metrics['page_loads'].keys())[i],
                'Avg Time (s)': f"{page['avg_time']:.3f}",
                'Loads': page['count'],
                'Slow Loads': page['slow_loads']
            } for i, page in enumerate(page_stats[:5])])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No page performance data available")
    
    # Performance actions
    st.markdown("#### Performance Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Clear Metrics"):
            performance_monitor_instance.clear_metrics()
            st.success("Performance metrics cleared")
            st.rerun()
    
    with col2:
        if st.button("📊 Generate Report"):
            st.info("Performance report generation would be implemented here")
    
    with col3:
        if st.button("🚀 Optimize Performance"):
            st.info("Performance optimization tools would be implemented here")

# Create global performance monitor instance
performance_monitor_instance = PerformanceMonitor()

# Helper function to track page loads
def track_page_load(page_name: str):
    """Helper to track page loads in Streamlit apps"""
    return PageLoadTimer(page_name, performance_monitor_instance)
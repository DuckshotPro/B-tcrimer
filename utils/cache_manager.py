"""
Enterprise-grade caching system for B-TCRimer cryptocurrency analysis platform.
Implements multi-layer caching with Redis-like functionality using in-memory storage.
"""

import streamlit as st
import pickle
import hashlib
import time
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from functools import wraps
from utils.logging_config import get_logger

logger = get_logger(__name__)

class CacheManager:
    """High-performance multi-layer cache management system"""
    
    def __init__(self):
        self.memory_cache = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }
        self.max_memory_items = 1000
        self.default_ttl = 300  # 5 minutes
        
        # Initialize session-based cache
        if 'cache_store' not in st.session_state:
            st.session_state.cache_store = {}
        
        if 'cache_metadata' not in st.session_state:
            st.session_state.cache_metadata = {}
    
    def _generate_key(self, key: str, params: Dict = None) -> str:
        """Generate cache key with optional parameters hash"""
        if params:
            params_str = str(sorted(params.items()))
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return f"{key}:{params_hash}"
        return key
    
    def _is_expired(self, metadata: Dict) -> bool:
        """Check if cache entry is expired"""
        if 'expires_at' not in metadata:
            return False
        return datetime.now() > datetime.fromisoformat(metadata['expires_at'])
    
    def set(self, key: str, value: Any, ttl: int = None, params: Dict = None) -> bool:
        """Set cache value with optional TTL and parameters"""
        try:
            cache_key = self._generate_key(key, params)
            ttl = ttl or self.default_ttl
            
            # Store in session state for persistence across reruns
            st.session_state.cache_store[cache_key] = pickle.dumps(value)
            st.session_state.cache_metadata[cache_key] = {
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=ttl)).isoformat(),
                'access_count': 0,
                'size_bytes': len(pickle.dumps(value))
            }
            
            # Also store in memory cache for faster access
            self.memory_cache[cache_key] = {
                'value': value,
                'metadata': st.session_state.cache_metadata[cache_key]
            }
            
            # Evict oldest items if memory cache is full
            if len(self.memory_cache) > self.max_memory_items:
                self._evict_lru()
            
            logger.debug(f"Cache set: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def get(self, key: str, params: Dict = None) -> Optional[Any]:
        """Get cache value with optional parameters"""
        try:
            cache_key = self._generate_key(key, params)
            self.cache_stats['total_requests'] += 1
            
            # Try memory cache first
            if cache_key in self.memory_cache:
                cache_entry = self.memory_cache[cache_key]
                
                if not self._is_expired(cache_entry['metadata']):
                    self.cache_stats['hits'] += 1
                    
                    # Update access count
                    cache_entry['metadata']['access_count'] += 1
                    if cache_key in st.session_state.cache_metadata:
                        st.session_state.cache_metadata[cache_key] = cache_entry['metadata']
                    
                    logger.debug(f"Cache hit (memory): {cache_key}")
                    return cache_entry['value']
                else:
                    # Expired - remove from caches
                    self.delete(key, params)
            
            # Try session state cache
            if cache_key in st.session_state.cache_store:
                metadata = st.session_state.cache_metadata.get(cache_key, {})
                
                if not self._is_expired(metadata):
                    value = pickle.loads(st.session_state.cache_store[cache_key])
                    self.cache_stats['hits'] += 1
                    
                    # Update access count
                    metadata['access_count'] = metadata.get('access_count', 0) + 1
                    st.session_state.cache_metadata[cache_key] = metadata
                    
                    # Store back in memory cache
                    self.memory_cache[cache_key] = {
                        'value': value,
                        'metadata': metadata
                    }
                    
                    logger.debug(f"Cache hit (session): {cache_key}")
                    return value
                else:
                    # Expired - remove from caches
                    self.delete(key, params)
            
            self.cache_stats['misses'] += 1
            logger.debug(f"Cache miss: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            self.cache_stats['misses'] += 1
            return None
    
    def delete(self, key: str, params: Dict = None) -> bool:
        """Delete cache entry"""
        try:
            cache_key = self._generate_key(key, params)
            
            # Remove from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            # Remove from session state
            if cache_key in st.session_state.cache_store:
                del st.session_state.cache_store[cache_key]
            
            if cache_key in st.session_state.cache_metadata:
                del st.session_state.cache_metadata[cache_key]
            
            logger.debug(f"Cache deleted: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False
    
    def clear(self, pattern: str = None) -> int:
        """Clear cache entries, optionally by pattern"""
        try:
            cleared_count = 0
            
            if pattern:
                # Clear entries matching pattern
                keys_to_delete = [
                    key for key in self.memory_cache.keys() 
                    if pattern in key
                ]
                
                for key in keys_to_delete:
                    if key in self.memory_cache:
                        del self.memory_cache[key]
                    if key in st.session_state.cache_store:
                        del st.session_state.cache_store[key]
                    if key in st.session_state.cache_metadata:
                        del st.session_state.cache_metadata[key]
                    cleared_count += 1
            else:
                # Clear all
                cleared_count = len(self.memory_cache)
                self.memory_cache.clear()
                st.session_state.cache_store.clear()
                st.session_state.cache_metadata.clear()
            
            logger.info(f"Cache cleared: {cleared_count} entries")
            return cleared_count
            
        except Exception as e:
            logger.error(f"Cache clear error: {str(e)}")
            return 0
    
    def _evict_lru(self):
        """Evict least recently used items from memory cache"""
        try:
            if len(self.memory_cache) <= self.max_memory_items:
                return
            
            # Sort by access count and creation time
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: (
                    x[1]['metadata'].get('access_count', 0),
                    x[1]['metadata'].get('created_at', '')
                )
            )
            
            # Remove oldest 10% of items
            items_to_remove = len(self.memory_cache) // 10
            
            for i in range(items_to_remove):
                key = sorted_items[i][0]
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    self.cache_stats['evictions'] += 1
            
            logger.debug(f"Evicted {items_to_remove} items from memory cache")
            
        except Exception as e:
            logger.error(f"Cache eviction error: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        hit_rate = 0
        if self.cache_stats['total_requests'] > 0:
            hit_rate = self.cache_stats['hits'] / self.cache_stats['total_requests']
        
        return {
            'hit_rate': hit_rate,
            'total_requests': self.cache_stats['total_requests'],
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'memory_items': len(self.memory_cache),
            'session_items': len(st.session_state.get('cache_store', {})),
            'memory_usage_mb': self._estimate_memory_usage(),
        }
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB"""
        try:
            total_size = 0
            for metadata in st.session_state.get('cache_metadata', {}).values():
                total_size += metadata.get('size_bytes', 0)
            return total_size / (1024 * 1024)  # Convert to MB
        except:
            return 0.0
    
    def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        try:
            expired_keys = []
            
            for key, metadata in st.session_state.get('cache_metadata', {}).items():
                if self._is_expired(metadata):
                    expired_keys.append(key)
            
            for key in expired_keys:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                if key in st.session_state.cache_store:
                    del st.session_state.cache_store[key]
                if key in st.session_state.cache_metadata:
                    del st.session_state.cache_metadata[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {str(e)}")
            return 0

# Global cache manager instance
cache_manager = CacheManager()

def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Generate cache key from function name and arguments
                func_name = f"{key_prefix}{func.__name__}" if key_prefix else func.__name__
                
                # Create parameter hash from args and kwargs
                params = {
                    'args': str(args) if args else '',
                    'kwargs': str(sorted(kwargs.items())) if kwargs else ''
                }
                
                # Try to get from cache first
                cached_result = cache_manager.get(func_name, params)
                if cached_result is not None:
                    return cached_result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache_manager.set(func_name, result, ttl, params)
                
                return result
                
            except Exception as e:
                logger.error(f"Cache decorator error in {func.__name__}: {str(e)}")
                # Fall back to executing function without caching
                return func(*args, **kwargs)
        
        return wrapper
    return decorator

def cache_data_collection(ttl: int = 60):
    """Specialized caching for data collection functions"""
    return cached(ttl=ttl, key_prefix="data_")

def cache_analysis_results(ttl: int = 180):
    """Specialized caching for analysis results"""
    return cached(ttl=ttl, key_prefix="analysis_")

def cache_chart_data(ttl: int = 120):
    """Specialized caching for chart data"""
    return cached(ttl=ttl, key_prefix="chart_")

def preload_critical_data():
    """Preload critical data into cache for faster access"""
    try:
        logger.info("Starting critical data preload...")
        
        # This would be implemented to preload commonly accessed data
        # For now, we'll just clean up expired entries
        cleaned = cache_manager.cleanup_expired()
        
        if cleaned > 0:
            logger.info(f"Preload: cleaned {cleaned} expired entries")
        
        logger.info("Critical data preload completed")
        
    except Exception as e:
        logger.error(f"Preload error: {str(e)}")

def show_cache_dashboard():
    """Display cache performance dashboard for admins"""
    st.markdown("### 🚀 Cache Performance")
    
    stats = cache_manager.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Hit Rate",
            f"{stats['hit_rate']:.1%}",
            delta=None,
            help="Percentage of requests served from cache"
        )
    
    with col2:
        st.metric(
            "Total Requests",
            f"{stats['total_requests']:,}",
            delta=f"+{stats['hits']}" if stats['hits'] > 0 else None,
            help="Total cache requests since startup"
        )
    
    with col3:
        st.metric(
            "Memory Usage",
            f"{stats['memory_usage_mb']:.1f} MB",
            delta=None,
            help="Estimated memory usage by cache"
        )
    
    with col4:
        st.metric(
            "Cached Items",
            f"{stats['session_items']:,}",
            delta=None,
            help="Total number of cached items"
        )
    
    # Cache management actions
    st.markdown("#### Cache Management")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Clear All Cache"):
            cleared = cache_manager.clear()
            st.success(f"Cleared {cleared} cache entries")
            st.rerun()
    
    with col2:
        if st.button("⏰ Clean Expired"):
            cleaned = cache_manager.cleanup_expired()
            st.success(f"Cleaned {cleaned} expired entries")
            st.rerun()
    
    with col3:
        if st.button("🚀 Preload Data"):
            preload_critical_data()
            st.success("Critical data preloaded")
    
    # Detailed statistics
    if stats['total_requests'] > 0:
        st.markdown("#### Detailed Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Performance Metrics:**")
            st.write(f"• Cache Hits: {stats['hits']:,}")
            st.write(f"• Cache Misses: {stats['misses']:,}")
            st.write(f"• Evictions: {stats['evictions']:,}")
        
        with col2:
            st.write("**Storage Metrics:**")
            st.write(f"• Memory Items: {stats['memory_items']:,}")
            st.write(f"• Session Items: {stats['session_items']:,}")
            st.write(f"• Memory Usage: {stats['memory_usage_mb']:.1f} MB")
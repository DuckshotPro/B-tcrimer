"""
Enterprise-grade error handling and monitoring system for B-TCRimer.
Provides comprehensive error tracking, user-friendly error displays, and system health monitoring.
"""

import streamlit as st
import traceback
import functools
import time
import psutil
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from utils.logging_config import get_logger
from database.operations import get_db_connection

logger = get_logger(__name__)

class ErrorHandler:
    """Centralized error handling and monitoring system"""
    
    def __init__(self):
        self.error_count = 0
        self.last_error_time = None
        self.system_health = {
            'status': 'healthy',
            'last_check': datetime.now(),
            'errors_24h': 0,
            'memory_usage': 0,
            'cpu_usage': 0,
            'disk_usage': 0
        }
        self._initialize_error_tracking()
    
    def _initialize_error_tracking(self):
        """Initialize error tracking database table"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    stack_trace TEXT,
                    user_id INTEGER,
                    session_id TEXT,
                    page TEXT,
                    severity TEXT DEFAULT 'error',
                    resolved BOOLEAN DEFAULT 0,
                    resolution_notes TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_health_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    memory_usage REAL,
                    cpu_usage REAL,
                    disk_usage REAL,
                    active_users INTEGER,
                    error_rate REAL,
                    response_time REAL
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to initialize error tracking: {str(e)}")
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, severity: str = "error"):
        """Log error with full context and user information"""
        try:
            self.error_count += 1
            self.last_error_time = datetime.now()
            
            # Extract error information
            error_type = type(error).__name__
            error_message = str(error)
            stack_trace = traceback.format_exc()
            
            # Get user context
            user = st.session_state.get('user', {})
            user_id = user.get('id')
            session_id = st.session_state.get('session_token')
            
            # Get page context
            current_page = st.session_state.get('current_page', 'unknown')
            
            # Store in database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO error_logs 
                (error_type, error_message, stack_trace, user_id, session_id, page, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (error_type, error_message, stack_trace, user_id, session_id, current_page, severity))
            
            conn.commit()
            conn.close()
            
            # Log to application logger
            logger.error(f"Error logged: {error_type} - {error_message}", extra={
                'user_id': user_id,
                'session_id': session_id,
                'page': current_page,
                'context': context
            })
            
            # Update system health
            self._update_system_health()
            
        except Exception as e:
            logger.critical(f"Failed to log error: {str(e)}")
    
    def display_user_friendly_error(self, error: Exception, show_details: bool = False):
        """Display user-friendly error message"""
        error_type = type(error).__name__
        
        # Map technical errors to user-friendly messages
        user_friendly_messages = {
            'ConnectionError': {
                'title': '🔗 Connection Issue',
                'message': 'Having trouble connecting to data sources. Please check your internet connection and try again.',
                'suggestion': 'Try refreshing the page or check your network connection.'
            },
            'FileNotFoundError': {
                'title': '📁 Missing Resource',
                'message': 'Some required files are missing. This might be a temporary issue.',
                'suggestion': 'Please refresh the page or contact support if the problem persists.'
            },
            'KeyError': {
                'title': '⚙️ Configuration Issue',
                'message': 'There seems to be a configuration problem. Our team has been notified.',
                'suggestion': 'Please try refreshing the page or contact support.'
            },
            'ValueError': {
                'title': '📊 Data Processing Error',
                'message': 'Unable to process some data. This might be due to invalid input or data format.',
                'suggestion': 'Please check your input and try again.'
            },
            'PermissionError': {
                'title': '🔒 Access Denied',
                'message': 'You don\'t have permission to access this resource.',
                'suggestion': 'Please contact an administrator if you need access.'
            },
            'TimeoutError': {
                'title': '⏱️ Request Timeout',
                'message': 'The operation took too long to complete. This might be due to high server load.',
                'suggestion': 'Please try again in a few moments.'
            }
        }
        
        error_info = user_friendly_messages.get(error_type, {
            'title': '❌ Unexpected Error',
            'message': 'Something went wrong. Our team has been automatically notified.',
            'suggestion': 'Please try refreshing the page or contact support if the issue persists.'
        })
        
        # Display error card
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%); 
                    color: white; padding: 1.5rem; border-radius: 12px; margin: 1rem 0;
                    box-shadow: 0 8px 25px rgba(239, 68, 68, 0.3);">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <h3 style="margin: 0; font-size: 1.25rem;">{error_info['title']}</h3>
            </div>
            
            <p style="margin: 0 0 1rem 0; font-size: 1rem; line-height: 1.4;">
                {error_info['message']}
            </p>
            
            <div style="background: rgba(255, 255, 255, 0.1); border-radius: 8px; 
                        padding: 1rem; font-size: 0.875rem;">
                💡 <strong>Suggestion:</strong> {error_info['suggestion']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show technical details for developers/admins
        if show_details and st.session_state.get('user', {}).get('role') in ['admin', 'superadmin']:
            with st.expander("🔧 Technical Details (Admin Only)"):
                st.code(f"Error Type: {error_type}\nMessage: {str(error)}\n\nStack Trace:\n{traceback.format_exc()}")
        
        # Error reporting
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📧 Report Issue", key=f"report_{hash(str(error))}"):
                self._create_error_report(error)
                st.success("Issue reported! We'll investigate promptly.")
    
    def _create_error_report(self, error: Exception):
        """Create detailed error report for support team"""
        try:
            report = {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'user_info': st.session_state.get('user', {}),
                'session_info': {
                    'session_token': st.session_state.get('session_token'),
                    'current_page': st.session_state.get('current_page'),
                    'user_agent': st.experimental_get_query_params().get('user_agent', ['unknown'])[0]
                },
                'system_info': {
                    'memory_usage': self.system_health['memory_usage'],
                    'cpu_usage': self.system_health['cpu_usage']
                }
            }
            
            logger.info(f"Error report created: {report}")
            
        except Exception as e:
            logger.error(f"Failed to create error report: {str(e)}")
    
    def _update_system_health(self):
        """Update system health metrics"""
        try:
            # Get system metrics
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=1)
            disk_percent = psutil.disk_usage('/').percent
            
            # Count errors in last 24 hours
            conn = get_db_connection()
            cursor = conn.cursor()
            
            twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
            cursor.execute("""
                SELECT COUNT(*) FROM error_logs 
                WHERE timestamp > ? AND severity IN ('error', 'critical')
            """, (twenty_four_hours_ago,))
            
            errors_24h = cursor.fetchone()[0]
            
            # Update health status
            status = 'healthy'
            if errors_24h > 10 or memory_percent > 90 or cpu_percent > 90:
                status = 'warning'
            if errors_24h > 25 or memory_percent > 95 or cpu_percent > 95:
                status = 'critical'
            
            self.system_health.update({
                'status': status,
                'last_check': datetime.now(),
                'errors_24h': errors_24h,
                'memory_usage': memory_percent,
                'cpu_usage': cpu_percent,
                'disk_usage': disk_percent
            })
            
            # Log health metrics
            cursor.execute("""
                INSERT INTO system_health_logs 
                (memory_usage, cpu_usage, disk_usage, active_users, error_rate)
                VALUES (?, ?, ?, ?, ?)
            """, (memory_percent, cpu_percent, disk_percent, self._get_active_users(), errors_24h))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update system health: {str(e)}")
    
    def _get_active_users(self) -> int:
        """Get count of active users (simplified for demo)"""
        # In a real implementation, this would query active sessions
        return len([key for key in st.session_state.keys() if 'user' in key])
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status"""
        self._update_system_health()
        return self.system_health
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the specified time period"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            time_threshold = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Total errors
            cursor.execute("""
                SELECT COUNT(*) FROM error_logs WHERE timestamp > ?
            """, (time_threshold,))
            total_errors = cursor.fetchone()[0]
            
            # Errors by type
            cursor.execute("""
                SELECT error_type, COUNT(*) as count 
                FROM error_logs 
                WHERE timestamp > ? 
                GROUP BY error_type 
                ORDER BY count DESC
            """, (time_threshold,))
            errors_by_type = dict(cursor.fetchall())
            
            # Errors by page
            cursor.execute("""
                SELECT page, COUNT(*) as count 
                FROM error_logs 
                WHERE timestamp > ? 
                GROUP BY page 
                ORDER BY count DESC
                LIMIT 10
            """, (time_threshold,))
            errors_by_page = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_errors': total_errors,
                'errors_by_type': errors_by_type,
                'errors_by_page': errors_by_page,
                'time_period': f"Last {hours} hours"
            }
            
        except Exception as e:
            logger.error(f"Failed to get error stats: {str(e)}")
            return {}

def safe_execute(func: Callable, error_handler: ErrorHandler = None, show_error: bool = True):
    """Decorator for safe function execution with error handling"""
    if error_handler is None:
        error_handler = ErrorHandler()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_handler.log_error(e)
            if show_error:
                error_handler.display_user_friendly_error(e)
            return None
    
    return wrapper

def create_system_health_dashboard(error_handler: ErrorHandler):
    """Create admin dashboard for system health monitoring"""
    st.markdown("### 🏥 System Health Dashboard")
    
    health = error_handler.get_system_health()
    
    # Health status indicator
    status_colors = {
        'healthy': '#10B981',
        'warning': '#F59E0B', 
        'critical': '#EF4444'
    }
    
    status_icons = {
        'healthy': '✅',
        'warning': '⚠️',
        'critical': '🚨'
    }
    
    status = health['status']
    color = status_colors[status]
    icon = status_icons[status]
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {color} 0%, {color}CC 100%); 
                color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <h2 style="margin: 0; font-size: 1.5rem;">{icon} System Status: {status.title()}</h2>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9;">
                    Last updated: {health['last_check'].strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # System metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Memory Usage", f"{health['memory_usage']:.1f}%", 
                 delta=None, delta_color="inverse")
    
    with col2:
        st.metric("CPU Usage", f"{health['cpu_usage']:.1f}%", 
                 delta=None, delta_color="inverse")
    
    with col3:
        st.metric("Disk Usage", f"{health['disk_usage']:.1f}%", 
                 delta=None, delta_color="inverse")
    
    with col4:
        st.metric("Errors (24h)", health['errors_24h'], 
                 delta=None, delta_color="inverse")
    
    # Error statistics
    st.markdown("### 📊 Error Analytics")
    
    error_stats = error_handler.get_error_stats(24)
    
    if error_stats.get('total_errors', 0) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Errors by Type**")
            for error_type, count in error_stats.get('errors_by_type', {}).items():
                st.write(f"• {error_type}: {count}")
        
        with col2:
            st.markdown("**Errors by Page**")
            for page, count in error_stats.get('errors_by_page', {}).items():
                st.write(f"• {page}: {count}")
    else:
        st.success("🎉 No errors in the last 24 hours!")

# Global error handler instance
error_handler = ErrorHandler()
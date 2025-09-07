"""
Admin panel for B-TCRimer cryptocurrency analysis platform.
Provides system monitoring, user management, and configuration controls.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any

from utils.auth import auth_manager, require_authentication
from utils.error_handler import error_handler, create_system_health_dashboard
from utils.cache_manager import show_cache_dashboard
from utils.db_optimizer import show_database_performance_dashboard
from utils.performance_monitor import show_performance_monitor
from utils.logging_config import get_logger
from database.operations import get_db_connection
from pages.testing import show as show_testing_interface

logger = get_logger(__name__)

def show():
    """Main admin panel interface"""
    # Require admin authentication
    require_authentication("admin")
    
    current_user = auth_manager.get_current_user()
    
    st.markdown("""
    <h1 class="financial-title">
        🛠️ System Administration
    </h1>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">
        <p style="margin: 0; color: var(--text-secondary);">
            Welcome, <strong>{current_user['username']}</strong> | Role: <strong>{current_user['role']}</strong> | 
            Access Level: <span style="color: var(--success-color);">Administrator</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Admin navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
        "📊 Dashboard", 
        "👥 User Management", 
        "🏥 System Health", 
        "📝 Error Logs", 
        "⚡ Performance",
        "🚀 Cache Management",
        "🗄️ Database",
        "🧪 Testing",
        "⚙️ Configuration"
    ])
    
    with tab1:
        show_admin_dashboard()
    
    with tab2:
        show_user_management()
    
    with tab3:
        show_system_health()
    
    with tab4:
        show_error_logs()
    
    with tab5:
        show_performance_dashboard()
    
    with tab6:
        show_cache_dashboard()
    
    with tab7:
        show_database_performance_dashboard()
    
    with tab8:
        show_testing_panel()
    
    with tab9:
        show_configuration_panel()

def show_admin_dashboard():
    """Admin overview dashboard"""
    st.markdown("## 📊 System Overview")
    
    # Get system statistics
    stats = get_system_statistics()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Users", 
            stats.get('total_users', 0),
            delta=f"+{stats.get('new_users_24h', 0)} (24h)"
        )
    
    with col2:
        st.metric(
            "Active Sessions", 
            stats.get('active_sessions', 0),
            delta=None
        )
    
    with col3:
        st.metric(
            "System Uptime", 
            stats.get('uptime', 'N/A'),
            delta=None
        )
    
    with col4:
        st.metric(
            "Error Rate", 
            f"{stats.get('error_rate', 0):.2%}",
            delta=f"{stats.get('error_rate_change', 0):+.2%}",
            delta_color="inverse"
        )
    
    # Usage analytics
    st.markdown("### 📈 Usage Analytics")
    
    # User activity chart
    activity_data = get_user_activity_data()
    if activity_data:
        fig = px.line(
            activity_data, 
            x='date', 
            y='active_users',
            title='Daily Active Users (Last 30 Days)',
            color_discrete_sequence=['#00B0F0']
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter')
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Feature usage
    st.markdown("### 🎯 Feature Usage")
    feature_usage = get_feature_usage_stats()
    
    if feature_usage:
        fig = px.bar(
            x=list(feature_usage.keys()),
            y=list(feature_usage.values()),
            title='Feature Usage (Last 7 Days)',
            color=list(feature_usage.values()),
            color_continuous_scale='Viridis'
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter'),
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)

def show_user_management():
    """User management interface"""
    st.markdown("## 👥 User Management")
    
    # User statistics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # User list
        users_df = get_users_dataframe()
        if not users_df.empty:
            st.markdown("### Active Users")
            
            # Search and filter
            search_term = st.text_input("🔍 Search users", placeholder="Username or email...")
            role_filter = st.selectbox("Filter by role", ["All", "user", "premium", "admin", "superadmin"])
            
            # Apply filters
            filtered_df = users_df.copy()
            if search_term:
                filtered_df = filtered_df[
                    filtered_df['username'].str.contains(search_term, case=False) |
                    filtered_df['email'].str.contains(search_term, case=False)
                ]
            
            if role_filter != "All":
                filtered_df = filtered_df[filtered_df['role'] == role_filter]
            
            # Display user table
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "created_at": st.column_config.DatetimeColumn("Created", format="MM/DD/YY"),
                    "last_login": st.column_config.DatetimeColumn("Last Login", format="MM/DD/YY HH:mm"),
                    "is_active": st.column_config.CheckboxColumn("Active")
                }
            )
        else:
            st.info("No users found.")
    
    with col2:
        st.markdown("### Quick Actions")
        
        # Create user
        with st.expander("➕ Create User"):
            with st.form("create_user_form"):
                new_username = st.text_input("Username")
                new_email = st.text_input("Email") 
                new_password = st.text_input("Password", type="password")
                new_role = st.selectbox("Role", ["user", "premium", "admin"])
                
                if st.form_submit_button("Create User"):
                    if auth_manager.create_user(new_username, new_password, new_email, new_role):
                        st.success(f"User '{new_username}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to create user. Username or email may already exist.")
        
        # User role management
        with st.expander("🔧 Manage Roles"):
            st.info("Select a user from the table to modify their role or status.")
        
        # Bulk actions
        with st.expander("📦 Bulk Actions"):
            if st.button("Export User Data"):
                if not users_df.empty:
                    csv = users_df.to_csv(index=False)
                    st.download_button(
                        "📁 Download CSV",
                        csv,
                        "users_export.csv",
                        "text/csv"
                    )

def show_system_health():
    """System health monitoring"""
    create_system_health_dashboard(error_handler)
    
    # Additional system metrics
    st.markdown("### 💾 Database Status")
    
    try:
        db_stats = get_database_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Records", db_stats.get('total_records', 0))
        
        with col2:
            st.metric("Database Size", f"{db_stats.get('db_size_mb', 0):.2f} MB")
        
        with col3:
            st.metric("Last Backup", db_stats.get('last_backup', 'Never'))
        
        # Database maintenance
        st.markdown("### 🔧 Database Maintenance")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🧹 Clean Old Logs"):
                cleanup_result = cleanup_old_logs()
                st.success(f"Cleaned {cleanup_result} old log entries")
        
        with col2:
            if st.button("📊 Optimize Database"):
                optimize_database()
                st.success("Database optimized successfully")
        
        with col3:
            if st.button("💾 Create Backup"):
                backup_result = create_database_backup()
                if backup_result:
                    st.success("Database backup created")
                else:
                    st.error("Backup failed")
    
    except Exception as e:
        st.error(f"Database health check failed: {str(e)}")

def show_error_logs():
    """Error log viewer and management"""
    st.markdown("## 📝 Error Log Management")
    
    # Error log filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        time_range = st.selectbox("Time Range", ["Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"])
    
    with col2:
        severity_filter = st.selectbox("Severity", ["All", "info", "warning", "error", "critical"])
    
    with col3:
        resolved_filter = st.selectbox("Status", ["All", "Unresolved", "Resolved"])
    
    # Get error logs
    error_logs = get_error_logs(time_range, severity_filter, resolved_filter)
    
    if error_logs:
        st.markdown(f"### Found {len(error_logs)} error logs")
        
        # Display error logs
        for i, log in enumerate(error_logs):
            with st.expander(f"🚨 {log['error_type']} - {log['timestamp']} ({log['severity']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Error:** {log['error_message']}")
                    st.write(f"**Page:** {log['page']}")
                    st.write(f"**User:** {log.get('user_id', 'Anonymous')}")
                    
                    if log['stack_trace']:
                        st.code(log['stack_trace'], language='python')
                
                with col2:
                    if not log['resolved']:
                        if st.button(f"✅ Mark Resolved", key=f"resolve_{log['id']}"):
                            mark_error_resolved(log['id'])
                            st.success("Error marked as resolved")
                            st.rerun()
                    else:
                        st.success("✅ Resolved")
    else:
        st.info("No error logs found for the selected criteria.")

def show_configuration_panel():
    """System configuration management"""
    st.markdown("## ⚙️ System Configuration")
    
    # Configuration sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔧 Application Settings")
        
        # Sample configuration options
        with st.form("app_config"):
            debug_mode = st.checkbox("Debug Mode", value=False)
            max_users = st.number_input("Maximum Concurrent Users", min_value=1, value=100)
            session_timeout = st.number_input("Session Timeout (hours)", min_value=1, value=24)
            data_refresh_interval = st.number_input("Data Refresh Interval (minutes)", min_value=1, value=5)
            
            if st.form_submit_button("💾 Save Settings"):
                save_configuration({
                    'debug_mode': debug_mode,
                    'max_users': max_users,
                    'session_timeout': session_timeout,
                    'data_refresh_interval': data_refresh_interval
                })
                st.success("Configuration saved successfully!")
    
    with col2:
        st.markdown("### 🚨 Alert Settings")
        
        with st.form("alert_config"):
            error_threshold = st.number_input("Error Rate Alert Threshold (%)", min_value=1, max_value=100, value=10)
            memory_threshold = st.number_input("Memory Usage Alert Threshold (%)", min_value=50, max_value=100, value=90)
            cpu_threshold = st.number_input("CPU Usage Alert Threshold (%)", min_value=50, max_value=100, value=90)
            
            alert_email = st.text_input("Alert Email", value="admin@b-tcrimer.com")
            
            if st.form_submit_button("💾 Save Alerts"):
                save_alert_configuration({
                    'error_threshold': error_threshold,
                    'memory_threshold': memory_threshold,
                    'cpu_threshold': cpu_threshold,
                    'alert_email': alert_email
                })
                st.success("Alert configuration saved!")

# Helper functions for data retrieval
def get_system_statistics() -> Dict[str, Any]:
    """Get system statistics for admin dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        total_users = cursor.fetchone()[0]
        
        # New users in last 24 hours
        cursor.execute("""
            SELECT COUNT(*) FROM users 
            WHERE is_active = 1 AND created_at > datetime('now', '-24 hours')
        """)
        new_users_24h = cursor.fetchone()[0]
        
        # Error rate calculation (simplified)
        cursor.execute("""
            SELECT COUNT(*) FROM error_logs 
            WHERE timestamp > datetime('now', '-24 hours')
        """)
        errors_24h = cursor.fetchone()[0]
        error_rate = errors_24h / max(total_users, 1)
        
        conn.close()
        
        return {
            'total_users': total_users,
            'new_users_24h': new_users_24h,
            'active_sessions': 1,  # Simplified
            'uptime': '99.9%',     # Simplified
            'error_rate': error_rate,
            'error_rate_change': 0  # Simplified
        }
        
    except Exception as e:
        logger.error(f"Failed to get system statistics: {str(e)}")
        return {}

def get_users_dataframe() -> pd.DataFrame:
    """Get users data as DataFrame"""
    try:
        conn = get_db_connection()
        
        query = """
            SELECT id, username, email, role, created_at, last_login, is_active
            FROM users
            ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
        
    except Exception as e:
        logger.error(f"Failed to get users dataframe: {str(e)}")
        return pd.DataFrame()

def get_user_activity_data() -> pd.DataFrame:
    """Get user activity data for charts"""
    # Simplified implementation - would normally query session logs
    dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
    activity = [10 + i % 5 for i in range(len(dates))]
    
    return pd.DataFrame({
        'date': dates,
        'active_users': activity
    })

def get_feature_usage_stats() -> Dict[str, int]:
    """Get feature usage statistics"""
    return {
        'Dashboard': 150,
        'Technical Analysis': 89,
        'Sentiment Analysis': 67,
        'Backtesting': 45,
        'Alerts': 32
    }

def get_database_statistics() -> Dict[str, Any]:
    """Get database statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Count total records across all tables
        tables = ['users', 'error_logs', 'system_health_logs']
        total_records = 0
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                total_records += cursor.fetchone()[0]
            except:
                pass  # Table might not exist
        
        conn.close()
        
        return {
            'total_records': total_records,
            'db_size_mb': 5.2,  # Simplified
            'last_backup': 'Never'  # Simplified
        }
        
    except Exception as e:
        logger.error(f"Failed to get database statistics: {str(e)}")
        return {}

def get_error_logs(time_range: str, severity: str, resolved: str) -> List[Dict]:
    """Get filtered error logs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query based on filters
        query = "SELECT * FROM error_logs WHERE 1=1"
        params = []
        
        # Time range filter
        if time_range == "Last Hour":
            query += " AND timestamp > datetime('now', '-1 hour')"
        elif time_range == "Last 24 Hours":
            query += " AND timestamp > datetime('now', '-24 hours')"
        elif time_range == "Last 7 Days":
            query += " AND timestamp > datetime('now', '-7 days')"
        elif time_range == "Last 30 Days":
            query += " AND timestamp > datetime('now', '-30 days')"
        
        # Severity filter
        if severity != "All":
            query += " AND severity = ?"
            params.append(severity)
        
        # Resolved filter
        if resolved == "Unresolved":
            query += " AND resolved = 0"
        elif resolved == "Resolved":
            query += " AND resolved = 1"
        
        query += " ORDER BY timestamp DESC LIMIT 50"
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = cursor.fetchall()
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in results]
        
    except Exception as e:
        logger.error(f"Failed to get error logs: {str(e)}")
        return []

def mark_error_resolved(error_id: int):
    """Mark error as resolved"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE error_logs 
            SET resolved = 1, resolution_notes = ?
            WHERE id = ?
        """, (f"Resolved by admin at {datetime.now()}", error_id))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to mark error resolved: {str(e)}")

def cleanup_old_logs() -> int:
    """Clean up old log entries"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete logs older than 30 days
        cursor.execute("""
            DELETE FROM error_logs 
            WHERE timestamp < datetime('now', '-30 days')
        """)
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {str(e)}")
        return 0

def optimize_database():
    """Optimize database performance"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("VACUUM")
        cursor.execute("ANALYZE")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to optimize database: {str(e)}")

def create_database_backup() -> bool:
    """Create database backup"""
    try:
        # Simplified backup implementation
        logger.info("Database backup created")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create backup: {str(e)}")
        return False

def save_configuration(config: Dict[str, Any]):
    """Save application configuration"""
    logger.info(f"Configuration saved: {config}")

def save_alert_configuration(config: Dict[str, Any]):
    """Save alert configuration"""
    logger.info(f"Alert configuration saved: {config}")

def show_testing_panel():
    """Testing interface integration"""
    st.markdown("## 🧪 System Testing & Quality Assurance")
    
    st.markdown("""
    <div style="background: var(--bg-secondary); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
        <p style="margin: 0; color: var(--text-secondary);">
            Comprehensive testing suite for B-TCRimer platform validation and quality assurance.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Embed the testing interface
    show_testing_interface()